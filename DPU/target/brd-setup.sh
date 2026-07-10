#!/bin/sh -v

modprobe brd rd_nr=1 rd_size=40960000 max_part=0

ls /dev/ | grep ram
