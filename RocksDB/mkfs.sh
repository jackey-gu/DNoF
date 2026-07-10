mkfs.ext4 /dev/nvme2n2
mkfs.ext4 /dev/nvme3n1
sudo umount /mnt/nvmeof



watch -n 1 df -h /mnt/nvmeof