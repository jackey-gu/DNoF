#!/bin/bash

# 定义变量
DEVICE="/dev/nvme4n1"
NUM_JOBS=4 # 总job数
SYNC_IO_PERCENTAGES=(0 25 50 75 100) # 不同同步I/O比例测试
RUNTIME=30 # 每次测试运行时间（秒）

# 输出目录
OUTPUT_DIR="syncCPU_async_benchmark"
mkdir -p "$OUTPUT_DIR"

# 支持的测试模式：rw_mode, block_size
RW_MODES=(
    "randwrite,4k"
    "randread,4k"
    "write,64k"
    "read,64k"
)

# 遍历每个测试模式
for mode in "${RW_MODES[@]}"; do
    IFS=',' read -r rw_mode bs <<< "$mode"
    echo "=== 开始测试模式: $rw_mode, bs=$bs ==="

    # 遍历每个同步I/O比例进行测试
    for SYNC_IO_PERCENTAGE in "${SYNC_IO_PERCENTAGES[@]}"; do
        echo "==> 开始测试同步I/O比例: ${SYNC_IO_PERCENTAGE}%"

        # 计算同步和异步job的数量
        SYNC_JOBS=$(( (NUM_JOBS * SYNC_IO_PERCENTAGE + 99) / 100 ))
        ASYNC_JOBS=$(( NUM_JOBS - SYNC_JOBS ))

        echo "==> Sync Jobs:   $SYNC_JOBS"
        echo "==> Async Jobs:  $ASYNC_JOBS"

        # 创建临时配置文件
        tmpfile=$(mktemp)

        cat > "$tmpfile" <<EOF
[global]
ioengine=libaio
direct=1
time_based
runtime=$RUNTIME
group_reporting=0  # 关键：禁用汇总，每个 job 独立输出
size=1G
EOF

        for ((i=1; i<=NUM_JOBS; i++)); do
            if [ $i -le $SYNC_JOBS ]; then
                # 同步 I/O job
                cat >> "$tmpfile" <<EOF

[psync_job$i]
rw=$rw_mode
bs=$bs
iodepth=32
numjobs=1
cpus_allowed=1
filename=$DEVICE
ioengine=psync
EOF
            else
                # 异步 I/O job
                cat >> "$tmpfile" <<EOF

[libaio_job$i]
rw=$rw_mode
bs=$bs
iodepth=32
numjobs=1
cpus_allowed=1
filename=$DEVICE
ioengine=libaio
EOF
            fi
        done

        output_file="$OUTPUT_DIR/test_${rw_mode}_bs${bs}_sync${SYNC_IO_PERCENTAGE}.json"

        # 执行 fio
        fio --output="$output_file" --output-format=json "$tmpfile"

        rm -f "$tmpfile"

        echo "==> 测试完成，结果保存至: $output_file"
    done
done

echo "✅ 所有测试已完成，结果保存在目录: $OUTPUT_DIR"