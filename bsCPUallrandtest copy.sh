#!/bin/bash -v

# ================== 配置区 ==================
DEVICE="/dev/nvme4n1"                # 测试设备
OUTPUT_DIR="fio_nvme4n1_benchmark"   # 输出目录
rw="randrw"                          # 读写模式
START_BS=4                           # 起始块大小 (KB)
MAX_BS=128                           # 最大块大小 (KB)
RWMIXWRITE_VALUES=(0 25 50 75 100)   # 混合读写比例
NUMJOBS_VALUES=(1 2 4 8 16)          # 并发 job 数
NBCPU_VALUES=(1 2 4 8 16)               # CPU 核心数（不能超过 numjobs）
IODEPTH_VALUES=(1 2 4 8 16 32 64 128) # 队列深度
REPEAT=3                             # 每组测试重复次数

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# ================== 主循环 ==================
for bs in "${NUMBS_VALUES[@]:-$(seq $START_BS $((START_BS*2)) $MAX_BS)}"; do
    for rwmixwrite in "${RWMIXWRITE_VALUES[@]}"; do
        for num in "${NUMJOBS_VALUES[@]}"; do
            for nbcpu in "${NBCPU_VALUES[@]}"; do
                # 限制 nbcpu 不超过 numjobs
                if (( nbcpu > num )); then
                    continue
                fi

                for iodepth in "${IODEPTH_VALUES[@]}"; do
                    for ((repeat = 1; repeat <= REPEAT; repeat++)); do

                        echo "=== 当前参数 ==="
                        echo "bs= $bs k"
                        echo "rwmixwrite= $rwmixwrite"
                        echo "num= $num"
                        echo "nbcpu= $nbcpu"
                        echo "iodepth= $iodepth"
                        echo "重复次数= $repeat"
                        echo "================"

                        # 构建输出文件名
                        output_file="$OUTPUT_DIR/test_bs${bs}k_rw${rwmixwrite}_iodepth${iodepth}_num${num}_cpu${nbcpu}_repeat${repeat}.json"

                        # 执行 FIO 命令
                        fio \
                            --name=nvme4 \
                            --filename="$DEVICE" \
                            --group_reporting \
                            --direct=1 \
                            --ioengine=libaio \
                            --size=15G \
                            --time_based \
                            --runtime=20 \
                            --iodepth="$iodepth" \
                            --numjobs="$num" \
                            --bs="${bs}k" \
                            --rw="$rw" \
                            --cpus_allowed=1-$nbcpu \
                            --rwmixwrite="$rwmixwrite" \
                            --output="$output_file" \
                            --output-format=json

                    done
                done
            done
        done
    done
done

echo "所有测试完成，结果保存在 $OUTPUT_DIR 目录中"