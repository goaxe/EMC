import string

class Log:
    def __init__(self):
        self.timeStamp = 0
        self.level = ""
        self.msg = ""

for i in range(1, 4):
    count = 0
    file = open("../galera-mysql/pxc-node" + str(i) + ".log")
    logs = []
    for line in file:
        count = count + 1
        strs = line.split(" ")
        if len(strs) < 4:
            continue
        level = strs[3]
        log = Log()
        if level == "[Note]":
            continue
        elif level == "[Warning]" or level == "[ERROR]":
            log.timeStamp = " ".join(strs[0: 2])
            log.level = level
            log.msg = " ".join(strs[4: ])
            logs.append(log)
        else:
            continue
    file.close()
    f = open("pxc-node" + str(i) + ".csv", 'w')
    f.write("time,levle,msg,\n")
    for log in logs:
        line = "%s,%s,%s,\n" % (log.timeStamp, log.level, log.msg[0: len(log.msg) - 1])
        f.write(line)
    f.close()



