#!/bin/bash -v

# 输出目录
OUTPUT_DIR="fio_buffered_direct_ratio_test"
mkdir -p "$OUTPUT_DIR"

# 设备路径
DEVICE="/dev/nvme4n1"

# 最外层：Buffered I/O 比例循环
BUFFERED_IO_PERCENTAGES=(0 25 50 75 100)

# 主循环参数
rw="randrw"

# 最外层循环：Buffered I/O 比例
for buffered_percentage in "${BUFFERED_IO_PERCENTAGES[@]}"; do

for ((bs = 4; bs <= 128; bs *= 2)); do
for ((rwmixwrite = 0; rwmixwrite <= 100; rwmixwrite += 25)); do
for ((num = 1; num <= 16; num *= 2 )); do
for ((nbcpu = 1; nbcpu <= num && nbcpu < 16; nbcpu *= 2)); do
for ((iodepth = 1; iodepth <= 128; iodepth *= 2 )); do
for ((repeat = 1; repeat <= 3; repeat++)); do

    echo "=== 当前参数 ==="
    echo "buffered_io_percentage= $buffered_percentage%"
    echo "bs= $bs k"
    echo "rwmixwrite= $rwmixwrite"
    echo "num= $num"
    echo "nbcpu= $nbcpu"
    echo "iodepth= $iodepth"
    echo "重复次数= $repeat"
    echo "================"

    # 计算 Buffered 和 Direct job 数量
    TOTAL_JOBS=10
    BUFFERED_JOBS=$(( (TOTAL_JOBS * buffered_percentage + 99) / 100 ))
    DIRECT_JOBS=$(( TOTAL_JOBS - BUFFERED_JOBS ))

    # 构建基础 FIO 参数
    args=(
        --name=nvme4
        --filename="$DEVICE"
        --group_reporting
        --ioengine=libaio
        --size=15G
        --time_based
        --runtime=20
        --iodepth="$iodepth"
        --bs="${bs}k"
        --rw="$rw"
        --cpus_allowed="1-$nbcpu"
        --rwmixwrite="$rwmixwrite"
    )

    # 构建每个 job 的参数
    for i in $(seq 1 $TOTAL_JOBS); do
        jobname="job$i"
        if (( i <= BUFFERED_JOBS )); then
            args+=(--name="$jobname" --filename="$DEVICE" --direct=0)
        else
            args+=(--name="$jobname" --filename="$DEVICE" --direct=1)
        fi
    done

    # 构建输出文件名
    output_file="$OUTPUT_DIR/test_bs${bs}k_rw${rwmixwrite}_iodepth${iodepth}_num${num}_cpu${nbcpu}_buf${buffered_percentage}_repeat${repeat}.json"

    # 执行 FIO 命令
    fio "${args[@]}" --output="$output_file" --output-format=json

done    # repeat
done    # iodepth
done    # nbcpu
done    # num
done    # rwmixwrite
done    # bs

done    # buffered_percentage