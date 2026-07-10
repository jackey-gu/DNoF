#!/bin/sh -v

rm -rf /sys/kernel/config/nvmet/ports/1/subsystems/nqn0
rmdir /sys/kernel/config/nvmet/ports/1
rmdir /sys/kernel/config/nvmet/subsystems/nqn0/namespaces/1
rmdir /sys/kernel/config/nvmet/subsystems/nqn0

sleep 2

rmmod /lib/modules/5.4.43/kernel/drivers/nvme/target/nvmet-rdma.ko
rmmod /lib/modules/5.4.43/kernel/drivers/nvme/target/nvmet.ko
