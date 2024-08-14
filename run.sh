#!/bin/bash
set -eux

./kill.sh

source .venv/bin/activate

python3 -m laserharp
