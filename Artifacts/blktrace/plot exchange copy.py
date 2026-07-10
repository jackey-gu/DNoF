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
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
# ----------------------------
# 绘图 1: Q2C 分布（Strip Plot + Broken Y-Axis）
# ----------------------------
from matplotlib import gridspec

from mpl_toolkits.axes_grid1.inset_locator import inset_axes

# ----------------------------
# 配置参数
# ----------------------------
INPUT_CSV = "figures/3blktrace_delays.csv"  # 输入 CSV 文件
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

# 验证结果
print(f"✅ 交换后包含的系统: {df['system'].unique().tolist()}")

system_order = ['CPU NVMe-oF', 'DPU NVMe-oF', 'DNoF']

# 此时应输出: ['CPU NVMe-oF', 'DPU NVMe-oF', 'DNoF'] 或任意顺序，但必须包含这三个


plt.rcParams.update({
    'font.size': 22,  # 增加字体大小
    'axes.labelsize': 22,  # x,y轴标签字体大小
    'xtick.labelsize': 22,  # x轴刻度字体大小
    'ytick.labelsize': 22,  # y轴刻度字体大小
    'legend.fontsize': 22,  # 图例字体大小
    'axes.titleweight': 'bold',  # 标题加粗
    'axes.labelweight': 'bold'  # x,y轴标签加粗
})


# ----------------------------
# 绘图 1: Q2C 分布（小提琴图）
# ----------------------------
# 仅展示如何修改绘图1部分，即Q2C分布（小提琴图）
# ----------------------------
# 绘图 1: 主图 + 局部放大（Inset）
# ----------------------------

plt.figure(figsize=(10, 6))

# 主图：完整数据的小提琴图，指定 order
ax_main = sns.violinplot(
    data=df,
    x='system',
    y='Q2C',
    hue='system',
    order=system_order,      # 👈 关键：指定顺序
    legend=False
)
ax_main.set_title('I/O Total Latency (Q→C) Distribution')
ax_main.set_ylabel('Latency (μs)')
ax_main.set_xlabel('System')
ax_main.grid(axis='y', alpha=0.3)

# 创建 inset axes
ax_inset = inset_axes(ax_main, width="40%", height="30%", loc='center right', borderpad=2)

# 在 inset 中绘制 20–50 μs 的小提琴图，同样指定 order
df_zoom = df[(df['Q2C'] >= 20) & (df['Q2C'] <= 50)]  # 👈 关键：限定区间

sns.violinplot(
    data=df_zoom,
    x='system',
    y='Q2C',
    hue='system',
    order=system_order,      # 👈 保持顺序一致
    legend=False,
    ax=ax_inset
)

# 设置 inset 样式
ax_inset.set_ylim(20, 50)  # 👈 修改为 20–50
ax_inset.set_xticks(range(len(system_order)))
ax_inset.set_xticklabels([])  # 隐藏 x 轴标签
ax_inset.set_yticks([20, 35, 50])  # 可按需调整，例如 [20, 30, 40, 50]
ax_inset.set_xlabel('')
ax_inset.set_ylabel('')
ax_inset.grid(True, alpha=0.3)

for spine in ax_inset.spines.values():
    spine.set_edgecolor('gray')
    spine.set_linewidth(1)

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/q2c_violin_with_inset.pdf", dpi=300, format='pdf')
plt.show()

# ----------------------------
# 绘图 3: Q2C 累积分布函数 (CDF) - 主图 + Inset (0–100 μs)
# ----------------------------

system_order = ['CPU NVMe-oF', 'DPU NVMe-oF', 'DNoF']

plt.figure(figsize=(10, 6))
ax_main = plt.gca()

# --- 主图：完整 CDF（对数坐标）---
for system in system_order:
    data = df[df['system'] == system]['Q2C'].dropna()
    sorted_data = np.sort(data[data > 0])
    cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    ax_main.plot(sorted_data, cdf, label=system, linewidth=2)

ax_main.set_title('CDF of I/O Total Latency (Q→C)', fontsize=22)
ax_main.set_xlabel('Latency (μs) [Log Scale]')
ax_main.set_ylabel('Cumulative Probability')
ax_main.set_xscale('log')
ax_main.grid(alpha=0.3, which="both")
ax_main.legend(title='System')

# --- 创建 inset 子图（20-50 μs，线性坐标），并调整其位置 ---
ax_inset = inset_axes(ax_main, width="100%", height="100%",
                      bbox_to_anchor=(0.55, 0.7, 0.4, 0.3), # 这里是关键修改点
                      bbox_transform=ax_main.transAxes,
                      borderpad=2, loc='upper right')

zoom_min, zoom_max = 20, 50  # 设置关注区间

for system in system_order:
    # 筛选20到50μs的数据
    data = df[(df['system'] == system) & (df['Q2C'] >= zoom_min) & (df['Q2C'] <= zoom_max)]['Q2C'].dropna()
    if len(data) == 0:  # 如果没有数据，则跳过
        continue
    sorted_data = np.sort(data)
    cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    ax_inset.plot(sorted_data, cdf, linewidth=2)

# 设置inset子图的x轴和y轴范围
ax_inset.set_xlim(zoom_min, zoom_max)  # 修改为20到50μs
ax_inset.set_ylim(0, 1)
ax_inset.set_xticks([20, 35, 50])  # 根据新的范围调整刻度
ax_inset.set_yticks([0, 0.5, 1.0])
ax_inset.set_xlabel('')
ax_inset.set_ylabel('')
ax_inset.grid(True, alpha=0.3)

# 可选：给 inset 加边框
for spine in ax_inset.spines.values():
    spine.set_edgecolor('gray')
    spine.set_linewidth(1)

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/q2c_cdf_log_with_inset_adjusted.pdf", dpi=300, format='pdf')
plt.show()