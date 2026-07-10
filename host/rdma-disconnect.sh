#! /bin/bash -v

nvme disconnect -n nqn0

sleep 2

rmmod /home/gwh/gwh-nvme-5.4.43/host/nvme-rdma.ko
rmmod /home/gwh/gwh-nvme-5.4.43/host/nvme-fabrics.ko
# rmmod /home/gwh/gwh-nvme-5.4.43/host/nvme-core.ko
