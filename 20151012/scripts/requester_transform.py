import string

file = open("../requester.sh.log")

count = 0
class Request:
    def __init__(self):
        self.startTime = 0
        self.endTime = 0
        #0 start 1 finish with cache hit 2 finish with warning
        self.status = -1 
dict = {}
unknowFinishStatus = []
unknowStatus = []
unStartId = []
for line in file:
    count = count + 1
    strList = line.split(" ")
    time = ' '.join(strList[0:6])
    id = strList[7][3: ]
    reqStatus = strList[8]
    if reqStatus == "started":
        req = Request()
        req.startTime = time
        dict[id] = req
    elif reqStatus == "finished:":
        if dict.has_key(id) == False:
            unStartId.append("line: %d %s" % (count, line))
            continue
        dict[id].endTime = time
        if strList[-1] == "<b>122</b>\n":
            dict[id].status = 2
        elif strList[-1] == ",\n":
            dict[id].status = 1
        else:
            unknowFinishStatus.append("line: %d %s" % (count, line))
    else:
        unknowStatus.append("line: %d %s" % (count, line))
#     if count > 10:
        # break

file.close()


f = open('request.sh.error', 'w')

if len(unStartId) > 0:
    f.write("UnStarted Id: \n")
    for line in unStartId:
        f.write(line + '\n')

if len(unknowStatus) > 0:
    f.write("UnknowStatus: \n")
    for line in unknowStatus:
        f.write(line + '\n')

if len(unknowFinishStatus) > 0:
    f.write("UnknowFinishStatus: \n")
    for line in unknowFinishStatus:
        f.write(line + '\n')
f.close()

f1 = open('requester.sh.csv', 'w')
f1.write("id,start_time,end_time,status(0: start 1:finished with cache hit 2: finish with warning),\n")
dict = sorted(dict.iteritems(), key = lambda d: string.atoi(d[0]))
for i in dict:
    id = i[0]
    req = i[1]
    if req.startTime == 0 or req.endTime == 0 or req.status == -1:
        continue
    line = "%s,%s,%s,%s,\n" % (id, req.startTime, req.endTime, req.status)
    f1.write(line)
f1.close()

