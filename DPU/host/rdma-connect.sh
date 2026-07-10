#! /bin/bash -v
modprobe nvme_core multipath=N
modprobe nvme-rdma

sleep 2

nvme discover -t rdma -a 25.8.0.12 -s 4420

sleep 2

nvme connect -t rdma -n nqn0 -a 25.8.0.12 -s 4420





spdk_rpc.py bdev_nvme_attach_controller -b nqn0 -t rdma -f ipv4 -a 25.8.0.12 -s 4420 -n nqn0

snap_rpc.py controller_nvme_namespace_attach -c NvmeEmu0pf0 spdk nqn0n1 2



