import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.markers import MarkerStyle
import os

# ==================== 配置路径 ====================
CPU_csv_file = r"c:/Users/jackey_gu/Desktop/脚本/DPIO/DPIO testjob/CPU_fio_variable_benchmark/only_CPUfio_results_summary_enhanced.csv"
DPU_csv_file = r"c:/Users/jackey_gu/Desktop/脚本/DPIO/DPIO testjob/DPU_fio_variable_benchmark/only_DPUfio_results_summary_enhanced.csv"

output_dir = r"c:/Users/jackey_gu/Desktop/脚本/DPIO/DPIO testjob/CPU_fio_variable_benchmark/only_CPUDPUfio_plots_comparison"
os.makedirs(output_dir, exist_ok=True)

# ==================== 读取并标记数据源 ====================
def load_data(csv_path, label):
    df = pd.read_csv(csv_path)
    df["source"] = label
    return df

df_cpu = load_data(CPU_csv_file, "CPU")
df_dpu = load_data(DPU_csv_file, "DPU")
df_combined = pd.concat([df_cpu, df_dpu], ignore_index=True)

# ==================== 测试类型与 X 轴字段映射 ====================
test_types = {
    "bs": "bs",
    "rwmixwrite-4k-32": "rwmixwrite",
    "rwmixwrite-4k-8": "rwmixwrite",
    "rwmixwrite-64k": "rwmixwrite",
    "rwmixwrite-4k-128": "rwmixwrite",
    "rwmixwrite-4k-16": "rwmixwrite",
    "rwmixwrite-64k-8": "rwmixwrite",
    "numjobs": "numjobs",
    "nbcpu": "cpus_allowed",
    "iodepth": "iodepth",
    "numjobs-bw": "numjobs",
    "nbcpu-bw": "cpus_allowed",
}

# ==================== 指标定义 ====================
metrics = {
    "IOPS": {
        "y_cols": ["read_iops", "write_iops"],
        "ylabel": "IOPS (KIOPS)"
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
    "CPU Total": {
        "y_cols": ["cpu_usr", "cpu_sys", "cpu_total"],
        "ylabel": "CPU Utilization (%)"
    }
}

# ==================== 标题映射 ====================
title_map = {
    "nbcpu": "Number of CPUs",
    "nbcpu-bw": "Number of CPUs (Bandwidth Mode)",
    "numjobs": "Number of Jobs",
    "numjobs-bw": "Number of Jobs (Bandwidth Mode)",
    "bs": "Block Size",
    "iodepth": "IO Depth",
    "rwmixwrite-4k-32": "Write Ratio (4K, iodepth=32)",
    "rwmixwrite-4k-8": "Write Ratio (4K, iodepth=8)",
    "rwmixwrite-64k": "Write Ratio (64K, iodepth=32)",
    "rwmixwrite-4k-128": "Write Ratio (4K, iodepth=128)",
    "rwmixwrite-4k-16": "Write Ratio (4K, iodepth=16)",
    "rwmixwrite-64k-8": "Write Ratio (64K, iodepth=8)",
}

# ==================== 辅助函数：从 cpus_allowed 提取核数 ====================
def extract_numeric_cpus(val):
    if pd.isna(val) or val == "":
        return 1
    val = str(val).strip()
    if '-' in val:
        start, end = val.split('-')
        try:
            return int(end) - int(start) + 1
        except:
            return 1
    elif ',' in val:
        return len(val.split(','))
    else:
        try:
            return int(val)
        except:
            return 1

# ==================== 设置全局风格 ====================
plt.style.use("ggplot")
colors = plt.cm.tab10.colors  # 使用 tab10 调色板
markers = {"CPU": "o", "DPU": "x"}  # 保持原 marker
linestyles = {"read": "-", "write": "--"}  # 读实线，写虚线

# ==================== 通用对比绘图函数（风格统一版） ====================
def plot_metric_combined(df, test_type, x_field, metric_name, y_cols, ylabel):
    df_test = df[df["test_type"] == test_type].copy()
    if df_test.empty:
        print(f"⚠️ 跳过 {test_type}: 无数据")
        return None

    # 排序逻辑
    if test_type in ["nbcpu", "nbcpu-bw"]:
        df_test['sort_key'] = df_test[x_field].apply(extract_numeric_cpus)
    else:
        temp = df_test[x_field].astype(str)
        if test_type == "bs":
            temp = temp.str.replace('k', '000').str.replace('m', '000000')
        try:
            df_test['sort_key'] = pd.to_numeric(temp)
        except:
            df_test['sort_key'] = range(len(df_test))
    df_test.sort_values('sort_key', inplace=True)

    fig, ax = plt.subplots(figsize=(10, 6))

    # ==================== 特殊处理：所有 rwmixwrite-* 类型 ====================
    if "rwmixwrite" in test_type:
        # 使用前两个颜色：蓝色和橙色
        color_map = {"CPU": colors[0], "DPU": colors[1]}

        for source in ["CPU", "DPU"]:
            df_src = df_test[df_test["source"] == source]
            color = color_map[source]
            marker = markers[source]

            # CPU-Read
            ax.plot(
                df_src[x_field], df_src["read_iops"],
                label=f"{source}-Read", color=color, marker=marker,
                markersize=6, linewidth=1.5, linestyle="-"
            )
            # CPU-Write
            ax.plot(
                df_src[x_field], df_src["write_iops"],
                label=f"{source}-Write", color=color, marker=marker,
                markersize=6, linewidth=1.5, linestyle="--"
            )

    # ==================== 普通测试类型（如 bs, numjobs 等） ====================
    else:
        for source in ["CPU", "DPU"]:
            df_src = df_test[df_test["source"] == source]
            color = colors[0] if source == "CPU" else colors[1]
            marker = markers[source]

            for rw_mode in sorted(df_src["rw_mode"].unique()):
                df_mode = df_src[df_src["rw_mode"] == rw_mode].copy()
                df_mode.sort_values('sort_key', inplace=True)

                if metric_name == "CPU Total":
                    ax.plot(df_mode[x_field], df_mode["cpu_usr"],
                            label=f"{source}-{rw_mode}-User", color=color, linestyle=":", marker=marker)
                    ax.plot(df_mode[x_field], df_mode["cpu_sys"],
                            label=f"{source}-{rw_mode}-System", color=color, linestyle="--", marker=marker)
                    ax.plot(df_mode[x_field], df_mode["cpu_total"],
                            label=f"{source}-{rw_mode}-Total", color=color, linestyle="-", marker=marker)
                else:
                    read_col, write_col = y_cols
                    if rw_mode in ['read', 'randread']:
                        ax.plot(df_mode[x_field], df_mode[read_col],
                                label=f"{source}-{rw_mode}", color=color, marker=marker, markersize=6, linestyle="-")
                    elif rw_mode in ['write', 'randwrite']:
                        ax.plot(df_mode[x_field], df_mode[write_col],
                                label=f"{source}-{rw_mode}", color=color, marker=marker, markersize=6, linestyle="--")

    # 设置标题和标签
    xlabel = title_map.get(test_type, test_type.replace('_', ' ').title())
    ax.set_title(f"{metric_name} vs {xlabel}", fontsize=14)
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.tick_params(axis='x', rotation=45)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
    fig.tight_layout()

    # 保存为 PDF
    metric_dir = os.path.join(output_dir, metric_name.lower().replace(" ", "_"))
    os.makedirs(metric_dir, exist_ok=True)
    pdf_path = os.path.join(metric_dir, f"{metric_name.replace(' ', '_')}_vs_{test_type}.pdf")
    fig.savefig(pdf_path, bbox_inches='tight', format='pdf')
    plt.close(fig)

    print(f"📄 保存 PDF: {pdf_path}")
    return pdf_path

# ==================== 主执行流程 ====================
total_plots = 0
for metric_name, metric_info in metrics.items():
    for test_type, x_field in test_types.items():
        result = plot_metric_combined(df_combined, test_type, x_field, metric_name, metric_info["y_cols"], metric_info["ylabel"])
        if result:
            total_plots += 1

print(f"\n✅ 所有对比图表生成完成！")
print(f"📁 输出目录: {output_dir}")
print(f"📈 共生成 {total_plots} 个 PDF 文件")