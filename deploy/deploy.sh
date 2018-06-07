#!/usr/bin/env bash

export VERSION=v`date +%Y%m%d%H%M%S`

export PROJECT_ID="$(gcloud config get-value project -q)"

export DOCKER_IMAGE=gcr.io/${PROJECT_ID}/hackaton-test:${VERSION}

echo Build docker container
sudo docker build -t  ${DOCKER_IMAGE} . -f deploy/Dockerfile

echo Push docker container to GCloud
sudo `which gcloud` docker -- push ${DOCKER_IMAGE}

envsubst < deploy/hackaton-kin.yml | kubectl apply -f -

kubectl get po -w