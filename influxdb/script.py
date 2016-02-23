import string
import time



fileList = ['./cpu1', './cpu2', './cpu3', './cpu_4q39x', './cpu_pub1y', './cpu_rgij3', './mem1', './mem2', './mem3', './mem_4q39x', './mem_pub1y', './mem_rgij3', './disk_read1', './disk_read2', './disk_read3', './disk_read_4q39x', './disk_read_pub1y', './disk_read_rgij3', './disk_write1', './disk_write2', './disk_write3', './disk_write_4q39x', './disk_write_pub1y', './disk_write_rgij3']
for fileName in fileList:
    fin = open(fileName, 'r')
    fout = open(fileName + '.csv', 'w')
    for line in fin:
        strs = line.split('\t')
        if (strs[0] != 'time'):
            timeTuple = time.localtime(float(strs[0][0:10]))
            strs[0] = time.strftime('%Y-%m-%d %H:%M:%S',timeTuple)
        fout.write(strs[0] + ',' + strs[1])
    fin.close()
    fout.close()
