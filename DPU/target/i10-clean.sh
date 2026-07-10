#!/bin/sh -v

rm -rf /sys/kernel/config/nvmet/ports/1/subsystems/nqn0
rmdir /sys/kernel/config/nvmet/ports/1
rmdir /sys/kernel/config/nvmet/subsystems/nqn0/namespaces/1
rmdir /sys/kernel/config/nvmet/subsystems/nqn0

sleep 2

rmmod /home/gwh/blk-switch-master/drivers/nvme/target/i10-target.ko
rmmod /home/gwh/blk-switch-master/drivers/nvme/target/nvmet.ko
