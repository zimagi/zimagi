#/usr/bin/env bash

#
# This script will wipe your Docker environment!  Don't run run unless you 
# know what you are doing or don't care about your current Docker work.
#
# Inspired by: https://stackoverflow.com/a/42116347
#

#
# Remove all containers
#
containers=$(docker ps -aq)

if [ ! -z "$containers" ]
then
  docker stop $containers
  docker rm $containers
fi

#
# Remove all networks
#
docker network prune -f

#
# Remove unused Docker images
#
images=$(docker images --filter dangling=true -qa)

if [ ! -z "$images" ]
then
  docker rmi -f $images
fi

#
# Remove all Docker volumes
#
volumes=$(docker volume ls --filter dangling=true -q)

if [ ! -z "$volumes" ]
then
  docker volume rm $volumes
fi

#
# Clean up any remaining images
#
images=$(docker images -qa)

if [ ! -z "$images" ]
then
  docker rmi -f $images
fi
