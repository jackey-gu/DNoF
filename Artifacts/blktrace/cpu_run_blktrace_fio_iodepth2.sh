#!/bin/bash

# ========================================
# 增强版 blktrace + fio 联动脚本（支持 CPU 绑定）
# ========================================

# ----------------------------
# 配置参数（可修改）
# ----------------------------

DEVICE_PATH="/dev/nvme4n1"

TEST_RUNTIME=10
FIO_JOB_NAME="randread"
FIO_RW="randread"
FIO_BS="4k"
FIO_DIRECT=1
FIO_IODEPTH=1
FIO_NUMJOBS=1
FIO_FILENAME="$DEVICE_PATH"

REPEAT=1
RESULT_ROOT="CPU_dnof_overhead_results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULT_DIR="$RESULT_ROOT/${FIO_JOB_NAME}_bs${FIO_BS}_depth${FIO_IODEPTH}_direct${FIO_DIRECT}"

# ----------------------------
# 🔧 新增：CPU 与 NUMA 配置
# ----------------------------

# 方法 1：手动指定 CPU 核心（推荐用于 DNoF 分析）
FIO_CPU_CORE=4          # 运行 fio 的 CPU 核心（建议选与 DPU 同 NUMA 的核心）
BLKTRACE_CPU_CORE=1     # blktrace 可绑定到轻负载核心


# ----------------------------
# 创建结果目录
# ----------------------------
mkdir -p "$RESULT_DIR"
echo "结果将保存到: $RESULT_DIR"

# ----------------------------
# 主循环
# ----------------------------
for i in $(seq 1 $REPEAT); do
    echo "=== 第 $i 次测试开始 ==="
    RUN_DIR="$RESULT_DIR/run_${i}"
    mkdir -p "$RUN_DIR"

    BLKTRACE_OUT="$RUN_DIR/blktrace"
    FIO_LOG="$RUN_DIR/fio_output.json"
    FIO_LOG_TXT="$RUN_DIR/fio_output.txt"

    # ----------------------------
    # 启动 blktrace（绑定到指定 CPU）
    # ----------------------------
    echo "启动 blktrace (CPU $BLKTRACE_CPU_CORE) ..."
    taskset -c $BLKTRACE_CPU_CORE sudo blktrace -d "$DEVICE_PATH" -o "$BLKTRACE_OUT" -w $((TEST_RUNTIME + 10)) &
    BLKTRACE_PID=$!
    sleep 2

    # ----------------------------
    # 启动 fio（绑定到指定 CPU，优先与 DPU 同 NUMA）
    # ----------------------------
    echo "启动 fio (CPU $FIO_CPU_CORE) ..."
    taskset -c $FIO_CPU_CORE fio --name="$FIO_JOB_NAME" \
        --ioengine=libaio \
        --rw="$FIO_RW" \
        --bs="$FIO_BS" \
        --size=1G \
        --direct="$FIO_DIRECT" \
        --iodepth="$FIO_IODEPTH" \
        --numjobs="$FIO_NUMJOBS" \
        --runtime="$TEST_RUNTIME" \
        --time_based \
        --filename="$FIO_FILENAME" \
        --output="$FIO_LOG" \
        --output-format=json \
        --log_avg_msec=100 \
        --write_iops_log="$RUN_DIR/iops_log" \
        --write_lat_log="$RUN_DIR/latency_log" > "$FIO_LOG_TXT" 2>&1

    # ----------------------------
    # 等待 blktrace 结束
    # ----------------------------
    wait $BLKTRACE_PID

    # 生成 btt 报告
    btt -i "$BLKTRACE_OUT" > "$RUN_DIR/btt_report.txt" 2>&1
    echo "第 $i 次测试完成"
    sleep 3
done

echo "所有测试完成！结果目录: $RESULT_DIR"