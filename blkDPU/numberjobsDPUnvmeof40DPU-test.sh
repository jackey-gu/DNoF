#!/bin/bash -v

# ================== 配置区 ==================
DEVICE="/dev/nvme3n2"               # 测试设备
OUTPUT_DIR="/home/gwh/DPIO/blktrace/fio_results_nbcu_vs_numjobs_cpu1"  # 新目录名，避免混淆
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$OUTPUT_DIR"

# numjobs 从 1 到 40
NUMJOBS_VALUES=($(seq 1 40))

# 读写模式
RAND_RW_MODES=("randwrite" "randread")
SEQ_RW_MODES=("write" "read")

# 固定绑定到 CPU 1
CPU_TO_BIND=1

# ================== 测试函数 ==================
run_test() {
    local var_name="$1"
    local var_values=("${!2}")
    local extra_args_template="$3"
    local fixed_args="$4"
    local rw_modes=("${!5}")

    echo "=== 正在测试变量: $var_name ==="

    for numjobs in "${var_values[@]}"; do
        for rw_mode in "${rw_modes[@]}"; do
            echo "==> 测试 $var_name=$numjobs (cpus_allowed=$CPU_TO_BIND, numjobs=$numjobs) [$rw_mode]"

            # 替换模板中的 % 为 numjobs（只替换一次）
            local extra_args=$(echo "$extra_args_template" | sed "s/%/$numjobs/g")

            local output_file="$OUTPUT_DIR/${TIMESTAMP}_test_${var_name,,}=${numjobs}_${rw_mode}.json"

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

echo "【FIO 测试开始】时间: $TIMESTAMP, 设备: $DEVICE, 绑定 CPU: $CPU_TO_BIND, numjobs=1~40" | tee "$OUTPUT_DIR/run.log"

# 1. 随机读写：4K + iodepth=64 + numjobs=N（所有 job 绑定到 CPU 1）
run_test "NUMJOBS" "NUMJOBS_VALUES[@]" \
    "--cpus_allowed=$CPU_TO_BIND --numjobs=%" \
    "--bs=4k --iodepth=64" \
    "RAND_RW_MODES[@]"

# 2. 顺序读写：64K + iodepth=64 + numjobs=N
run_test "NUMJOBS-BW" "NUMJOBS_VALUES[@]" \
    "--cpus_allowed=$CPU_TO_BIND --numjobs=%" \
    "--bs=64k --iodepth=64" \
    "SEQ_RW_MODES[@]"

echo "【FIO 测试完成】结果保存在: $OUTPUT_DIR"