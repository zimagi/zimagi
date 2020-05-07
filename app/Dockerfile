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
    "redis==3.3.11" \
    "django-db-mutex==1.2.0" \
    "django-timezone-field==4.0" \
    "git+https://github.com/dccs-tech/django-rest-framework-filters.git@master#egg=djangorestframework-filters" \
    "git+https://github.com/dccs-tech/django-celery-beat.git@master#egg=django-celery-beat"
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
RUN mkdir /var/local/mcmi
VOLUME /var/local/mcmi
#
# Library directory
#
RUN mkdir /usr/local/lib/mcmi
VOLUME /usr/local/lib/mcmi
#
# Application directory
#
COPY ./app /usr/local/share/mcmi
WORKDIR /usr/local/share/mcmi
VOLUME /usr/local/share/mcmi
#
# Application entrypoints
#
RUN ln -s /usr/local/share/mcmi/scripts/cli.sh /usr/local/bin/mcmi
RUN ln -s /usr/local/share/mcmi/scripts/command.sh /usr/local/bin/mcmi-command
RUN ln -s /usr/local/share/mcmi/scripts/data.sh /usr/local/bin/mcmi-data
RUN ln -s /usr/local/share/mcmi/scripts/scheduler.sh /usr/local/bin/mcmi-scheduler
RUN ln -s /usr/local/share/mcmi/scripts/worker.sh /usr/local/bin/mcmi-worker
#
# Application certificates
#
ARG MCMI_CA_KEY
ARG MCMI_CA_CERT
ARG MCMI_KEY
ARG MCMI_CERT

RUN ln -s /usr/local/share/mcmi/scripts/store-key.py /usr/local/bin/store-key
RUN ln -s /usr/local/share/mcmi/scripts/store-cert.py /usr/local/bin/store-cert

RUN store-key /etc/ssl/private/mcmi-ca.key "${MCMI_CA_KEY}"
RUN store-cert /usr/local/share/ca-certificates/mcmi-ca.crt "${MCMI_CA_CERT}"
RUN update-ca-certificates

RUN store-key /etc/ssl/private/mcmi.key "${MCMI_KEY}"
RUN store-cert /etc/ssl/certs/mcmi.crt "${MCMI_CERT}"
#
# Execution gateway
#
EXPOSE 5123
EXPOSE 5323
ENTRYPOINT ["mcmi"]
