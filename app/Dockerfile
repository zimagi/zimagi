FROM python:3.6-slim-stretch
#
# Container environment variables
#
ENV DEBIAN_FRONTEND noninteractive
ENV LANG C.UTF-8
ENV PYTHONUNBUFFERED 1
ENV HELM_TLS_VERIFY false
ENV HELM_TLS_ENABLE true
#
# Application directory
#
COPY ./app /usr/local/share/cenv
WORKDIR /usr/local/share/cenv
VOLUME /usr/local/share/cenv
#
# Data directory
#
RUN mkdir /var/local/cenv
VOLUME /var/local/cenv
#
# Package repositories
#
RUN apt-get update -y \
    && apt-get install -y \
        # Package management helpers
        apt-utils \
        software-properties-common \
        # Security packages
        apt-transport-https \
        ca-certificates \
        gnupg2 \
        # Web clients
        curl \
        wget \
    && rm -rf /var/lib/apt/lists/*

RUN apt-key adv --fetch-keys https://packages.cloud.google.com/apt/doc/apt-key.gpg
RUN echo "deb http://apt.kubernetes.io/ kubernetes-xenial main" > /etc/apt/sources.list.d/kubernetes.list
#
# Base dependencies
#
RUN apt-get update -y \
    && apt-get install -y \
        # Dependency building
        "gcc" \
        "g++" \
        "make" \
        # Version control
        "git" \
        # Database support
        "sqlite3" \
        "libsqlite3-dev" \
        # Kubernetes client
        "kubectl" \
    && rm -rf /var/lib/apt/lists/*
#
# Python dependencies
#
RUN pip install --no-cache-dir \
    # Cluster provisioning requirements
    "ansible>=2.5.0,!=2.7.0" \
    "jinja2>=2.9.6" \
    "netaddr==0.7.19" \
    "pbr>=1.6" \
    "passlib==1.7.1" \
    # Orchestration application requirements
    "django==2.1.3" \
    "django-db-mutex==1.1.0" \
    "pandas==0.23.4" \
    "pytz==2018.7" \
    "titlecase==0.12.0" \
    "psutil==5.4.8" \
    "tblib==1.3.2" \
    "tabulate==0.8.2" \
    "terminaltables==3.1.0" \
    "paramiko==2.4.2" \
    # API application requirements
    "djangorestframework==3.9.0" \
    "coreapi==2.3.3" \
    "coreschema==0.0.4" \
    "greenlet==0.4.15" \
    "gevent==1.3.7" \
    "gunicorn==19.9.0" \
    # Cloud service integrations
    "boto3==1.9.66"
#
# Kubernetes dependencies
#
RUN curl -o /tmp/helm_install.sh https://raw.githubusercontent.com/helm/helm/v2.9.1/scripts/get && \
    chmod 700 /tmp/helm_install.sh
RUN /tmp/helm_install.sh && rm -f /tmp/helm_install.sh
#
# Application scripts
#
COPY ./scripts/ce.sh /usr/local/bin/ce
RUN chmod 755 /usr/local/bin/ce

COPY ./scripts/start-ce.sh /usr/local/bin/start-ce
RUN chmod 755 /usr/local/bin/start-ce
#
# Application certificates
#
RUN openssl req -new -x509 -sha256 -days 3650 -newkey rsa:4096 \
    -subj "/C=US/ST=DC/L=Washington/O=cenv/CN=localhost" \
    -keyout /etc/ssl/private/cenv-ca.key \
    -out /etc/ssl/certs/cenv-ca.crt

RUN cp /etc/ssl/certs/cenv-ca.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates

RUN openssl req -new -sha256 -days 3650 -newkey rsa:4096 \
    -subj "/C=US/ST=DC/L=Washington/O=cenv/CN=localhost" \
    -keyout /etc/ssl/private/cenv.key \
    -out /etc/ssl/certs/cenv.csr

RUN openssl x509 -req -CAcreateserial \
    -CA /etc/ssl/certs/cenv-ca.crt 
    -CAkey /etc/ssl/private/cenv-ca.key \
    -in /etc/ssl/certs/cenv.csr \
    -out /etc/ssl/certs/cenv.crt
#
# Application entrypoint
#
EXPOSE 5123
ENTRYPOINT ["bash", "-c", "ce"]
