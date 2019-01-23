#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

APP_USER="${1:-root}"
LOG_FILE="${2:-/dev/stderr}"
DEV_BUILD="${3:-false}"
TIME_ZONE="${4:-EST}"

if [ "$APP_USER" == 'root' ]
then
    APP_HOME="/root"
else
    APP_HOME="/home/${APP_USER}"
fi
#-------------------------------------------------------------------------------

echo "Upgrading core OS packages" | tee -a "$LOG_FILE"
apt-get update -y >>"$LOG_FILE" 2>&1
apt-get upgrade -y >>"$LOG_FILE" 2>&1

echo "Installing core dependencies" | tee -a "$LOG_FILE"
apt-get install -y \
        iptables \
        apt-utils \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg2 \
        curl \
        wget \
        nfs-common \
     >>"$LOG_FILE" 2>&1

echo "Syncronizing time" | tee -a "$LOG_FILE"
apt-get --yes install ntpdate >>"$LOG_FILE" 2>&1
ntpdate 0.amazon.pool.ntp.org >>"$LOG_FILE" 2>&1

echo "Installing development tools" | tee -a "$LOG_FILE"
apt-get install -y \
        net-tools \
        git \
     >>"$LOG_FILE" 2>&1

echo "Installing Docker" | tee -a "$LOG_FILE"
apt-key adv --fetch-keys https://download.docker.com/linux/ubuntu/gpg >>"$LOG_FILE" 2>&1
add-apt-repository \
        "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) \
        stable" \
    >>"$LOG_FILE" 2>&1

sudo apt-get update >>"$LOG_FILE" 2>&1
apt-get install -y docker-ce >>"$LOG_FILE" 2>&1
usermod -aG docker "$APP_USER" >>"$LOG_FILE" 2>&1

echo "Installing Docker Compose" | tee -a "$LOG_FILE"
curl -L -o /usr/local/bin/docker-compose https://github.com/docker/compose/releases/download/1.23.2/docker-compose-Linux-x86_64 >>"$LOG_FILE" 2>&1
chmod 755 /usr/local/bin/docker-compose >>"$LOG_FILE" 2>&1

echo "Configuring firewall" | tee -a "$LOG_FILE"
mkdir -p /etc/iptables >>"$LOG_FILE" 2>&1
echo "
*filter
:INPUT ACCEPT [0:0]
:FORWARD DROP [0:0]
:OUTPUT ACCEPT [0:0]
:FILTERS - [0:0]
:DOCKER-USER - [0:0]

-F INPUT
-F DOCKER-USER
-F FILTERS

-A INPUT -i lo -j ACCEPT
-A INPUT -p icmp --icmp-type any -j ACCEPT
-A INPUT -j FILTERS

-A DOCKER-USER -i ens33 -j FILTERS

-A FILTERS -m state --state ESTABLISHED,RELATED -j ACCEPT
-A FILTERS -m state --state NEW -m tcp -p tcp --dport 5123 -j ACCEPT
" > /etc/iptables/rules

if [ "$DEV_BUILD" == "true" ]
then
    echo "
-A FILTERS -m state --state NEW -m tcp -p tcp --dport 22 -j ACCEPT
-A FILTERS -m state --state NEW -m tcp -p tcp --dport 5432 -j ACCEPT
" >> /etc/iptables/rules
fi

echo "
-A FILTERS -m limit --limit 5/min -j LOG --log-prefix \"iptables denied: \" --log-level 7
-A FILTERS -j REJECT --reject-with icmp-host-prohibited
COMMIT
" >> /etc/iptables/rules

iptables-restore -n /etc/iptables/rules >>"$LOG_FILE" 2>&1
echo "
[Unit]
Description=Restore iptables firewall rules
Before=network-pre.target

[Service]
Type=oneshot
ExecStart=/sbin/iptables-restore -n /etc/iptables/rules

[Install]
WantedBy=multi-user.target
" > /etc/systemd/system/iptables.service

systemctl enable --now iptables >>"$LOG_FILE" 2>&1

echo "Updating system variables" | tee -a "$LOG_FILE"
if ! grep -q -F '# IPv6 disable' /etc/sysctl.d/99-sysctl.conf 2>/dev/null
then
    echo "
###################################################################
# IPv6 disable
#
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
net.ipv6.conf.lo.disable_ipv6 = 1
" >> /etc/sysctl.d/99-sysctl.conf
fi

sysctl -p >>"$LOG_FILE" 2>&1

echo "
#!/bin/bash
# Load kernel variables from /etc/sysctl.d
/etc/init.d/procps restart
exit 0
" > /etc/rc.local

chmod 755 /etc/rc.local >>"$LOG_FILE" 2>&1

echo "Initializing application" | tee -a "$LOG_FILE"
if [ "$DEV_BUILD" != "true" ]
then
    mkdir -p /var/local/cenv >>"$LOG_FILE" 2>&1
    mkdir -p /usr/local/lib/cenv >>"$LOG_FILE" 2>&1
    
    curl -L -o "${APP_HOME}/docker-compose.yml" https://raw.githubusercontent.com/venturiscm/ce/master/app/docker-compose.prod.yml >>"$LOG_FILE" 2>&1
fi

if [ ! -f /var/local/cenv/django.env ]
then
    echo "
SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 40 | head -n 1)
TIME_ZONE=$TIME_ZONE
" > /var/local/cenv/django.env
fi

if [ ! -f /var/local/cenv/pg.credentials.env ]
then
    echo "
POSTGRES_DB=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
POSTGRES_USER=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
POSTGRES_PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
" > /var/local/cenv/pg.credentials.env
fi

docker-compose -f "${APP_HOME}/docker-compose.yml" build >>"$LOG_FILE" 2>&1
docker-compose -f "${APP_HOME}/docker-compose.yml" up -d >>"$LOG_FILE" 2>&1
