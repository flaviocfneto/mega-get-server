#!/usr/bin/env bash
# Log in to dhi.io using credentials from .env (DHI_REGISTRY_USERNAME, DHI_REGISTRY_TOKEN).
# Run this before building the hardened image. Copy .env.example to .env and fill in values.
set -e

if [ ! -f .env ]; then
  echo "Missing .env. Copy .env.example to .env and set DHI_REGISTRY_USERNAME and DHI_REGISTRY_TOKEN."
  exit 1
fi

# shellcheck source=/dev/null
. .env

if [ -z "${DHI_REGISTRY_USERNAME}" ] || [ -z "${DHI_REGISTRY_TOKEN}" ]; then
  echo "Set DHI_REGISTRY_USERNAME and DHI_REGISTRY_TOKEN in .env."
  exit 1
fi

echo "${DHI_REGISTRY_TOKEN}" | docker login dhi.io -u "${DHI_REGISTRY_USERNAME}" --password-stdin
