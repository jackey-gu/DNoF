#!/usr/bin/env python3

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

# 读取数据
input_csv = "results_summary.csv"
df = pd.read_csv(input_csv)

# 创建输出目录
output_dir = "charts_all"
os.makedirs(output_dir, exist_ok=True)

# 设置绘图风格
sns.set(style="whitegrid")

# 添加测试组编号（用于 x 轴排序）
df['test_number'] = df['filename'].str.extract(r'_(sync\d+|async\d+|sync\d+_\d+)?')[0]

# 定义绘图函数：用于生成统一格式的图表
def plot_metric(data, x, y, hue, style, title, xlabel, ylabel, filename):
    plt.figure(figsize=(12, 6))
    plot = sns.lineplot(
        data=data,
        x=x,
        y=y,
        hue=hue,
        style=style,
        markers=True,
        dashes=False,
        palette="Set1"
    )
    plt.title(title, fontsize=14)
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename))
    plt.close()

# -------------------------------
# 图表 1：Read IOPS vs Async/Sync Jobs
# -------------------------------
plot_metric(
    data=df,
    x='test_number',
    y='read_iops',
    hue='jobtype',
    style='rw_mode',
    title="Read IOPS vs Async/Sync Job Count",
    xlabel="Test Group",
    ylabel="Read IOPS",
    filename="read_iops_comparison.png"
)

# -------------------------------
# 图表 2：Write IOPS vs Async/Sync Jobs
# -------------------------------
plot_metric(
    data=df,
    x='test_number',
    y='write_iops',
    hue='jobtype',
    style='rw_mode',
    title="Write IOPS vs Async/Sync Job Count",
    xlabel="Test Group",
    ylabel="Write IOPS",
    filename="write_iops_comparison.png"
)

# -------------------------------
# 图表 3：Read Latency (Mean) vs Async/Sync Jobs
# -------------------------------
plot_metric(
    data=df,
    x='test_number',
    y='read_lat_mean',
    hue='jobtype',
    style='rw_mode',
    title="Read Latency (Mean) vs Async/Sync Job Count",
    xlabel="Test Group",
    ylabel="Read Latency Mean (μs)",
    filename="read_latency_mean_comparison.png"
)

# -------------------------------
# 图表 4：Read Latency (99%) vs Async/Sync Jobs
# -------------------------------
plot_metric(
    data=df,
    x='test_number',
    y='read_lat_99',
    hue='jobtype',
    style='rw_mode',
    title="Read Latency (99%) vs Async/Sync Job Count",
    xlabel="Test Group",
    ylabel="Read Latency 99% (μs)",
    filename="read_latency_99_comparison.png"
)

# -------------------------------
# 图表 5：Write Latency (Mean) vs Async/Sync Jobs
# -------------------------------
plot_metric(
    data=df,
    x='test_number',
    y='write_lat_mean',
    hue='jobtype',
    style='rw_mode',
    title="Write Latency (Mean) vs Async/Sync Job Count",
    xlabel="Test Group",
    ylabel="Write Latency Mean (μs)",
    filename="write_latency_mean_comparison.png"
)

# -------------------------------
# 图表 6：Write Latency (99%) vs Async/Sync Jobs
# -------------------------------
plot_metric(
    data=df,
    x='test_number',
    y='write_lat_99',
    hue='jobtype',
    style='rw_mode',
    title="Write Latency (99%) vs Async/Sync Job Count",
    xlabel="Test Group",
    ylabel="Write Latency 99% (μs)",
    filename="write_latency_99_comparison.png"
)

# -------------------------------
# 图表 7：Read Bandwidth vs Async/Sync Jobs
# -------------------------------
plot_metric(
    data=df,
    x='test_number',
    y='read_bw',
    hue='jobtype',
    style='rw_mode',
    title="Read Bandwidth (MB/s) vs Async/Sync Job Count",
    xlabel="Test Group",
    ylabel="Read Bandwidth (MB/s)",
    filename="read_bw_comparison.png"
)

# -------------------------------
# 图表 8：Write Bandwidth vs Async/Sync Jobs
# -------------------------------
plot_metric(
    data=df,
    x='test_number',
    y='write_bw',
    hue='jobtype',
    style='rw_mode',
    title="Write Bandwidth (MB/s) vs Async/Sync Job Count",
    xlabel="Test Group",
    ylabel="Write Bandwidth (MB/s)",
    filename="write_bw_comparison.png"
)

# -------------------------------
# 图表 9：User CPU Usage vs Async/Sync Jobs
# -------------------------------
plot_metric(
    data=df,
    x='test_number',
    y='cpu_usr',
    hue='jobtype',
    style='rw_mode',
    title="User CPU Usage (%) vs Async/Sync Job Count",
    xlabel="Test Group",
    ylabel="User CPU Usage (%)",
    filename="cpu_usr_comparison.png"
)

# -------------------------------
# 图表 10：System CPU Usage vs Async/Sync Jobs
# -------------------------------
plot_metric(
    data=df,
    x='test_number',
    y='cpu_sys',
    hue='jobtype',
    style='rw_mode',
    title="System CPU Usage (%) vs Async/Sync Job Count",
    xlabel="Test Group",
    ylabel="System CPU Usage (%)",
    filename="cpu_sys_comparison.png"
)

# -------------------------------
# 图表 11：IOPS vs Latency (Mean) 散点图
# -------------------------------
plt.figure(figsize=(10, 6))
sns.scatterplot(
    data=df,
    x='read_iops',
    y='read_lat_mean',
    hue='jobtype',
    style='rw_mode',
    size='bs',
    sizes=(30, 200),
    alpha=0.8,
    label="Read"
)
sns.scatterplot(
    data=df,
    x='write_iops',
    y='write_lat_mean',
    hue='jobtype',
    style='rw_mode',
    size='bs',
    sizes=(30, 200),
    alpha=0.8,
    label="Write",
    marker='X'
)
plt.title("IOPS vs Latency (Mean)", fontsize=14)
plt.xlabel("IOPS", fontsize=12)
plt.ylabel("Latency Mean (μs)", fontsize=12)
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "iops_vs_latency_mean.png"))
plt.close()

print(f"✅ 所有图表已生成，共 11 张，保存在目录: {output_dir}")