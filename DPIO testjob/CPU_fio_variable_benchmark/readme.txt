这两个脚本非常好，我的测试脚本参数如下，我希望提取关键指标的 Python 脚本，能将这些测试参数，对应的IOPS、延迟、带宽、CPU 使用率都统计到。
参数	测试值	固定值（其他参数）
bs	4k, 8k, 16k, 32k, 64k, 128k	rw=randwrite/randread, numjobs=1, nbcpu=1, iodepth=32
rwmixwrite	0, 25, 50, 75, 100	bs=4k, numjobs=1, nbcpu=1, iodepth=32
numjobs	1~16	bs=4k, rw=randwrite/randread, nbcpu=16, iodepth=32
nbcpu	1~16	bs=4k, rw=randwrite/randread, numjobs=16, iodepth=32
iodepth	1, 2, 4, 8, 16, 32, 64, 128	bs=4k, rw=randwrite/randread, numjobs=1, nbcpu=1
numjobs（bandwidth）	1~16	bs=64k, rw=write/read, nbcpu=16, iodepth=32
nbcpu（bandwidth）	1~16	bs=64k, rw=write/read, numjobs=16, iodepth=32


举个例子：以CPU_Total_vs_bs.png为例现在的绘图效果是CPU randread User，CPU randread System 两者都是一个颜色，而里面有CPU randread User，CPU randread System，DPU randread User，DPU randread System，CPU randwrite User，CPU randwrite System，DPU randwrite User，DPU randwrite System，一共8条线。我希望的是CPU randread User和DPU randread User，两条线是一个颜色，CPU randread System和DPU randread System两条线是另一个颜色。每两条线分配一个颜色。
现在颜色之间还是有点接近。以CPU_Utilization_vs_bs.png为例，现在的绘图效果是CPU randread User，CPU randread System，DPU randread User，DPU randread System是一个颜色，CPU randwrite User，CPU randwrite System，DPU randwrite User，DPU randwrite System是一个颜色。我希望CPU randread User和DPU randread User，两条线是一个颜色，CPU randread System和DPU randread System两条线是另一个颜色；CPU randwrite User和DPU randwrite User，两条线是一个颜色，CPU randwrite System和DPUrandwrite System两条线是另一个颜色。一共四个颜色。