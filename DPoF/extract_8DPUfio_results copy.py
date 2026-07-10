import os
import json
import csv
import re

# ================== 配置区 ==================
# 请修改为你的实际路径
input_dir = r"C:\Users\jackey_gu\Desktop\脚本\DPIO\DPoF\DPU_nvmeof_8CPU_fio_variable_benchmark_supplement"
output_csv = r"C:\Users\jackey_gu\Desktop\脚本\DPIO\DPoF\DPU_nvmeof_8DPUsupplement_summary.csv"

# CSV 输出字段
# 🔔 注意：numjobs 字段实际表示 "使用的 CPU 数量"，可考虑改名，但为兼容绘图脚本先保留
fields = [
    "filename", "test_type", "rw_mode", "bs", "numjobs",  # numjobs 实际是 ncpu
    "read_iops_K", "write_iops_K", "read_bw_MiB", "write_bw_MiB",
    "read_lat_mean_us", "read_lat_p99_us", "write_lat_mean_us", "write_lat_p99_us",
    "cpu_usr", "cpu_sys", "cpu_total"
]

# ✅ 修改这里：nbcpu 而不是 ncpu
test_type_patterns = {
    "nbcpu": re.compile(r"^test_nbcpu=(\d+)_(randwrite|randread)\.json$"),
    "nbcpu-bw": re.compile(r"^test_nbcpu-bw=(\d+)_(read|write)\.json$")
}

# 排序顺序：ncpu 从 1 到 8
test_order = [str(i) for i in range(1, 9)]  # ✅ 从 1 到 8

# =============================================
#               解析函数
# =============================================

def parse_job(job):
    """解析单个 job 的性能数据"""
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
    """获取排序键：按 test_type + ncpu 数值排序"""
    for test_type, pattern in test_type_patterns.items():
        match = pattern.match(filename)
        if match:
            ncpu_val = int(match.group(1))
            type_order = 0 if test_type == "ncpu" else 1
            return (type_order, ncpu_val)
    return (float('inf'), 0)

# =============================================
#               主程序
# =============================================

with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fields)
    writer.writeheader()

    # 获取所有 JSON 文件
    files = [f for f in os.listdir(input_dir) if f.endswith(".json")]
    files.sort(key=get_sort_key)  # 按 test_type 和 ncpu 排序

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

        job_data = data["jobs"][0]  # 假设只有一个 job

        # 匹配测试类型和提取参数
        test_type = "unknown"
        ncpu_val = ""
        rw_mode = ""

        for ttype, pattern in test_type_patterns.items():
            match = pattern.match(file)
            if match:
                test_type = ttype
                ncpu_val = match.group(1)  # 提取 CPU 数量
                rw_mode = match.group(2)
                break

        if test_type == "unknown":
            print(f"⏭️ 跳过未知文件: {file}")
            continue

        # 固定参数：bs 根据 test_type 设置
        bs_val = "4k" if test_type == "ncpu" else "64k"

        # 构建输出行
        row = {
            "filename": file,
            "test_type": test_type,
            "rw_mode": rw_mode,
            "bs": bs_val,
            "numjobs": ncpu_val,  # 🔔 注意：这里 "numjobs" 字段实际存储的是 CPU 数量
        }

        row.update(parse_job(job_data))
        writer.writerow(row)

print(f"✅ 测试结果已成功汇总至: {output_csv}")