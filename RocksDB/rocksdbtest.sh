#!/bin/bash

# ===================================================================
# NVMeoF + RocksDB 性能测试脚本（CPU 绑定版）
# 功能：所有测试在 CPU1 上运行，确保公平对比
# 环境：无 DPU、无 NUMA、标准 x86_64
# ===================================================================

# === 配置区 ===
CPU_CORE=1                                # 绑定到 CPU1
DEVICE_NAME="md0"                     # 你的 NVMeoF 设备名
PARTITION="/dev/md0"         # 若未分区，请改为 /dev/nvme4n1 PARTITION="/dev/${DEVICE_NAME}p1"   
MOUNT_POINT="/mnt/nvmeof"                 # 挂载目录
DB_PATH="${MOUNT_POINT}/rocksdb_bench"    # RocksDB 数据库存储路径
DB_BENCH="/home/gwh/filebench/rocksdb-main/db_bench"         # db_bench 可执行文件路径
LOG_DIR="/home/gwh/DPIO/rocksdb/rocksdbnvmeof_perf_logs"        # 日志保存目录

# 测试参数
KEY_SIZE=16
VALUE_SIZE=100
NUM_KEYS=10000000          # 1000万条记录（约 1.16GB）
DURATION=30               # 混合测试运行时间（秒）
THREADS=4                  # 推荐较小线程数以匹配单核性能

# 时间戳与日志
DATE_TAG=$(date +"%Y%m%d_%H%M%S")
RESULT_FILE="${LOG_DIR}/result_cpu${CPU_CORE}_${DATE_TAG}.log"
mkdir -p "$LOG_DIR" "$MOUNT_POINT" "$DB_PATH"

# ===================================================================
# 工具函数
# ===================================================================

log() {
    echo "[$(date +'%H:%M:%S')] $1" | tee -a "$RESULT_FILE"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

# 检查 taskset 是否可用
check_taskset() {
    if ! command -v taskset &> /dev/null; then
        error_exit "taskset 未找到，请安装 util-linux"
    fi
    log "taskset 检测正常，将绑定到 CPU$CPU_CORE"
}

# 检查设备
check_device() {
    if ! lsblk | grep -q "$DEVICE_NAME"; then
        error_exit "设备 $DEVICE_NAME 未连接或未识别"
    fi
    log "设备 $DEVICE_NAME 检测正常"
}

# 挂载设备
mount_device() {
    if ! mountpoint -q "$MOUNT_POINT"; then
        log "挂载 $PARTITION 到 $MOUNT_POINT"
        sudo mount "$PARTITION" "$MOUNT_POINT" || error_exit "挂载失败"
        sudo chown -R $USER:$USER "$MOUNT_POINT"
    else
        log "$MOUNT_POINT 已挂载"
    fi
}

# 清理数据库
cleanup() {
    log "清理数据库 $DB_PATH"
    rm -rf "$DB_PATH"/*
}

# 运行带 CPU 绑定的 db_bench
run_bench() {
    local test_name=$1
    local extra_args=$2
    log "开始测试: $test_name (CPU$CPU_CORE, threads=$THREADS)"

    # 关键：使用 taskset 绑定 CPU
    taskset -c $CPU_CORE $DB_BENCH \
        --db="$DB_PATH" \
        --benchmarks="$test_name" \
        --num="$NUM_KEYS" \
        --key_size="$KEY_SIZE" \
        --value_size="$VALUE_SIZE" \
        --use_direct_io_for_flush_and_compaction=true \
        --use_direct_reads=true \
        --duration="$DURATION" \
        --threads="$THREADS" \
        --stats_interval_seconds=10 \
        --statistics \
        $extra_args 2>&1 | tee -a "$RESULT_FILE"

    log "测试完成: $test_name"
    echo -e "\n#----------------------------------------\n" >> "$RESULT_FILE"
    sleep 3
}

# ===================================================================
# 主流程
# ===================================================================

log "NVMeoF RocksDB 性能测试启动(CPU 绑定模式)"
log "目标 CPU: CPU$CPU_CORE | 设备: $DEVICE_NAME | 线程: $THREADS"

# 检查依赖
[ ! -x "$DB_BENCH" ] && error_exit "db_bench 不存在或不可执行: $DB_BENCH"
check_taskset
check_device
mount_device
cleanup

# === 开始测试序列 ===
run_bench "fillrandom" "--disable_auto_compactions=false"
run_bench "readrandom" ""
run_bench "readwhilewriting" "--threads=3"          # 3读 + 1写
# run_bench "seekrandom" "--seek_nexts=10"
# run_bench "compact" "--num=20000000 --num_levels=6"

# 最终清理
cleanup

log "所有测试完成，结果已保存至: $RESULT_FILE"
log "建议使用: ps -eo pid,psr,comm | grep db_bench 验证 CPU 绑定"