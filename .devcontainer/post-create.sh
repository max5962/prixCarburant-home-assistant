#!/usr/bin/env bash

source /opt/container/helpers/common/paths.sh
mkdir -p /config

# Required to get automations to work
echo "Creatin automations.yaml"
touch /config/automations.yaml

# source: /opt/container/helpers/commons/homeassistant/start.sh
if test -d "custom_components"; then
  echo "Symlink the custom component directory"

  if test -d "custom_components"; then
    rm -R /config/custom_components
  fi

  ln -sf "$(workspacePath)custom_components/" /config/custom_components || echo "Could not copy the custom_component" exit 1
elif  test -f "__init__.py"; then
  echo "Having the component in the root is currently not supported"
fi

# Install
echo "Install home assistant"
container install

echo "Installing Requirements_dev.txt"
pip install -r $(workspacePath)requirements_dev.txt


# pre-commit
echo "Install pre-commit dependencies"
sudo apt update; apt install -y ruby vim

echo "Install Pre-Commit in this repo"
pre-commit install

# Custom Cards & Modules
echo "Installing NodeJS"
curl -fsSL https://deb.nodesource.com/setup_16.x | bash -
apt-get install -y nodejs
