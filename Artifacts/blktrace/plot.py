#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 blktrace_delays.csv 读取数据并绘图
仅执行绘图，不解析原始 blktrace
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
print(f"包含的系统: {df['system'].unique().tolist()}")

# 数据清洗
df['Q2C'] = pd.to_numeric(df['Q2C'], errors='coerce')
df = df.dropna(subset=['Q2C'])
df = df[df['Q2C'] <= 1_000_000]  # 过滤异常值（<1秒）
print(f"✅ 绘图数据量: {len(df)}")


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
plt.savefig(f"{OUTPUT_DIR}/q2c_violin.pdf", dpi=300, format='pdf')  # 保存为 PDF
plt.show()


# ----------------------------
# 绘图 2: 平均延迟分解（堆叠图）
# ----------------------------
# mean_delays = df.groupby('system')[['Q2G', 'G2I', 'I2D', 'D2C']].mean().reset_index()

# plt.figure(figsize=(10, 6))
# categories = ['Q2G', 'G2I', 'I2D', 'D2C']
# colors = sns.color_palette("Blues", len(categories))

# bottom = None
# for i, cat in enumerate(categories):
#     values = mean_delays[cat]
#     if i == 0:
#         bottom = None
#     else:
#         bottom = sum(mean_delays[c] for c in categories[:i])
#     plt.bar(mean_delays['system'], values, bottom=bottom, color=colors[i], label=cat.replace('2', '→'))

# plt.title('Average I/O Latency Breakdown by Stage', fontsize=14)
# plt.ylabel('Latency (μs)')
# plt.xlabel('System')
# plt.legend(title='Stage')
# plt.grid(axis='y', alpha=0.3)
# plt.tight_layout()
# plt.savefig(f"{OUTPUT_DIR}/latency_breakdown.pdf", dpi=300, format='pdf')  # 保存为 PDF
# plt.show()


# ----------------------------
# 绘图 3: Q2C 累积分布函数 (CDF)
# ----------------------------
# plt.figure(figsize=(10, 6))
# for system in df['system'].unique():
#     data = df[df['system'] == system]['Q2C'].dropna()
#     sorted_data = np.sort(data)
#     cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
#     plt.plot(sorted_data, cdf, label=system, linewidth=2)

# plt.title('CDF of I/O Total Latency (Q→C)', fontsize=14)
# plt.xlabel('Latency (μs)')
# plt.ylabel('Cumulative Probability')
# plt.legend(title='System')
# plt.grid(alpha=0.3)
# plt.tight_layout()
# plt.savefig(f"{OUTPUT_DIR}/q2c_cdf.pdf", dpi=300, format='pdf')  # 保存为 PDF
# plt.show()

# print("✅ 所有图表已生成!")

# ----------------------------
# 绘图 3: Q2C 累积分布函数 (CDF) - 使用对数坐标
# ----------------------------
plt.figure(figsize=(10, 6))
for system in df['system'].unique():
    data = df[df['system'] == system]['Q2C'].dropna()
    sorted_data = np.sort(data[data > 0])  # 去掉0或负值，避免 log(0)
    cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    plt.plot(sorted_data, cdf, label=system, linewidth=2)

plt.title('CDF of I/O Total Latency (Q→C)', fontsize=14)
plt.xlabel('Latency (μs) [Log Scale]')
plt.ylabel('Cumulative Probability')
plt.legend(title='System')
plt.grid(alpha=0.3, which="both")  # 同时显示主次网格
plt.xscale('log')  # ✅ 关键：X轴对数显示
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/q2c_cdf_log.pdf", dpi=300, format='pdf')
plt.show()