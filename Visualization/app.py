# -*- coding: UTF_8 -*-

from flask import Flask, render_template
import os

app = Flask(__name__)

def genDiskUnavailable():
    data = []
    for i in range(1, 16):
        for j in range(30, 60):
            if j > 35 and j <= 40:
                data.append(1)
            else:
                data.append(0)
        for j in range(0, 30):
            if j > 5 and j <= 10:
                data.append(1)
            else:
                data.append(0)

    return data

def genDiskUseup():
    data = []
    for i in range(1, 16):
        for j in range(30, 60):
            if j > 45 and j <= 50:
                data.append(1)
            else:
                data.append(0)
        for j in range(0, 30):
            if j > 8 and j <= 13:
                data.append(1)
            else:
                data.append(0)

    return data


def parseRequestData():
    f = open('static/csv/requester.sh.csv')
    counts = []
    prevMin = 20
    count = 0
    startTime = "13:20:00"
    hasStart = False
    for line in f:
        strs = line.split(",")
        if strs[1].startswith('[') == False:
            continue
        time = strs[1].split(' ')[3]
        m = (int)(time.split(':')[1])
        if hasStart == False:
            if time < startTime:
                continue
            else:
                hasStart = True
                prevMin = 20
                while (prevMin != m):
                    prevMin = (prevMin + 1) % 60
                    counts.append(0)
                    count = 0

        if m ==prevMin:
            count = count + 1
        else:
            counts.append(count)
            prevMin = m
            count = 1
    f.close()
    counts.append(count)
    # print('request data len:', len(counts))
#     for i in range(0, 20):
        # print(counts[i])
    return counts[10:]

def parseRedisData():
    datas = []
    for i in range(1, 4):
        f = open('static/csv/redis-master' + str(i) + '.csv')
        data = []
        prevMin = -1
        startTime = "13:20:00"
        hasStart = False

        for line in f:
            if line.endswith('MB\n') == False:
                continue
            # print line
            strs = line.split(',')
            time = strs[0].split(' ')[2].split('.')[0]
            m = int(time.split(':')[1])
            if hasStart == False:
                if time < startTime:
                    continue
                else:
                    hasStart = True
                    prevMin = 20
                    while (prevMin + 1) % 60 != m:
                        prevMin = (prevMin + 1) % 60
                        data.append(0)
            mem = int(strs[2][0: len(strs[2]) - 3])
            prevMin = (prevMin + 1) % 60
            while prevMin != m:
                prevMin = (prevMin + 1) % 60
                data.append(0)
            data.append(mem)
        f.close()
        # print('redis data len:', len(data))
        datas.append(data[10:])
#     for i in range(0, 3):
        # for j in range(0, 200):
            # # print datas[i][j]
        # print '============'

    return datas

def parseDiskIO():
    f = open('static/csv/diskio.csv')
    data = [[], [], []]
    count = [0, 0, 0]
    prevMin = -1
    startTime = "13:20:00"
    hasStart = False

    for line in f:
        if line.endswith('er\n'):
            continue
        strs = line.split(',')
        time = strs[0].split(' ')[3]
        m = int(time.split(':')[1])
        if hasStart == False:
            if time < startTime:
                continue
            else:
                hasStart = True
                prevMin = 20
                while prevMin != m:
                    prevMin = (prevMin + 1) % 60
                    for i in range(0, 3):
                        data[i].append(0)
        id = int(line[len(line) - 2: len(line) - 1]) - 1
        if m == prevMin:
            count[id] = count[id] + 1
        else:
            for i in range(0, 3):
                data[i].append(count[i])
                count[i] = 0
            count[id] = 1
            prevMin = m
    f.close()
    for i in range(0, 3):
        data[i].append(count[i])
        data[i] = data[i][10:]

#     print('io in node1:', len(data[0]))
    # print('io in node2:', len(data[1]))
    # print('io in node3:', len(data[2]))
    return data
#     for i in range(0, 3):
        # for j in range(0, 20):
            # print(data[i][j])
        # print('=========')

def parseMySQLData():
    warnData = []
    errorData = []

    for i in range(1, 4):
        f = open('static/csv/pxc-node' + str(i) + '.csv')
        warnCount = 0
        errorCount = 0
        warns = []
        errors = []
        prevMin = 20
        prevHour = 13
        for line in f:
            if line.endswith('\"\n') == False:
                continue
            strs = line.split(',')
            time = strs[0].split(' ')[1]
            m = int(time.split(':')[1])
            h = int(time.split(':')[0])
            level = strs[1]
            if prevMin != m or prevHour != h:
                warns.append(warnCount)
                errors.append(errorCount)
                warnCount = 0
                errorCount = 0
                prevMin = prevMin + 1
                if  prevMin == 60:
                    prevMin = 0
                    prevHour = prevHour + 1
                    if prevHour == 24:
                        prevHour = 0
            while prevMin != m or prevHour != h:
                prevMin = prevMin + 1
                if  prevMin == 60:
                    prevMin = 0
                    prevHour = prevHour + 1
                    if prevHour == 24:
                        prevHour = 0               
                warns.append(0)
                errors.append(0)
            if level == '[Warning]':
                warnCount = warnCount + 1
            else:
                errorCount = errorCount + 1


        f.close()
        warns.append(warnCount)
        errors.append(errorCount)
        warnData.append(warns[10:])
        errorData.append(errors[10:])
#     for i in range(0, 3):
        # print("mysql len:", len(warnData[i]), len(errorData[i]))
    return warnData, errorData

def parseSQLCpu():
    datas = []
    files = ['./static/csv/cpu1.csv', './static/csv/cpu2.csv', './static/csv/cpu3.csv']
    for i in range(0, 3):
        f = open(files[i])
        data = []

        for line in f:
            if line.startswith('time'):
                continue
            strs = line.split(',')
            data.append(float(strs[1]))
        f.close()
        # print('sql cpu data len:', len(data))
        datas.append(data)
#     for i in range(0, 3):
        # for j in range(0, 200):
            # print datas[i][j]
        # print '============'

    return datas

def parseSQLRead():
    datas = []
    files = ['./static/csv/disk_read1.csv', './static/csv/disk_read2.csv', './static/csv/disk_read3.csv']
    for i in range(0, 3):
        f = open(files[i])
        data = []

        for line in f:
            if line.startswith('time'):
                continue
            strs = line.split(',')
            data.append(float(strs[1]))
        f.close()
        # print('sql read data len:', len(data))
        datas.append(data)
#     for i in range(0, 3):
        # for j in range(0, 200):
            # print datas[i][j]
        # print '============'

    return datas

def parseSQLWrite():
    datas = []
    files = ['./static/csv/disk_write1.csv', './static/csv/disk_write2.csv', './static/csv/disk_write3.csv']
    for i in range(0, 3):
        f = open(files[i])
        data = []

        for line in f:
            if line.startswith('time'):
                continue
            strs = line.split(',')
            data.append(float(strs[1]))
        f.close()
        # print('sql write data len:', len(data))
        datas.append(data)
#     for i in range(0, 3):
        # for j in range(0, 200):
            # print datas[i][j]
        # print '============'

    return datas


@app.route('/')
def graphs():
    unavailable = genDiskUnavailable()
    useup = genDiskUseup()
#     print useup
    # print unavailable
    requestData = parseRequestData()
    redisDatas = parseRedisData()
    ioDatas = parseDiskIO()
    warnDatas, errorDatas= parseMySQLData()
    cpuDatas = parseSQLCpu()
    readDatas = parseSQLRead()
    writeDatas = parseSQLWrite()
    # maxNum = 0
    # for tmp in requestData:
        # if tmp > maxNum:
            # maxNum = tmp
    # print('maxRequest: ', maxNum)
    # maxNum = 0
    # for i in range(0, 3):
        # for j in redisDatas[i]:
            # if redisDatas[i][j] != 0 and redisDatas[i][j] != 2 and  redisDatas[i][j] != 4 and redisDatas[i][j] != 6:
                # print('in reids ', redisDatas[i][j])
    # for i in range(0, 3):
        # maxNum = 0
        # for  j in ioDatas[i]:
            # if j > maxNum:
                # maxNum = j
        # print('io', maxNum)

    # maxNum = 0
    # for i in warnDatas[0]:
        # if i > maxNum:
            # maxNum = i
    # print('warn1', maxNum)

    # for i in warnDatas[1]:
        # if i != 0 and i != 1 and i != 2:
            # print('warn2', i)
    # for i in warnDatas[2]:
        # if i != 0 and i != 1 and i != 2 and i != 4 and i != 27:
            # print('warn3', i)
    # maxNum = 0
    # for  i in errorDatas[0]:
        # if i > maxNum:
            # maxNum = i
    # print('error1', maxNum)
    # for i in errorDatas[1]:
        # if i != 0:
            # print('error2', i)
    # for i in errorDatas[2]:
        # if i != 0:
            # print('error3', i)




    # print('requestData\n')
    # print(requestData)
    # print('redisDatas\n')
    # print('ioDatas\n')
    # print(ioDatas)
    # print(redisDatas)
    # print('warnDatas\n')
    # print(warnDatas)
    # print('errorDatas\n')
    # print(errorDatas)
    print useup
    return render_template('layout.html', unavailable = unavailable, useup = useup, requestData=requestData, redisData1=redisDatas[0], redisData2 = redisDatas[1], redisData3 = redisDatas[2], diskIO1=ioDatas[0], diskIO2=ioDatas[1], diskIO3=ioDatas[2], warn1=warnDatas[0], warn2=warnDatas[1], warn3=warnDatas[2], error1=errorDatas[0], error2=errorDatas[1], error3=errorDatas[2], cpu1 = cpuDatas[0], cpu2 = cpuDatas[1], cpu3 = cpuDatas[2], read1 = readDatas[0], read2 = readDatas[1], read3 = readDatas[2], write1 = writeDatas[0], write2 = writeDatas[1], write3 = writeDatas[2])



if __name__ == '__main__':
    app.run(debug=True, port=8000)
