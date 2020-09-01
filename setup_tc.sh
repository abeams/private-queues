tc qdisc add dev veth1 root handle 1: htb default 6
tc class add dev veth1 parent 1: classid 1:1 htb rate 400kbit ceil 400kbit
tc class add dev veth1 parent 1:1 classid 1:6 htb rate 100kbit ceil 400kbit prio 0
tc class add dev veth1 parent 1:1 classid 1:5 htb rate 100kbit ceil 400kbit prio 5
tc filter add dev veth1 protocol ip parent 1:0 prio 1 u32 match ip src 1.1.1.1/32 flowid 1:5
