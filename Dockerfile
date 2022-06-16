# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
FROM	ubuntu:20.04

RUN 	apt-get update && apt-get install sudo -y
RUN	ln -sf /bin/bash /bin/sh

COPY	. /app
WORKDIR	/app

ENV 	DEBIAN_FRONTEND=noninteractive

RUN	apt-get -y install build-essential
RUN     apt-get -y install python3 python3-distutils python3-pip python3-dev
RUN	apt-get -y install python3-intbitset python3-magic
RUN	apt-get -y install libxml2-dev
RUN	apt-get -y install libxslt1-dev
RUN 	apt-get -y install libhdf5-dev
RUN 	apt-get -y install bzip2 xz-utils zlib1g libpopt0 
RUN	apt-get -y install gcc-10 g++-10
RUN	pip3 install --upgrade pip
RUN	pip3 install .
RUN	pip3 install dparse

ENTRYPOINT ["/usr/local/bin/fosslight_source"] 
