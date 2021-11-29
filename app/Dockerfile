FROM ubuntu:20.04
#
#====================================================================
# OS environment configuration
#
#
# Default shell
#
SHELL ["/bin/bash", "--login", "-c"]
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

RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
            https://download.docker.com/linux/ubuntu/ $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list

RUN curl -fsSL https://repo.anaconda.com/pkgs/misc/gpgkeys/anaconda.asc | gpg --dearmor -o /usr/share/keyrings/conda-archive-keyring.gpg
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/conda-archive-keyring.gpg] \
            https://repo.anaconda.com/pkgs/misc/debrepo/conda stable main" > /etc/apt/sources.list.d/conda.list
#
# System dependencies
#
COPY ./app/packages.app.txt /root/packages.app.txt
RUN apt-get update -y \
    && sed '/^\s*\#.*$/d' /root/packages.app.txt | xargs -r apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

ENV LIBGIT_VERSION 1.3.0
RUN wget --quiet https://github.com/libgit2/libgit2/archive/v${LIBGIT_VERSION}.tar.gz \
    && tar xzf v${LIBGIT_VERSION}.tar.gz \
    && cd libgit2-${LIBGIT_VERSION}/ \
    && cmake . \
    && make \
    && make install \
    && cd .. \
    && rm -Rf libgit2-${LIBGIT_VERSION}/ \
    && rm -f v${LIBGIT_VERSION}.tar.gz

RUN ldconfig
RUN usermod -aG docker root
#
# Python initialization
#
ENV PYTHON_VERSION 3.7
ENV CONDA_HOME /opt/conda
ENV CONDA_BIN ${CONDA_HOME}/bin

RUN echo "export PATH=${CONDA_BIN}:${PATH}" >> /root/.profile
RUN echo "source ${CONDA_HOME}/etc/profile.d/conda.sh" >> /root/.profile

RUN conda create --name zimagi python=${PYTHON_VERSION} \
    && echo "conda activate zimagi" >> /root/.profile

RUN find ${CONDA_HOME}/ -follow -type f -name '*.a' -delete \
    && find ${CONDA_HOME}/ -follow -type f -name '*.js.map' -delete \
    && conda clean -afy
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

ENV DATA_DIR /var/local/zimagi
ENV LIB_DIR /usr/local/lib/zimagi
ENV APP_DIR /usr/local/share/zimagi
#
# Data directory
#
RUN mkdir ${DATA_DIR}
VOLUME ${DATA_DIR}
#
# Library directory
#
RUN mkdir ${LIB_DIR}
VOLUME ${LIB_DIR}
#
# Application directory
#
COPY ./app ${APP_DIR}
VOLUME ${APP_DIR}
WORKDIR ${APP_DIR}
#
# Application entrypoints
#
RUN ln -s ${APP_DIR}/scripts/cli.sh /usr/local/bin/zimagi
RUN ln -s ${APP_DIR}/scripts/command.sh /usr/local/bin/zimagi-command
RUN ln -s ${APP_DIR}/scripts/data.sh /usr/local/bin/zimagi-data
RUN ln -s ${APP_DIR}/scripts/scheduler.sh /usr/local/bin/zimagi-scheduler
RUN ln -s ${APP_DIR}/scripts/worker.sh /usr/local/bin/zimagi-worker
#
# Application certificates
#
ARG ZIMAGI_CA_KEY
ARG ZIMAGI_CA_CERT
ARG ZIMAGI_KEY
ARG ZIMAGI_CERT

RUN ln -s ${APP_DIR}/scripts/store-key.py /usr/local/bin/store-key
RUN ln -s ${APP_DIR}/scripts/store-cert.py /usr/local/bin/store-cert

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
