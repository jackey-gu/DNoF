import os
import json
import csv
import re

# 输入目录和输出文件
input_dir = r"C:\Users\jackey_gu\Desktop\脚本\DPIO\DPIO testjob\CPU_fio_variable_benchmark"
output_csv = r"C:\Users\jackey_gu\Desktop\脚本\DPIO\DPIO testjob\CPU_fio_variable_benchmark\CPUfio_results_summary_enhanced.csv"

# 定义字段
fields = [
    "filename", "test_type", "rw_mode", "bs", "rwmixwrite", "numjobs", "cpus_allowed", "iodepth",
    "read_iops", "write_iops", "read_bw_Mb", "write_bw_Mb",
    "read_lat_mean_us", "read_lat_p99_us", "write_lat_mean_us", "write_lat_p99_us",
    "cpu_usr", "cpu_sys", "cpu_total"
]

# 测试类型映射
test_type_map = {
    "bs": re.compile(r"^test_bs=.*$"),
    "rwmixwrite": re.compile(r"^test_rwmixwrite=.*$"),
    "numjobs": re.compile(r"^test_numjobs=.*$"),
    "nbcpu": re.compile(r"^test_nbcpu=.*$"),           # ✅ 正确映射为 nbcpu
    "iodepth": re.compile(r"^test_iodepth=.*$"),
    "numjobs-bw": re.compile(r"^test_numjobs-bw=.*$"),
    "nbcpu-bw": re.compile(r"^test_nbcpu-bw=.*$"),     # ✅ 正确映射为 nbcpu-bw
}

# 定义你期望的参数顺序（按测试类型）
test_order = {
    "bs": ["4k", "8k", "16k", "32k", "64k", "128k"],
    "rwmixwrite": ["0", "25", "50", "75", "100"],
    "numjobs": [str(i) for i in range(1, 17)],
    "nbcpu": [str(i) for i in range(1, 17)],         # ✅ 正确排序
    "iodepth": ["1", "2", "4", "8", "16", "32", "64", "128"],
    "numjobs-bw": [str(i) for i in range(1, 17)],
    "nbcpu-bw": [str(i) for i in range(1, 17)],     # ✅ 正确排序
}

def parse_job(job):
    read = job.get("read", {})
    write = job.get("write", {})
    return {
        "read_iops": read.get("iops", 0) / 1000,
        "write_iops": write.get("iops", 0) / 1000,
        "read_bw_Mb": read.get("bw", 0) / 1024,
        "write_bw_Mb": write.get("bw", 0) / 1024,
        "read_lat_mean_us": read.get("clat_ns", {}).get("mean", 0) / 1000,
        "read_lat_p99_us": read.get("clat_ns", {}).get("percentile", {}).get("99.000000", 0) / 1000,
        "write_lat_mean_us": write.get("clat_ns", {}).get("mean", 0) / 1000,
        "write_lat_p99_us": write.get("clat_ns", {}).get("percentile", {}).get("99.000000", 0) / 1000,
        "cpu_usr": job.get("usr_cpu", 0),
        "cpu_sys": job.get("sys_cpu", 0),
        "cpu_total": job.get("usr_cpu", 0) + job.get("sys_cpu", 0),
    }

def extract_test_params(filename):
    base = os.path.basename(filename).replace(".json", "")
    parts = base.split("_")
    params = {}
    for part in parts:
        if "=" in part:
            k, v = part.split("=", 1)
            params[k.lower()] = v
    return params

def get_sort_key(file):
    params = extract_test_params(file)
    test_type = "unknown"
    for key, pattern in test_type_map.items():
        if pattern.match(file):
            test_type = key
            break

    if test_type == "bs":
        value = params.get("bs", "")
    elif test_type in ["numjobs", "cpus_allowed", "iodepth", "rwmixwrite", "numjobs-bw", "nbcpu", "nbcpu-bw"]:
        value = params.get(test_type, "")
    else:
        value = ""

    return test_type, value

def custom_sort(file):
    test_type, value = get_sort_key(file)
    if test_type not in test_order:
        return (float('inf'), 0)
    order_list = test_order[test_type]
    try:
        idx = order_list.index(value)
    except ValueError:
        idx = len(order_list)
    return (list(test_order.keys()).index(test_type), idx)

# 主程序
with open(output_csv, "w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fields)
    writer.writeheader()

    files = [f for f in os.listdir(input_dir) if f.endswith(".json")]
    files.sort(key=custom_sort)

    for file in files:
        filepath = os.path.join(input_dir, file)
        with open(filepath, "r") as f:
            data = json.load(f)

        # 提取文件名参数
        params = extract_test_params(file)

        # 自动识别 rw_mode
        base = os.path.basename(file)
        if "randread" in base:
            rw_mode = "randread"
        elif "randwrite" in base:
            rw_mode = "randwrite"
        elif "read" in base:
            rw_mode = "read"
        elif "write" in base:
            rw_mode = "write"
        else:
            rw_mode = "unknown"

        # 识别测试类型
        test_type = "unknown"
        for key, pattern in test_type_map.items():
            if pattern.match(file):
                test_type = key
                break

        # 确保 jobs 存在
        if not data.get("jobs"):
            continue

        job_data = data["jobs"][0]  # 假设只有一个 job

        # 根据 test_type 填充字段
        # 默认值（根据测试配置）
        default_values = {
            "bs": "4k",
            "rwmixwrite": "0",
            "numjobs": "1",
            "cpus_allowed": "1",
            "iodepth": "64"
        }

        if test_type == "bs":
            bs_val = params.get("bs", "")
            rwmixwrite_val = params.get("rwmixwrite", "0")
            numjobs_val = params.get("numjobs", "1")
            cpus_allowed_val = params.get("nbcpu", "1")
            iodepth_val = params.get("iodepth", "64")

        elif test_type == "rwmixwrite":
            bs_val = params.get("bs", "4k")
            rwmixwrite_val = params.get("rwmixwrite", "")
            numjobs_val = params.get("numjobs", "1")
            cpus_allowed_val = params.get("nbcpu", "1")
            iodepth_val = params.get("iodepth", "64")

        elif test_type == "numjobs":
            bs_val = params.get("bs", "4k")
            rwmixwrite_val = params.get("rwmixwrite", "0")
            numjobs_val = params.get("numjobs", "")
            cpus_allowed_val = params.get("nbcpu", "16")
            iodepth_val = params.get("iodepth", "64")

        elif test_type == "nbcpu":
            bs_val = params.get("bs", "4k")
            rwmixwrite_val = params.get("rwmixwrite", "0")
            numjobs_val = params.get("numjobs", "16")
            cpus_allowed_val = params.get("nbcpu", "")  # ✅ 变动参数
            iodepth_val = params.get("iodepth", "64")

        elif test_type == "iodepth":
            bs_val = params.get("bs", "4k")
            rwmixwrite_val = params.get("rwmixwrite", "0")
            numjobs_val = params.get("numjobs", "1")
            cpus_allowed_val = params.get("nbcpu", "1")
            iodepth_val = params.get("iodepth", "")

        elif test_type == "numjobs-bw":
            bs_val = params.get("bs", "64k")
            rwmixwrite_val = params.get("rwmixwrite", "0")
            numjobs_val = params.get("numjobs-bw", "")  # ✅ 变动参数
            cpus_allowed_val = params.get("nbcpu-bw", "16")
            iodepth_val = params.get("iodepth", "64")

        elif test_type == "nbcpu-bw":
            bs_val = params.get("bs", "64k")
            rwmixwrite_val = params.get("rwmixwrite", "0")
            numjobs_val = params.get("numjobs-bw", "16")
            cpus_allowed_val = params.get("nbcpu-bw", "")  # ✅ 变动参数
            iodepth_val = params.get("iodepth", "64")

        else:
            # 未知 test_type，默认提取所有字段
            bs_val = params.get("bs", "")
            rwmixwrite_val = params.get("rwmixwrite", "")
            numjobs_val = params.get("numjobs", "")
            cpus_allowed_val = params.get("nbcpu", "")
            iodepth_val = params.get("iodepth", "")

        row = {
            "filename": file,
            "test_type": test_type,
            "rw_mode": rw_mode,
            "bs": bs_val,
            "rwmixwrite": rwmixwrite_val,
            "numjobs": numjobs_val,
            "cpus_allowed": cpus_allowed_val,
            "iodepth": iodepth_val,
        }

        row.update(parse_job(job_data))
        writer.writerow(row)

print(f"结果已保存至 {output_csv}")