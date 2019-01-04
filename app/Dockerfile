FROM python:3.6-slim-stretch
#
#====================================================================
# OS environment configuration
#
#
# Core environment variables
#
ENV DEBIAN_FRONTEND noninteractive
ENV LANG C.UTF-8
ENV PYTHONUNBUFFERED 1
#
# Package repository management
#
RUN apt-get update -y \
    && apt-get install -y \
        # Security packages
        "apt-transport-https" \
        "ca-certificates" \
        "gnupg2" \
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
        # Utilities
        "curl" \
        "git" \
        # Database support
        "sqlite3" \
        "libsqlite3-dev" \
        # Service clients
        "kubectl" \
    && rm -rf /var/lib/apt/lists/*
#
# Python dependencies
#
RUN pip install --no-cache-dir \
    # Orchestration application requirements
    "django==2.1.3" \
    "psycopg2-binary==2.7.6.1" \
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
    "pycryptodome==3.7.2" \
    # Cloud service integrations
    "boto3==1.9.66" \
    # Repository integrations
    "GitPython==2.1.11"
#
# Kubernetes dependencies
#
RUN curl -o /tmp/helm_install.sh https://raw.githubusercontent.com/helm/helm/v2.9.1/scripts/get && \
    chmod 700 /tmp/helm_install.sh
RUN /tmp/helm_install.sh && rm -f /tmp/helm_install.sh
#
#====================================================================
# Application configuration
#
#
# Application environment variables
#
ENV REQUESTS_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt
ENV HELM_TLS_VERIFY false
ENV HELM_TLS_ENABLE true
#
# Data directory
#
RUN mkdir /var/local/cenv
VOLUME /var/local/cenv
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
