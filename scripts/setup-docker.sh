#!/usr/bin/env bash
# Setup Docker and Docker Compose.

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/.."

DOCKER_USER="${1:-vagrant}"

LOG_FILE="${1:-./logs/docker.log}"
if [ "$LOG_FILE" != "/dev/stdout" -a "$LOG_FILE" != "/dev/stderr" ]
then
  rm -f "$LOG_FILE"
fi

if ! id -u "$DOCKER_USER" >/dev/null 2>&1
then 
  echo "> Docker user '$DOCKER_USER' does not exist."
  echo "> Specify valid username as script argument."
  exit 1
fi

#download and install Docker if it does not exist
if ! which docker >/dev/null
then
  apt-get update >>"$LOG_FILE" 2>&1
  
  echo "> Installing Docker dependencies" | tee -a "$LOG_FILE"
  apt-get install -y lxc wget bsdtar curl >>"$LOG_FILE" 2>&1
  apt-get install -y linux-image-extra-$(uname -r) >>"$LOG_FILE" 2>&1
  modprobe aufs >>"$LOG_FILE" 2>&1
  
  echo "> Installing Docker" | tee -a "$LOG_FILE"
  wget --quiet -O- https://get.docker.com/ | sh >>"$LOG_FILE" 2>&1
  sed -i "s/^start on (local-filesystems and net-device-up IFACE!=lo)/start on docker-ready/" /etc/init/docker.conf >>"$LOG_FILE" 2>&1
  usermod -aG docker "$DOCKER_USER" >>"$LOG_FILE" 2>&1
fi
initctl emit docker-ready >>"$LOG_FILE" 2>&1

#download and install Docker Compose if it does not exist
if ! which docker-compose >/dev/null
then
  echo "> Installing Docker Compose" | tee -a "$LOG_FILE"
  curl -L -o /usr/local/bin/docker-compose https://github.com/docker/compose/releases/download/1.23.1/docker-compose-Linux-x86_64 >>"$LOG_FILE" 2>&1
  chmod +x /usr/local/bin/docker-compose >>"$LOG_FILE" 2>&1
fi
