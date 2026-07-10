#! /bin/bash -v

insmod /home/gwh/blk-switch-master/drivers/nvme/host/nvme-core.ko
insmod /home/gwh/blk-switch-master/drivers/nvme/host/nvme-fabrics.ko
insmod /home/gwh/blk-switch-master/drivers/nvme/host/nvme-pci.ko

sleep 2

nvme connect -t rdma -n testnqn -a 192.168.1.1 
