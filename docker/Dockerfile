FROM grafana/grafana:latest
MAINTAINER liyumi <chn.lee.yumi@gmail.com>
USER root
COPY run_all.sh /
COPY prometheus-2.19.2.linux-amd64 /prometheus
#RUN mkdir /prometheus/data && chown nobody:nobody /prometheus/data
EXPOSE 3000 9090
VOLUME /prometheus/data
ENTRYPOINT /bin/bash /run_all.sh