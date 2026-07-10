#! /bin/bash -v

nvme disconnect -n nqn0

sleep 2

modprobe -r nvme-rdma

rmmod /lib/modules/5.15.0-1065-bluefield/updates/host/nvme-rdma.ko
rmmod /lib/modules/5.15.0-1065-bluefield/updates/host/nvme-fabrics.ko
rmmod /lib/modules/5.15.0-1065-bluefield/updates/host/nvme-core.ko



snap_rpc.py controller_nvme_namespace_detach -c NvmeEmu0pf0 2

spdk_rpc.py bdev_nvme_detach_controller nqn0
