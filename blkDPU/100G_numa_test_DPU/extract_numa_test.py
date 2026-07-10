import os
import json
import csv
import re

# ================== 配置区 ==================
input_dir = r"C:\Users\jackey_gu\Desktop\脚本\DPIO\blkDPU\100G_numa_test_DPU"
output_csv = r"C:\Users\jackey_gu\Desktop\脚本\DPIO\blkDPU\100G_numa_test_DPU\100G_numa_test_DPU_summary.csv"

fields = [
    "filename", "test_type", "rw_mode", "bs", "cpu_list",  # ✅ 新增 cpu_list 字段
    "read_iops_K", "write_iops_K", "read_bw_MiB", "write_bw_MiB",
    "read_lat_mean_us", "read_lat_p99_us", "write_lat_mean_us", "write_lat_p99_us",
    "cpu_usr", "cpu_sys", "cpu_total"
]

# ✅ 修复：正则匹配你实际生成的文件名格式
test_type_patterns = {
    # 匹配: test_NBCPU-RAND_cpus0_randwrite.json
    "NBCPU-RAND": re.compile(r"test_NBCPU-RAND_cpus([0-9_,]+)_(randwrite|randread)\.json$"),
    # 匹配: test_NBCPU-BW_cpus0_1_10_21_write.json
    "NBCPU-BW": re.compile(r"test_NBCPU-BW_cpus([0-9_,]+)_(write|read)\.json$")
}

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
    """排序：先 NBCPU-RAND，再 NBCPU-BW；按 CPU 列表字符串排序（可自定义）"""
    for test_type, pattern in test_type_patterns.items():
        match = pattern.search(filename)
        if match:
            type_order = 0 if test_type == "NBCPU-RAND" else 1
            cpu_list = match.group(1)
            # 可以按 CPU 数量粗略排序（可选）
            cpu_count = len(cpu_list.split('_'))
            return (type_order, cpu_count)
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
        cpu_list = ""
        rw_mode = ""

        for ttype, pattern in test_type_patterns.items():
            match = pattern.search(file)
            if match:
                test_type = ttype
                cpu_list = match.group(1)  # 提取 CPU 列表，如 "0", "0_1_10_21"
                rw_mode = match.group(2)
                break

        if test_type == "unknown":
            print(f"⏭️ 跳过未知文件: {file}")
            continue

        # 固定参数：根据 test_type 设置 bs
        bs_val = "4k" if test_type == "NBCPU-RAND" else "64k"

        row = {
            "filename": file,
            "test_type": test_type,
            "rw_mode": rw_mode,
            "bs": bs_val,
            "cpu_list": cpu_list,  # ✅ 记录实际使用的 CPU 列表
        }

        row.update(parse_job(job_data))
        writer.writerow(row)

print(f"✅ 测试结果已成功汇总至: {output_csv}")