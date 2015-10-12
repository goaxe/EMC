import string
class Log:
    def __init__(self):
        self.startTime = 0
        self.endTime = 0
        self.memUsed = 0

for i in range(1, 4):
    file = open("../redis-cache/redis-master" + str(i) + ".log")
    for j in range(1, 25):
        file.readline()

    logs = []
    count = 0
    lineNum = 0
    while 1:
        log = Log()
        line = file.readline()
        if not line:
            break
        strs = line.split(" ")
        log.startTime = " ".join(strs[1: 4])
        file.readline()
        if not line:
            break
        file.readline()
        if not line:
            break
        line = file.readline()
        if not line:
            break
        strs = line.split(" ")
        log.memUsed = strs[6] + "MB"
        line = file.readline()
        if not line:
            break
        strs = line.split(" ")
        log.endTime = " ".join(strs[1: 4])
        logs.append(log)
    file.close()
    f = open("redis-master" + str(i) + ".csv", 'w')
    f.write("start_time,end_time,mem_used,\n")
    for log in logs:
        line = "%s,%s,%s,\n" % (log.startTime, log.endTime, log.memUsed)
        f.write(line)
    f.close()
