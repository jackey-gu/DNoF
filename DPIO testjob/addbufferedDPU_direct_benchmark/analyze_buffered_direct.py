#!/usr/bin/env python3

import os
import json
import csv
import re

def extract_metrics_from_job(job, filename):
    jobname = job['jobname']
    
    # 判断 job 类型
    if jobname.startswith('buffered_job'):
        jobtype = 'Buffered'
    elif jobname.startswith('direct_job'):
        jobtype = 'Direct'
    else:
        jobtype = 'Unknown'

    read = job.get('read', {})
    write = job.get('write', {})

    # === 1. 解析 test_type, rw_mode, bs（保留单位 k）===
    base = os.path.basename(filename)
    match = re.match(
        r'test_(mixed|buffered1_directN|direct1_bufferedN)_(randread|randwrite|read|write)_bs(\d+k).*\.json', 
        base
    )
    if match:
        test_type, rw_mode, bs = match.groups()
    else:
        test_type, rw_mode, bs = 'unknown', 'unknown', 'unknown'

    # === 2. 从文件名中提取 buffered_jobs 和 direct_jobs 数量 ===
    buffered_jobs = 1
    direct_jobs = 1

    m_buffered = re.search(r'_buffered(\d+)', base)
    if m_buffered:
        buffered_jobs = int(m_buffered.group(1))

    m_direct = re.search(r'_direct(\d+)', base)
    if m_direct:
        direct_jobs = int(m_direct.group(1))

    # === 3. 特殊 test_type 的默认值调整 ===
    if test_type == "mixed":
        direct_jobs = 1
    elif test_type == "buffered1_directN":
        buffered_jobs = 1
    elif test_type == "direct1_bufferedN":
        direct_jobs = 1

    # === 4. 计算总 job 数 ===
    total_jobs = buffered_jobs + direct_jobs

    # === 5. 构建结果字典 ===
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
        # === 新增字段 ===
        'buffered_jobs': buffered_jobs,
        'direct_jobs': direct_jobs,
        'total_jobs': total_jobs,
    }

    return result


# ✅ 修改点：添加自然排序逻辑
def natural_sort_key(filename):
    """
    生成自然排序键：提取所有数字并转换为整数，其他保持字符串
    例如：'test_direct10.json' -> ['test_direct', 10, '.json']
    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', filename)]

def extract_all_json_files(input_dir, output_csv):
    results = []

    # 收集所有 JSON 文件路径
    json_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))

    # ✅ 按文件名自然排序
    json_files.sort(key=natural_sort_key)

    # 按排序后的顺序处理文件
    for filepath in json_files:
        filename = os.path.basename(filepath)
        print(f"🔍 正在处理: {filename}")
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            for job in data.get('jobs', []):
                result = extract_metrics_from_job(job, filename)
                results.append(result)
        except Exception as e:
            print(f"❌ 无法解析文件 {filename}: {e}")

    # 写入 CSV
    fieldnames = [
        'filename', 'test_type', 'rw_mode', 'bs',
        'jobname', 'jobtype',
        'read_iops', 'read_bw', 'read_lat_mean', 'read_lat_99',
        'write_iops', 'write_bw', 'write_lat_mean', 'write_lat_99',
        'cpu_usr', 'cpu_sys',
        'buffered_jobs', 'direct_jobs', 'total_jobs'
    ]

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"✅ 数据提取完成，共提取 {len(results)} 条 job 性能数据")
    print(f"📊 输出文件: {output_csv}")


if __name__ == '__main__':
    input_dir = r"c:/Users/jackey_gu/Desktop/脚本/DPIO/DPIO testjob/addbufferedDPU_direct_benchmark"
    output_csv = os.path.join(input_dir, "buffered_direct_results_summary.csv")

    extract_all_json_files(input_dir, output_csv)