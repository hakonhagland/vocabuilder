FROM python:3.10

RUN uname -a               # 22.04.1-Ubuntu
RUN python --version       # 3.10.12
RUN pip --version          # 23.0.1
WORKDIR /root
COPY entrypoint.sh .
ENTRYPOINT ["./entrypoint.sh"]
