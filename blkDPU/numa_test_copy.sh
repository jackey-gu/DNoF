#!/bin/bash -v

# ================== 配置区 ==================
DEVICE="/dev/nvme4n1"                # 测试设备
OUTPUT_DIR="numa_test_DPU"           # 固定目录名
mkdir -p "$OUTPUT_DIR"

# 🔽 精确指定你要测试的 CPU 组合（共 8 组）
CPU_COMBINATIONS=(
    "0"                       # 基线
    "0,1"                     # 双核并行
    "0,1,10"                  # 扩展 NUMA 0
    "0,1,10,20"               # 跨 NUMA 到 20（非关键核心）
    "0,1,10,21"               # 🔥 关键：包含中断核心 CPU 21
    "19"                      # 🔥 单独测试主中断核心 CPU 19
    "21"                      # 🔥 单独测试 q0 中断核心 CPU 21
    "9,19,21,39"              # 🔥 四大中断核心并行  cat /proc/interrupts | grep nvme3 发现只有9，19,39
    "1,10,20"                 # 🔥 三大numa并行
    "19,21,39"                # 🔥 三大中断核心并行
    "10,20,30"
    "0,10"
    "0,10,20"
    "10,20"
)

# 读写模式
RAND_RW_MODES=("randwrite" "randread")
SEQ_RW_MODES=("write" "read")

# ================== 测试函数 ==================
run_test() {
    local test_name="$1"           # 测试名称，如 "NBCPU-RAND"
    local cpu_list="$2"            # 要绑定的 CPU 列表，如 "0,1,10,20"
    local bs="$3"                  # 块大小
    local rw_modes=("${!4}")       # 读写模式数组

    echo "=== 正在测试: $test_name (cpus_allowed=$cpu_list, bs=$bs) ==="

    for rw_mode in "${rw_modes[@]}"; do
        echo "==> 测试 $test_name: cpus=$cpu_list, bs=$bs ($rw_mode)"

        # 构建输出文件名：用下划线连接 CPU，更清晰
        local cpu_tag=$(echo "$cpu_list" | tr ',' '_')
        local output_file="$OUTPUT_DIR/test_${test_name}_cpus${cpu_tag}_${rw_mode}.json"

        # 执行 FIO 命令（⚠️ 注意：每行末尾的 \ 后不能有任何空格或制表符！）
        fio \
            --name=nvme3_${test_name}_${rw_mode} \
            --filename="$DEVICE" \
            --group_reporting \
            --direct=1 \
            --ioengine=libaio \
            --size=100G \
            --time_based \
            --runtime=30 \
            --numjobs=5 \
            --iodepth=64 \
            --bs="$bs" \
            --cpus_allowed="$cpu_list" \
            --cpus_allowed_policy=split \
            --rw="$rw_mode" \
            --output="$output_file" \
            --output-format=json
    done
}

# ================== 开始精准测试 ==================

echo "✅ 开始 DPU CPU 亲和性精准测试"
echo "设备: $DEVICE"
echo "结果目录: $OUTPUT_DIR"
echo ""

# 1. 随机读写测试（randread/randwrite, bs=4k）
for cpu_set in "${CPU_COMBINATIONS[@]}"; do
    run_test "NBCPU-RAND" "$cpu_set" "4k" "RAND_RW_MODES[@]"
done

# 2. 顺序读写测试（read/write, bs=64k）
for cpu_set in "${CPU_COMBINATIONS[@]}"; do
    run_test "NBCPU-BW" "$cpu_set" "64k" "SEQ_RW_MODES[@]"
done

echo "🎉 所有 $((${#CPU_COMBINATIONS[@]} * 2 * 2)) 项测试完成！"
echo "结果保存在: ./$OUTPUT_DIR/"