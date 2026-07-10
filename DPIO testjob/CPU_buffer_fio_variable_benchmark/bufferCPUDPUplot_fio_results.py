import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.markers import MarkerStyle
import os

# ==================== 配置路径 ====================
# 输入 CSV 文件（四个测试）
CPU_DIRECT_csv = r"c:/Users/jackey_gu/Desktop/脚本/DPIO/DPIO testjob/CPU_fio_variable_benchmark/CPUfio_results_summary_enhanced.csv"
DPU_DIRECT_csv = r"c:/Users/jackey_gu/Desktop/脚本/DPIO/DPIO testjob/DPU_fio_variable_benchmark/DPUfio_results_summary_enhanced.csv"
CPU_BUFFER_csv = r"C:\Users\jackey_gu\Desktop\脚本\DPIO\DPIO testjob\CPU_buffer_fio_variable_benchmark\CPUbufferfio_results_summary_enhanced.csv"
DPU_BUFFER_csv = r"C:\Users\jackey_gu\Desktop\脚本\DPIO\DPIO testjob\DPU_buffer_fio_variable_benchmark\DPUbufferfio_results_summary_enhanced.csv"

# 输出目录
output_dir = r"c:/Users/jackey_gu/Desktop/脚本/DPIO/DPIO testjob/CPU_buffer_fio_variable_benchmark/bufferCPUDPUfio_plots_comparison_all4"
os.makedirs(output_dir, exist_ok=True)

# ==================== 读取并标记数据源 ====================
def load_data(csv_path, label):
    df = pd.read_csv(csv_path)
    df["source"] = label  # 添加来源标记
    return df

df_cpu_direct = load_data(CPU_DIRECT_csv, "CPU-Direct")
df_dpu_direct = load_data(DPU_DIRECT_csv, "DPU-Direct")
df_cpu_buffer = load_data(CPU_BUFFER_csv, "CPU-Buffered")
df_dpu_buffer = load_data(DPU_BUFFER_csv, "DPU-Buffered")

# 合并所有数据
df_combined = pd.concat([df_cpu_direct, df_dpu_direct, df_cpu_buffer, df_dpu_buffer], ignore_index=True)

# ==================== 测试配置（完全复用原脚本）====================
test_order = {
    "bs": ["4k", "8k", "16k", "32k", "64k", "128k"],
    "rwmixwrite": ["0", "25", "50", "75", "100"],
    "numjobs": [str(i) for i in range(1, 17)],
    "nbcpu": [str(i) for i in range(1, 17)],
    "iodepth": ["1", "2", "4", "8", "16", "32", "64", "128"],
    "numjobs-bw": [str(i) for i in range(1, 17)],
    "nbcpu-bw": [str(i) for i in range(1, 17)],
}

test_types = {
    "bs": "bs",
    "rwmixwrite": "rwmixwrite",
    "numjobs": "numjobs",
    "nbcpu": "cpus_allowed",
    "iodepth": "iodepth",
    "numjobs-bw": "numjobs",
    "nbcpu-bw": "cpus_allowed"
}

# 修改：移除了 'cpu_total'，只保留 usr 和 sys
metrics = {
    "CPU Utilization": {
        "y_cols": ["cpu_usr", "cpu_sys"],
        "ylabel": "CPU Utilization (%)"
    },
    "IOPS": {
        "y_cols": ["read_iops", "write_iops"],
        "ylabel": "IOPS (K)"
    },
    "Bandwidth": {
        "y_cols": ["read_bw_Mb", "write_bw_Mb"],
        "ylabel": "Bandwidth (MB/s)"
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

# 为四个 source 定义不同的标记（markers）和颜色（colors）
sources = ["CPU-Direct", "DPU-Direct", "CPU-Buffered", "DPU-Buffered"]
markers = {
    "CPU-Direct": "o",      # 圆圈
    "DPU-Direct": "x",      # 叉号
    "CPU-Buffered": "s",    # 方块
    "DPU-Buffered": "^",    # 三角
}

# 使用不同颜色区分 rw_mode
colors = plt.cm.Set1.colors  # 更多颜色，适合多类别
linestyles = {"randread": "-", "randwrite": "--", "read": "-", "write": "--"}

# ==================== 保存函数 ====================
def save_plot(fig, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # 修改：替换扩展名为 .pdf，并设置 bbox_inches 和 dpi
    pdf_output_path = output_path.replace(".png", ".pdf")
    fig.savefig(pdf_output_path, format='pdf', bbox_inches='tight')
    plt.close(fig)

# ==================== 通用对比绘图函数（支持四种 source）====================
def plot_metric_combined(df, test_type, x_field, metric_name, y_cols, ylabel):
    df_test = df[df["test_type"] == test_type].copy()
    if df_test.empty:
        print(f"⚠️ 无数据: test_type={test_type}")
        return

    # 强制转换 x 轴字段为字符串
    df_test[x_field] = df_test[x_field].astype(str)

    # 按预定义顺序排序
    order_list = test_order.get(test_type, [])
    if order_list:
        df_test['order'] = pd.Categorical(df_test[x_field], categories=order_list, ordered=True)
        df_test = df_test.sort_values('order')
        df_test.drop('order', axis=1, inplace=True)

    fig, ax = plt.subplots(figsize=(12, 7))

    # 按 rw_mode 分配颜色（不同 rw_mode 不同颜色）
    unique_rw_modes = sorted(df_test["rw_mode"].unique())
    color_map = {}
    for i, rw_mode in enumerate(unique_rw_modes):
        color_map[rw_mode] = colors[i % len(colors)]

    # 绘图：遍历每个 source 和每个 rw_mode
    for source in sources:
        df_src = df_test[df_test["source"] == source]
        marker = markers[source]

        for rw_mode in unique_rw_modes:
            df_mode = df_src[df_src["rw_mode"] == rw_mode]
            if df_mode.empty:
                continue

            color = color_map[rw_mode]

            if metric_name == "CPU Utilization":
                # User: 实线，System: 虚线，同色
                ax.plot(
                    df_mode[x_field], df_mode["cpu_usr"],
                    marker=marker, linestyle="-", color=color,
                    label=f"{source}-{rw_mode} - User",
                    markersize=6, linewidth=1.5
                )
                ax.plot(
                    df_mode[x_field], df_mode["cpu_sys"],
                    marker=marker, linestyle="--", color=color,
                    label=f"{source}-{rw_mode} - System",
                    markersize=6, linewidth=1.5, alpha=0.8
                )
            else:
                # IOPS/Bandwidth/Latency
                if rw_mode in ['read', 'randread']:
                    y_col = y_cols[0]
                elif rw_mode in ['write', 'randwrite']:
                    y_col = y_cols[1]
                else:
                    continue

                ax.plot(
                    df_mode[x_field], df_mode[y_col],
                    marker=marker, linestyle=linestyles.get(rw_mode, "-"),
                    color=color, label=f"{source}-{rw_mode}",
                    markersize=6, linewidth=1.5
                )

    ax.set_title(f"{metric_name} vs {test_type} (CPU vs DPU, Direct vs Buffered)", fontsize=14)
    ax.set_xlabel(test_type, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    # 图例：自动换行，避免遮挡
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9, ncol=1)

    fig.tight_layout()

    # 保存
    metric_dir = os.path.join(output_dir, metric_name.lower().replace(" ", "_"))
    os.makedirs(metric_dir, exist_ok=True)
    output_path = os.path.join(metric_dir, f"{metric_name.replace(' ', '_')}_vs_{test_type}_all4.png")
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

print(f"✅ 所有四组对比图表已保存至目录：{output_dir}")