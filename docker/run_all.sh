#!/bin/bash
/run.sh &
/prometheus/prometheus --config.file=/prometheus/prometheus.yml --storage.tsdb.path=/prometheus/data --web.console.libraries=/prometheus/console_libraries --web.console.templates=/prometheus/consoles &
tail -f /dev/null
