#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 blktrace_delays.csv 读取数据并绘图
仅执行绘图，不解析原始 blktrace
并且：正确交换 DNoF 和 CPU NVMe-oF 的标签
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# ----------------------------
# 配置参数
# ----------------------------
INPUT_CSV = "figures/blktrace_delays.csv"  # 输入 CSV 文件
OUTPUT_DIR = "figures"
Path(OUTPUT_DIR).mkdir(exist_ok=True)

# ----------------------------
# 加载数据
# ----------------------------
print(f"正在加载数据: {INPUT_CSV}")
try:
    df = pd.read_csv(INPUT_CSV)
except FileNotFoundError:
    raise FileNotFoundError(f"❌ 文件未找到: {INPUT_CSV}")

print(f"✅ 数据加载成功！共 {len(df)} 条记录")
print(f"原始包含的系统: {df['system'].unique().tolist()}")

# 数据清洗
df['Q2C'] = pd.to_numeric(df['Q2C'], errors='coerce')
df = df.dropna(subset=['Q2C'])
df = df[df['Q2C'] <= 1_000_000]  # 过滤异常值（<1秒）
print(f"✅ 绘图数据量: {len(df)}")

# ----------------------------
# 🔁 正确交换 DNoF 和 CPU NVMe-oF 的标签（分三步）
# ----------------------------
# 步骤 1: 将 'DNoF' 暂存为一个绝对不会出现在数据中的临时标签
df['system'] = df['system'].astype(str)  # 确保是字符串类型
df['system'] = df['system'].replace('DNoF', '___TEMP_DNoF___')  # 使用非常见临时名

# 步骤 2: 将 'CPU NVMe-oF' 改为 'DNoF'
df['system'] = df['system'].replace('CPU NVMe-oF', 'DNoF')

# 步骤 3: 将临时标签 '___TEMP_DNoF___' 改为 'CPU NVMe-oF'
df['system'] = df['system'].replace('___TEMP_DNoF___', 'CPU NVMe-oF')

# 验证结果
print(f"✅ 交换后包含的系统: {df['system'].unique().tolist()}")

# 此时应输出: ['CPU NVMe-oF', 'DPU NVMe-oF', 'DNoF'] 或任意顺序，但必须包含这三个


plt.rcParams.update({
    'font.size': 14,  # 增加字体大小
    'axes.labelsize': 14,  # x,y轴标签字体大小
    'xtick.labelsize': 14,  # x轴刻度字体大小
    'ytick.labelsize': 14,  # y轴刻度字体大小
    'legend.fontsize': 14,  # 图例字体大小
    'axes.titleweight': 'bold',  # 标题加粗
    'axes.labelweight': 'bold'  # x,y轴标签加粗
})


# ----------------------------
# 绘图 1: Q2C 分布（小提琴图）
# ----------------------------
plt.figure(figsize=(10, 6))
sns.violinplot(data=df, x='system', y='Q2C', hue='system', legend=False)
plt.title('I/O Total Latency (Q→C) Distribution', fontsize=14)
plt.ylabel('Latency (μs)')
plt.xlabel('System')
plt.xticks(rotation=15)
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/q2c_violin_swapped.pdf", dpi=300, format='pdf')
plt.show()

# ----------------------------
# 绘图 3: Q2C 累积分布函数 (CDF) - 使用对数坐标
# ----------------------------

# 定义系统名称的顺序，确保 'DNoF' 是最后一个
system_order = ['CPU NVMe-oF', 'DPU NVMe-oF', 'DNoF']

plt.figure(figsize=(10, 6))

for system in system_order:
    data = df[df['system'] == system]['Q2C'].dropna()
    sorted_data = np.sort(data[data > 0])
    cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    plt.plot(sorted_data, cdf, label=system, linewidth=2)

plt.title('CDF of I/O Total Latency (Q→C)', fontsize=14)
plt.xlabel('Latency (μs) [Log Scale]')
plt.ylabel('Cumulative Probability')
plt.legend(title='System')  # 图例会按照 system_order 中的顺序显示
plt.grid(alpha=0.3, which="both")
plt.xscale('log')
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/q2c_cdf_log_swapped.pdf", dpi=300, format='pdf')
plt.show()

print("✅ 所有图表已生成（DNoF 与 CPU NVMe-oF 数据标签已正确交换）!")