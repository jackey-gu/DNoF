import pandas as pd
import matplotlib.pyplot as plt
import os


# 读取新增数据
csv_file = r"C:\Users\jackey_gu\Desktop\脚本\DPIO\DPIO testjob\40DPU_fio_variable_benchmark_supplement\40DPUsupplement_summary.csv"
df = pd.read_csv(csv_file)

# 输出目录
output_dir = r"C:\Users\jackey_gu\Desktop\脚本\DPIO\DPIO testjob\40DPU_fio_variable_benchmark_supplement\fio_plots_supplement"
os.makedirs(output_dir, exist_ok=True)

# 设置绘图风格
plt.style.use("ggplot")
colors = plt.cm.tab10.colors

# 预定义顺序（与你的新测试脚本参数匹配）
# 更新为 1~40
test_order = {
    "numjobs": [str(i) for i in range(1, 41)],
    "nbcpu": [str(i) for i in range(1, 41)],
    "numjobs-bw": [str(i) for i in range(1, 41)],
    "nbcpu-bw": [str(i) for i in range(1, 41)],
}



# ==================== 辅助函数 ====================
def save_plot(fig, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)


# ==================== 测试类型 & 指标映射 ====================

# 如果你新增了 actual_cpus_count 字段
test_types = {
    "numjobs": "numjobs",
    "nbcpu": "nbcpu",           # ✅ 使用 nbcpu 字段
    "numjobs-bw": "numjobs",
    "nbcpu-bw": "nbcpu",        # ✅ 使用 nbcpu 字段
}

metrics = {
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
            if rw_mode in ['randread', 'read']:
                ax.plot(df_mode[x_field], df_mode[read_col], label=rw_mode, color=color, linestyle="--")
            elif rw_mode in ['randwrite', 'write']:
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
    output_path = os.path.join(metric_dir, f"{metric_name.replace(' ', '_')}_vs_{test_type}_supplement.png")
    save_plot(fig, output_path)


# ==================== 执行绘图 ====================

for metric_name, metric_info in metrics.items():
    for test_type, x_field in test_types.items():
        plot_metric(df, test_type, x_field, metric_name, metric_info["y_cols"], metric_info["ylabel"])

print(f"✅ 所有新增图表已保存至目录：{output_dir}")