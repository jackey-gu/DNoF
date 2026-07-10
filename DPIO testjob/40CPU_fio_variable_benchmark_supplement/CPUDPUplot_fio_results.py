import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.markers import MarkerStyle
import os

# ==================== 配置路径 ====================
CPU_csv_file = r"C:\Users\jackey_gu\Desktop\脚本\DPIO\DPIO testjob\40CPU_fio_variable_benchmark_supplement\40CPUsupplement_summary.csv"
DPU_csv_file = r"C:\Users\jackey_gu\Desktop\脚本\DPIO\DPIO testjob\40DPU_fio_variable_benchmark_supplement\40DPUsupplement_summary.csv"

output_dir = r"C:\Users\jackey_gu\Desktop\脚本\DPIO\DPIO testjob\40CPU_fio_variable_benchmark_supplement\comparison_plots"
os.makedirs(output_dir, exist_ok=True)

# ==================== 读取并标记数据源 ====================
def load_data(csv_path, label):
    df = pd.read_csv(csv_path)
    df["source"] = label
    return df

df_cpu = load_data(CPU_csv_file, "CPU")
df_dpu = load_data(DPU_csv_file, "DPU")
df_combined = pd.concat([df_cpu, df_dpu], ignore_index=True)

# ==================== 测试配置（适配 1~40）====================
test_order = {
    "bs": ["4k", "8k", "16k", "32k", "64k", "128k"],
    "rwmixwrite": ["0", "25", "50", "75", "100"],
    "numjobs": [str(i) for i in range(1, 41)],
    "nbcpu": [str(i) for i in range(1, 41)],
    "iodepth": ["1", "2", "4", "8", "16", "32", "64", "128"],
    "numjobs-bw": [str(i) for i in range(1, 41)],
    "nbcpu-bw": [str(i) for i in range(1, 41)],
}

test_types = {
    "bs": "bs",
    "rwmixwrite": "rwmixwrite",
    "numjobs": "numjobs",
    "nbcpu": "nbcpu",              # ✅ 使用 nbcpu 字段
    "iodepth": "iodepth",
    "numjobs-bw": "numjobs",
    "nbcpu-bw": "nbcpu",           # ✅ 使用 nbcpu 字段
}

# ==================== 指标定义（字段名与 CSV 一致）====================
metrics = {
    "CPU Utilization": {
        "y_cols": ["cpu_usr", "cpu_sys"],
        "ylabel": "CPU Utilization (%)"
    },
    "IOPS": {
        "y_cols": ["read_iops_K", "write_iops_K"],
        "ylabel": "IOPS (K)"
    },
    "Bandwidth": {
        "y_cols": ["read_bw_MiB", "write_bw_MiB"],
        "ylabel": "Bandwidth (MiB/s)"
    },
    "Latency Mean": {
        "y_cols": ["read_lat_mean_us", "write_lat_mean_us"],
        "ylabel": "Latency Mean (μs)"
    },
    "Latency P99": {
        "y_cols": ["read_lat_p99_us", "write_lat_p99_us"],
        "ylabel": "Latency P99 (μs)"
    },
}

# ==================== 绘图样式 ====================
plt.style.use("ggplot")
colors = plt.cm.tab10.colors
markers = {"CPU": "o", "DPU": "x"}
linestyles = {"randread": "--", "randwrite": "-"}

# ==================== 保存函数 ====================
def save_plot(fig, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # 修改：替换扩展名为 .pdf，并设置 bbox_inches 和 dpi
    pdf_output_path = output_path.replace(".png", ".pdf")
    fig.savefig(pdf_output_path, format='pdf', bbox_inches='tight')
    plt.close(fig)

# ==================== 通用对比绘图函数 ====================
def plot_metric_combined(df, test_type, x_field, metric_name, y_cols, ylabel):
    df_test = df[df["test_type"] == test_type].copy()
    if df_test.empty:
        print(f"⚠️ 无数据: test_type={test_type}")
        return

    df_test[x_field] = df_test[x_field].astype(str)

    order_list = test_order.get(test_type, [])
    if order_list:
        df_test['order'] = pd.Categorical(df_test[x_field], categories=order_list, ordered=True)
        df_test = df_test.sort_values('order')
        df_test.drop('order', axis=1, inplace=True)

    fig, ax = plt.subplots(figsize=(10, 6))

    unique_rw_modes = sorted(df_test["rw_mode"].unique())
    color_map = {}
    for i, rw_mode in enumerate(unique_rw_modes):
        color_map[rw_mode] = colors[i % len(colors)]

    for source in ["CPU", "DPU"]:
        df_src = df_test[df_test["source"] == source]
        marker = markers[source]

        for rw_mode in unique_rw_modes:
            df_mode = df_src[df_src["rw_mode"] == rw_mode]
            if df_mode.empty:
                continue

            color = color_map[rw_mode]

            if metric_name == "CPU Utilization":
                ax.plot(df_mode[x_field], df_mode["cpu_usr"],
                        marker=marker, linestyle="-", color=color,
                        label=f"{source}-{rw_mode} - User", markersize=6, linewidth=1.5)
                ax.plot(df_mode[x_field], df_mode["cpu_sys"],
                        marker=marker, linestyle="--", color=color,
                        label=f"{source}-{rw_mode} - System", markersize=6, linewidth=1.5, alpha=0.8)
            else:
                if rw_mode in ['read', 'randread']:
                    y_col = y_cols[0]
                elif rw_mode in ['write', 'randwrite']:
                    y_col = y_cols[1]
                else:
                    continue

                ax.plot(df_mode[x_field], df_mode[y_col],
                        marker=marker, linestyle=linestyles.get(rw_mode, "-"),
                        color=color, label=f"{source}-{rw_mode}",
                        markersize=6, linewidth=1.5)

    ax.set_title(f"{metric_name} vs {test_type} (CPU vs DPU)", fontsize=14)
    ax.set_xlabel(test_type, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles=handles, labels=labels, bbox_to_anchor=(1.05, 1), loc='upper left')

    fig.tight_layout()

    metric_dir = os.path.join(output_dir, metric_name.lower().replace(" ", "_"))
    os.makedirs(metric_dir, exist_ok=True)
    output_path = os.path.join(metric_dir, f"{metric_name.replace(' ', '_')}_vs_{test_type}.png")
    save_plot(fig, output_path)

# ==================== 执行绘图 ====================
for metric_name, metric_info in metrics.items():
    for test_type, x_field in test_types.items():
        plot_metric_combined(
            df_combined,
            test_type,
            x_field,
            metric_name,
            metric_info["y_cols"],
            metric_info["ylabel"]
        )

print(f"✅ 所有对比图表已保存至目录：{output_dir}")