################################################################################
# Build frontend
################################################################################
FROM node:20-alpine AS frontend

WORKDIR /src

COPY freedata_gui ./

RUN npm install && npm run build

################################################################################
# Build server
################################################################################
FROM python:3.11-slim-bookworm AS server

ARG HAMLIB_VERSION=4.5.5
ENV HAMLIB_VERSION=${HAMLIB_VERSION}

RUN apt-get update && \
  apt-get install --upgrade -y fonts-noto-color-emoji git build-essential cmake portaudio19-dev python3-pyaudio python3-colorama wget && \
  mkdir -p /app/FreeDATA

WORKDIR /src

ADD https://github.com/Hamlib/Hamlib/releases/download/${HAMLIB_VERSION}/hamlib-${HAMLIB_VERSION}.tar.gz ./hamlib.tar.gz

RUN tar -xplf hamlib.tar.gz

WORKDIR /src/hamlib-${HAMLIB_VERSION}

RUN ./configure --prefix=/app/FreeDATA-hamlib && \
		make && \
		make install

WORKDIR /app/FreeDATA

ADD https://github.com/DJ2LS/FreeDATA.git#v0.16.10-alpha ./

RUN python3 -m venv /app/FreeDATA/venv
ENV PATH="/app/FreeDATA/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip wheel && \
  pip install --no-cache-dir -r requirements.txt

WORKDIR /app/FreeDATA/freedata_server/lib

ADD https://github.com/drowe67/codec2.git ./codec2

WORKDIR /app/FreeDATA/freedata_server/lib/codec2

RUN mkdir build_linux

WORKDIR /app/FreeDATA/freedata_server/lib/codec2/build_linux

RUN cmake .. && make codec2 -j4

################################################################################
# Final image
################################################################################
FROM python:3.11-slim-bookworm

ENV PATH="/app/FreeDATA-hamlib/bin:/app/FreeDATA/venv/bin:$PATH"

ENV FREEDATA_CONFIG=/data/config.ini
ENV FREEDATA_DATABASE=/data/freedata-messages.db
ENV HOME=/home/freedata

WORKDIR /app

COPY --from=server /app ./
COPY --from=frontend /src/dist/ ./FreeDATA/freedata_gui/dist/
COPY entrypoint.sh /entrypoint.sh

RUN mkdir -p /data && \
  cp FreeDATA/freedata_server/config.ini.example /data/config.ini && \
  apt-get update && \
  apt-get install --upgrade -y \
    portaudio19-dev \
    alsa-utils \
    libasound2 \
    libasound2-plugins \
    pulseaudio \
	pulseaudio-utils && \
  rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --home-dir $HOME freedata \
	&& usermod -aG audio,pulse,pulse-access freedata \
	&& chown -R freedata:freedata $HOME

USER freedata

ENTRYPOINT [ "/entrypoint.sh" ]
