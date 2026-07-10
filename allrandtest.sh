#! /bin/bash -v
rw=randrw
for ((bs = 4;bs <= 128; bs *= 2))
do
for ((rwmixwrite = 0; rwmixwrite <= 100;rwmixwrite += 25))
do
for ((num = 1; num <= 16; num *= 2 ))
do
for ((nbcpu = 1; nbcpu <= num && nbcpu < 16; nbcpu *= 2))
do
for ((iodepth = 1; iodepth <= 128; iodepth = iodepth * 2 ))
do
for((repeat = 1; repeat <= 3; repeat++))
do
    echo "rw= "$rw "bs= "$bs"k" "rwmixwrite= "$rwmixwrite "num= "$num  "nbcpu= "$nbcpu "iodepth= "$iodepth "repeat= "$repeat 
    fio --name=nvme3 --filename=/dev/nvme3n2 --name=nvme4 --filename=/dev/nvme4n1 --direct=1 --ioengine=libaio --size=15G --time_based --runtime=20 --iodepth=$iodepth --numjobs=$num --bs=$bs'k' --rw=$rw --cpus_allowed=1-$nbcpu --rwmixwrite=$rwmixwrite  --output=test$bs'k'-$rwmixwrite'rw'-$iodepth'dep'-$num'num'-$nbcpu'cpu'-$repeat.txt
done
done
done
done
done
done
