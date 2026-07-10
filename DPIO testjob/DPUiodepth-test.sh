#!/bin/bash -v

# ================== 配置区 ==================
DEVICE="/dev/nvme3n2"                # 测试设备
OUTPUT_DIR="DPU_fio_variable_benchmark" # 输出目录
mkdir -p "$OUTPUT_DIR"

# 测试参数列表
BS_VALUES=("4k" "8k" "16k" "32k" "64k" "128k")
RWMIXWRITE_VALUES=(0 25 50 75 100)
NUMJOBS_VALUES=(1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16)
NBCPU_VALUES=(1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16)
IODEPTH_VALUES=(1 2 4 8 16 32 64 128)

# 支持的读写模式
RW_MODES=("randwrite" "randread")
BW_MODES=("write" "read")  # 带宽测试使用顺序读写

# ================== 测试函数 ==================
run_test() {
    local var_name="$1"               # 要测试的参数名
    local var_values=("${!2}")        # 参数值数组
    local extra_args_template="$3"    # 参数替换模板
    local fixed_args="$4"             # 固定参数
    local rw_mode="$5"                # 当前读写模式

    echo "=== 正在测试变量: $var_name ($rw_mode) ==="

    for value in "${var_values[@]}"; do
        echo "==> 测试 $var_name=$value ($rw_mode)"

        # 替换模板中的 % 为实际值
        local extra_args=$(echo "$extra_args_template" | sed "s/%/$value/")

        # 构建输出文件名
        local output_file="$OUTPUT_DIR/test_${var_name,,}=${value}_${rw_mode}.json"

        # 执行 FIO 命令
        fio \
            --name=nvme4 \
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
}

# ================== 开始测试 ==================

# # --- 随机读写测试 ---
# for rw_mode in "${RW_MODES[@]}"; do

#     echo "==> 开始测试随机读写模式: $rw_mode"

#     # 测试块大小 (bs)
#     run_test "BS" "BS_VALUES[@]" "--bs=%" "--numjobs=1 --iodepth=32 --cpus_allowed=1-1" "$rw_mode"

#     # 测试读写比例 (rwmixwrite)
#     run_test "RWMIXWRITE" "RWMIXWRITE_VALUES[@]" "--rwmixwrite=% --rw=randrw" "--bs=4k --numjobs=1 --iodepth=32 --cpus_allowed=1-1" "$rw_mode"

#     # 测试并发 job 数 (numjobs) - 默认场景
#     run_test "NUMJOBS" "NUMJOBS_VALUES[@]" "--numjobs=%" "--bs=4k --iodepth=32 --cpus_allowed=1-16 --rw=$rw_mode" "$rw_mode"

#     # 测试 CPU 核心数 (nbcpu) - 默认场景
#     run_test "NBCPU" "NBCPU_VALUES[@]" "--cpus_allowed=1-%" "--bs=4k --numjobs=16 --iodepth=32 --rw=$rw_mode" "$rw_mode"

#     # 测试队列深度 (iodepth)
#     run_test "IODEPTH" "IODEPTH_VALUES[@]" "--iodepth=%" "--bs=4k --numjobs=1 --cpus_allowed=1-1 --rw=$rw_mode" "$rw_mode"

# done

# --- 带宽测试（顺序读写）---
for rw_mode in "${BW_MODES[@]}"; do

    echo "==> 开始测试带宽模式: $rw_mode"

    # # 测试并发 job 数 (numjobs) - 带宽优化场景
    # run_test "NUMJOBS-BW" "NUMJOBS_VALUES[@]" "--numjobs=%" "--bs=64k --iodepth=32 --cpus_allowed=1-16 --rw=$rw_mode" "$rw_mode"

    # # 测试 CPU 核心数 (nbcpu) - 带宽优化场景
    # run_test "NBCPU-BW" "NBCPU_VALUES[@]" "--cpus_allowed=1-%" "--bs=64k --numjobs=16 --iodepth=32 --rw=$rw_mode" "$rw_mode"

    # 测试读写比例 (rwmixwrite)
    run_test "RWMIXWRITE" "RWMIXWRITE_VALUES[@]" "--rwmixwrite=%" "--bs=64k --numjobs=1 --iodepth=32 --cpus_allowed=1-1" "$rw_mode"

    # 测试队列深度 (iodepth)
    run_test "IODEPTH" "IODEPTH_VALUES[@]" "--iodepth=%" "--bs=64k --numjobs=1 --cpus_allowed=1-1 --rw=$rw_mode" "$rw_mode"

done

echo "所有测试完成，结果保存在 $OUTPUT_DIR 目录中"