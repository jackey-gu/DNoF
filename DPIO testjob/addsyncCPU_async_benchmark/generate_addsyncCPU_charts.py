#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import os

# ==================== 配置 ====================

# 读取我们汇总脚本生成的 CSV
csv_file = r"c:/Users/jackey_gu/Desktop/脚本/DPIO/DPIO testjob/addsyncCPU_async_benchmark/CPU_results_summary.csv"
df = pd.read_csv(csv_file)

# 输出目录
output_dir = r"c:/Users/jackey_gu/Desktop/脚本/DPIO/DPIO testjob/addsyncCPU_async_benchmark/fio_plots_enhanced"
os.makedirs(output_dir, exist_ok=True)

# 设置绘图风格
plt.style.use("ggplot")
colors = plt.cm.tab10.colors

# 预定义排序顺序（确保图表 x 轴有序）
test_order = {
    "mixed": [str(i) for i in range(0, 17)],  # sync_jobs: 0,1,2,... (mixed 中 sync_jobs=0,1,2,3,4)
    "sync1_asyncN": [str(i) for i in range(0, 17)],  # async_jobs = 0~16
    "async1_syncN": [str(i) for i in range(0, 17)],  # sync_jobs = 0~16
}

# ==================== 辅助函数 ====================
def save_plot(fig, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

# ==================== 指标映射 ====================
metrics = {
    "IOPS": {
        "y_cols": ["read_iops", "write_iops"],
        "ylabel": "Total IOPS",
        "agg": "sum"
    },
    "Bandwidth": {
        "y_cols": ["read_bw", "write_bw"],
        "ylabel": "Bandwidth (MB/s)",
        "agg": "sum"
    },
    "Latency Mean": {
        "y_cols": ["read_lat_mean", "write_lat_mean"],
        "ylabel": "Latency Mean (μs)",
        "agg": "mean"
    },
    "Latency P99": {
        "y_cols": ["read_lat_99", "write_lat_99"],
        "ylabel": "Latency P99 (μs)",
        "agg": "mean"
    },
    "CPU Utilization": {
        "y_cols": ["cpu_usr", "cpu_sys"],
        "ylabel": "CPU Utilization (%)",
        "agg": "sum"
    }
}

# ==================== 通用绘图函数（聚合版） ====================
def plot_metric_by_test_type(df, test_type_key):
    df_test = df[df["test_type"] == test_type_key].copy()
    if df_test.empty:
        print(f"⚠️ 无数据用于测试类型: {test_type_key}")
        return

    # 确定 x 轴字段
    if test_type_key == "mixed":
        x_field = "sync_jobs"
        x_label = "Sync Jobs"
    elif test_type_key == "sync1_asyncN":
        x_field = "async_jobs"
        x_label = "Async Jobs"
    elif test_type_key == "async1_syncN":
        x_field = "sync_jobs"
        x_label = "Sync Jobs"
    else:
        return

    # 转换为数值型，便于排序
    df_test[x_field] = pd.to_numeric(df_test[x_field], errors='coerce')

    # === ✅ 关键：按 filename + rw_mode + jobtype 聚合 ===
    # 先定义聚合规则
    agg_rules = {}
    for metric_name, metric_info in metrics.items():
        for col in metric_info["y_cols"]:
            if metric_info["agg"] == "sum":
                agg_rules[col] = "sum"
            elif metric_info["agg"] == "mean":
                agg_rules[col] = "mean"

    # 分组字段
    group_cols = ['filename', 'rw_mode', 'jobtype', x_field]
    df_agg = df_test.groupby(group_cols, as_index=False).agg(agg_rules)

    # 排序：按 x_field 数值排序
    df_agg = df_agg.sort_values(x_field)

    # === 拆分：顺序 vs 随机 ===
    for metric_name, metric_info in metrics.items():
        y_cols = metric_info["y_cols"]
        ylabel = metric_info["ylabel"]

        for mode_group, modes, prefix in [
            (['read', 'write'], ['read', 'write'], 'seq'),
            (['randread', 'randwrite'], ['randread', 'randwrite'], 'rand')
        ]:
            df_group = df_agg[df_agg["rw_mode"].isin(mode_group)]
            if df_group.empty:
                continue

            fig, ax = plt.subplots(figsize=(10, 6))

            for rw_mode in modes:
                df_mode = df_group[df_group["rw_mode"] == rw_mode]
                for jobtype in ['sync', 'async']:
                    df_job = df_mode[df_mode["jobtype"] == jobtype]
                    if df_job.empty:
                        continue

                    color_idx = ['sync', 'async'].index(jobtype) + 2 * list(modes).index(rw_mode)
                    color = colors[color_idx % len(colors)]
                    label = f"{rw_mode} ({jobtype})"

                    if metric_name == "CPU Utilization":
                        ax.plot(df_job[x_field], df_job["cpu_usr"], label=f"{label} - User", color=color, linestyle=":")
                        ax.plot(df_job[x_field], df_job["cpu_sys"], label=f"{label} - System", color=color, linestyle="--")
                    else:
                        read_col, write_col = y_cols
                        data_col = read_col if rw_mode in ['read', 'randread'] else write_col
                        linestyle = "--" if rw_mode in ['read', 'randread'] else "-"
                        ax.plot(df_job[x_field], df_job[data_col], label=label, color=color, linestyle=linestyle)

            ax.set_title(f"{metric_name} vs {x_label} ({test_type_key}) - {prefix.upper()}", fontsize=14)
            ax.set_xlabel(x_label, fontsize=12)
            ax.set_ylabel(ylabel, fontsize=12)
            ax.grid(True, which='both', linestyle='--', linewidth=0.5)
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

            fig.tight_layout()

            # 输出路径
            metric_dir = os.path.join(output_dir, metric_name.lower().replace(" ", "_"))
            os.makedirs(metric_dir, exist_ok=True)
            output_path = os.path.join(
                metric_dir,
                f"{prefix}_{metric_name.replace(' ', '_')}_vs_{test_type_key}.png"
            )
            save_plot(fig, output_path)

# ==================== 执行绘图 ====================
test_types_to_plot = ["mixed", "sync1_asyncN", "async1_syncN"]

for test_type in test_types_to_plot:
    plot_metric_by_test_type(df, test_type)

print(f"✅ 所有图表已保存至目录：{output_dir}")