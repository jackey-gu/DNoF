import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.markers import MarkerStyle  # 引入 MarkerStyle 用于不同的标记点
import os

# ==================== 配置路径 ====================
# 输入 CSV 文件
CPU_csv_file = r"c:/Users/jackey_gu/Desktop/脚本/DPIO/DPIO testjob/CPU_fio_variable_benchmark/CPUfio_results_summary_enhanced.csv"
DPU_csv_file = r"c:/Users/jackey_gu/Desktop/脚本/DPIO/DPIO testjob/DPU_fio_variable_benchmark/DPUfio_results_summary_enhanced.csv"

# 输出目录
output_dir = r"c:/Users/jackey_gu/Desktop/脚本/DPIO/DPIO testjob/CPU_fio_variable_benchmark/CPUDPUfio_plots_comparison"
os.makedirs(output_dir, exist_ok=True)


# ==================== 读取并标记数据源 ====================
def load_data(csv_path, label):
    df = pd.read_csv(csv_path)
    df["source"] = label  # 添加来源标记
    return df

df_cpu = load_data(CPU_csv_file, "CPU")
df_dpu = load_data(DPU_csv_file, "DPU")
df_combined = pd.concat([df_cpu, df_dpu], ignore_index=True)

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
    "nbcpu-bw": "cpus_allowed"  # ← 原始脚本就是这样用的，没问题
}

# 修改：移除了 'cpu_total'，只保留 usr 和 sys
metrics = {
    "CPU Utilization": {  # 更名以更准确反映内容
        "y_cols": ["cpu_usr", "cpu_sys"],  # 只保留 User 和 System
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
colors = plt.cm.tab10.colors
markers = {"CPU": "o", "DPU": "x"}
linestyles = {"randread": "--", "randwrite": "-"}

# ==================== 保存函数 ====================
def save_plot(fig, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

# ==================== 通用对比绘图函数（按 rw_mode + User/System 分配独立颜色）====================
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

    fig, ax = plt.subplots(figsize=(10, 6))

    # === 关键修改：为每个 (rw_mode, component) 创建唯一组合 ===
    # component: 'User' or 'System'
    combinations = set()
    for _, row in df_test.iterrows():
        rw_mode = row["rw_mode"]
        # 只处理 CPU Utilization 的 User/System
        if metric_name == "CPU Utilization":
            combinations.add((rw_mode, "User"))
            combinations.add((rw_mode, "System"))
        else:
            combinations.add((rw_mode, None))  # 其他指标不区分 User/System

    # 按 rw_mode 排序，确保颜色顺序一致
    sorted_combinations = sorted(combinations, key=lambda x: (x[0], x[1] or ""))

    # 为每个组合分配唯一颜色
    color_map = {}
    for i, (rw_mode, comp) in enumerate(sorted_combinations):
        color_map[(rw_mode, comp)] = colors[i % len(colors)]

    # === 开始绘图 ===
    for source in ["CPU", "DPU"]:
        df_src = df_test[df_test["source"] == source]  # ✅ 修复：使用 df_test
        marker = markers[source]

        for rw_mode in sorted(df_src["rw_mode"].unique()):
            df_mode = df_src[df_src["rw_mode"] == rw_mode]
            if df_mode.empty:
                continue

            if metric_name == "CPU Utilization":
                # === 分别绘制 User 和 System，各自用独立颜色 ===
                # User
                if "cpu_usr" in df_mode.columns and not df_mode["cpu_usr"].dropna().empty:
                    color = color_map[(rw_mode, "User")]
                    ax.plot(
                        df_mode[x_field], df_mode["cpu_usr"],
                        marker=marker, linestyle="-", color=color,
                        label=f"{source}-{rw_mode} - User",
                        markersize=6, linewidth=1.5
                    )
                # System
                if "cpu_sys" in df_mode.columns and not df_mode["cpu_sys"].dropna().empty:
                    color = color_map[(rw_mode, "System")]
                    ax.plot(
                        df_mode[x_field], df_mode["cpu_sys"],
                        marker=marker, linestyle="--", color=color,
                        label=f"{source}-{rw_mode} - System",
                        markersize=6, linewidth=1.5, alpha=0.9
                    )
            else:
                # 其他指标：IOPS/Bandwidth/Latency
                if rw_mode in ['read', 'randread']:
                    y_col = y_cols[0]
                elif rw_mode in ['write', 'randwrite']:
                    y_col = y_cols[1]
                else:
                    continue

                color = color_map.get((rw_mode, None), colors[0])
                ax.plot(
                    df_mode[x_field], df_mode[y_col],
                    marker=marker, linestyle=linestyles.get(rw_mode, "-"),
                    color=color, label=f"{source}-{rw_mode}",
                    markersize=6, linewidth=1.5
                )

    ax.set_title(f"{metric_name} vs {test_type} (CPU vs DPU)", fontsize=14)
    ax.set_xlabel(test_type, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    # 图例
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles=handles, labels=labels, bbox_to_anchor=(1.05, 1), loc='upper left')

    fig.tight_layout()

    # 保存
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