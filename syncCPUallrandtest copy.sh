#!/bin/bash -v

# 输出目录
OUTPUT_DIR="fio_sync_async_ratio_test"
mkdir -p "$OUTPUT_DIR"

# 设备路径
DEVICE="/dev/nvme4n1"

# 最外层循环：同步写比例
SYNC_IO_PERCENTAGES=(0 10 20 30 40 50 60 70 80 90 100)

# 主循环参数
rw="randwrite"

for sync_percentage in "${SYNC_IO_PERCENTAGES[@]}"; do

for ((bs = 4; bs <= 128; bs *= 2)); do
for ((rwmixwrite = 0; rwmixwrite <= 100; rwmixwrite += 25)); do
for ((num = 1; num <= 16; num *= 2 )); do
for ((nbcpu = 1; nbcpu <= num && nbcpu < 16; nbcpu *= 2)); do
for ((iodepth = 1; iodepth <= 128; iodepth *= 2 )); do
for ((repeat = 1; repeat <= 3; repeat++)); do

    echo "=== 当前参数 ==="
    echo "sync_io_percentage= $sync_percentage%"
    echo "bs= $bs k"
    echo "rwmixwrite= $rwmixwrite"
    echo "num= $num"
    echo "nbcpu= $nbcpu"
    echo "iodepth= $iodepth"
    echo "重复次数= $repeat"
    echo "================"

    # 总 job 数
    TOTAL_JOBS=10

    # 计算同步和异步 job 数量
    SYNC_JOBS=$(( (TOTAL_JOBS * sync_percentage + 99) / 100 ))
    ASYNC_JOBS=$(( TOTAL_JOBS - SYNC_JOBS ))

    # 构建基础 FIO 参数
    args=(
        --name=nvme4
        --filename="$DEVICE"
        --group_reporting
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
        if (( i <= SYNC_JOBS )); then
            # 同步写：使用 psync 引擎
            args+=(--name="$jobname" --filename="$DEVICE" --ioengine=psync --direct=1)
        else
            # 异步写：使用 libaio 引擎
            args+=(--name="$jobname" --filename="$DEVICE" --ioengine=libaio --direct=1)
        fi
    done

    # 构建输出文件名
    output_file="$OUTPUT_DIR/test_bs${bs}k_rw${rwmixwrite}_iodepth${iodepth}_num${num}_cpu${nbcpu}_sync${sync_percentage}_repeat${repeat}.json"

    # 执行 FIO 命令
    fio "${args[@]}" --output="$output_file" --output-format=json

done    # repeat
done    # iodepth
done    # nbcpu
done    # num
done    # rwmixwrite
done    # bs

done    # sync_percentage