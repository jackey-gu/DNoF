#!/bin/sh -v

insmod /lib/modules/5.15.0-1065-bluefield/updates/target/nvmet.ko
insmod /lib/modules/5.15.0-1065-bluefield/updates/target/nvmet-rdma.ko

sleep 2

mkdir /sys/kernel/config/nvmet/subsystems/nqn0
echo 1 > /sys/kernel/config/nvmet/subsystems/nqn0/attr_allow_any_host
mkdir /sys/kernel/config/nvmet/subsystems/nqn0/namespaces/1
echo -n /dev/ram0 > /sys/kernel/config/nvmet/subsystems/nqn0/namespaces/1/device_path
echo 1 > /sys/kernel/config/nvmet/subsystems/nqn0/namespaces/1/enable

mkdir /sys/kernel/config/nvmet/ports/1
echo 25.8.0.12 > /sys/kernel/config/nvmet/ports/1/addr_traddr
echo 4420 > /sys/kernel/config/nvmet/ports/1/addr_trsvcid
echo ipv4 > /sys/kernel/config/nvmet/ports/1/addr_adrfam
echo rdma > /sys/kernel/config/nvmet/ports/1/addr_trtype

ln -s /sys/kernel/config/nvmet/subsystems/nqn0 /sys/kernel/config/nvmet/ports/1/subsystems/nqn0
