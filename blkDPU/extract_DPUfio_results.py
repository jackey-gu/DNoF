import os
import json
import csv
import re

# ================== 配置区 ==================
input_dir = r"C:\Users\jackey_gu\Desktop\脚本\DPIO\blkDPU\fio_results_nbcu_vs_numjobs"
output_csv = r"C:\Users\jackey_gu\Desktop\脚本\DPIO\blkDPU\DPU_nvmeof_40DPUsupplement_summary.csv"

fields = [
    "filename", "test_type", "rw_mode", "bs", "numjobs",
    "read_iops_K", "write_iops_K", "read_bw_MiB", "write_bw_MiB",
    "read_lat_mean_us", "read_lat_p99_us", "write_lat_mean_us", "write_lat_p99_us",
    "cpu_usr", "cpu_sys", "cpu_total"
]

# ✅ 修复：将 'numjobs' 改为 'nbcpu'，与实际文件名一致
test_type_patterns = {
    # ✅ 原来是 numjobs -> 现在改为 nbcpu
    "nbcpu": re.compile(r"test_nbcpu=(\d+)_(randwrite|randread)\.json$"),
    "nbcpu-bw": re.compile(r"test_nbcpu-bw=(\d+)_(read|write)\.json$")
}

# 排序顺序：numjobs/nbcpu 从 1 到 40
test_order = [str(i) for i in range(1, 41)]

# =============================================
#               解析函数
# =============================================

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

def get_sort_key(filename):
    """获取排序键：按 test_type + numjobs 数值排序"""
    for test_type, pattern in test_type_patterns.items():
        match = pattern.search(filename)
        if match:
            numjobs_val = int(match.group(1))
            type_order = 0 if test_type == "nbcpu" else 1  # ✅ 同步修改判断条件
            return (type_order, numjobs_val)
    return (float('inf'), 0)

# =============================================
#               主程序
# =============================================

with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fields)
    writer.writeheader()

    files = [f for f in os.listdir(input_dir) if f.endswith(".json")]
    files.sort(key=get_sort_key)

    for file in files:
        filepath = os.path.join(input_dir, file)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ 无法读取文件: {file}，错误: {e}")
            continue

        if not data.get("jobs"):
            print(f"⚠️ 文件 {file} 中没有 jobs 数据")
            continue

        job_data = data["jobs"][0]

        # 匹配测试类型和提取参数
        test_type = "unknown"
        numjobs_val = ""
        rw_mode = ""

        for ttype, pattern in test_type_patterns.items():
            match = pattern.search(file)
            if match:
                test_type = ttype
                numjobs_val = match.group(1)
                rw_mode = match.group(2)
                break

        if test_type == "unknown":
            print(f"⏭️ 跳过未知文件: {file}")
            continue

        # 固定参数：根据 test_type 设置 bs
        bs_val = "4k" if test_type == "nbcpu" else "64k"  # ✅ 这里也改为 nbcpu

        row = {
            "filename": file,
            "test_type": test_type,
            "rw_mode": rw_mode,
            "bs": bs_val,
            "numjobs": numjobs_val,
        }

        row.update(parse_job(job_data))
        writer.writerow(row)

print(f"✅ 测试结果已成功汇总至: {output_csv}")