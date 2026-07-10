import os
import json
import csv
import re

# 输入目录和输出文件（请根据实际路径修改）
input_dir = r"C:\Users\jackey_gu\Desktop\脚本\DPIO\DPIO testjob\40DPU_fio_variable_benchmark_supplement"
output_csv = r"C:\Users\jackey_gu\Desktop\脚本\DPIO\DPIO testjob\40DPU_fio_variable_benchmark_supplement\40DPUsupplement_summary.csv"

# CSV 输出字段
fields = [
    "filename", "test_type", "rw_mode", "bs", "numjobs", "nbcpu", "iodepth",
    "read_iops_K", "write_iops_K", "read_bw_MiB", "write_bw_MiB",
    "read_lat_mean_us", "read_lat_p99_us", "write_lat_mean_us", "write_lat_p99_us",
    "cpu_usr", "cpu_sys", "cpu_total"
]

# 测试类型正则匹配
test_type_patterns = {
    "numjobs": re.compile(r"^test_numjobs=\d+_(randwrite|randread|read|write)\.json$"),
    "nbcpu": re.compile(r"^test_nbcpu=\d+_(randwrite|randread|read|write)\.json$"),
    "numjobs-bw": re.compile(r"^test_numjobs-bw=\d+_(randwrite|randread|read|write)\.json$"),
    "nbcpu-bw": re.compile(r"^test_nbcpu-bw=\d+_(randwrite|randread|read|write)\.json$"),
}

# 参数排序顺序（用于排序输出）
test_order = {
    "numjobs": [str(i) for i in range(1, 41)],
    "nbcpu": [str(i) for i in range(1, 41)],
    "numjobs-bw": [str(i) for i in range(1, 41)],
    "nbcpu-bw": [str(i) for i in range(1, 41)],
}

# 解析 FIO job 数据
def parse_job(job):
    read = job.get("read", {})
    write = job.get("write", {})
    return {
        "read_iops_K": round(read.get("iops", 0) / 1000, 2),
        "write_iops_K": round(write.get("iops", 0) / 1000, 2),
        "read_bw_MiB": round(read.get("bw", 0) / 1024, 2),
        "write_bw_MiB": round(write.get("bw", 0) / 1024, 2),
        "read_lat_mean_us": round(read.get("clat_ns", {}).get("mean", 0) / 1000, 2),
        "read_lat_p99_us": round(read.get("clat_ns", {}).get("percentile", {}).get("99.000000", 0) / 1000, 2),
        "write_lat_mean_us": round(write.get("clat_ns", {}).get("mean", 0) / 1000, 2),
        "write_lat_p99_us": round(write.get("clat_ns", {}).get("percentile", {}).get("99.000000", 0) / 1000, 2),
        "cpu_usr": round(job.get("usr_cpu", 0), 2),
        "cpu_sys": round(job.get("sys_cpu", 0), 2),
        "cpu_total": round(job.get("usr_cpu", 0) + job.get("sys_cpu", 0), 2),
    }

# 提取文件名参数
def extract_test_params(filename):
    base = os.path.basename(filename).replace(".json", "")
    parts = base.split("_")
    params = {}
    for part in parts:
        if "=" in part:
            k, v = part.split("=", 1)
            params[k.lower()] = v
    return params

# 获取排序键
def custom_sort_key(file):
    test_type = "unknown"
    value = ""

    for key, pattern in test_type_patterns.items():
        if pattern.match(file):
            test_type = key
            break

    if test_type == "unknown":
        return (float('inf'), 0)

    # 提取参数值
    if test_type in ["numjobs", "nbcpu", "numjobs-bw", "nbcpu-bw"]:
        value = extract_test_params(file).get(test_type, "")

    # 排序依据：test_type 在 test_order 中的顺序 + 参数值排序
    order_list = test_order.get(test_type, [])
    try:
        idx = order_list.index(value)
    except ValueError:
        idx = len(order_list)

    return (list(test_type_patterns.keys()).index(test_type), idx)

# 主程序
with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fields)
    writer.writeheader()

    files = [f for f in os.listdir(input_dir) if f.endswith(".json")]
    files.sort(key=custom_sort_key)

    for file in files:
        filepath = os.path.join(input_dir, file)
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
        except Exception as e:
            print(f"无法读取文件: {file}，错误: {e}")
            continue

        if not data.get("jobs"):
            print(f"文件 {file} 中没有 jobs 数据")
            continue

        job_data = data["jobs"][0]  # 假设只有一个 job

        # 提取参数
        params = extract_test_params(file)

        # 判断测试类型
        test_type = "unknown"
        for key, pattern in test_type_patterns.items():
            if pattern.match(file):
                test_type = key
                break

        # 提取读写模式
        base = os.path.basename(file)
        rw_mode = "unknown"
        if "randread" in base:
            rw_mode = "randread"
        elif "randwrite" in base:
            rw_mode = "randwrite"
        elif "read" in base:
            rw_mode = "read"
        elif "write" in base:
            rw_mode = "write"

        # 根据 test_type 设置参数
        if test_type == "numjobs":
            bs_val = params.get("bs", "4k")
            numjobs_val = params.get("numjobs", "")
            nbcpu = "40"
            iodepth_val = "64"
        elif test_type == "nbcpu":
            bs_val = params.get("bs", "4k")
            numjobs_val = "40"
            nbcpu = params.get("nbcpu", "")
            iodepth_val = "64"
        elif test_type == "numjobs-bw":
            bs_val = params.get("bs", "64k")
            numjobs_val = params.get("numjobs-bw", "")
            nbcpu = "0-39"
            iodepth_val = "64"
        elif test_type == "nbcpu-bw":
            bs_val = params.get("bs", "64k")
            numjobs_val = "40"
            nbcpu = params.get("nbcpu-bw", "")
            iodepth_val = "64"
        else:
            continue

        row = {
            "filename": file,
            "test_type": test_type,
            "rw_mode": rw_mode,
            "bs": bs_val,
            "numjobs": numjobs_val,
            "nbcpu": nbcpu,
            "iodepth": iodepth_val,
        }

        row.update(parse_job(job_data))
        writer.writerow(row)

print(f"✅ 新增测试结果已汇总至: {output_csv}")