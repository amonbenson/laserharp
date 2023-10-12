# default values: minn: 24, max: 40
echo 6 > /sys/kernel/debug/bluetooth/hci0/conn_min_interval
echo 15 > /sys/kernel/debug/bluetooth/hci0/conn_max_interval
