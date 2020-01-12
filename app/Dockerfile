FROM python:3.7-stretch
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
RUN echo "deb [arch=amd64] https://download.docker.com/linux/debian/ stretch stable" > /etc/apt/sources.list.d/docker.list
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

ENV LIBGIT_VERSION=0.28.1
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
    "pyyaml==5.1" \
    "paramiko==2.4.2" \
    "terminaltables==3.1.0" \
    "colorful==0.5.0" \
    "cryptography==2.4.2" \
    "pycryptodome==3.7.3" \
    # Service management
    "docker==3.7.1" \
    # Web server
    "gunicorn==19.9.0" \
    "gevent==1.4.0" \
    "greenlet==0.4.15" \
    # API application
    "django==2.2" \
    "psycopg2-binary==2.7.7" \
    "mysqlclient==1.4.2.post1" \
    "djangorestframework==3.9.2" \
    "coreapi==2.3.3" \
    "coreschema==0.0.4" \
    "django-db-mutex==1.1.0" \
    # Repository integrations
    "pygit2==0.28.0"
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
# Application scripts
#
RUN ln -s /usr/local/share/mcmi/scripts/ce.sh /usr/local/bin/ce
RUN ln -s /usr/local/share/mcmi/scripts/start-ce.sh /usr/local/bin/start-ce
#
# Application certificates
#
COPY ./certs/mcmi-ca.key /etc/ssl/private/mcmi-ca.key
RUN chmod 640 /etc/ssl/private/mcmi-ca.key
COPY ./certs/mcmi-ca.crt /usr/local/share/ca-certificates/mcmi-ca.crt
RUN chmod 644 /usr/local/share/ca-certificates/mcmi-ca.crt
RUN update-ca-certificates

COPY ./certs/mcmi.key /etc/ssl/private/mcmi.key
RUN chmod 640 /etc/ssl/private/mcmi.key
COPY ./certs/mcmi.crt /etc/ssl/certs/mcmi.crt
RUN chmod 644 /etc/ssl/certs/mcmi.crt
#
# Application entrypoint
#
EXPOSE 5123
ENTRYPOINT ["ce"]
