#!/bin/bash -v

# ========================================
# 超级增强版 blktrace + fio 联动脚本
# 支持：
#   - 多 CPU 组合测试
#   - 随机读写 (4k) + 顺序读写 (64k)
#   - 自动 btt 报告生成
# ========================================

# 设备路径
DEVICE_PATH="/dev/nvme3n2"

# 测试运行时间（秒）
TEST_RUNTIME=10

# 结果根目录
RESULT_ROOT="blktrace_DPU_analysis"
RESULT_DIR="$RESULT_ROOT"

# blktrace 控制 CPU（建议选一个空闲 CPU）
BLKTRACE_CONTROL_CPU=5

# 是否启用 NUMA 绑定（取消注释以启用）
# USE_NUMA_BIND=true
# NUMA_NODE=1  # 根据实际 DPU/NVMe 所在 NUMA 节点调整

# CPU 组合测试（格式：0,1,2）
CPU_COMBINATIONS=(
    "0"
    "0,1"
    "0,1,10"
    "0,1,10,20"
    "0,1,10,21"
    "19"
    "21"
    "9,19,21,39"
    "1,10,20"
    "19,21,39"
    "10,20,30"
    "0,10"
    "0,10,20"
    "10,20"
)

# ✅ FIO 测试模式：包含随机和顺序
FIO_RW_MODES=("randread" "randwrite" "read" "write")

# 公共 FIO 参数
FIO_DIRECT=1
FIO_IODEPTH=64
FIO_NUMJOBS=5
FIO_FILENAME="$DEVICE_PATH"

# 创建结果目录
mkdir -p "$RESULT_DIR"
echo "结果将保存到: $RESULT_DIR"

# 遍历每个 CPU 组合
for cpu_set in "${CPU_COMBINATIONS[@]}"; do
    # 生成目录名（替换逗号为下划线）
    CPU_TAG=$(echo "$cpu_set" | tr ',' '_')
    RUN_DIR="$RESULT_DIR/cpus_${CPU_TAG}"
    mkdir -p "$RUN_DIR"

    # blktrace 输出前缀
    BLKTRACE_OUT="$RUN_DIR/blktrace"
    FIO_LOG="$RUN_DIR/fio_output.json"

    # 遍历每种读写模式
    for rw_mode in "${FIO_RW_MODES[@]}"; do
        echo "=== 开始测试: cpus=${cpu_set}, rw=${rw_mode} ==="

        # 设置块大小：随机用 4k，顺序用 64k
        if [[ "$rw_mode" == "randread" || "$rw_mode" == "randwrite" ]]; then
            FIO_BS="4k"
        else
            FIO_BS="64k"
        fi

        # 启动 blktrace
        echo "启动 blktrace (控制 CPU ${BLKTRACE_CONTROL_CPU}) ..."
        taskset -c "$BLKTRACE_CONTROL_CPU" sudo blktrace -d "$DEVICE_PATH" \
            -o "${BLKTRACE_OUT}.${rw_mode}" -w 20 &
        BLKTRACE_PID=$!
        sleep 2  # 确保 blktrace 先启动

        # 构造 FIO 命令
        CMD="fio \
            --name=nvme3_blktrace_${rw_mode} \
            --filename=${FIO_FILENAME} \
            --rw=${rw_mode} \
            --bs=${FIO_BS} \
            --direct=${FIO_DIRECT} \
            --iodepth=${FIO_IODEPTH} \
            --numjobs=${FIO_NUMJOBS} \
            --runtime=${TEST_RUNTIME} \
            --time_based \
            --size=100G \
            --cpus_allowed=${cpu_set} \
            --cpus_allowed_policy=split \
            --output=${FIO_LOG} \
            --output-format=json \
            --log_avg_msec=100 \
            --write_iops_log=${RUN_DIR}/iops_${rw_mode} \
            --write_lat_log=${RUN_DIR}/lat_${rw_mode}"

        # 添加 NUMA 绑定（如果启用）
        if [ "${USE_NUMA_BIND}" = true ]; then
            CMD="numactl --cpunodebind=${NUMA_NODE} --membind=${NUMA_NODE} $CMD"
        fi

        echo "执行 FIO 命令..."
        taskset -c "$BLKTRACE_CONTROL_CPU" bash -c "$CMD"

        # 等待 blktrace 结束
        wait $BLKTRACE_PID

       # 生成 btt 报告
        echo "生成 btt 报告: $rw_mode"
        blkparse -q -i "${BLKTRACE_OUT}.${rw_mode}" | btt > "$RUN_DIR/btt_report.${rw_mode}.txt" 2>&1

        # 提取延迟分解（Q2G, G2I, I2C）
        LATENCY_TMP="$RUN_DIR/latency_tmp.${rw_mode}.txt"
        echo -e "\n=== 延迟分解 (Q2G, G2I, I2C) ===" >> "$RUN_DIR/btt_report.${rw_mode}.txt"
        blkparse -q -i "${BLKTRACE_OUT}.${rw_mode}" | btt -l "$LATENCY_TMP" >> "$RUN_DIR/btt_report.${rw_mode}.txt" 2>&1
        head -30 "$LATENCY_TMP" >> "$RUN_DIR/btt_report.${rw_mode}.txt" 2>/dev/null || true
        rm -f "$LATENCY_TMP"

        echo "✅ btt 报告已生成: $RUN_DIR/btt_report.${rw_mode}.txt"
    done
done

echo "✅ 所有测试完成！结果位于: $RESULT_DIR"