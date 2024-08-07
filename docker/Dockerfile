#
#====================================================================
# Zimagi Docker image
#
#
# Base image
#
ARG ZIMAGI_PARENT_IMAGE="ubuntu:22.04"
FROM ${ZIMAGI_PARENT_IMAGE}
#
# Dockerfile arguments
#
ARG ZIMAGI_USER_UID=1000
ARG ZIMAGI_USER_PASSWORD="zimagi"

ARG ZIMAGI_CA_KEY
ARG ZIMAGI_CA_CERT
ARG ZIMAGI_KEY
ARG ZIMAGI_CERT

ARG ZIMAGI_DATA_KEY="zimagi"

ARG ZIMAGI_DEFAULT_MODULES="[]"
#
#====================================================================
# Core system configuration
#
#
# Core environment variables
#
ENV LANG=C.UTF-8
ENV PYTHONUNBUFFERED=1
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

ENV LIBGIT_VERSION=1.5.0
#
# Shell environment
#
SHELL ["/bin/bash", "--login", "-c"]
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections
#
# Package repository management
#
COPY ./docker/packages.core.txt /root/packages.core.txt
RUN apt-get update -y \
    && apt-get upgrade -y \
    && sed '/^\s*\#.*$/d' /root/packages.core.txt | xargs -r apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
    https://download.docker.com/linux/ubuntu/ $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
#
# System dependencies
#
COPY ./docker/packages.app.txt /root/packages.app.txt
RUN apt-get update -y \
    && sed '/^\s*\#.*$/d' /root/packages.app.txt | xargs -r apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

RUN wget --quiet https://github.com/libgit2/libgit2/archive/v${LIBGIT_VERSION}.tar.gz \
    && tar xzf v${LIBGIT_VERSION}.tar.gz \
    && cd libgit2-${LIBGIT_VERSION}/ \
    && cmake . \
    && make \
    && make install \
    && cd .. \
    && rm -Rf libgit2-${LIBGIT_VERSION}/ \
    && rm -f v${LIBGIT_VERSION}.tar.gz \
    && ldconfig
#
# User initialization
#
RUN groupadd -f --system --gid ${ZIMAGI_USER_UID} zimagi \
    && useradd --system --create-home \
    --home-dir /home/zimagi \
    --shell /bin/bash \
    --uid ${ZIMAGI_USER_UID} \
    --gid zimagi \
    --groups sudo \
    zimagi \
    && echo "zimagi:${ZIMAGI_USER_PASSWORD}" | chpasswd
#
#====================================================================
# Application configuration
#
#
# Application environment variables
#
ENV DATA_DIR=/var/local/zimagi
ENV LIB_DIR=/usr/local/lib/zimagi
ENV MODULE_DIR=${LIB_DIR}/modules
ENV FILE_DIR=${LIB_DIR}/files
ENV APP_DIR=/usr/local/share/zimagi
ENV PACKAGE_DIR=/usr/local/share/zimagi-client
ENV KEY_DIR=/var/local/keys

ENV ZIMAGI_DEFAULT_MODULES="${ZIMAGI_DEFAULT_MODULES}"

ENV PATH="/home/zimagi/.local/bin:$PATH"
#
# Application directory
#
COPY --chown=zimagi:zimagi ./app ${APP_DIR}
VOLUME ${APP_DIR}
WORKDIR ${APP_DIR}
#
# Python packages
#
COPY ./app/requirements.txt /home/zimagi/requirements.txt
RUN pip3 install --no-cache-dir -r /home/zimagi/requirements.txt

COPY --chown=zimagi:zimagi ./package ${PACKAGE_DIR}
VOLUME ${PACKAGE_DIR}
RUN cd ${PACKAGE_DIR} \
    && cp -f ${APP_DIR}/VERSION VERSION \
    && rm -Rf build dist \
    && python3 setup.py sdist bdist_wheel --universal \
    && pip3 install "dist/zimagi-`cat VERSION`-py2.py3-none-any.whl" --no-cache-dir \
    && rm -f /usr/local/bin/zimagi
#
# Data directory
#
RUN mkdir ${DATA_DIR} && chown zimagi:zimagi ${DATA_DIR}
VOLUME ${DATA_DIR}
#
# Library directory
#
RUN mkdir ${LIB_DIR} && chown zimagi:zimagi ${LIB_DIR}
COPY --chown=zimagi:zimagi ./lib/modules ${MODULE_DIR}
VOLUME ${LIB_DIR}
#
# Application entrypoints and dependencies
#
RUN ln -s ${APP_DIR}/scripts/cli.sh /usr/local/bin/zimagi \
    && ln -s ${APP_DIR}/scripts/install.sh /usr/local/bin/zimagi-install \
    && ln -s ${APP_DIR}/scripts/gateway.sh /usr/local/bin/zimagi-gateway \
    && ln -s ${APP_DIR}/scripts/command.sh /usr/local/bin/zimagi-command \
    && ln -s ${APP_DIR}/scripts/data.sh /usr/local/bin/zimagi-data \
    && ln -s ${APP_DIR}/scripts/scheduler.sh /usr/local/bin/zimagi-scheduler \
    && ln -s ${APP_DIR}/scripts/controller.sh /usr/local/bin/zimagi-controller \
    && ln -s ${APP_DIR}/scripts/worker.sh /usr/local/bin/zimagi-worker \
    && ln -s ${APP_DIR}/scripts/celery-flower.sh /usr/local/bin/celery-flower
#
# Application certificates
#
RUN ln -s ${APP_DIR}/scripts/store-key.py /usr/local/bin/store-key \
    && ln -s ${APP_DIR}/scripts/store-cert.py /usr/local/bin/store-cert \
    && store-key /etc/ssl/private/zimagi-ca.key "${ZIMAGI_CA_KEY}" \
    && store-cert /usr/local/share/ca-certificates/zimagi-ca.crt "${ZIMAGI_CA_CERT}" \
    && update-ca-certificates \
    && store-key /etc/ssl/private/zimagi.key "${ZIMAGI_KEY}" \
    && store-cert /etc/ssl/certs/zimagi.crt "${ZIMAGI_CERT}" \
    && chown -R zimagi:zimagi /etc/ssl/private \
    && chown -R zimagi:zimagi /usr/local/share/ca-certificates \
    && chown -R zimagi:zimagi /etc/ssl/certs
#
# Encryption keys
#
RUN mkdir ${KEY_DIR} \
    && echo "${ZIMAGI_DATA_KEY}" > "${KEY_DIR}/data.key" \
    && chown -R zimagi:zimagi ${KEY_DIR}
#
# Execution gateway
#
EXPOSE 5000
USER zimagi
RUN zimagi-install
ENTRYPOINT ["zimagi"]
