#!/usr/bin/env bash

usage(){
    echo "Usage: $0 list"
    echo "Usage: $0 [操作] [容器名] [端口绑定的ip地址]"
    echo "可选操作: create start stop restart delete"
    echo "Example: $0 create test 192.168.1.1"
    exit 2
}

if [[ $1 != "list" && -z $3 ]]; then
    usage
fi

operation=$1
container_name=$2
ip_addr=$3
data_path=/home/cloud/saas/${container_name}_${ip_addr}
pro_cfg_path=/home/cloud/saas/prometheus.yml
image_name=pro_gra_saas

case $operation in
    create)
        ip addr add ${ip_addr} dev docker0
        if [[ $? != 0 ]]; then
            echo "IP already in use!"
            exit 1
        fi
        mkdir ${data_path}
        cp ${pro_cfg_path} ${data_path}/prometheus.yml
        docker run -itd -v ${data_path}/data:/prometheus/data -v ${data_path}/prometheus.yml:/prometheus/prometheus.yml -p ${ip_addr}:80:3000 -p ${ip_addr}:9090:9090 --name=${container_name}_${ip_addr} ${image_name}
        ;;
    start)
        docker start ${container_name}_${ip_addr}
        ;;
    stop)
        docker kill ${container_name}_${ip_addr}
        ;;
    restart)
        docker kill ${container_name}_${ip_addr}
        docker start ${container_name}_${ip_addr}
        ;;
    delete)
        docker rm ${container_name}_${ip_addr}
        ip addr del ${ip_addr} dev docker0
        rm -rf ${data_path}
        ;;
    list)
        docker ps -a --format '{{.Names}} {{.Status}}' | awk '{print $1,$2}'
        ;;
esac