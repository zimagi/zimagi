FROM python:3.7-slim-stretch
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
RUN apt-get update -y \
    && apt-get install -y \
        # Package management utilities
        "apt-utils" \
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
    "djangorestframework==3.9.2" \
    "coreapi==2.3.3" \
    "coreschema==0.0.4" \
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
RUN mkdir /var/local/cenv
VOLUME /var/local/cenv
#
# Library directory
#
RUN mkdir /usr/local/lib/cenv
VOLUME /usr/local/lib/cenv
#
# Application directory
#
COPY ./app /usr/local/share/cenv
WORKDIR /usr/local/share/cenv
VOLUME /usr/local/share/cenv
#
# Application scripts
#
RUN ln -s /usr/local/share/cenv/scripts/ce.sh /usr/local/bin/ce
RUN ln -s /usr/local/share/cenv/scripts/start-ce.sh /usr/local/bin/start-ce
#
# Application certificates
#
COPY ./certs/cenv-ca.key /etc/ssl/private/cenv-ca.key
RUN chmod 640 /etc/ssl/private/cenv-ca.key
COPY ./certs/cenv-ca.crt /usr/local/share/ca-certificates/cenv-ca.crt
RUN chmod 644 /usr/local/share/ca-certificates/cenv-ca.crt
RUN update-ca-certificates

COPY ./certs/cenv.key /etc/ssl/private/cenv.key
RUN chmod 640 /etc/ssl/private/cenv.key
COPY ./certs/cenv.crt /etc/ssl/certs/cenv.crt
RUN chmod 644 /etc/ssl/certs/cenv.crt
#
# Application entrypoint
#
EXPOSE 5123
ENTRYPOINT ["ce"]
