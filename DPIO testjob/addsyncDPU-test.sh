#!/bin/bash

# 定义变量
DEVICE="/dev/nvme3n2"
RUNTIME=30 # 每次测试运行时间（秒）
OUTPUT_DIR="addsyncDPU_async_benchmark"
mkdir -p "$OUTPUT_DIR"

# 支持的测试模式：rw_mode, block_size
RW_MODES=(
    "randwrite,4k"
    "randread,4k"
    "write,64k"
    "read,64k"
)

# 支持的测试类型
TEST_TYPES=(
    "mixed"     # 原有混合同步/异步比例测试
    "sync1_asyncN"  # 固定 1 个同步，异步从 0 到 16
    "async1_syncN"  # 固定 1 个异步，同步从 0 到 16
)

# 遍历每个测试类型
for test_type in "${TEST_TYPES[@]}"; do
    echo "=== 开始测试类型: $test_type ==="

    # 遍历每个测试模式
    for mode in "${RW_MODES[@]}"; do
        IFS=',' read -r rw_mode bs <<< "$mode"
        echo "==> 开始测试模式: $rw_mode, bs=$bs"

        case "$test_type" in
            "mixed")
                # 原有混合同步/异步比例测试
                SYNC_IO_PERCENTAGES=(0 25 50 75 100)
                for SYNC_IO_PERCENTAGE in "${SYNC_IO_PERCENTAGES[@]}"; do
                    echo "==> 开始测试同步I/O比例: ${SYNC_IO_PERCENTAGE}%"

                    SYNC_JOBS=$(( (4 * SYNC_IO_PERCENTAGE + 99) / 100 ))
                    ASYNC_JOBS=$(( 4 - SYNC_JOBS ))

                    echo "==> Sync Jobs: $SYNC_JOBS, Async Jobs: $ASYNC_JOBS"

                    tmpfile=$(mktemp)
                    cat > "$tmpfile" <<EOF
[global]
ioengine=libaio
direct=1
time_based
runtime=$RUNTIME
group_reporting=0
size=1G
EOF

                    for ((i=1; i<=4; i++)); do
                        if [ $i -le $SYNC_JOBS ]; then
                            cat >> "$tmpfile" <<EOF

[sync_job$i]
rw=$rw_mode
bs=$bs
iodepth=32
numjobs=1
cpus_allowed=1
filename=$DEVICE
ioengine=sync
EOF
                        else
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

                    output_file="$OUTPUT_DIR/test_${test_type}_${rw_mode}_bs${bs}_sync${SYNC_IO_PERCENTAGE}.json"
                    fio --output="$output_file" --output-format=json "$tmpfile"
                    rm -f "$tmpfile"
                    echo "==> 测试完成，结果保存至: $output_file"
                done
                ;;

            "sync1_asyncN")
                # 固定 1 个同步 job，异步 job 从 0 到 16
                for ASYNC_JOBS in {0..16}; do
                    SYNC_JOBS=1
                    echo "==> Sync Jobs: $SYNC_JOBS, Async Jobs: $ASYNC_JOBS"

                    tmpfile=$(mktemp)
                    cat > "$tmpfile" <<EOF
[global]
ioengine=libaio
direct=1
time_based
runtime=$RUNTIME
group_reporting=0
size=1G
EOF

                    # 同步 job
                    cat >> "$tmpfile" <<EOF

[sync_job1]
rw=$rw_mode
bs=$bs
iodepth=32
numjobs=1
cpus_allowed=1
filename=$DEVICE
ioengine=sync
EOF

                    # 异步 jobs
                    for ((i=1; i<=$ASYNC_JOBS; i++)); do
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
                    done

                    output_file="$OUTPUT_DIR/test_${test_type}_${rw_mode}_bs${bs}_async${ASYNC_JOBS}.json"
                    fio --output="$output_file" --output-format=json "$tmpfile"
                    rm -f "$tmpfile"
                    echo "==> 测试完成，结果保存至: $output_file"
                done
                ;;

            "async1_syncN")
                # 固定 1 个异步 job，同步 job 从 0 到 16
                for SYNC_JOBS in {0..16}; do
                    ASYNC_JOBS=1
                    echo "==> Sync Jobs: $SYNC_JOBS, Async Jobs: $ASYNC_JOBS"

                    tmpfile=$(mktemp)
                    cat > "$tmpfile" <<EOF
[global]
ioengine=libaio
direct=1
time_based
runtime=$RUNTIME
group_reporting=0
size=1G
EOF

                    # 同步 jobs
                    for ((i=1; i<=$SYNC_JOBS; i++)); do
                        cat >> "$tmpfile" <<EOF

[sync_job$i]
rw=$rw_mode
bs=$bs
iodepth=32
numjobs=1
cpus_allowed=1
filename=$DEVICE
ioengine=sync
EOF
                    done

                    # 异步 job
                    cat >> "$tmpfile" <<EOF

[libaio_job1]
rw=$rw_mode
bs=$bs
iodepth=32
numjobs=1
cpus_allowed=1
filename=$DEVICE
ioengine=libaio
EOF

                    output_file="$OUTPUT_DIR/test_${test_type}_${rw_mode}_bs${bs}_sync${SYNC_JOBS}.json"
                    fio --output="$output_file" --output-format=json "$tmpfile"
                    rm -f "$tmpfile"
                    echo "==> 测试完成，结果保存至: $output_file"
                done
                ;;
        esac
    done
done

echo "✅ 所有测试已完成，结果保存在目录: $OUTPUT_DIR"