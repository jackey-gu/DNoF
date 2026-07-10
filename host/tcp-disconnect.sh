#! /bin/bash -v

nvme disconnect -n nqn0

sleep 2

rmmod /home/gwh/blk-switch-master/drivers/nvme/host/nvme-tcp.ko
rmmod /home/gwh/blk-switch-master/drivers/nvme/host/nvme-fabrics.ko
rmmod /home/gwh/blk-switch-master/drivers/nvme/host/nvme-core.ko
