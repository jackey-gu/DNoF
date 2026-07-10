测试变量	参数值	固定参数	读写模式
numjobs	1~40	bs=4k, nbcpu=40, iodepth=64	randwrite / randread
nbcpu	1~40	bs=4k, numjobs=40, iodepth=64	randwrite / randread
numjobs-bw	1~40	bs=64k, nbcpu=40, iodepth=64	write / read
nbcpu-bw	1~40	bs=64k, numjobs=40, iodepth=64	write / read