#! /bin/bash -v

modprobe mlx5_ib
modprobe mlx4_ib
modprobe mlx4_core
modprobe mlx4_en
modprobe ib_core
modprobe ib_umad
modprobe ib_cm
modprobe ib_ipoib

modprobe rdma_cm
