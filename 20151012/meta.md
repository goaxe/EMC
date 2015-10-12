Simulation metadata which decribes the simulation setup

    Time: 20151011 22:00 to 20151012 14:00 (GMT+8) (I actually started at about 5 min after 22:00, and ended at about 5 min before 14:00)
    Experiment results data at 10.62.98.243:/data/experiments/20151012/

Cluster setup

    3 web app nodes
    3 redis caching nodes
    3 galera mysql node
    Metrics sampling interval: 10s

Client requestor works as follows

    Request at every 5s
    Concurrent request count of (|current_minute_in_hour - 30| / 5 + 1)
    The workload to web app: `cpu_loop=1000&db_read=10&db_update=10&db_append=1`

Failure injector works as follows:

    DISK_UNAVAILABLE_INJECT_TIME="05 35"    # minute in hour
    DISK_UNAVAILABLE_RECOVER_TIME="10 40"

    DISK_USE_UP_INJECTION_TIME="08 45"
    DISK_USE_UP_RECOVER_TIME="13 50"

    Only inject at odd hour `$(expr $(date +%H) % 2) == 1`, do nothing at even hour. So you have compare
    P.S. I found that even disk use up, mysql still keeps some preallocated space, so that db-append won't fail at most time.

Data includes (log files use UTC timestamp)

    CPU, memory, disk, etc metrics at InfluxDB
    Web app access log and error log
    Mysql node log
    Redis node logs
    Client requestor log
    Failure injector log
    Diskio metrics fetcher log
    A screenshot of the result graphs on Grafana

