#!/bin/bash

# 定义变量
DEVICE="/dev/nvme4n1"
RUNTIME=30 # 每次测试运行时间（秒）
OUTPUT_DIR="addbufferedCPU_direct_benchmark"
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
    "mixed"               # 混合比例：0%~100% Buffered I/O
    "buffered1_directN"   # 固定 1 个 Buffered job，Direct job 从 0 到 16
    "direct1_bufferedN"   # 固定 1 个 Direct job，Buffered job 从 0 到 16
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
                # 混合 Buffered/Direct 比例测试（共 4 个 job）
                BUFFERED_PERCENTAGES=(0 25 50 75 100)
                for BUFFERED_PERCENTAGE in "${BUFFERED_PERCENTAGES[@]}"; do
                    echo "==> 开始测试 Buffered I/O 比例: ${BUFFERED_PERCENTAGE}%"

                    BUFFERED_JOBS=$(( (4 * BUFFERED_PERCENTAGE + 99) / 100 ))
                    DIRECT_JOBS=$(( 4 - BUFFERED_JOBS ))

                    echo "==> Buffered Jobs: $BUFFERED_JOBS, Direct Jobs: $DIRECT_JOBS"

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

                    # 添加 Buffered jobs (direct=0)
                    for ((i=1; i<=BUFFERED_JOBS; i++)); do
                        cat >> "$tmpfile" <<EOF

[buffered_job$i]
rw=$rw_mode
bs=$bs
iodepth=32
numjobs=1
cpus_allowed=1
filename=$DEVICE
direct=0
EOF
                    done

                    # 添加 Direct jobs (direct=1)
                    for ((i=1; i<=DIRECT_JOBS; i++)); do
                        cat >> "$tmpfile" <<EOF

[direct_job$i]
rw=$rw_mode
bs=$bs
iodepth=32
numjobs=1
cpus_allowed=1
filename=$DEVICE
direct=1
EOF
                    done

                    output_file="$OUTPUT_DIR/test_${test_type}_${rw_mode}_bs${bs}_buffered${BUFFERED_PERCENTAGE}.json"
                    fio --output="$output_file" --output-format=json "$tmpfile"
                    rm -f "$tmpfile"
                    echo "==> 测试完成，结果保存至: $output_file"
                done
                ;;

            "buffered1_directN")
                # 固定 1 个 Buffered job，Direct job 数量从 0 到 16
                for DIRECT_JOBS in {0..16}; do
                    BUFFERED_JOBS=1
                    echo "==> Buffered Jobs: $BUFFERED_JOBS, Direct Jobs: $DIRECT_JOBS"

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

                    # Buffered job (direct=0)
                    cat >> "$tmpfile" <<EOF

[buffered_job1]
rw=$rw_mode
bs=$bs
iodepth=32
numjobs=1
cpus_allowed=1
filename=$DEVICE
direct=0
EOF

                    # Direct jobs (direct=1)
                    for ((i=1; i<=DIRECT_JOBS; i++)); do
                        cat >> "$tmpfile" <<EOF

[direct_job$i]
rw=$rw_mode
bs=$bs
iodepth=32
numjobs=1
cpus_allowed=1
filename=$DEVICE
direct=1
EOF
                    done

                    output_file="$OUTPUT_DIR/test_${test_type}_${rw_mode}_bs${bs}_direct${DIRECT_JOBS}.json"
                    fio --output="$output_file" --output-format=json "$tmpfile"
                    rm -f "$tmpfile"
                    echo "==> 测试完成，结果保存至: $output_file"
                done
                ;;

            "direct1_bufferedN")
                # 固定 1 个 Direct job，Buffered job 数量从 0 到 16
                for BUFFERED_JOBS in {0..16}; do
                    DIRECT_JOBS=1
                    echo "==> Buffered Jobs: $BUFFERED_JOBS, Direct Jobs: $DIRECT_JOBS"

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

                    # Buffered jobs (direct=0)
                    for ((i=1; i<=BUFFERED_JOBS; i++)); do
                        cat >> "$tmpfile" <<EOF

[buffered_job$i]
rw=$rw_mode
bs=$bs
iodepth=32
numjobs=1
cpus_allowed=1
filename=$DEVICE
direct=0
EOF
                    done

                    # Direct job (direct=1)
                    cat >> "$tmpfile" <<EOF

[direct_job1]
rw=$rw_mode
bs=$bs
iodepth=32
numjobs=1
cpus_allowed=1
filename=$DEVICE
direct=1
EOF

                    output_file="$OUTPUT_DIR/test_${test_type}_${rw_mode}_bs${bs}_buffered${BUFFERED_JOBS}.json"
                    fio --output="$output_file" --output-format=json "$tmpfile"
                    rm -f "$tmpfile"
                    echo "==> 测试完成，结果保存至: $output_file"
                done
                ;;
        esac
    done
done

echo "✅ 所有测试已完成，结果保存在目录: $OUTPUT_DIR"