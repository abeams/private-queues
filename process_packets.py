import json
import os
import argparse
from decimal import Decimal
from itertools import groupby
import scipy.stats
import numpy
import matplotlib.pyplot as plt

DEFAULT_MULTIPLIER = 100 #(in milliseconds)
#The expected round trip time when things are idle
EXPECTED_RTT = .8 #Decimal(0.0003309563566812180496615196195)

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("input_file")
parser.add_argument("-m", "--multiplier", type=int, default=DEFAULT_MULTIPLIER, help="Defines the interval with - int(MULTIPLIER * float(x[timestamp]))")
args = parser.parse_args()

multiplier = args.multiplier

# Open file
input_filename, input_ext = os.path.splitext(args.input_file)
f = open(args.input_file)
raw_data = json.load(f)
f.close()

# Extract the relevant fields
cleaned = []
packets = {}
for item in raw_data:
    cleaned_item = item["_source"]["layers"]
    cleaned.append(cleaned_item)
    packets[cleaned_item["frame.number"][0]] = cleaned_item

ping_times = []
ping_delays = []

#Match response times with the originating pings
for v in packets.values():
    if v.get("icmp.resptime") and v["frame.interface_name"][0] == "veth3" and float(v["icmp.resptime"][0]) < 50:
        ping_times.append(float(packets[v["icmp.resp_to"][0]]["frame.time_epoch"][0]))
        ping_delays.append(float(v["icmp.resptime"][0]))
       
print(len(ping_times))

#Group packets by window
get_key = lambda x: int(multiplier * float(x["frame.time_epoch"][0]))

#Sort packets
cleaned = sorted(cleaned, key=get_key)

times = []
sizes = []

intervals = {}
for k, g in groupby(cleaned, get_key):
    cur_interval = {"interval": k, "packets": list(g)}
    cur_interval["size"] = sum(map(lambda x: int(x["frame.len"][0]), filter(lambda pkt: pkt["frame.interface_name"][0] == "veth1", cur_interval["packets"])))
    intervals[k] = cur_interval
    
    times.append(k / float(multiplier))
    sizes.append(cur_interval["size"])
    

# Shift timestamps to start at 0
start_time = min(times)
times = [time - start_time for time in times]
ping_times = [time - start_time for time in ping_times]

# Print correlation
#print("Pearson Correlation: " + str(scipy.stats.pearsonr(sizes, ping_)))

fig, ax1 = plt.subplots()
color = 'tab:red'
ax1.set_xlabel('Timestamp')
ax1.set_ylabel('bytes', color=color)  
ax1.plot(times, sizes, color=color)
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()
color = 'tab:blue'
ax2.set_ylabel('Ping RTT (milliseconds)', color=color)
ax2.plot(ping_times, ping_delays, color=color)
ax2.tick_params(axis='y', labelcolor=color)

fig.tight_layout()  # otherwise the right y-label is slightly clipped
plt.show()
