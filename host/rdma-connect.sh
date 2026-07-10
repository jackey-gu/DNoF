#! /bin/bash -v

# insmod /home/gwh/gwh-nvme-5.4.43/host/nvme-core.ko
insmod /home/gwh/gwh-nvme-5.4.43/host/nvme-fabrics.ko
insmod /home/gwh/gwh-nvme-5.4.43/host/nvme-rdma.ko

sleep 2

nvme connect -t rdma -n nqn0 -a 25.8.0.12 -s 4420 
