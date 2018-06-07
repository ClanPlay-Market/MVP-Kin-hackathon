FROM python:3.6.2-slim

LABEL description="KIN Hackaton image"

RUN apt-get update && apt-get install -y \
        gcc \
        vim \
        sudo \
        libffi-dev \
        curl

RUN groupadd --gid 999 kin && useradd --no-log-init --uid 999 -g kin -G sudo kin && \
    echo 'kin:kin' | chpasswd

WORKDIR /home/kin

RUN pip install --upgrade pip

RUN pip install --upgrade https://github.com/divomen/kin-core-python/tarball/master

COPY src/requirements.txt src/requirements.txt

RUN pip install -r src/requirements.txt

COPY src/ src/
COPY logs/ logs/

RUN chown -Rh kin:kin . *

USER kin

CMD ["python", "src/rest_server.py"]

