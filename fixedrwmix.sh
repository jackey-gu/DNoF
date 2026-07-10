#! /bin/bash -v
for ((bs = 4;bs <= 4; bs *= 2))
do
for ((iops = 10000,wiops = 0; iops >= 0;iops -= 2500, wiops +=2500))
do
for ((numjobs = 1; numjobs <= 1; numjobs++ ))
do
for ((iodepth = 8; iodepth <= 8; iodepth = iodepth * 2 ))
do
for((repeat = 1; repeat <= 3; repeat++))
do
    echo "rw= "$rw "bs= "$bs"k" "iops= "$iops "wiops= "$wiops "numjobs="$numjobs  "iodepth="$iodepth "repeat="$repeat 
    # Run R-app
    fio --filename=/dev/nvme3n1 \
            --name=nvme3 \
            --ioengine=libaio \
            --rate_iops=$iops \
            --direct=1 \
            --rw=randread \
            --gtod_reduce=0 \
            --cpus_allowed_policy=split \
            --size=1G \
            --bs=4k \
            --time_based \
            --runtime=60 \
            --iodepth=8 \
            --cpus_allowed=1 \
            --numjobs=$numjobs \
            --group_reporting > Rapp$bs'k'-$iops-$wiops-$iodepth-$numjobs-$repeat &

    # Run WW-app 
    fio --filename=/dev/nvme4n1 \
            --name=nvme4 \
            --name=nvme0n1 \
            --rate_iops=$wiops \
            --direct=1 \
            --rw=randwrite \
            --gtod_reduce=0 \
            --cpus_allowed_policy=split \
            --size=1G \
            --bs=$bs'k' \
            --time_based \
            --runtime=60 \
            --iodepth=$iodepth \
            --cpus_allowed=1 \
            --numjobs=1 \
            --group_reporting > Wapp$bs'k'-$iops-$wiops-$iodepth-$numjobs-$repeat
done
done
done
done
done



# fio \
#   --ioengine=libaio \
#   --direct=1 \
#   --time_based \
#   --runtime=60 \
#   --bs=4k \
#   --iodepth=16 \
#   --rw=randread \
#   --name=nvme3 \
#   --filename=/dev/nvme3n2 \
#   --name=nvme4 \
#   --filename=/dev/nvme4n1
