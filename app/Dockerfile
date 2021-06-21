FROM python:3.7-slim-buster
#
#====================================================================
# OS environment configuration
#
#
# Core environment variables
#
ENV LANG C.UTF-8
ENV PYTHONUNBUFFERED 1
#
# Package repository management
#
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

COPY ./app/packages.core.txt /root/packages.core.txt
RUN apt-get update -y \
    && sed '/^\s*\#.*$/d' /root/packages.core.txt | xargs -r apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

RUN apt-key adv --fetch-keys https://download.docker.com/linux/ubuntu/gpg
RUN echo "deb [arch=amd64] https://download.docker.com/linux/debian/ buster stable" > /etc/apt/sources.list.d/docker.list
#
# System dependencies
#
COPY ./app/packages.app.txt /root/packages.app.txt
RUN apt-get update -y \
    && sed '/^\s*\#.*$/d' /root/packages.app.txt | xargs -r apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

ENV LIBGIT_VERSION=1.0.1
RUN wget https://github.com/libgit2/libgit2/archive/v${LIBGIT_VERSION}.tar.gz \
    && tar xzf v${LIBGIT_VERSION}.tar.gz \
    && cd libgit2-${LIBGIT_VERSION}/ \
    && cmake . \
    && make \
    && make install \
    && cd .. \
    && rm -Rf libgit2-${LIBGIT_VERSION}/ \
    && rm -f v${LIBGIT_VERSION}.tar.gz
#
# System initialization
#
RUN ldconfig
RUN usermod -aG docker root
#
# Python dependencies
#
COPY ./app/requirements.txt /root/requirements.txt
RUN pip install --no-cache-dir -r /root/requirements.txt
#
#====================================================================
# Application configuration
#
#
# Application environment variables
#
ENV REQUESTS_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt
#
# Data directory
#
RUN mkdir /var/local/zimagi
VOLUME /var/local/zimagi
#
# Library directory
#
RUN mkdir /usr/local/lib/zimagi
VOLUME /usr/local/lib/zimagi
#
# Application directory
#
COPY ./app /usr/local/share/zimagi
WORKDIR /usr/local/share/zimagi
VOLUME /usr/local/share/zimagi
#
# Application entrypoints
#
RUN ln -s /usr/local/share/zimagi/scripts/cli.sh /usr/local/bin/zimagi
RUN ln -s /usr/local/share/zimagi/scripts/command.sh /usr/local/bin/zimagi-command
RUN ln -s /usr/local/share/zimagi/scripts/data.sh /usr/local/bin/zimagi-data
RUN ln -s /usr/local/share/zimagi/scripts/scheduler.sh /usr/local/bin/zimagi-scheduler
RUN ln -s /usr/local/share/zimagi/scripts/worker.sh /usr/local/bin/zimagi-worker
#
# Application certificates
#
ARG ZIMAGI_CA_KEY
ARG ZIMAGI_CA_CERT
ARG ZIMAGI_KEY
ARG ZIMAGI_CERT

RUN ln -s /usr/local/share/zimagi/scripts/store-key.py /usr/local/bin/store-key
RUN ln -s /usr/local/share/zimagi/scripts/store-cert.py /usr/local/bin/store-cert

RUN store-key /etc/ssl/private/zimagi-ca.key "${ZIMAGI_CA_KEY}"
RUN store-cert /usr/local/share/ca-certificates/zimagi-ca.crt "${ZIMAGI_CA_CERT}"
RUN update-ca-certificates

RUN store-key /etc/ssl/private/zimagi.key "${ZIMAGI_KEY}"
RUN store-cert /etc/ssl/certs/zimagi.crt "${ZIMAGI_CERT}"
#
# Execution gateway
#
EXPOSE 5123
EXPOSE 5323
ENTRYPOINT ["zimagi"]
