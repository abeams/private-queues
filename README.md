# private-queues

Before you begin:

- Make sure you have installed the p4 simple_switch compiler, etc: https://p4.org/p4/getting-started-with-p4.html

- Identify your upstream ip address. In this document I'm using 192.168.0.1

- (optional) Create a lightweight VirtualBox VM with a Bridged Network Adaptor set to veth1

1) First, set up the network by running 

$ sudo setup_network.sh

Modify the ip address assigned to veth3 if necessary.

2) Now compile forwarder.p4:

$ p4c -b bmv2 forwarder.p4 -o forwarder.bmv2 

3) Now start the switch (substitute enps4s0 for your ethernet connection):

$ sudo simple_switch --interface 0@veth0 --interface 1@veth2 --interface 2@enp4s0 forwarder.bmv2/forwarder.json 

4) Open another terminal and start the CLI

$ simple_switch_CLI

We want to add the following rules:

First, we will redirect packets from port 0 (victim) to port 2 (ethernet)

% table_add forward_by_port set_egress_spec 0 => 2

And redirect packets from port 1 (adversary) to port 2 (ethernet)

% table_add forward_by_port set_egress_spec 1 => 2

Redirect packets from the adversary address (the address we set to veth3 in setup_network.sh) to port 1

% table_add forward_by_address set_egress_spec 192.168.2.31 => 1

Finally redirect all the other packets from port 2 (ethernet) back to port 0 (victim) - in the p4 program we insure the previous rule takes precedence over this one.

% table_add forward_by_port set_egress_spec 2 => 0

5) Open another terminal, and start pinging upstream from the adversary. The -i here is the interval between pings.

$ sudo ping -i .01 -I veth3 192.168.0.1

6) Open another terminal and start a tshark capture. Here I'm identifying the interfaces I'm monitoring, filtering the fields I care about, and setting the duration to 300 seconds.

sudo tshark -i veth1 -i veth3 -T json -e frame.interface_name -e frame.number -e frame.time_epoch -e frame.len -e ip.len -e ip.src -e ip.dst -e icmp.type -e icmp.resp_to -e icmp.resptime -a duration:300 > tshark_out/idle_5min.json

6a) In the meantime you can create traffic on veth1 either using the vm or manually redirecting traffic to use this interface.

7) You can graph the RTTS and traffic of the json with 

$ python3 process_packets.py <filename>
