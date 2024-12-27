obj-m := killd.o
ccflags-y := -std=gnu11

all:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

run:
	insmod ./killd.ko pid=7680
	rmmod ./killd.ko

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean
