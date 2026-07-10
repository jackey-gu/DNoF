#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解析 blktrace.combined.txt 文件并汇总为 CSV
仅执行数据解析，不绘图
"""

import pandas as pd
from pathlib import Path

# ----------------------------
# 配置参数
# ----------------------------
TESTS = [
    ("DNoF", r"C:\Users\jackey_gu\Desktop\脚本\blktrace\dnof_CPU_overhead_results\randread_bs4k_depth2_direct1\run_1\blktrace.combined.txt"),
    ("DPU NVMe-oF", r"C:\Users\jackey_gu\Desktop\脚本\blktrace\DPU_dnof_overhead_results\2randread_bs4k_depth1_direct1\run_1\blktrace.combined.txt"),
    ("CPU NVMe-oF", r"C:\Users\jackey_gu\Desktop\脚本\blktrace\CPU_dnof_overhead_results\randread_bs4k_depth1_direct1\run_1\blktrace.combined.txt"),
]

OUTPUT_DIR = "figures"
Path(OUTPUT_DIR).mkdir(exist_ok=True)


# ----------------------------
# 解析 blkparse 文本文件
# ----------------------------
def parse_blktrace(txt_file):
    """
    解析 blkparse 生成的文本文件（合并后）
    适配格式：259,9    4        1     0.000000000 471705  Q   R 126480 + 8 [fio]
    """
    data = []
    with open(txt_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(('#', 'CPU', 'Device')):
                continue

            parts = line.split()
            if len(parts) < 10:
                continue

            try:
                float(parts[3])  # 验证时间
                time = float(parts[3])
                pid = int(parts[4])
                event = parts[5]
                rwbs = parts[6]
                offset = int(parts[7])
                size = int(parts[9])
                is_write = 'W' in rwbs
                key = f"{pid}_{offset}_{size}_{'W' if is_write else 'R'}"

                if event not in 'QGISDC':
                    continue

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
                continue

    return pd.DataFrame(data)


# ----------------------------
# 计算延迟
# ----------------------------
def compute_delays(df):
    events = ['Q', 'G', 'I', 'D', 'C']
    delay_data = []

    df['key'] = df['offset'].astype(str) + '_' + \
                df['size'].astype(str) + '_' + \
                df['rwbs'].str[0]

    for key, group in df.groupby('key'):
        times = {ev: float('nan') for ev in events}
        for _, row in group.iterrows():
            if row['event'] in events:
                times[row['event']] = row['time']

        base_time = times['Q']
        if pd.isna(base_time):
            continue

        delays = {
            'Q2G': (times['G'] - base_time) * 1e6 if not pd.isna(times['G']) else None,
            'G2I': (times['I'] - times['G']) * 1e6 if not pd.isna(times['G']) and not pd.isna(times['I']) else None,
            'I2D': (times['I'] - times['I']) * 1e6 if not pd.isna(times['I']) and not pd.isna(times['D']) else None,
            'D2C': (times['C'] - times['D']) * 1e6 if not pd.isna(times['D']) and not pd.isna(times['C']) else None,
            'Q2C': (times['C'] - base_time) * 1e6 if not pd.isna(times['C']) else None,
            'is_write': 'W' in key,
            'size_kb': int(key.split('_')[1]) * 0.5,
        }
        delay_data.append(delays)

    return pd.DataFrame(delay_data)


# ----------------------------
# 主流程
# ----------------------------
if __name__ == "__main__":
    all_results = []

    for label, txt_path in TESTS:
        print(f"\n=== 分析: {label} ===")
        txt_file = Path(txt_path)
        if not txt_file.exists():
            print(f"❌ 文件不存在: {txt_path}")
            continue

        df = parse_blktrace(txt_file)
        print(f"共解析 {len(df)} 个事件")

        delay_df = compute_delays(df)
        delay_df['system'] = label
        all_results.append(delay_df)

    if not all_results:
        print("❌ 未解析到任何数据，请检查文件路径")
        exit(1)

    final_df = pd.concat(all_results, ignore_index=True)
    output_csv = f"{OUTPUT_DIR}/2blktrace_delays.csv"
    final_df.to_csv(output_csv, index=False)
    print(f"\n✅ 延迟数据已保存: {output_csv}")