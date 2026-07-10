import pandas as pd
import matplotlib.pyplot as plt
import os

# ==================== 配置 ====================
csv_file = r"c:/Users/jackey_gu/Desktop/脚本/DPIO/DPIO testjob/DPU_fio_variable_benchmark/only_DPUfio_results_summary_enhanced.csv"
output_dir = r"c:/Users/jackey_gu/Desktop/脚本/DPIO/DPIO testjob/DPU_fio_variable_benchmark/only_fio_plots_enhanced"

# 创建输出目录
os.makedirs(output_dir, exist_ok=True)

# 读取数据
df = pd.read_csv(csv_file)
print(f"📊 数据加载完成，共 {len(df)} 行")

# 设置风格
plt.style.use("ggplot")
colors = plt.cm.tab10.colors

# ==================== 辅助函数：从 cpus_allowed 提取核数 ====================
def extract_numeric_cpus(val):
    """将 '1', '1-4', '1,2,3' 转为数字数量"""
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

# ==================== 测试类型与 X 轴字段映射 ====================
# ✅ 修改：移除旧的 "rwmixwrite"，新增三种独立场景
test_types = {
    "bs": "bs",
    "rwmixwrite-4k-32": "rwmixwrite",   # 使用 rwmixwrite 字段作为 X 轴
    "rwmixwrite-4k-8": "rwmixwrite",
    "rwmixwrite-64k": "rwmixwrite",
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
# ✅ 修改：为三种 rwmixwrite 场景提供清晰标题
title_map = {
    "nbcpu": "Number of CPUs",
    "nbcpu-bw": "Number of CPUs (Bandwidth Mode)",
    "numjobs": "Number of Jobs",
    "numjobs-bw": "Number of Jobs (Bandwidth Mode)",
    "bs": "Block Size",
    "iodepth": "IO Depth",
    # ✅ 为三种 rwmixwrite 场景设置独立标题
    "rwmixwrite-4k-32": "Write Ratio (4K, iodepth=32)",
    "rwmixwrite-4k-8": "Write Ratio (4K, iodepth=8)",
    "rwmixwrite-64k": "Write Ratio (64K, iodepth=32)",
}

# ==================== 通用绘图函数 ====================
def plot_metric(df, test_type, x_field, metric_name, y_cols, ylabel):
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

    # 特殊处理 rwmixwrite 类型（包括 -4k-32, -4k-8, -64k）
    if "rwmixwrite" in test_type:  # 匹配所有包含 rwmixwrite 的类型
        x_labels = df_test[x_field].astype(str).values
        ax.plot(x_labels, df_test['read_iops'], label='Read', color=colors[0], marker='o', markersize=4)
        ax.plot(x_labels, df_test['write_iops'], label='Write', color=colors[1], marker='s', markersize=4)
    else:
        for i, rw_mode in enumerate(sorted(df_test["rw_mode"].unique())):
            df_mode = df_test[df_test["rw_mode"] == rw_mode].copy()
            df_mode.sort_values('sort_key', inplace=True)
            color = colors[i % len(colors)]

            if metric_name == "CPU Total":
                ax.plot(df_mode[x_field], df_mode["cpu_usr"], label=f"{rw_mode}-User", color=color, linestyle=":", marker='o')
                ax.plot(df_mode[x_field], df_mode["cpu_sys"], label=f"{rw_mode}-System", color=color, linestyle="--", marker='s')
                ax.plot(df_mode[x_field], df_mode["cpu_total"], label=f"{rw_mode}-Total", color=color, linestyle="-", marker='^')
            else:
                read_col, write_col = y_cols
                if rw_mode in ['read', 'randread']:
                    ax.plot(df_mode[x_field], df_mode[read_col], label=rw_mode, color=color, marker='o', markersize=4)
                elif rw_mode in ['write', 'randwrite']:
                    ax.plot(df_mode[x_field], df_mode[write_col], label=rw_mode, color=color, marker='s', markersize=4)
                elif rw_mode == 'unknown':
                    ax.plot(df_mode[x_field], df_mode[read_col], label="randrw-Read", color=color, linestyle="--", marker='^')
                    ax.plot(df_mode[x_field], df_mode[write_col], label="randrw-Write", color=color, linestyle="-", marker='v')

    # 设置标题和标签
    xlabel = title_map.get(test_type, test_type.replace('_', ' ').title())
    ax.set_title(f"{metric_name} vs {xlabel}")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis='x', rotation=45)
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    # 🔽 保存为独立 PDF 文件 🔽
    metric_dir = os.path.join(output_dir, metric_name.lower().replace(" ", "_"))
    os.makedirs(metric_dir, exist_ok=True)
    pdf_path = os.path.join(metric_dir, f"{metric_name.replace(' ', '_')}_vs_{test_type}.pdf")
    fig.savefig(pdf_path, bbox_inches='tight', format='pdf')  # 只保存 PDF
    plt.close(fig)

    print(f"📄 保存 PDF: {pdf_path}")
    return pdf_path  # 返回文件路径

# ==================== 主执行流程 ====================
total_plots = 0
for metric_name, metric_info in metrics.items():
    for test_type, x_field in test_types.items():
        result = plot_metric(df, test_type, x_field, metric_name, metric_info["y_cols"], metric_info["ylabel"])
        if result:
            total_plots += 1

print(f"\n✅ 所有图表生成完成！")
print(f"📄 每张图已单独保存为 PDF")
print(f"📁 输出目录: {output_dir}")
print(f"📈 共生成 {total_plots} 个 PDF 文件")