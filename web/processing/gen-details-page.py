#!/usr/env/python
import sys, os
import re
import subprocess
import json
import operator


data_dir = sys.argv[1]
results_dir = data_dir + "/results"
out_dir = sys.argv[2]
target_cpus = sys.argv[3]
name = sys.argv[4]
outfile = out_dir + "/" + name + ".html"

github_user = "ms705"

def make_cpus(a):
	a = a.replace( "\n","")
	if(a.find("-")<0):
		return a.split(',')
	else:
		k=a.split(',')
		temp=[]
		for i in range(0, len(k)):
			if(k[i].find("-")<0):
				temp.append(k[i])
			else:
				t = k[i].split("-")
				for j in range(int (t[0]), int(t[1]) + 1):
					temp.append(str (j))
		return temp

class TargetCPUs:
	def __init__(self, ht_part, sameNUMA, diffNUMA, sameSock, diffSock):
		self.ht_part=ht_part
		self.sameNUMA=sameNUMA
		self.diffNUMA=diffNUMA
		self.sameSock=sameSock
		self.diffSock=diffSock
	def jsonize(self):
		return self.__dict__

class NodesTopology:
	def __init__(self, name, nodes, caches):
		self.name = name
		self.nodes = nodes
		self.caches = caches
	def jsonize(self):
		return self.__dict__

class Node:
	def __init__(self, cores, distances):
		self.cores = cores
		self.distances = distances
	def jsonize(self):
		return self.__dict__

class Cache:
	def __init__(self, level, size, cpu_list):
		self.level = level
		self.size = size
		self.cpu_list = cpu_list
	def jsonize(self):
		return self.__dict__


def ComplexHandler(Obj):
        return Obj.jsonize()








# Generating throughput comparison json objects
tar_cpus=target_cpus.split(",")

ht_part='N'


try:
	ht_parts=make_cpus(open(data_dir + "/logs/sys-cpu/cpu0/topology/thread_siblings_list").readline())
	for i in reversed ( range ( 0, len (ht_parts) ) ):
		if ht_parts[i] in tar_cpus:
			ht_part = ht_parts[i]
	
except: 
	print data_dir + "/logs/sys-cpu/cpu0/topology/thread_siblings_list" + ": DOES NOT EXIST!"
	
print " HT_PART %s" % ht_part


sameNuma = '0'

diffNuma = 'N'

try:
	sameNuma_List=make_cpus(open(data_dir + "/logs/sys-node/node0/cpulist").readline())
	for i in reversed ( range ( 0, len (sameNuma_List) ) ):
		if sameNuma_List[i] in tar_cpus:
			sameNuma = sameNuma_List[i]
			break
except:
	print data_dir + "/logs/sys-node/node0/cpulist" + ": DOES NOT EXIST!"


print " SAME NUMA %s" % sameNuma

try:
	diffNuma_List=make_cpus(open(data_dir + "/logs/sys-node/node1/cpulist").readline())
	for i in reversed ( range ( 0, len (diffNuma_List) ) ):
		if diffNuma_List[i] in tar_cpus:
			diffNuma = diffNuma_List[i]
			break
except :
	print data_dir + "/logs/sys-node/node1/cpulist" + ": DOES NOT EXIST!"

print " DIFF NUMA %s" % diffNuma

sameSock = '0'
diffSock = 'N'

try:
	physical_package_id = open(data_dir + "/logs/sys-cpu/cpu0/topology/physical_package_id").readline()
except :
	print data_dir + "/logs/sys-cpu/cpu0/topology/physical_package_id" + ": DOES NOT EXIST!"

for j in reversed(range(1, len(tar_cpus))):
	t = (open(data_dir + "/logs/sys-cpu/cpu%s/topology/physical_package_id" % tar_cpus[j]).readline())
	if t == physical_package_id:
		sameSock = tar_cpus[j]
		break


for j in reversed(range(1, len(tar_cpus))):
	t = (open(data_dir + "/logs/sys-cpu/cpu%s/topology/physical_package_id" % tar_cpus[j]).readline())
	if t != physical_package_id:
		diffSock = tar_cpus[j]
		break 

print " SAME SOCK %s" % sameSock
print " DIFF Sock %s" % diffSock


dat = TargetCPUs(ht_part, sameNuma, diffNuma, sameSock, diffSock)

f=open(data_dir + "/graphs/th_put.json", 'w+')

f.write ( json.dumps(dat, default=ComplexHandler) )

f.close() 

print "Generating details page for %s" % name
#print "Target CPUs are: %s" % target_cpus.split(",")

processor_ids = []
model_names = []
for line in open(data_dir + "/logs/cpuinfo").readlines():
  r = re.search("processor\t: ([0-9]+)", line)
  if r:
    processor_ids.append(r.group(1))
  r = re.search("model name\t: (.+)", line)
  if r:
    model_names.append(r.group(1))

num_cores = len(processor_ids)

# NUMA-ness & number of nodes
numa_string = "unknown"
try:
  l = os.listdir(data_dir + "/logs/sys-node")
  if len(l) > 1:
    numa_string = "yes %d nodes" % len(l)
  else:
    numa_string = "no"
except:
  pass

# Memory
mem_string = "unknown"
for line in open(data_dir + "/logs/meminfo").readlines():
  r = re.search("MemTotal:[ ]+([0-9]+) kB", line)
  if r:
    mem_string = str(round((float(r.group(1)) / float(1024*1024)), 2)) + " GB"

# virtualization
virtualized_string = "unknown"
for line in open(data_dir + "/logs/dmesg_virt").readlines():
  r = re.search("bare hardware", line)
  if r:
    virtualized_string = "no"
    break
  r = re.search("(Xen|virtual hardware|virtualized system)", line)
  # need to differentiate between different forms of virtualization
  if r:
    virtualized_string = "yes"
    break

# uname/OS
os_string = "unknown"
for line in open(data_dir + "/logs/uname").readlines():
  fields = line.split()
  os_id = fields[0]
  ver = fields[1]
  arch = fields[2]
  os_string = "%s %s %s" % (os_id, ver, arch)

# Generating topology json data

node_list=[]
for root, dirs, files in os.walk(data_dir +"/logs/sys-node", topdown=False):
    for name_ in dirs:
        node_list.append(name_)

node_list.sort()



node_data_list=[]
for node in node_list:
	cores = make_cpus(open(data_dir + "/logs/sys-node/" + node +"/cpulist").readline())	
	distances  = open(data_dir + "/logs/sys-node/" + node +"/distance").readline().replace('\n', "").split(" ")
	dat = Node (cores, distances)
	node_data_list.append(dat)

first_node = node_data_list[0]

	#Getting cache data
cache_objs = []

try:
	for cpu in first_node.cores:
			caches = []
			for root, dirs, files in os.walk(data_dir +"/logs/sys-cpu/cpu" +cpu +"/cache", topdown=False):
		   		 for name_ in dirs:
					caches.append(name_)
			caches.sort()

			c_objs = []
			for c in caches:
				cpu_list = make_cpus ( open(data_dir +"/logs/sys-cpu/cpu" +cpu +"/cache/" + c +"/shared_cpu_list").readline() )
				level = open(data_dir +"/logs/sys-cpu/cpu" +cpu +"/cache/" + c +"/level").readline().replace("\n", "")
				size = open(data_dir +"/logs/sys-cpu/cpu" +cpu +"/cache/" + c +"/size").readline().replace("\n", "")
				c_obj = Cache(level, size, cpu_list)
				c_objs.append(c_obj)
			temp_obj = []
			for i in c_objs:
				flag = 1;
				for j in cache_objs:
					if( i.size == j.size and i.cpu_list == j.cpu_list and i.level == j.level):
						flag = 0
						break
				if (flag):
					temp_obj.append(i)

			for i in temp_obj:
				cache_objs.append(i)

except:
	cache_objs = []
	temp_obj = []
	maps = []
	cpulist = []
	for i in range(0, len(first_node.cores)):
			caches = []
			for root, dirs, files in os.walk(data_dir +"/logs/sys-cpu/cpu" +first_node.cores[i] +"/cache", topdown=False):
		   		 for name_ in dirs:
					caches.append(name_)
			caches.sort()

			c_objs = []
			for c in caches:
				cpu_list =  [open(data_dir +"/logs/sys-cpu/cpu" +first_node.cores[i] +"/cache/" + c +"/shared_cpu_map").readline()] 
				level = open(data_dir +"/logs/sys-cpu/cpu" +first_node.cores[i] +"/cache/" + c +"/level").readline().replace("\n", "")
				size = open(data_dir +"/logs/sys-cpu/cpu" +first_node.cores[i] +"/cache/" + c +"/size").readline().replace("\n", "")
				c_obj = Cache(level, size, cpu_list)
				c_objs.append(c_obj)
				
			temp_obj = []
			for t in c_objs:
				flag = 1;
				for j in cache_objs:
					if( t.size == j.size and t.cpu_list == j.cpu_list and t.level == j.level):
						
						flag = 0
						mp = maps.index(j.cpu_list[0])
						cpulist[mp].append(i)
						break
				if (flag):
						
					maps.append(t.cpu_list[0])
					mp = maps.index(t.cpu_list[0])
					cpulist.append([i])
					temp_obj.append(t)

			for i in temp_obj:
				cache_objs.append(i)

	for i in cache_objs:
		index = maps.index (i.cpu_list[0])
		i.cpu_list = cpulist[index]
		
				
cache_objs.sort(key=operator.attrgetter('level'))		

		


nodTop = NodesTopology ( model_names[0], node_data_list, cache_objs )

f=open(data_dir + "/graphs/topology.json", 'w+')

f.write ( json.dumps(nodTop, default=ComplexHandler) )

f.close() 
	 


# Generate latency graphs & json data
lat_ls = None
try:
  lat_ls = os.listdir(results_dir + "/lat")
  for lat_file in lat_ls:
    if not re.search("\.csv", lat_file):
      continue
    argv = ["python", "plot_lat.py", results_dir + "/lat/" + lat_file, \
            lat_file, data_dir + "/graphs", str(len(processor_ids))]
    subprocess.check_call(argv)
    argv = ["python", "json_lat.py", results_dir + "/lat/" + lat_file, \
            lat_file, data_dir + "/graphs", str(len(processor_ids)), ((str(len(processor_ids)) + ", " + model_names[0])) +"," + numa_string +","+ mem_string + "," + os_string + "," +virtualized_string ]
    
    subprocess.check_call(argv)
except:
  pass

# Generate throughput graphs & json data
argv = ["python", "plot_thr.py", results_dir, target_cpus, "0"]
subprocess.check_call(argv)

argv = ["python", "json_thr.py", results_dir, target_cpus, "0"]
subprocess.check_call(argv)

out_html = "<p style=\"background-color: lightgray;\"><b>" \
    "<a href=\"../results.html\">&laquo; Back to overview</a></b></p>"

# Generate hardware overview section
html = "<h2>Hardware overview</h2>"



hw_string = "<table>"
row_string = "<tr><td>%s</td><td>%s</td></tr>"
hw_string = hw_string + row_string \
    % ("Cores (threads):", (str(len(processor_ids)) + ", " + model_names[0]))
hw_string = hw_string + row_string % ("NUMA:", numa_string)
hw_string = hw_string + row_string % ("Total memory:", mem_string)
hw_string = hw_string + row_string % ("Operating system:", os_string)
hw_string = hw_string + row_string % ("Virtualized:", virtualized_string)
hw_string = hw_string + "</table>"

html = html + hw_string
out_html = out_html + html

# Generate latency heatmap section
html = "<h2>Latency</h2>"
html = html + "<p>These graphs show the pairwise IPC latency between cores."
html = html + "<table><tr>"
thr_graphs_links = ""
i = 0
graphs_per_row = 3
if lat_ls is None:
  html = html + "<td><b><em>No data.</em></b></td>"
else:
  for t in lat_ls:
    if not re.search("\.csv", t):
      continue
    graph_file = "../graphs/%s/lat_%s.png" % (name, t)
    if i % graphs_per_row == 0:
      html = html + "</tr><tr>"
    html = html + "<td><a href=\"%s\"><img src=\"%s\" /></a></td>" \
        % (graph_file, graph_file)
    i = i + 1

html = html + "</tr></table>"
out_html = out_html + html

# Generate throughput graphs section
html = "<h2>Throughput</h2>"
html = html + "<p>These graphs show the IPC throughput for continous " \
    "communication between a pair of cores. The y-axis shows throughput in " \
    "Gbps, and the x-axis different chunk sizes.<br />" \
    "<b>Click on the graphs to show a larger version.</b></p>" \
    "<p><img src=\"../images/thr_legend.png\" class=\"aleft\" " \
    "style=\"border: none;\" /></p>"
html = html + "<table><tr>"
thr_graphs_links = ""
i = 0
graphs_per_row = 4
for c in target_cpus.split(","):
  graph_file = "../graphs/%s/core_0_to_%s.png" % (name, c)
  thumb_file = "../graphs/%s/core_0_to_%s-small.png" % (name, c)
  if i % graphs_per_row == 0:
    html = html + "</tr><tr>"
  html = html + "<td><a href=\"%s\"><img src=\"%s\" /></a></td>" \
      % (graph_file, thumb_file)
  i = i + 1

#  if thr_graphs_links != "":
#    thr_graphs_links = thr_graphs_links + ", "
#  thr_graphs_links = thr_graphs_links + "<a href=\"%s\">0 to %s</a>" \
#      % (graph_file, c)

html = html + "</tr></table>"
out_html = out_html + html


# Raw data link section
html = "<h2>Raw data</h2><p>The raw results data for this experiment can " \
    "be downloaded "
raw_data_link = "<a href=\"https://raw.github.com/%s/ipc-bench/master/" \
    "results/%s.tar.gz\">here</a>" % (github_user, name)
html = html + raw_data_link + ".</p>"

out_html = out_html + html

out_html = out_html + "<p style=\"background-color: lightgray;\"><b>" \
    "<a href=\"../results.html\">&laquo; Back to overview</a></b></p>"

out_fd = open(outfile, "a")
out_fd.write(out_html)
out_fd.close()
