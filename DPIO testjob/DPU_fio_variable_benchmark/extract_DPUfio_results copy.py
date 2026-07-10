import os
import json
import csv
import re

# 输入目录和输出文件
input_dir = r"C:\Users\jackey_gu\Desktop\脚本\DPIO\DPIO testjob\DPU_fio_variable_benchmark"
output_csv = r"C:\Users\jackey_gu\Desktop\脚本\DPIO\DPIO testjob\DPU_fio_variable_benchmark\DPUfio_results_summary_enhanced.csv"

# 定义字段
fields = [
    "filename", "test_type", "rw_mode", "bs", "rwmixwrite", "numjobs", "cpus_allowed", "iodepth",
    "read_iops", "write_iops", "read_bw_Mb", "write_bw_Mb",
    "read_lat_mean_us", "read_lat_p99_us", "write_lat_mean_us", "write_lat_p99_us",
    "cpu_usr", "cpu_sys", "cpu_total"
]

# 测试类型映射（✅ 修改：iodepth 匹配所有 test_iodepth= 开头）
test_type_map = {
    "bs": re.compile(r"^test_bs=.*$"),
    "rwmixwrite": re.compile(r"^test_rwmixwrite=.*$"),
    "numjobs": re.compile(r"^test_numjobs=.*$"),
    "nbcpu": re.compile(r"^test_nbcpu=.*$"),           # ✅ 正确映射为 nbcpu
    "iodepth": re.compile(r"^test_iodepth=.*$"),           # ✅ 支持 write/read
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
    test_type = "unknown"
    for key, pattern in test_type_map.items():
        if pattern.match(file):
            test_type = key
            break
    params = extract_test_params(file)
    value = params.get(test_type, "") if test_type in ["iodepth"] else ""
    if test_type == "bs":
        value = params.get("bs", "")
    elif test_type == "rwmixwrite":
        value = params.get("rwmixwrite", "")
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
with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fields)
    writer.writeheader()

    files = [f for f in os.listdir(input_dir) if f.endswith(".json")]
    files.sort(key=custom_sort)

    for file in files:
        filepath = os.path.join(input_dir, file)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        params = extract_test_params(file)
        base = os.path.basename(file)

        # === ✅ 更新 rw_mode 判断逻辑 ===
        if "randread" in base:
            rw_mode = "randread"
        elif "randwrite" in base:
            rw_mode = "randwrite"
        elif "_read.json" in base:      # 显式匹配 _read.json
            rw_mode = "read"
        elif "_write.json" in base:     # 显式匹配 _write.json
            rw_mode = "write"
        else:
            rw_mode = "unknown"

        # 识别测试类型
        test_type = "unknown"
        for key, pattern in test_type_map.items():
            if pattern.match(base):
                test_type = key
                break

        if not data.get("jobs"):
            continue
        job_data = data["jobs"][0]

        # 参数提取逻辑（以 iodepth 为例）
        # === 智能设置 bs 默认值 ===
        if test_type == "iodepth":
            if rw_mode in ["randread", "randwrite"]:
                bs_val = params.get("bs", "4k")   # 随机：4k
            elif rw_mode in ["read", "write"]:
                bs_val = params.get("bs", "64k")  # 顺序：64k ✅
            else:
                bs_val = params.get("bs", "4k")
        else:
            # 其他测试类型使用原始逻辑
            bs_val = params.get("bs", "")
            if not bs_val:
                if test_type == "bs":
                    bs_val = ""  # bs 测试本身就在变，留空
                else:
                    bs_val = "4k"  # 默认 fallback

        rwmixwrite_val = params.get("rwmixwrite", "0")

        numjobs_val = ""
        cpus_allowed_val = ""
        iodepth_val = ""

        if test_type == "iodepth":
    # ✅ 不再重新设置 bs_val！保留上面已计算好的值
            numjobs_val = params.get("numjobs", "1")
            cpus_allowed_val = params.get("nbcpu", "1")
            iodepth_val = params.get("iodepth", "")

        # 其他 test_type 分支保持不变...
        # （此处省略，使用你原始脚本中的其他分支即可）

        else:
            # fallback：使用原始逻辑填充
            if test_type == "bs":
                bs_val = params.get("bs", "")
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
                numjobs_val = params.get("numjobs", "")
                cpus_allowed_val = params.get("nbcpu", "16")
                iodepth_val = params.get("iodepth", "64")
            elif test_type == "nbcpu":
                bs_val = params.get("bs", "4k")
                numjobs_val = params.get("numjobs", "16")
                cpus_allowed_val = params.get("nbcpu", "")
                iodepth_val = params.get("iodepth", "64")
            elif test_type == "numjobs-bw":
                bs_val = params.get("bs", "64k")
                numjobs_val = params.get("numjobs-bw", "")
                cpus_allowed_val = params.get("nbcpu-bw", "16")
                iodepth_val = params.get("iodepth", "64")
            elif test_type == "nbcpu-bw":
                bs_val = params.get("bs", "64k")
                numjobs_val = params.get("numjobs-bw", "16")
                cpus_allowed_val = params.get("nbcpu-bw", "")
                iodepth_val = params.get("iodepth", "64")
            else:
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