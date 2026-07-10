#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解析 blkparse 生成的文本文件（无需 blktrace 工具链）
适用于 Windows/Linux
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# ----------------------------
# 配置参数
# ----------------------------
TESTS = [
    ("DNoF", r"C:\Users\jackey_gu\Desktop\脚本\blktrace\dnof_overhead_results\randread_bs4k_depth32_direct1\run_1\blktrace.combined.txt"),
    ("DPU NVMe-oF", r"C:\Users\jackey_gu\Desktop\脚本\blktrace\DPU_dnof_overhead_results\randread_bs4k_depth32_direct1\run_1\blktrace.combined.txt"),
    ("CPU NVMe-oF", r"C:\Users\jackey_gu\Desktop\脚本\blktrace\CPU_dnof_overhead_results\randread_bs4k_depth32_direct1\run_1\blktrace.combined.txt"),
]

OUTPUT_DIR = "figures"
Path(OUTPUT_DIR).mkdir(exist_ok=True)


# ----------------------------
# 解析 blkparse 文本文件
# ----------------------------
def parse_blktrace(txt_file):
    """
    解析 blkparse 生成的文本文件（合并后）
    适配您的 blktrace 输出格式：
    259,9    4        1     0.000000000 471705  Q   R 126480 + 8 [fio]
    """
    data = []
    with open(txt_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(('#', 'CPU', 'Device')):
                continue  # 跳过空行、注释、标题

            parts = line.split()
            if len(parts) < 10:
                continue  # 至少要有10列

            try:
                # 验证时间字段（第4列）
                float(parts[3])

                # 提取关键字段
                time = float(parts[3])        # 时间
                pid = int(parts[4])           # PID
                event = parts[5]              # 事件类型 Q/G/I/D/C
                rwbs = parts[6]               # R/W/S/M
                offset = int(parts[7])        # 起始扇区
                size = int(parts[9])          # 大小（扇区数）

                # 只保留有效事件
                if event not in 'QGISDC':
                    continue

                is_write = 'W' in rwbs
                key = f"{pid}_{offset}_{size}_{'W' if is_write else 'R'}"

                data.append({
                    'time': time,
                    'pid': pid,
                    'event': event,
                    'rwbs': rwbs,
                    'offset': offset,
                    'size': size,
                    'is_write': is_write,
                    'key': key
                })
            except (ValueError, IndexError):
                continue  # 解析失败则跳过

    return pd.DataFrame(data)

# ----------------------------
# 计算延迟
# ----------------------------
def compute_delays(df):
    events = ['Q', 'G', 'I', 'D', 'C']
    delay_data = []

    grouped = df.groupby('key')
    for key, group in grouped:
        times = {ev: float('nan') for ev in events}
        for _, row in group.iterrows():
            if row['event'] in events:
                times[row['event']] = row['time']

        base_time = times['Q']
        if pd.isna(base_time):
            continue

        delays = {
            'Q2G': (times['G'] - base_time) * 1e6 if not pd.isna(times['G']) else np.nan,
            'G2I': (times['I'] - times['G']) * 1e6 if not pd.isna(times['G']) and not pd.isna(times['I']) else np.nan,
            'I2D': (times['D'] - times['I']) * 1e6 if not pd.isna(times['I']) and not pd.isna(times['D']) else np.nan,
            'D2C': (times['C'] - times['D']) * 1e6 if not pd.isna(times['D']) and not pd.isna(times['C']) else np.nan,
            'Q2C': (times['C'] - base_time) * 1e6 if not pd.isna(times['C']) else np.nan,
            'is_write': group['is_write'].iloc[0],
            'size_kb': group['size'].iloc[0] * 0.25,  # 扇区 -> KB (512B/扇区)
        }
        delay_data.append(delays)

    return pd.DataFrame(delay_data)


# ----------------------------
# 主流程
# ----------------------------
all_results = []

for label, txt_path in TESTS:
    print(f"\n=== 分析: {label} ===")
    if not Path(txt_path).exists():
        print(f"❌ 文件不存在: {txt_path}")
        continue

    df = parse_blktrace(txt_path)
    print(f"共解析 {len(df)} 个事件")

    delay_df = compute_delays(df)
    delay_df['system'] = label
    all_results.append(delay_df)

if not all_results:
    print("❌ 未解析到任何数据，请检查文件路径")
    exit(1)

final_df = pd.concat(all_results, ignore_index=True)
final_df.to_csv(f"{OUTPUT_DIR}/blktrace_delays.csv", index=False)
print(f"\n✅ 延迟数据已保存: {OUTPUT_DIR}/blktrace_delays.csv")


# ----------------------------
# 绘图 1: Q2C 分布（小提琴图）
# ----------------------------
plt.figure(figsize=(10, 6))
sns.violinplot(data=final_df, x='system', y='Q2C', hue='system', legend=False)
plt.title('I/O Total Latency (Q→C) Distribution', fontsize=14)
plt.ylabel('Latency (μs)')
plt.xlabel('System')
plt.xticks(rotation=15)
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/q2c_violin.png", dpi=300)
plt.show()


# ----------------------------
# 绘图 2: 平均延迟分解（堆叠图）
# ----------------------------
mean_delays = final_df.groupby('system')[['Q2G', 'G2I', 'I2D', 'D2C']].mean().reset_index()

plt.figure(figsize=(10, 6))
categories = ['Q2G', 'G2I', 'I2D', 'D2C']
colors = sns.color_palette("Blues", len(categories))

bottom = None
for i, cat in enumerate(categories):
    if i == 0:
        bottom = None
    else:
        bottom = sum(mean_delays[c] for c in categories[:i])
    plt.bar(mean_delays['system'], mean_delays[cat], bottom=bottom,
            color=colors[i], label=cat.replace('2', '→'))

plt.title('Average I/O Latency Breakdown by Stage', fontsize=14)
plt.ylabel('Latency (μs)')
plt.xlabel('System')
plt.legend(title='Stage')
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/latency_breakdown.png", dpi=300)
plt.show()


# ----------------------------
# 绘图 3: Q2C 累积分布函数 (CDF)
# ----------------------------
plt.figure(figsize=(10, 6))
for system in final_df['system'].unique():
    data = final_df[final_df['system'] == system]['Q2C'].dropna()
    sorted_data = np.sort(data)
    cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    plt.plot(sorted_data, cdf, label=system, linewidth=2)

plt.title('CDF of I/O Total Latency (Q→C)', fontsize=14)
plt.xlabel('Latency (μs)')
plt.ylabel('Cumulative Probability')
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/q2c_cdf.png", dpi=300)
plt.show()

print("✅ 所有图表已生成!")