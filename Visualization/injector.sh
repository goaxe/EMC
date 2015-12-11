#!/bin/bash

#######################################################
# Ineject failure to mysql time to time.
# It should be launched on the same host of mysql container
#######################################################

BASEDIR=$(dirname $0)

DISK_UNAVAILABLE_INJECT_TIME="05 35"    # minute in hour
DISK_UNAVAILABLE_RECOVER_TIME="10 40"

DISK_USE_UP_INJECTION_TIME="08 45"
DISK_USE_UP_RECOVER_TIME="13 50"

logger() {
    echo $(date -u)":" "failure injector:" $1 
}

inject_or_recover() {
    local inject_time=$1
    local recover_time=$2
    local script_name=$3

    current_minute=$(date +"%M")
    if [[ " $inject_time " == *" $current_minute "* ]]; then    # array contains
        ${BASEDIR}/$script_name inject
        logger "$script_name inject"
    fi
    if [[ " $recover_time " == *" $current_minute "* ]]; then
        ${BASEDIR}/$script_name recover
        logger "$script_name recover"
    fi
}

while true; do
    current_hour=$(date +%H)
    if [ $(expr $current_hour % 2) == 1 ]; then
        inject_or_recover "$DISK_UNAVAILABLE_INJECT_TIME" "$DISK_UNAVAILABLE_RECOVER_TIME" disk-unavailable.sh
        inject_or_recover "$DISK_USE_UP_INJECTION_TIME" "$DISK_USE_UP_RECOVER_TIME" disk-use-up.sh
    fi
    sleep 60
done

