import os
import json
import csv
import re

# ==================== 配置 ====================
input_dir = r"C:\Users\jackey_gu\Desktop\脚本\DPIO\DPIO testjob\CPU_fio_variable_benchmark"
output_csv = r"C:\Users\jackey_gu\Desktop\脚本\DPIO\DPIO testjob\CPU_fio_variable_benchmark\only_CPUfio_results_summary_enhanced.csv"

# 定义输出字段
fields = [
    "filename", "test_type", "rw_mode", "bs", "rwmixwrite", "numjobs", "cpus_allowed", "iodepth",
    "read_iops", "write_iops", "read_bw_Mb", "write_bw_Mb",
    "read_lat_mean_us", "read_lat_p99_us", "write_lat_mean_us", "write_lat_p99_us",
    "cpu_usr", "cpu_sys", "cpu_total"
]

# === 修改：将 rwmixwrite 拆分为六种独立类型（新增三项）===
test_type_map = {
    "bs": re.compile(r"^test_bs=.*$"),

    # ✅ 原有三种 rwmixwrite 场景
    "rwmixwrite-4k-32": re.compile(r"^test_rwmixwrite-4k-32=.*$"),   # bs=4k, iodepth=32
    "rwmixwrite-4k-8": re.compile(r"^test_rwmixwrite-4k-8=.*$"),     # bs=4k, iodepth=8
    "rwmixwrite-64k": re.compile(r"^test_rwmixwrite-64k=.*$"),       # bs=64k, iodepth=32

    # ✅ 新增三种 rwmixwrite 场景
    "rwmixwrite-4k-128": re.compile(r"^test_rwmixwrite-4k-128=.*$"), # bs=4k, iodepth=128
    "rwmixwrite-4k-16": re.compile(r"^test_rwmixwrite-4k-16=.*$"),   # bs=4k, iodepth=16
    "rwmixwrite-64k-8": re.compile(r"^test_rwmixwrite-64k-8=.*$"),   # bs=64k, iodepth=8

    "numjobs": re.compile(r"^test_numjobs=.*$"),
    "nbcpu": re.compile(r"^test_nbcpu=.*$"),
    "iodepth": re.compile(r"^test_iodepth=.*$"),
    "numjobs-bw": re.compile(r"^test_numjobs-bw=.*$"),
    "nbcpu-bw": re.compile(r"^test_nbcpu-bw=.*$"),
}

# === 修改：为六种 rwmixwrite 场景定义排序规则（新增三项）===
test_order = {
    "bs": ["4k", "8k", "16k", "32k", "64k", "128k"],

    # ✅ 原有三种
    "rwmixwrite-4k-32": ["0", "25", "50", "75", "100"],
    "rwmixwrite-4k-8": ["0", "25", "50", "75", "100"],
    "rwmixwrite-64k": ["0", "25", "50", "75", "100"],

    # ✅ 新增三种
    "rwmixwrite-4k-128": ["0", "25", "50", "75", "100"],
    "rwmixwrite-4k-16": ["0", "25", "50", "75", "100"],
    "rwmixwrite-64k-8": ["0", "25", "50", "75", "100"],

    "numjobs": [str(i) for i in range(1, 17)],
    "nbcpu": [str(i) for i in range(1, 17)],
    "iodepth": ["1", "2", "4", "8", "16", "32", "64", "128"],
    "numjobs-bw": [str(i) for i in range(1, 17)],
    "nbcpu-bw": [str(i) for i in range(1, 17)],
}


# ==================== 辅助函数 ====================

def parse_job(job):
    """解析单个 job 的性能数据"""
    read = job.get("read", {})
    write = job.get("write", {})
    return {
        "read_iops": round(read.get("iops", 0) / 1000, 6),        # KIOPS
        "write_iops": round(write.get("iops", 0) / 1000, 6),
        "read_bw_Mb": round(read.get("bw", 0) / 1024, 6),         # MB/s
        "write_bw_Mb": round(write.get("bw", 0) / 1024, 6),
        "read_lat_mean_us": round(read.get("clat_ns", {}).get("mean", 0) / 1000, 6),    # μs
        "read_lat_p99_us": round(read.get("clat_ns", {}).get("percentile", {}).get("99.000000", 0) / 1000, 6),
        "write_lat_mean_us": round(write.get("clat_ns", {}).get("mean", 0) / 1000, 6),
        "write_lat_p99_us": round(write.get("clat_ns", {}).get("percentile", {}).get("99.000000", 0) / 1000, 6),
        "cpu_usr": round(job.get("usr_cpu", 0), 6),
        "cpu_sys": round(job.get("sys_cpu", 0), 6),
        "cpu_total": round(job.get("usr_cpu", 0) + job.get("sys_cpu", 0), 6),
    }


def extract_test_params(filename):
    """
    从文件名提取参数，支持：
    - test_bs=4k.json
    - test_rwmixwrite-4k-32=50_randrw.json → bs=4k, iodepth=32, rwmixwrite=50
    - test_rwmixwrite-64k=100_randrw.json → bs=64k, rwmixwrite=100
    - 新增：test_rwmixwrite-4k-128=75_randrw.json → bs=4k, iodepth=128, rwmixwrite=75
    """
    base = os.path.basename(filename).replace(".json", "")
    parts = base.split("_")
    params = {}

    for part in parts:
        if "=" in part:
            key_end = part.find("=")
            k = part[:key_end]
            v = part[key_end+1:]

            # 特殊处理 rwmixwrite-*：从中提取 bs 和 iodepth
            if k.startswith("rwmixwrite"):
                suffix = k[len("rwmixwrite-"):]  # 得到 "4k-32" 或 "64k" 或 "4k-128"
                subparts = suffix.split("-")
                if len(subparts) >= 1:
                    bs_candidate = subparts[0]
                    if any(c in bs_candidate.lower() for c in 'kmKM'):
                        params["bs"] = bs_candidate.lower()
                if len(subparts) >= 2:
                    try:
                        int(subparts[1])  # 判断是否为数字（iodepth）
                        params["iodepth"] = subparts[1]
                    except ValueError:
                        pass  # 忽略非数字
                params["rwmixwrite"] = v  # rwmixwrite 值来自 "=" 右边

            # 常规参数
            elif k == "bs":
                params["bs"] = v
            elif k == "numjobs":
                params["numjobs"] = v
            elif k == "nbcpu":
                params["nbcpu"] = v
            elif k == "iodepth":
                params["iodepth"] = v
            elif k == "rwmixwrite":
                params["rwmixwrite"] = v
            elif k == "numjobs-bw":
                params["numjobs"] = v
            elif k == "nbcpu-bw":
                params["nbcpu"] = v

    return params


def get_test_type(filename):
    """识别测试类型"""
    base = os.path.basename(filename)
    for key, pattern in test_type_map.items():
        if pattern.match(base):
            return key
    return "unknown"


def get_sort_key(filename):
    """获取排序键，用于正确排序数据"""
    test_type = get_test_type(filename)
    if test_type not in test_order:
        return (float('inf'), 0)

    params = extract_test_params(filename)
    
    # 根据测试类型决定排序值
    if test_type in ["bs"]:
        value = params.get("bs", "")
    elif test_type.startswith("rwmixwrite"):  # 所有 rwmixwrite 类型统一处理
        value = params.get("rwmixwrite", "0")
    elif test_type in ["numjobs", "numjobs-bw"]:
        value = params.get("numjobs", "1")
    elif test_type in ["nbcpu", "nbcpu-bw"]:
        value = params.get("nbcpu", "1")
    elif test_type == "iodepth":
        value = params.get("iodepth", "32")
    else:
        value = ""

    try:
        idx = test_order[test_type].index(value)
    except ValueError:
        idx = len(test_order[test_type])
    
    type_idx = list(test_order.keys()).index(test_type)
    return (type_idx, idx)


# ==================== 主程序 ====================
def main():
    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()

        # 获取所有 JSON 文件
        files = [f for f in os.listdir(input_dir) if f.endswith(".json")]
        files.sort(key=get_sort_key)  # 按测试类型和参数排序

        for file in files:
            filepath = os.path.join(input_dir, file)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"❌ 无法读取 {file}: {e}")
                continue

            if not data.get("jobs"):
                print(f"⚠️ 无 jobs 数据: {file}")
                continue

            job_data = data["jobs"][0]
            base = os.path.basename(file)
            params = extract_test_params(file)

            # === 识别 rw_mode ===
            if "randread" in base and "randrw" not in base:
                rw_mode = "randread"
            elif "randwrite" in base and "randrw" not in base:
                rw_mode = "randwrite"
            elif "_read.json" in base and "randrw" not in base:
                rw_mode = "read"
            elif "_write.json" in base and "randrw" not in base:
                rw_mode = "write"
            elif "randrw" in base:
                rw_mode = "randrw"
            else:
                rw_mode = "unknown"

            # === 识别测试类型 ===
            test_type = get_test_type(file)

            # === 提取参数（优先使用 extract_test_params 的结果）===
            bs_val = params.get("bs", "4k")
            rwmixwrite_val = params.get("rwmixwrite", "0")
            numjobs_val = params.get("numjobs", "1")
            cpus_allowed_val = params.get("nbcpu", "1")
            iodepth_val = params.get("iodepth", "32")

            # === 构造输出行 ===
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

    print(f"✅ 所有结果已汇总并保存至 {output_csv}")


if __name__ == "__main__":
    main()