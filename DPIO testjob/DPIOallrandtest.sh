#!/bin/bash -v

# 固定参数
iodepth=32
nbcpu=40
cpus_allowed="0-39"

# numjobs 从 1 到 40（可选：1~40 之间逐步增加）
for num in {1..40}
do
    # ========== IOPS 测试（bs=4k, randread/randwrite）==========
    for rw_mode in randread randwrite
    do
        bs=4
        output_file="test_numjobs=${num}_${rw_mode}.json"
        echo "Running: numjobs=$num, bs=${bs}k, rw=$rw_mode, nbcpu=$nbcpu, iodepth=$iodepth"
        fio --name=nvme3 --filename=/dev/nvme3n2 \
            --name=nvme4 --filename=/dev/nvme4n1 \
            --direct=1 --ioengine=libaio --size=15G --time_based --runtime=30 \
            --iodepth=$iodepth --numjobs=$num --bs=${bs}k --rw=$rw_mode \
            --cpus_allowed=$cpus_allowed \
            --output=$output_file --output-format=json
    done

    # ========== Bandwidth 测试（bs=64k, read/write）==========
    for rw_mode in read write
    do
        bs=64
        output_file="test_numjobs-bw=${num}_${rw_mode}.json"
        echo "Running: numjobs=$num, bs=${bs}k, rw=$rw_mode, nbcpu=$nbcpu, iodepth=$iodepth"
        fio --name=nvme3 --filename=/dev/nvme3n2 \
            --name=nvme4 --filename=/dev/nvme4n1 \
            --direct=1 --ioengine=libaio --size=15G --time_based --runtime=30 \
            --iodepth=$iodepth --numjobs=$num --bs=${bs}k --rw=$rw_mode \
            --cpus_allowed=$cpus_allowed \
            --output=$output_file --output-format=json
    done
done