import os
import json
import csv
import re

# ================== 配置区 ==================
# 输入目录：对应 Bash 脚本中的 OUTPUT_DIR
input_dir = r"C:\Users\jackey_gu\Desktop\脚本\DPIO\RWVirtSSD\remote_CPU_fio_variable_benchmark" 
# 输出文件
output_csv = r"C:\Users\jackey_gu\Desktop\脚本\DPIO\RWVirtSSD\remote_CPU_fio_variable_benchmark\results_summary.csv"

# 定义 CSV 字段
fields = [
    "filename", "test_type", "rw_mode", "bs", "rwmixwrite", "numjobs", "cpus_allowed", "iodepth",
    "read_iops", "write_iops", "read_bw_Mb", "write_bw_Mb",
    "read_lat_mean_us", "read_lat_p99_us", "write_lat_mean_us", "write_lat_p99_us",
    "cpu_usr", "cpu_sys", "cpu_total"
]

# ================== 测试类型映射与排序 ==================
# 根据 Bash 脚本生成的文件名模式进行匹配
test_type_map = {
    "bs": re.compile(r"^test_bs=.*$"),
    "numjobs": re.compile(r"^test_numjobs=.*$"),
    "cpus_allowed": re.compile(r"^test_cpumask=.*$"),       # 注意：Bash 脚本中变量名为 NBCPU，但参数是 --cpus_allowed
    "iodepth": re.compile(r"^test_iodepth=.*$"),
    "rwmixwrite": re.compile(r"^test_rwmixwrite=.*$"),
    "numjobs-bw": re.compile(r"^test_numjobs-bw=.*$"),
    "cpus_allowed-bw": re.compile(r"^test_cpumask-bw=.*$"), # 带宽测试的 CPU 绑定
}

# 定义期望的参数顺序（用于排序）
test_order = {
    "bs": ["4k", "8k", "16k", "32k", "64k", "128k"],
    "numjobs": [str(i) for i in range(1, 17)],
    "cpus_allowed": [str(i) for i in range(1, 17)],
    "iodepth": ["1", "2", "4", "8", "16", "32", "64", "128"],
    "rwmixwrite": ["0", "25", "50", "75", "100"],
    "numjobs-bw": [str(i) for i in range(1, 17)],
    "cpus_allowed-bw": [str(i) for i in range(1, 17)],
}

# ================== 辅助函数 ==================

def parse_job(job):
    """从 FIO JSON 中提取关键性能指标"""
    read = job.get("read", {})
    write = job.get("write", {})
    
    # 安全获取嵌套字典数据
    def get_lat_p99(data):
        return data.get("clat_ns", {}).get("percentile", {}).get("99.000000", 0) / 1000 if data else 0

    return {
        "read_iops": read.get("iops", 0) / 1000, # 转换为 K IOPS
        "write_iops": write.get("iops", 0) / 1000,
        "read_bw_Mb": read.get("bw", 0) / 1024,  # 转换为 MB/s
        "write_bw_Mb": write.get("bw", 0) / 1024,
        "read_lat_mean_us": read.get("clat_ns", {}).get("mean", 0) / 1000,
        "read_lat_p99_us": get_lat_p99(read),
        "write_lat_mean_us": write.get("clat_ns", {}).get("mean", 0) / 1000,
        "write_lat_p99_us": get_lat_p99(write),
        "cpu_usr": job.get("usr_cpu", 0),
        "cpu_sys": job.get("sys_cpu", 0),
        "cpu_total": job.get("usr_cpu", 0) + job.get("sys_cpu", 0),
    }

def extract_test_params(filename):
    """解析文件名提取参数"""
    base = os.path.basename(filename).replace(".json", "")
    parts = base.split("_")
    params = {}
    for part in parts:
        if "=" in part:
            k, v = part.split("=", 1)
            params[k.lower()] = v
    return params

def get_sort_key(file):
    """获取排序键"""
    test_type = "unknown"
    for key, pattern in test_type_map.items():
        if pattern.match(file):
            test_type = key
            break
    
    params = extract_test_params(file)
    
    # 针对不同的测试类型提取对应的变量值
    if test_type == "bs":
        value = params.get("bs", "")
    elif test_type in ["numjobs", "iodepth", "rwmixwrite", "numjobs-bw"]:
        value = params.get(test_type, "")
    elif test_type in ["cpus_allowed", "cpus_allowed-bw"]:
        # 文件名中可能是 cpumask=1-4 这种格式，这里简单处理取第一个数字或直接用字符串排序
        # 如果文件名是 cpumask=4，直接取值；如果是 1-4，取开头
        raw_val = params.get("cpumask", "") 
        value = raw_val.split("-")[0] if "-" in raw_val else raw_val
    else:
        value = ""
        
    return test_type, value

def custom_sort(file):
    """自定义排序逻辑"""
    test_type, value = get_sort_key(file)
    if test_type not in test_order:
        return (float('inf'), 0)
    
    order_list = test_order[test_type]
    try:
        idx = order_list.index(value)
    except ValueError:
        idx = len(order_list) # 如果找不到，排在最后
    
    # 先按测试类型排序，再按参数值排序
    return (list(test_order.keys()).index(test_type), idx)

# ================== 主程序 ==================

print(f"正在扫描目录: {input_dir}")
files = [f for f in os.listdir(input_dir) if f.endswith(".json")]

if not files:
    print("❌ 未找到 JSON 文件，请检查 input_dir 路径是否正确。")
else:
    # 排序文件
    files.sort(key=custom_sort)
    
    with open(output_csv, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()

        for file in files:
            filepath = os.path.join(input_dir, file)
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"读取文件失败 {file}: {e}")
                continue

            # 1. 提取基础参数
            params = extract_test_params(file)
            
            # 2. 识别读写模式
            base = os.path.basename(file)
            rw_mode = "unknown"
            if "randread" in base: rw_mode = "randread"
            elif "randwrite" in base: rw_mode = "randwrite"
            elif "read" in base: rw_mode = "read"
            elif "write" in base: rw_mode = "write"
            elif "randrw" in base: rw_mode = "randrw"

            # 3. 识别测试类型
            test_type = "unknown"
            for key, pattern in test_type_map.items():
                if pattern.match(file):
                    test_type = key
                    break

            if not data.get("jobs"):
                continue
            
            job_data = data["jobs"][0]
            
            # 4. 根据测试类型填充固定参数 (参考 Bash 脚本中的固定参数设置)
            # 初始化默认值
            bs_val = params.get("bs", "")
            rwmixwrite_val = params.get("rwmixwrite", "")
            numjobs_val = params.get("numjobs", "")
            # 处理 cpumask 参数提取
            cpus_raw = params.get("cpumask", "")
            cpus_allowed_val = cpus_raw.split("-")[0] if "-" in cpus_raw else cpus_raw # 简化显示
            iodepth_val = params.get("iodepth", "")

            # 根据 Bash 脚本逻辑补全非变量参数
            if test_type == "bs":
                # Bash: --numjobs=1 --iodepth=32 --cpus_allowed=1-1
                numjobs_val = "1"
                iodepth_val = "32"
                cpus_allowed_val = "1"
            
            elif test_type == "numjobs":
                # Bash: --bs=4k --iodepth=32 --cpus_allowed=1-16
                bs_val = "4k"
                iodepth_val = "32"
                cpus_allowed_val = "1-16" # 允许所有核
            
            elif test_type == "cpus_allowed":
                # Bash: --bs=4k --numjobs=16 --iodepth=32
                bs_val = "4k"
                numjobs_val = "16"
                iodepth_val = "32"
            
            elif test_type == "iodepth":
                # Bash: --bs=4k --numjobs=1 --cpus_allowed=1-1
                bs_val = "4k"
                numjobs_val = "1"
                cpus_allowed_val = "1"

            elif test_type == "rwmixwrite":
                # Bash: --bs=4k --numjobs=1 --iodepth=32 (或 8)
                bs_val = "4k"
                numjobs_val = "1"
                # iodepth 保持文件名中的值（32 或 8）
                cpus_allowed_val = "1"

            elif test_type == "numjobs-bw":
                # Bash: --bs=64k --iodepth=32 --cpus_allowed=1-16
                bs_val = "64k"
                iodepth_val = "32"
                cpus_allowed_val = "1-16"

            elif test_type == "cpus_allowed-bw":
                # Bash: --bs=64k --numjobs=16 --iodepth=32
                bs_val = "64k"
                numjobs_val = "16"
                iodepth_val = "32"

            # 5. 构建行数据
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

            # 更新性能数据
            row.update(parse_job(job_data))
            writer.writerow(row)

    print(f"✅ 处理完成！共处理 {len(files)} 个文件。")
    print(f"📄 结果已保存至: {output_csv}")