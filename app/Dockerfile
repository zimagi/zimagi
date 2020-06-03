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

RUN apt-get update -y \
    && apt-get install -y \
        # Package management utilities
        "apt-utils" \
        "software-properties-common" \
        # Security packages
        "apt-transport-https" \
        "ca-certificates" \
        "gnupg2" \
    && rm -rf /var/lib/apt/lists/*

RUN apt-key adv --fetch-keys https://download.docker.com/linux/ubuntu/gpg
RUN echo "deb [arch=amd64] https://download.docker.com/linux/debian/ buster stable" > /etc/apt/sources.list.d/docker.list
#
# System dependencies
#
RUN apt-get update -y \
    && apt-get install -y \
        # Dependency building
        "gcc" \
        "g++" \
        "make" \
        "cmake" \
        "libssl-dev" \
        "unzip" \
        # Utilities
        "curl" \
        "wget" \
        "git" \
        "sshpass" \
        # Database support
        "sqlite3" \
        "libsqlite3-dev" \
        "default-libmysqlclient-dev" \
        # Service clients
        "docker-ce" \
    && rm -rf /var/lib/apt/lists/*

ENV LIBGIT_VERSION=0.28.4
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
RUN pip install --no-cache-dir \
    # Utilities
    "pyyaml==5.3" \
    "oyaml==0.9" \
    "inflect==4.1.0" \
    "paramiko==2.7.1" \
    "terminaltables==3.1.0" \
    "colorful==0.5.4" \
    "cryptography==2.8" \
    "pycryptodome==3.9.4" \
    # Service management
    "docker==4.1.0" \
    # Web server
    "gunicorn==20.0.4" \
    "gevent==1.4.0" \
    "greenlet==0.4.15" \
    # API application
    "django==3.0" \
    "django-filter==2.2.0" \
    "psycopg2-binary==2.8.4" \
    "mysqlclient==1.4.6" \
    "djangorestframework==3.11.0" \
    "drf-writable-nested==0.6.0" \
    "coreapi==2.3.3" \
    "coreschema==0.0.4" \
    # Repository integrations
    "pygit2==1.0.2" \
    # Task management
    "celery==4.4.0" \
    "django-celery-beat==2.0.0" \
    "redis==3.3.11" \
    "django-db-mutex==1.2.0" \
    "django-timezone-field==4.0" \
    "git+https://github.com/dccs-tech/django-rest-framework-filters.git@master#egg=djangorestframework-filters"
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
