FROM python:3.10

RUN uname -a               # 22.04.1-Ubuntu
RUN python --version       # 3.10.12
RUN pip --version          # 23.0.1
SHELL ["/bin/bash", "-c"]  # use bash such that "source" below is working
RUN cd opt && \
    git clone --depth=1 https://github.com/hakonhagland/vocabuilder.git &&\
    cd vocabuilder && \
    python -m venv .venv && \
    source .venv/bin/activate && \
    pip install .
