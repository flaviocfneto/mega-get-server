FROM ubuntu:19.10

ENV DOWNLOAD_DIR /data
ENV EXTERNAL_HOST localhost
ENV WEBSOCKET_PORT 8080
ENV TRANSFER_LIST_LIMIT 50
ENV PATH_DISPLAY_SIZE 80
ENV INPUT_TIMEOUT 0.0166
ENV FILE_UPDATE_TIMEOUT 0.1

ADD https://github.com/joewalnes/websocketd/releases/download/v0.3.0/websocketd-0.3.0_amd64.deb ./
ADD https://mega.nz/linux/MEGAsync/xUbuntu_19.10/amd64/megacmd-xUbuntu_19.10_amd64.deb ./

RUN apt-get update; \
    apt-get install ./websocketd*.deb ./megacmd*.deb -y; \
    apt-get clean; \
    rm ./websocketd*.deb ./megacmd*.deb;

COPY files/ /root
EXPOSE ${WEBSOCKET_PORT}

ENTRYPOINT /root/entrypoint.sh
