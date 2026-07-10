#!/bin/bash

# ===================================================================
# NVMeoF + RocksDB 性能测试脚本（40GB 磁盘适配版 - 默认读写混合）
# 新增：默认 readwhilewriting 混合负载测试
# ===================================================================




# === 配置区 ===
CPU_CORE="1,2"                                # 绑定到 CPU1 2
DEVICE_NAME="nvme2n2"                     # 你的 NVMeoF 设备名
PARTITION="/dev/nvme2n2"                  # 若未分区，请改为 /dev/nvme2n2p1
MOUNT_POINT="/mnt/nvmeof"                 # 挂载目录
DB_PATH="${MOUNT_POINT}/rocksdb_bench"    # RocksDB 数据库存储路径
DB_BENCH="/home/gwh/filebench/rocksdb-main/db_bench"        # db_bench 可执行文件路径
LOG_DIR="/home/gwh/DPIO/rocksdb/small_multibs_DPU_rocksdbnvmeof_perf_logs" # 日志保存目录


# 测试块大小：64B 到 1K
BLOCK_SIZES=(64 128 256 512 1024) 

# 数据量：1000万条
NUM_KEYS=10000000        
KEY_SIZE=16                               
DURATION=60                               
THREADS=4                                 

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

check_taskset() {
    if ! command -v taskset &> /dev/null; then
        error_exit "taskset 未找到"
    fi
    log "taskset 检测正常，绑定到 CPU$CPU_CORE"
}

check_device() {
    if ! lsblk | grep -q "$DEVICE_NAME"; then
        error_exit "设备 $DEVICE_NAME 未识别"
    fi
    log "设备 $DEVICE_NAME 检测正常"
}

mount_device() {
    if ! mountpoint -q "$MOUNT_POINT"; then
        log "挂载 $PARTITION 到 $MOUNT_POINT"
        sudo mount "$PARTITION" "$MOUNT_POINT" || error_exit "挂载失败"
        sudo chown -R $USER:$USER "$MOUNT_POINT"
    else
        log "$MOUNT_POINT 已挂载"
    fi
}

cleanup() {
    log "清理数据库 $DB_PATH 及系统缓存"
    rm -rf "$DB_PATH"/*
    sync
    echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null 2>&1
}

# 通用测试运行函数
run_bench() {
    local test_name=$1
    local current_value_size=$2
    local extra_args=$3
    
    local total_data_gb=$(echo "scale=2; $NUM_KEYS * $current_value_size / 1024 / 1024 / 1024" | bc)
    
    log ">>> 开始测试: $test_name | 块大小=$current_value_size 字节 | 理论数据量≈${total_data_gb}GB"

    taskset -c $CPU_CORE $DB_BENCH \
        --db="$DB_PATH" \
        --benchmarks="$test_name" \
        --num="$NUM_KEYS" \
        --key_size="$KEY_SIZE" \
        --value_size="$current_value_size" \
        --use_direct_io_for_flush_and_compaction=true \
        --use_direct_reads=true \
        --duration="$DURATION" \
        --threads="$THREADS" \
        --stats_interval_seconds=10 \
        --statistics \
        $extra_args 2>&1 | tee -a "$RESULT_FILE"

    log ">>> 测试完成: $test_name | 块大小=$current_value_size"
    echo -e "\n#----------------------------------------\n" >> "$RESULT_FILE"
    
    sleep 3
}

# ===================================================================
# 主流程
# ===================================================================

log "NVMeoF RocksDB 解耦测试启动"
log "目标 CPU: CPU$CPU_CORE | 设备: $DEVICE_NAME"
log "测试块大小: ${BLOCK_SIZES[*]}"

# 检查依赖
[ ! -x "$DB_BENCH" ] && error_exit "db_bench 不存在"
check_taskset
check_device
mount_device

# === 核心大循环：针对每一个块大小，完成 测写 -> 清空 -> 填靶 -> 测读/混合 ===
for size in "${BLOCK_SIZES[@]}"; do
    log "==========================================================="
    log "【开始针对块大小 ${size} 字节的完整闭环测试】"
    log "==========================================================="

    # 1. 随机写入性能测试 (fillrandom) - 60秒测爆发性能，测完数据直接抛弃
    log "【1/4 随机写入性能测试 (fillrandom, 60秒)】"
    run_bench "fillrandom" "$size" "--disable_auto_compactions=false"

    # 2. 清空数据库，为接下来的读取测试准备干净环境
    log "【2/4 清理环境，准备填充读取测试的靶数据】"
    cleanup
    sleep 2

    # 3. 填充靶数据：不设时间限制，必须老老实实写完 15 万条，作为后续读取的“靶子”
    log "【3/4 填充读取测试的靶数据 (fillrandom, 不限时)】"
    taskset -c $CPU_CORE $DB_BENCH \
        --db="$DB_PATH" \
        --benchmarks="fillrandom" \
        --num="$NUM_KEYS" \
        --key_size="$KEY_SIZE" \
        --value_size="$size" \
        --use_direct_io_for_flush_and_compaction=true \
        --threads="$THREADS" \
        --disable_auto_compactions=true 2>&1 | tee -a "$RESULT_FILE"

    # 4. 随机读取测试 (readrandom) - 基于刚才填充的 15 万条靶数据进行 60 秒测试
    log "【4/4 随机读取 (readrandom)】"
    run_bench "readrandom" "$size" "--use_existing_db=1 --use_existing_keys=1"

    # 5. 读写混合测试 (readwhilewriting) - 继续基于现有的靶数据进行 60 秒混合测试
    log "【5/5 读写混合 (readwhilewriting)】"
    run_bench "readwhilewriting" "$size" "--use_existing_db=1 --use_existing_keys=1"

    # 当前块大小的所有测试做完后，彻底清理环境和缓存，准备测试下一个块大小
    log "【块大小 ${size} 测试全部完成，清理环境准备下一轮】"
    cleanup
    sleep 5
done

log "所有测试完成，结果已保存至: $RESULT_FILE"