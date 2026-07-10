#!/bin/bash -v

# ================== 配置区 ==================
DEVICE="/dev/nvme3n2"               # 测试设备
OUTPUT_DIR="/home/gwh/DPIO/blktrace/fio_results_nbcu_vs_numjobs" # 建议放在 blktrace 目录下
# ✅ 移除 TIMESTAMP

mkdir -p "$OUTPUT_DIR"

# 系统有 40 个 CPU (0-39)，所以可以直接测试 1~40
NBCPU_VALUES=($(seq 1 40))

# 读写模式
RAND_RW_MODES=("randwrite" "randread")
SEQ_RW_MODES=("write" "read")

# ================== 测试函数 ==================
run_test() {
    local var_name="$1"
    local var_values=("${!2}")
    local extra_args_template="$3"
    local fixed_args="$4"
    local rw_modes=("${!5}")

    echo "=== 正在测试变量: $var_name ==="

    for value in "${var_values[@]}"; do
        local cpu_end=$((value - 1))  # cpus_allowed=0-(N-1)

        for rw_mode in "${rw_modes[@]}"; do
            echo "==> 测试 $var_name=$value (cpus_allowed=0-$cpu_end, numjobs=$value) [$rw_mode]"

            # 同时替换 cpus_allowed 和 numjobs
            local extra_args=$(echo "$extra_args_template" | sed "s/%/$cpu_end/g; s/%/$value/g")

            # ✅ 移除 $TIMESTAMP
            local output_file="$OUTPUT_DIR/test_${var_name,,}=${value}_${rw_mode}.json"

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

# ================== 开始测试 ==================

# 检查设备
if [ ! -b "$DEVICE" ]; then
    echo "错误：设备 $DEVICE 不存在或不是块设备！"
    exit 1
fi

# ✅ 移除日志中的时间戳
echo "【FIO 测试开始】设备: $DEVICE, CPU: 40 核 (0-39)" | tee "$OUTPUT_DIR/run.log"

# 1. 随机读写：4K + iodepth=64 + numjobs=NBCPU
run_test "NBCPU" "NBCPU_VALUES[@]" \
    "--cpus_allowed=0-% --numjobs=%" \
    "--bs=4k --iodepth=64" \
    "RAND_RW_MODES[@]"

# 2. 顺序读写：64K + iodepth=64 + numjobs=NBCPU
run_test "NBCPU-BW" "NBCPU_VALUES[@]" \
    "--cpus_allowed=0-% --numjobs=%" \
    "--bs=64k --iodepth=64" \
    "SEQ_RW_MODES[@]"

echo "【FIO 测试完成】结果保存在: $OUTPUT_DIR"