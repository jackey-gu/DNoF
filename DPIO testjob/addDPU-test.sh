#!/bin/bash -v

# ================== 配置区 ==================
DEVICE="/dev/nvme3n2"                # 测试设备
OUTPUT_DIR="addDPU_fio_variable_benchmark_supplement" # 新增输出目录
mkdir -p "$OUTPUT_DIR"

# 扩展参数范围
NUMJOBS_VALUES=({1..32})
NBCPU_VALUES=({1..32})

# 读写模式
RAND_RW_MODES=("randwrite" "randread")
SEQ_RW_MODES=("write" "read")

# ================== 测试函数 ==================
run_test() {
    local var_name="$1"               # 要测试的参数名
    local var_values=("${!2}")        # 参数值数组
    local extra_args_template="$3"    # 参数替换模板
    local fixed_args="$4"             # 固定参数
    local rw_modes=("${!5}")          # 当前读写模式数组

    echo "=== 正在测试变量: $var_name ==="

    for value in "${var_values[@]}"; do
        for rw_mode in "${rw_modes[@]}"; do
            echo "==> 测试 $var_name=$value ($rw_mode)"

            # 替换模板中的 % 为实际值
            local extra_args=$(echo "$extra_args_template" | sed "s/%/$value/")

            # 构建输出文件名
            local output_file="$OUTPUT_DIR/test_${var_name,,}=${value}_${rw_mode}.json"

            # 执行 FIO 命令
            fio \
                --name=nvme3 \
                --filename="$DEVICE" \
                --group_reporting \
                --direct=1 \
                --ioengine=libaio \
                --size=15G \
                --time_based \
                --runtime=30 \
                $fixed_args \
                $extra_args \
                --rw="$rw_mode" \
                --output="$output_file" \
                --output-format=json
        done
    done
}

# ================== 开始补充测试 ==================

# 1. numjobs 测试（随机读写）
run_test "NUMJOBS" "NUMJOBS_VALUES[@]" "--numjobs=%" "--bs=4k --iodepth=64 --cpus_allowed=1-16" "RAND_RW_MODES[@]"

# 2. nbcpu 测试（随机读写）
run_test "NBCPU" "NBCPU_VALUES[@]" "--cpus_allowed=1-%" "--bs=4k --numjobs=16 --iodepth=64" "RAND_RW_MODES[@]"

# 3. numjobs-bw 测试（顺序读写）
run_test "NUMJOBS-BW" "NUMJOBS_VALUES[@]" "--numjobs=%" "--bs=64k --iodepth=64 --cpus_allowed=1-16" "SEQ_RW_MODES[@]"

# 4. nbcpu-bw 测试（顺序读写）
run_test "NBCPU-BW" "NBCPU_VALUES[@]" "--cpus_allowed=1-%" "--bs=64k --numjobs=16 --iodepth=64" "SEQ_RW_MODES[@]"

echo "补充测试完成，结果保存在 $OUTPUT_DIR 目录中"