import pandas as pd
import matplotlib.pyplot as plt
import os



# 读取数据
csv_file = r"c:/Users/jackey_gu/Desktop/脚本/DPIO/DPIO testjob/DPU_fio_variable_benchmark/DPUfio_results_summary_enhanced.csv"
df = pd.read_csv(csv_file)

# 输出目录
output_dir = r"c:/Users/jackey_gu/Desktop/脚本/DPIO/DPIO testjob/DPU_fio_variable_benchmark/fio_plots_enhanced"
os.makedirs(output_dir, exist_ok=True)

# 设置绘图风格
plt.style.use("ggplot")
colors = plt.cm.tab10.colors

test_order = {
    "bs": ["4k", "8k", "16k", "32k", "64k", "128k"],
    "rwmixwrite": ["0", "25", "50", "75", "100"],
    "numjobs": [str(i) for i in range(1, 17)],
    "nbcpu": [str(i) for i in range(1, 17)],
    "iodepth": ["1", "2", "4", "8", "16", "32", "64", "128"],
    "numjobs-bw": [str(i) for i in range(1, 17)],
    "nbcpu-bw": [str(i) for i in range(1, 17)],
}


# ==================== 辅助函数 ====================
def save_plot(fig, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)


# ==================== 测试类型 & 指标映射 ====================

test_types = {
    "bs": "bs",
    "rwmixwrite": "rwmixwrite",
    "numjobs": "numjobs",
    "nbcpu": "cpus_allowed",
    "iodepth": "iodepth",
    "numjobs-bw": "numjobs",
    "nbcpu-bw": "cpus_allowed"
}

metrics = {
    "IOPS": {
        "y_cols": ["read_iops", "write_iops"],
        "ylabel": "IOPS (K)"
    },
    "Bandwidth": {
        "y_cols": ["read_bw_Mb", "write_bw_Mb"],
        "ylabel": "Bandwidth (Mb/s)"
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

# ==================== 通用绘图函数 ====================

def plot_metric(df, test_type, x_field, metric_name, y_cols, ylabel):
    df_test = df[df["test_type"] == test_type].copy()
    if df_test.empty:
        return

    # 强制转换 x 轴字段为字符串，避免后续错误
    df_test[x_field] = df_test[x_field].astype(str)

    # 获取当前测试类型的预定义顺序
    order_list = test_order.get(test_type, [])

    # 根据预定义顺序对数据框进行排序
    if order_list:
        df_test['order'] = pd.Categorical(df_test[x_field], categories=order_list, ordered=True)
        df_test.sort_values('order', inplace=True)
        df_test.drop('order', axis=1, inplace=True)

    fig, ax = plt.subplots(figsize=(10, 6))

    for i, rw_mode in enumerate(df_test["rw_mode"].unique()):
        df_mode = df_test[df_test["rw_mode"] == rw_mode]
        color = colors[i % len(colors)]
        if metric_name == "CPU Total":
            ax.plot(df_mode[x_field], df_mode["cpu_usr"], label=f"{rw_mode} - User", color=color, linestyle=":")
            ax.plot(df_mode[x_field], df_mode["cpu_sys"], label=f"{rw_mode} - System", color=color, linestyle="--")
            ax.plot(df_mode[x_field], df_mode["cpu_total"], label=f"{rw_mode} - Total", color=color, linestyle="-")
        else:
            read_col, write_col = y_cols
            if rw_mode in ['read', 'randread']:
                ax.plot(df_mode[x_field], df_mode[read_col], label=rw_mode, color=color, linestyle="--")
            elif rw_mode in ['write', 'randwrite']:
                ax.plot(df_mode[x_field], df_mode[write_col], label=rw_mode, color=color, linestyle="-")

    ax.set_title(f"{metric_name} vs {test_type}", fontsize=14)
    ax.set_xlabel(test_type, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)

    handles, labels = ax.get_legend_handles_labels()
    if len(handles) > 0:
        ax.legend(handles=handles, labels=labels, bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)

    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    fig.tight_layout()

    metric_dir = os.path.join(output_dir, metric_name.lower().replace(" ", "_"))
    os.makedirs(metric_dir, exist_ok=True)
    output_path = os.path.join(metric_dir, f"{metric_name.replace(' ', '_')}_vs_{test_type}.png")
    save_plot(fig, output_path)


# ==================== 执行绘图 ====================

for metric_name, metric_info in metrics.items():
    for test_type, x_field in test_types.items():
        plot_metric(df, test_type, x_field, metric_name, metric_info["y_cols"], metric_info["ylabel"])

print(f"✅ 所有图表已保存至目录：{output_dir}")