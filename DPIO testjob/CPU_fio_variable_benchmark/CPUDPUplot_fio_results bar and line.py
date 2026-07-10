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
    "nbcpu-bw": "cpus_allowed"
}

# ==================== 定义使用柱状图的 test_types ====================
bar_test_types = {"bs", "iodepth", "rwmixwrite"}  # 这些用 bar 图

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


# ==================== 通用对比绘图函数（按 rw_mode 分配颜色，User/System 同色不同线型）====================
def plot_metric_combined(df, test_type, x_field, metric_name, y_cols, ylabel, rw_group_filter=None):
    """
    增强版绘图函数：支持按 test_type 自动选择柱状图或折线图，并支持 rw_mode 分组过滤。
    """
    df_test = df[df["test_type"] == test_type].copy()
    if df_test.empty:
        print(f"⚠️ 无数据: test_type={test_type}")
        return

    # === 根据 rw_group_filter 过滤数据 ===
    if rw_group_filter == "seq":
        df_test = df_test[df_test["rw_mode"].isin(["read", "write"])]
        suffix = "_readwrite"
    elif rw_group_filter == "rand":
        df_test = df_test[df_test["rw_mode"].isin(["randread", "randwrite"])]
        suffix = "_randreadrandwrite"
    else:
        suffix = ""

    if df_test.empty:
        print(f"⚠️ 无数据: test_type={test_type}, rw_group={rw_group_filter}")
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

    # 按 rw_mode 分配颜色
    unique_rw_modes = sorted(df_test["rw_mode"].unique())
    color_map = {}
    for i, rw_mode in enumerate(unique_rw_modes):
        color_map[rw_mode] = colors[i % len(colors)]

    width = 0.35  # 柱子宽度（用于 bar）
    n_sources = len(["CPU", "DPU"])
    n_rwmodes = len(unique_rw_modes)
    total_width_per_x = width * n_sources * n_rwmodes
    offset_step = total_width_per_x / (n_sources * n_rwmodes)

    use_bar = test_type in bar_test_types  # 判断是否使用柱状图

    # 所有 x 位置（字符串标签）
    x_labels = df_test[x_field].unique()
    x_positions = range(len(x_labels))
    x_mapping = {label: pos for pos, label in enumerate(x_labels)}
    df_test['x_pos'] = df_test[x_field].map(x_mapping)

    # 绘图主循环
    for source_idx, source in enumerate(["CPU", "DPU"]):
        df_src = df_test[df_test["source"] == source]
        marker = markers[source]

        for rw_mode_idx, rw_mode in enumerate(unique_rw_modes):
            df_mode = df_src[df_src["rw_mode"] == rw_mode]
            if df_mode.empty:
                continue

            color = color_map[rw_mode]
            label_suffix = f"{source}-{rw_mode}"

            # 计算偏移量（错开柱子）
            offset = (source_idx * n_rwmodes + rw_mode_idx) * offset_step - total_width_per_x / 2

            if use_bar:
                # ===== 柱状图模式 =====
                if metric_name == "CPU Utilization":
                    # User: 实心柱, System: 透明边框柱
                    x_pos = df_mode['x_pos'].values + offset
                    y_usr = df_mode["cpu_usr"].values
                    y_sys = df_mode["cpu_sys"].values

                    ax.bar(x_pos, y_usr,
                           width=width/n_rwmodes/2,
                           color=color, edgecolor='black', linewidth=0.8,
                           label=f"{label_suffix} - User",
                           alpha=0.9)

                    ax.bar(x_pos, y_sys,
                           width=width/n_rwmodes/2,
                           color='none', edgecolor=color, linewidth=1.5,
                           linestyle='--',
                           label=f"{label_suffix} - System",
                           alpha=0.7)

                else:
                    # IOPS/Bandwidth/Latency
                    x_pos = df_mode['x_pos'].values + offset
                    if rw_mode in ['read', 'randread']:
                        y_col = y_cols[0]
                    elif rw_mode in ['write', 'randwrite']:
                        y_col = y_cols[1]
                    else:
                        continue

                    y_vals = df_mode[y_col].values

                    ax.bar(x_pos, y_vals,
                           width=width/n_rwmodes,
                           color=color, edgecolor='black', linewidth=0.8,
                           label=label_suffix,
                           alpha=0.85)

            else:
                # ===== 折线图模式（原有逻辑）=====
                if metric_name == "CPU Utilization":
                    ax.plot(
                        df_mode[x_field], df_mode["cpu_usr"],
                        marker=marker, linestyle="-", color=color,
                        label=f"{label_suffix} - User",
                        markersize=6, linewidth=1.5
                    )
                    ax.plot(
                        df_mode[x_field], df_mode["cpu_sys"],
                        marker=marker, linestyle="--", color=color,
                        label=f"{label_suffix} - System",
                        markersize=6, linewidth=1.5, alpha=0.8
                    )
                else:
                    if rw_mode in ['read', 'randread']:
                        y_col = y_cols[0]
                    elif rw_mode in ['write', 'randwrite']:
                        y_col = y_cols[1]
                    else:
                        continue

                    ax.plot(
                        df_mode[x_field], df_mode[y_col],
                        marker=marker, linestyle=linestyles.get(rw_mode, "-"),
                        color=color, label=label_suffix,
                        markersize=6, linewidth=1.5
                    )

    # 设置标题和标签
    title_suffix_text = {"seq": " (Sequential)", "rand": " (Random)"}.get(rw_group_filter, "")
    ax.set_title(f"{metric_name} vs {test_type}{title_suffix_text}", fontsize=14)
    ax.set_xlabel(test_type, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    # x 轴刻度设置
    if use_bar:
        ax.set_xticks(range(len(x_labels)))
        ax.set_xticklabels(x_labels, rotation=0)

    # 图例
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles=handles, labels=labels, bbox_to_anchor=(1.05, 1), loc='upper left')

    fig.tight_layout()

    # 保存文件
    metric_dir = os.path.join(output_dir, metric_name.lower().replace(" ", "_"))
    os.makedirs(metric_dir, exist_ok=True)
    output_filename = f"{metric_name.replace(' ', '_')}_vs_{test_type}{suffix}.png"
    output_path = os.path.join(metric_dir, output_filename)
    save_plot(fig, output_path)


# ==================== 执行绘图（增强版：iodepth 拆分）====================
for metric_name, metric_info in metrics.items():
    for test_type, x_field in test_types.items():
        if test_type == "iodepth":
            # 分别绘制三类图
            plot_metric_combined(
                df_combined, test_type, x_field, metric_name,
                metric_info["y_cols"], metric_info["ylabel"],
                rw_group_filter=None   # 可选：保留原始合并图（或删除）
            )
            # ✅ 拆分图：顺序读写
            plot_metric_combined(
                df_combined, test_type, x_field, metric_name,
                metric_info["y_cols"], metric_info["ylabel"],
                rw_group_filter="seq"
            )
            # ✅ 拆分图：随机读写
            plot_metric_combined(
                df_combined, test_type, x_field, metric_name,
                metric_info["y_cols"], metric_info["ylabel"],
                rw_group_filter="rand"
            )
        else:
            # 其他 test_type 正常绘制
            plot_metric_combined(
                df_combined, test_type, x_field, metric_name,
                metric_info["y_cols"], metric_info["ylabel"],
                rw_group_filter=None  # 不过滤
            )

print(f"✅ 所有对比图表已保存至目录：{output_dir}")