#!/usr/bin/env python3

import os
import json
import csv
import re

def extract_metrics_from_job(job, filename):
    jobname = job['jobname']
    read = job.get('read', {})
    write = job.get('write', {})

    # 判断 job 类型
    jobtype = 'sync' if jobname.startswith('psync') else 'async'

    # 解析文件名中的测试类型、读写模式、块大小
    base = os.path.basename(filename)
    match = re.match(r'test_(mixed|sync1_asyncN|async1_syncN)_(randread|randwrite|read|write)_bs(\d+)(?:_sync\d+|_async\d+)?\.json', base)
    if match:
        test_type, rw_mode, bs = match.groups()
    else:
        test_type, rw_mode, bs = 'unknown', 'unknown', 'unknown'

    result = {
        'filename': base,
        'test_type': test_type,
        'rw_mode': rw_mode,
        'bs': bs,
        'jobname': jobname,
        'jobtype': jobtype,
        'read_iops': round(read.get('iops', 0), 2),
        'read_bw': round(read.get('bw', 0) / 1024, 2),  # KB/s -> MB/s
        'read_lat_mean': round(read['clat_ns'].get('mean', 0) / 1000, 2),  # ns -> μs
        'read_lat_99': round(read['clat_ns']['percentile'].get('99.000000', 0) / 1000, 2),
        'write_iops': round(write.get('iops', 0), 2),
        'write_bw': round(write.get('bw', 0) / 1024, 2),
        'write_lat_mean': round(write['clat_ns'].get('mean', 0) / 1000, 2),
        'write_lat_99': round(write['clat_ns']['percentile'].get('99.000000', 0) / 1000, 2),
        'cpu_usr': round(job.get('usr_cpu', 0), 2),
        'cpu_sys': round(job.get('sys_cpu', 0), 2),
    }

    return result


def extract_all_json_files(input_dir, output_csv):
    results = []

    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.json'):
                filepath = os.path.join(root, file)
                print(f"🔍 正在处理: {file}")
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    for job in data.get('jobs', []):
                        result = extract_metrics_from_job(job, file)
                        results.append(result)
                except Exception as e:
                    print(f"❌ 无法解析文件 {file}: {e}")

    # 写入 CSV
    fieldnames = [
        'filename', 'test_type', 'rw_mode', 'bs',
        'jobname', 'jobtype',
        'read_iops', 'read_bw', 'read_lat_mean', 'read_lat_99',
        'write_iops', 'write_bw', 'write_lat_mean', 'write_lat_99',
        'cpu_usr', 'cpu_sys'
    ]

    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"✅ 数据提取完成，共提取 {len(results)} 条 job 性能数据")
    print(f"📊 输出文件: {output_csv}")


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print("用法: python3 extract_all_json.py <输入目录> <输出CSV文件>")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_csv = sys.argv[2]

    extract_all_json_files(input_dir, output_csv)