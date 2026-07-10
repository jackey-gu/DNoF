#!/bin/bash

# 定义变量
DEVICE="/dev/nvme3n2"
NUM_JOBS=4
BUFFERED_PERCENTAGES=(0 25 50 75 100)
RUNTIME=30

RW_MODES=(
    "randwrite,4k"
    "randread,4k"
    "write,64k"
    "read,64k"
)

OUTPUT_DIR="bufferedDPU_direct_benchmark"
mkdir -p "$OUTPUT_DIR"

# 遍历模式
for mode in "${RW_MODES[@]}"; do
    IFS=',' read -r rw_mode bs <<< "$mode"
    echo "=== 开始测试模式: $rw_mode, bs=$bs ==="

    for BUFFERED_PERCENTAGE in "${BUFFERED_PERCENTAGES[@]}"; do
        echo "==> 缓存比例: ${BUFFERED_PERCENTAGE}%"

        BUFFERED_JOBS=$(( (NUM_JOBS * BUFFERED_PERCENTAGE + 99) / 100 ))
        DIRECT_JOBS=$(( NUM_JOBS - BUFFERED_JOBS ))

        echo "==> Buffered: $BUFFERED_JOBS, Direct: $DIRECT_JOBS"

        # 构建 fio 配置文件
        tmpfile=$(mktemp)
        cat > "$tmpfile" <<EOF
[global]
ioengine=libaio
direct=1
time_based
runtime=$RUNTIME
group_reporting=0  # 关键：禁用汇总，每个 job 独立输出
size=1G

[test_buffered_vs_direct]
EOF

        for ((i=1; i<=NUM_JOBS; i++)); do
            if [ $i -le $BUFFERED_JOBS ]; then
                direct=0
                jobname=buffered_job$i
            else
                direct=1
                jobname=direct_job$i
            fi

            cat >> "$tmpfile" <<EOF

[$jobname]
rw=$rw_mode
bs=$bs
iodepth=32
numjobs=1
cpus_allowed=1
filename=$DEVICE
direct=$direct
EOF
        done

        output_file="$OUTPUT_DIR/test_${rw_mode}_bs${bs}_buffered${BUFFERED_PERCENTAGE}.json"

        # 执行 fio
        fio --output="$output_file" --output-format=json "$tmpfile"

        rm -f "$tmpfile"

        echo "==> 结果保存至: $output_file"
    done
done

echo "✅ 测试完成"