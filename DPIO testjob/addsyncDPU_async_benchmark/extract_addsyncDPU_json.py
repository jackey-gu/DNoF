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

    # === 修复：改进正则表达式，支持 bs4k、bs64k ===
    base = os.path.basename(filename)
    match = re.match(
        r'test_(mixed|sync1_asyncN|async1_syncN)'
        r'_(randread|randwrite|read|write)'
        r'_bs(\d+k?)'           # 匹配 4k, 64k 等
        r'.*\.json$',           # 忽略后面的 sync/async 部分
        base,
        re.IGNORECASE
    )

    if match:
        test_type, rw_mode, bs = match.groups()
    else:
        test_type, rw_mode, bs = 'unknown', 'unknown', 'unknown'

    # === 新增：从文件名提取 sync 和 async job 数量 ===
    sync_match = re.search(r'_sync(\d+)', base)
    async_match = re.search(r'_async(\d+)', base)

    sync_jobs = int(sync_match.group(1)) if sync_match else 0
    async_jobs = int(async_match.group(1)) if async_match else 0
    total_jobs = sync_jobs + async_jobs

    result = {
        'filename': base,
        'test_type': test_type,
        'rw_mode': rw_mode,
        'bs': bs,
        'jobname': jobname,
        'jobtype': jobtype,
        'sync_jobs': sync_jobs,
        'async_jobs': async_jobs,
        'total_jobs': total_jobs,
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
        # === ✅ 关键：对 files 按 sync_jobs 数值排序 ===
        def sort_key(file):
            if not file.endswith('.json'):
                return float('inf')  # 非 json 文件放最后
            # 提取 sync(\d+) 或 async(\d+)
            sync_match = re.search(r'_sync(\d+)', file)
            async_match = re.search(r'_async(\d+)', file)
            num = 0
            if sync_match:
                num = int(sync_match.group(1))
            elif async_match:
                num = int(async_match.group(1))
            # 可选：加上 test_type 权重，确保不同测试不混序
            prefix = re.match(r'test_(mixed|sync1_asyncN|async1_syncN)', file)
            type_weight = {'mixed': 0, 'sync1_asyncN': 1, 'async1_syncN': 2}.get(prefix.group(1) if prefix else 'unknown', 3)
            return (type_weight, num)  # 先按测试类型，再按数字排序

        sorted_files = sorted([f for f in files if f.endswith('.json')], key=sort_key)

        for file in sorted_files:
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

    # === ✅ 按 filename + sync_jobs 数值排序整个 results ===
    def result_sort_key(row):
        sync_jobs = row['sync_jobs']
        async_jobs = row['async_jobs']
        # 可选：加上 test_type 和 rw_mode 分组
        type_order = {'mixed': 0, 'sync1_asyncN': 1, 'async1_syncN': 2}.get(row['test_type'], 3)
        rw_order = {'read': 0, 'randread': 1, 'write': 2, 'randwrite': 3}.get(row['rw_mode'], 4)
        return (type_order, rw_order, sync_jobs, async_jobs)

    results.sort(key=result_sort_key)

    # 写入 CSV
    fieldnames = [
        'filename', 'test_type', 'rw_mode', 'bs',
        'jobname', 'jobtype',
        'sync_jobs', 'async_jobs', 'total_jobs',
        'read_iops', 'read_bw', 'read_lat_mean', 'read_lat_99',
        'write_iops', 'write_bw', 'write_lat_mean', 'write_lat_99',
        'cpu_usr', 'cpu_sys'
    ]

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"✅ 数据提取完成，共提取 {len(results)} 条 job 性能数据")
    print(f"📊 输出文件: {output_csv}")
    print(f"📁 文件已按 sync_jobs 数值顺序排列")


if __name__ == '__main__':
    input_dir = r"c:/Users/jackey_gu/Desktop/脚本/DPIO/DPIO testjob/addsyncDPU_async_benchmark"
    output_csv = os.path.join(input_dir, "DPU_results_summary.csv")

    extract_all_json_files(input_dir, output_csv)