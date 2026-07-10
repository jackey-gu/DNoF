import pandas as pd
import matplotlib.pyplot as plt
import os

# ================== 配置区 ==================
csv_file = r"C:\Users\jackey_gu\Desktop\脚本\DPIO\blkDPU\DPU_nvmeof_40DPUsupplement_summary.csv"
output_dir = r"C:\Users\jackey_gu\Desktop\脚本\DPIO\blkDPU\fio_results_nbcu_vs_numjobs\fio_plots_supplement"

# 创建输出目录
os.makedirs(output_dir, exist_ok=True)

# 设置绘图风格
plt.style.use("ggplot")
colors = plt.cm.tab10.colors  # 使用经典颜色集

# 预定义 numjobs 排序顺序：1 到 40
test_order = [str(i) for i in range(1, 41)]

# ================== 指标定义 ==================
metrics = {
    "IOPS": {
        "y_cols": ["read_iops_K", "write_iops_K"],
        "ylabel": "IOPS (K)"
    },
    "Bandwidth": {
        "y_cols": ["read_bw_MiB", "write_bw_MiB"],
        "ylabel": "Bandwidth (MiB/s)"
    },
    "Latency_Mean": {
        "y_cols": ["read_lat_mean_us", "write_lat_mean_us"],
        "ylabel": "Latency Mean (μs)"
    },
    "Latency_P99": {
        "y_cols": ["read_lat_p99_us", "write_lat_p99_us"],
        "ylabel": "Latency P99 (μs)"
    },
    "CPU_Total": {
        "y_cols": ["cpu_usr", "cpu_sys", "cpu_total"],
        "ylabel": "CPU Utilization (%)"
    }
}

# ================== 辅助函数 ==================
def save_plot(fig, output_path):
    """保存图为 PDF，并关闭 figure"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close(fig)

# ================== 绘图函数 ==================
def plot_metric(df, test_type_key, x_field, metric_name, y_cols, ylabel):
    """
    通用绘图函数
    :param df: 数据框
    :param test_type_key: 如 'nbcpu', 'nbcpu-bw'
    :param x_field: X 轴字段名（如 'numjobs'）
    :param metric_name: 指标名称
    :param y_cols: Y 轴列名列表
    :param ylabel: Y 轴标签
    """
    df_test = df[df["test_type"] == test_type_key].copy()
    if df_test.empty:
        print(f"⏭️ 无数据可绘: {test_type_key} - {metric_name}")
        return

    # 确保 x 轴字段为字符串用于排序
    df_test[x_field] = df_test[x_field].astype(str)

    # 按预定义顺序排序
    df_test['order'] = pd.Categorical(df_test[x_field], categories=test_order, ordered=True)
    df_test = df_test.sort_values('order')

    fig, ax = plt.subplots(figsize=(10, 6))

    for i, rw_mode in enumerate(df_test["rw_mode"].unique()):
        df_mode = df_test[df_test["rw_mode"] == rw_mode]
        color = colors[i % len(colors)]

        if metric_name == "CPU_Total":
            ax.plot(df_mode[x_field], df_mode["cpu_usr"], label=f"{rw_mode} - User", color=color, linestyle=":")
            ax.plot(df_mode[x_field], df_mode["cpu_sys"], label=f"{rw_mode} - System", color=color, linestyle="--")
            ax.plot(df_mode[x_field], df_mode["cpu_total"], label=f"{rw_mode} - Total", color=color, linestyle="-")
        else:
            read_col, write_col = y_cols
            if rw_mode in ['randread', 'read']:
                ax.plot(df_mode[x_field], df_mode[read_col], label=rw_mode, color=color, linestyle="--")
            elif rw_mode in ['randwrite', 'write']:
                ax.plot(df_mode[x_field], df_mode[write_col], label=rw_mode, color=color, linestyle="-")

    ax.set_title(f"{metric_name} vs {test_type_key}", fontsize=14)
    ax.set_xlabel("Number of Jobs", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    # 图例靠右外置
    handles, labels = ax.get_legend_handles_labels()
    if len(handles) > 0:
        ax.legend(handles=handles, labels=labels, bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)

    fig.tight_layout()

    # 输出路径：按指标分类 + PDF 格式
    metric_dir = os.path.join(output_dir, metric_name.lower().replace(" ", "_"))
    os.makedirs(metric_dir, exist_ok=True)
    output_path = os.path.join(metric_dir, f"{metric_name.replace(' ', '_')}_vs_{test_type_key}.pdf")
    save_plot(fig, output_path)

# ================== 主程序 ==================
if __name__ == "__main__":
    # 读取数据
    df = pd.read_csv(csv_file)

    # ✅ 修复：将 'numjobs' 改为 'nbcpu'，与实际 test_type 值一致
    test_types = {
        "nbcpu": "numjobs",       # 随机读写测试，X轴字段是 'numjobs'
        "nbcpu-bw": "numjobs"     # 顺序读写测试，X轴字段也是 'numjobs'
    }

    # 执行绘图
    for metric_name, metric_info in metrics.items():
        for test_type_key, x_field in test_types.items():
            plot_metric(df, test_type_key, x_field, metric_name, metric_info["y_cols"], metric_info["ylabel"])

    print(f"✅ 所有图表已生成并保存为 PDF, 输出目录: {output_dir}")