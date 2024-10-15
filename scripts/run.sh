#!/bin/bash
set -eux

# kill any other instances
./scripts/kill.sh

# run in python environment
source .venv/bin/activate
python3 -m laserharp.server
