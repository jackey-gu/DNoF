#! /bin/bash -v

insmod /home/gwh/blk-switch-master/drivers/nvme/host/nvme-core.ko
insmod /home/gwh/blk-switch-master/drivers/nvme/host/nvme-fabrics.ko
insmod /home/gwh/blk-switch-master/drivers/nvme/host/nvme-tcp.ko

sleep 2

nvme connect -t tcp -n nqn0 -a 12.0.0.88 -s 4420
