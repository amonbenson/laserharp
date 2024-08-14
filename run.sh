#!/bin/bash
set -eux

./kill.sh

LH_MODULE=$(basename $PWD)

source .venv/bin/activate

cd ..
python3 -m $LH_MODULE
cp cap_*.jpg laserharp # store tmp captures
cd -
