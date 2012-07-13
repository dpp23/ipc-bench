import sys, os
import json
import matplotlib as mpl
mpl.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
import pylab as pyl
class ThPut:
		def __init__(self, mempipe_spin_unsafe,
			    mempipe_spin_safe,
			    mempipe_futex_unsafe,
			    mempipe_futex_safe,
			    shmpipe_unsafe,
			    shmpipe_safe,
			    vmsplice,
			    pipe,
			    unix,
			    tcp_nd,
			    tcp):
			self.mempipe_spin_unsafe=mempipe_spin_unsafe
			self.mempipe_spin_safe=mempipe_spin_safe
			self.mempipe_futex_unsafe= mempipe_futex_unsafe
			self.mempipe_futex_safe=mempipe_futex_safe
			self.shmpipe_unsafe=shmpipe_unsafe
			self.shmpipe_safe=shmpipe_safe
			self.vmsplice=vmsplice
			self.pipe=pipe
			self.unix=unix
			self.tcp_nd=tcp_nd
			self.tcp=tcp
		def jsonize(self):
			return self.__dict__  

def ComplexHandler(Obj):
        return Obj.jsonize()

def get_data(filename, is_series, plot_chunksizes):
  dst_core_colid = 1
  chunksize_colid = 3
  safe_colid = 6

#  print "%s %d" % (filename, is_series)

  if is_series:
    data = np.loadtxt(filename,
                      usecols=(1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21))
    throughput_colid = 19
    stddev_colid = 20
  else:
    data = np.loadtxt(filename, usecols=(1,2,3,4,5,6,7,8,9,10))
    throughput_colid = 9

  retdata = {}
  maxval = 0
  for i in range(len(data)):
#    print "%d: %f (safe: %d, chunksize: %d)" % (data[i][dst_core_colid],
#                                                data[i][throughput_colid],
#                                                data[i][safe_colid],
#                                                data[i][chunksize_colid])
    dst_core = data[i][dst_core_colid]
    chunksize = data[i][chunksize_colid]
    # Skip chunk sizes that we have data for, but do not want to plot
    if chunksize not in plot_chunksizes:
      continue
    safe = data[i][safe_colid]
    throughput = float(data[i][throughput_colid]) / 1000.0
    maxval = max(throughput, maxval)
    if is_series:
      stddev = data[i][stddev_colid]
    else:
      stddev = 0
    if not dst_core in retdata:
      retdata[dst_core] = {0: {}, 1: {}}
    retdata[dst_core][safe][chunksize] = (throughput, stddev)
  return (retdata, maxval)

def get_series(data, dst_core, safe=1):
  values = [v[0] for c, v in data[dst_core][safe].items()]
#  print str(dst_core) + ": " + str(values)
  return values

def get_stddev_series(data, dst_core, safe=1):
  values = [v[1] for c, v in data[dst_core][safe].items()]
#  print str(dst_core) + ": " + str(values)
  return values

def autolabel(rects):
  # attach some text labels
  for rect in rects:
    height = rect.get_height()
    ax.text(rect.get_x()+float(rect.get_width())/2.0, height+1, '%f' % float(height),
            ha='center', va='bottom', rotation='vertical', size='x-small')

# ------------------------------------------------------------------
# Modify the below variables for different experimental setups
# - in particular, for different machines, modify cores
#   (tigger's config is [0, 1, 6, 12, 18])

#cores = [0, 1, 6, 18]  # the core IDs benchmarked (first ID of pair is always 0)
cores = [int(c) for c in sys.argv[2].split(",")]
chunksizes = [64, 4096, 65536]
n_bars = 11   # number of bars (tests) per group
labels = ['(a)', '(b)', '(c)', '(d)', '(e)']

n_groups = len(chunksizes)  # number of chunk sizes

# ---------------------------
# Handle command line args

if len(sys.argv) < 3:
  print "usage: python plot_thr.py <results directory> <target_cpus> <is_series: (0|1)> [filenames ...]"
  sys.exit(0)

res_dir = sys.argv[1]
output_dir = res_dir + "/../graphs"

is_series = int(sys.argv[3])

# ---------------------------
# Get result filenames

if len(sys.argv) > 4:
  mempipe_spin_filename = sys.argv[4]
else:
  mempipe_spin_filename = res_dir + '/01-mempipe_spin_thr-headline.log'

if len(sys.argv) > 5:
  mempipe_futex_filename = sys.argv[5]
else:
  mempipe_futex_filename = res_dir + '/01-mempipe_thr-headline.log'

if len(sys.argv) > 6:
  shmem_pipe_filename = sys.argv[6]
else:
  shmem_pipe_filename = res_dir + '/01-shmem_pipe_thr-headline.log'

if len(sys.argv) > 7:
  vmsplice_filename = sys.argv[7]
else:
  vmsplice_filename = res_dir + '/01-vmsplice_coop_pipe_thr-headline.log'

if len(sys.argv) > 8:
  pipe_filename = sys.argv[8]
else:
  pipe_filename = res_dir + '/01-pipe_thr-headline.log'

if len(sys.argv) > 9:
  unix_filename = sys.argv[9]
else:
  unix_filename = res_dir + '/01-unix_thr-headline.log'

if len(sys.argv) > 10:
  tcp_nd_filename = sys.argv[10]
else:
  tcp_nd_filename = res_dir + '/01-tcp_nodelay_thr-headline.log'

if len(sys.argv) > 11:
  tcp_filename = sys.argv[11]
else:
  tcp_filename = res_dir + '/01-tcp_thr-headline.log'

# --------------------------

# Overall maximum value (for upper y-axis limit); note that get_data may modify
# this variable
all_max = 10

mempipe_spin_data = get_data(mempipe_spin_filename, is_series, chunksizes)
mempipe_futex_data = get_data(mempipe_futex_filename, is_series, chunksizes)
shmpipe_data = get_data(shmem_pipe_filename, is_series, chunksizes)
vmsplice_data = get_data(vmsplice_filename, is_series, chunksizes)
pipe_data = get_data(pipe_filename, is_series, chunksizes)
unix_data = get_data(unix_filename, is_series, chunksizes)
tcp_nd_data = get_data(tcp_nd_filename, is_series, chunksizes)
tcp_data = get_data(tcp_filename, is_series, chunksizes)



f=open(output_dir + "/th_mempipe_spin" + ".json", 'w+')
f.write ( json.dumps(mempipe_spin_data ))
f.close()

f=open(output_dir + "/th_mempipe_futex" + ".json", 'w+')
f.write ( json.dumps(mempipe_futex_data ))
f.close()

f=open(output_dir + "/th_shmpipe" + ".json", 'w+')
f.write ( json.dumps ( shmpipe_data ))
f.close()

f=open(output_dir + "/th_vmsplice" + ".json", 'w+')
f.write ( json.dumps( vmsplice_data ))
f.close()

f=open(output_dir + "/th_pipe" + ".json", 'w+')
f.write ( json.dumps( pipe_data ))
f.close()

f=open(output_dir + "/th_unix" + ".json", 'w+')
f.write ( json.dumps( unix_data ))
f.close()

f=open(output_dir + "/th_tcp_nd" + ".json", 'w+')
f.write ( json.dumps( tcp_nd_data ))
f.close()

f=open(output_dir + "/th_tcp" + ".json", 'w+')
f.write ( json.dumps( tcp_data ))
f.close()



fig_idx = 1
fig = plt.figure(figsize=(6,4))
pyl.rc('font', size='8.0')

for dst_core in cores:
  # get data series
  if dst_core != 0:
    mempipe_spin_unsafe_series = get_series(mempipe_spin_data[0], dst_core, safe=0)
    mempipe_spin_safe_series = get_series(mempipe_spin_data[0], dst_core, safe=1)
  else:
    # if we have dst_core set to 0 (i.e. we're communicating with ourselves), we skip
    # the spin test, so we set the values to zero here (they are not in the result files)
    mempipe_spin_unsafe_series = [0] * n_groups
    mempipe_spin_safe_series = [0] * n_groups
  mempipe_futex_unsafe_series = get_series(mempipe_futex_data[0], dst_core, safe=0)
  mempipe_futex_safe_series = get_series(mempipe_futex_data[0], dst_core, safe=1)
  shmpipe_unsafe_series = get_series(shmpipe_data[0], dst_core, safe=1)
  shmpipe_safe_series = get_series(shmpipe_data[0], dst_core, safe=0)
  vmsplice_series = get_series(vmsplice_data[0], dst_core)
  pipe_series = get_series(pipe_data[0], dst_core)
  unix_series = get_series(unix_data[0], dst_core)
  tcp_nd_series = get_series(tcp_nd_data[0], dst_core)
  tcp_series = get_series(tcp_data[0], dst_core)

for dst_core in cores:
  # get data series
  if dst_core != 0:
    mempipe_spin_unsafe_series = get_series(mempipe_spin_data[0], dst_core, safe=0)
    mempipe_spin_safe_series = get_series(mempipe_spin_data[0], dst_core, safe=1)
  else:
    # if we have dst_core set to 0 (i.e. we're communicating with ourselves), we skip
    # the spin test, so we set the values to zero here (they are not in the result files)
    mempipe_spin_unsafe_series = [0] * n_groups
    mempipe_spin_safe_series = [0] * n_groups
  mempipe_futex_unsafe_series = get_series(mempipe_futex_data[0], dst_core, safe=0)
  mempipe_futex_safe_series = get_series(mempipe_futex_data[0], dst_core, safe=1)
  shmpipe_unsafe_series = get_series(shmpipe_data[0], dst_core, safe=1)
  shmpipe_safe_series = get_series(shmpipe_data[0], dst_core, safe=0)
  vmsplice_series = get_series(vmsplice_data[0], dst_core)
  pipe_series = get_series(pipe_data[0], dst_core)
  unix_series = get_series(unix_data[0], dst_core)
  tcp_nd_series = get_series(tcp_nd_data[0], dst_core)
  tcp_series = get_series(tcp_data[0], dst_core)

  if is_series:
    if dst_core != 0:
      mempipe_spin_unsafe_stddev_series = get_stddev_series(mempipe_spin_data,
                                                            dst_core, safe=0)
      mempipe_spin_safe_stddev_series = get_stddev_series(mempipe_spin_data,
                                                          dst_core, safe=1)
    else:
      mempipe_spin_unsafe_stddev_series = [0] * n_groups
      mempipe_spin_safe_stddev_series = [0] * n_groups
    mempipe_futex_unsafe_stddev_series = get_stddev_series(mempipe_futex_data,
                                                           dst_core, safe=0)
    mempipe_futex_safe_stddev_series = get_stddev_series(mempipe_futex_data,
                                                         dst_core, safe=1)
    shmpipe_unsafe_stddev_series = get_stddev_series(shmpipe_data, dst_core,
                                                     safe=1)
    shmpipe_safe_stddev_series = get_stddev_series(shmpipe_data, dst_core,
                                                   safe=0)
    vmsplice_stddev_series = get_stddev_series(vmsplice_data, dst_core)
    pipe_stddev_series = get_stddev_series(pipe_data, dst_core)
    unix_stddev_series = get_stddev_series(unix_data, dst_core)
    tcp_nd_stddev_series = get_stddev_series(tcp_nd_data, dst_core)
    tcp_stddev_series = get_stddev_series(tcp_data, dst_core)
  else:
    mempipe_spin_unsafe_stddev_series = None
    mempipe_spin_safe_stddev_series = None
    mempipe_futex_unsafe_stddev_series = None
    mempipe_futex_safe_stddev_series = None
    shmpipe_unsafe_stddev_series = None
    shmpipe_safe_stddev_series = None
    vmsplice_stddev_series = None
    pipe_stddev_series = None
    unix_stddev_series = None
    tcp_nd_stddev_series = None
    tcp_stddev_series = None
  
  k=ThPut(mempipe_spin_unsafe_series,
    mempipe_spin_safe_series,
    mempipe_futex_unsafe_series,
    mempipe_futex_safe_series,
    shmpipe_unsafe_series ,
    shmpipe_safe_series ,
    vmsplice_series ,
    pipe_series ,
    unix_series ,
    tcp_nd_series ,
    tcp_series )

  f=open(output_dir + "/core_0_to_" + str(dst_core) + ".json", 'w+')

  f.write ( json.dumps(k, default=ComplexHandler) )

  f.close()














 
