import string

class Log:
    def __init__(self):
        self.time = 0
        self.ip = ""
        self.pod = ""
        self.container = ""

file = open("../fetch-diskio-to-influxdb.sh.log")
logs = []
for line in file:
    strs = line.split(" ")
    log = Log()
    log.time = " ".join(strs[0: 6])
    log.ip = strs[9][0: len(strs[9]) - 1]
    log.pod = strs[12][0: len(strs[12]) - 1]
    log.container = strs[15][0: len(strs[15]) - 1]
    logs.append(log)
file.close()

f = open("diskio.csv", 'w')
f.write("time,ip,pod,container\n")
for log in logs:
    line = "%s,%s,%s,%s\n" % (log.time, log.ip, log.pod, log.container)
    f.write(line)
f.close()


