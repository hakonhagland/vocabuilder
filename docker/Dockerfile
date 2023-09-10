FROM python:3.10

ARG GIT_ARCH
RUN uname -a               # 22.04.1-Ubuntu
RUN python --version       # 3.10.12
RUN pip --version          # 23.0.1
RUN apt-get update && apt-get install -y libgl1-mesa-glx libegl1-mesa libxkbcommon-x11-dev \
        libdbus-1-dev
WORKDIR /root/vocabuilder
ADD ${GIT_ARCH} .
COPY entrypoint.sh .
ENTRYPOINT ["./entrypoint.sh"]
