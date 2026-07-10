#! /bin/bash -v

insmod /home/gwh/blk-switch-master/drivers/nvme/host/nvme-core.ko
insmod /home/gwh/blk-switch-master/drivers/nvme/host/nvme-fabrics.ko
insmod /home/gwh/blk-switch-master/drivers/nvme/host/i10-host.ko

sleep 2

nvme connect -t i10 -n nqn0 -a 12.0.0.88 -s 4420
