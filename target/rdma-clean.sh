#!/bin/sh -v

rm -rf /sys/kernel/config/nvmet/ports/1/subsystems/nqn0
rmdir /sys/kernel/config/nvmet/ports/1
rmdir /sys/kernel/config/nvmet/subsystems/nqn0/namespaces/1
rmdir /sys/kernel/config/nvmet/subsystems/nqn0

sleep 2

rmmod /home/gwh/gwh-nvme-5.4.43/target/nvmet-rdma.ko
rmmod /home/gwh/gwh-nvme-5.4.43/target/nvmet.ko

