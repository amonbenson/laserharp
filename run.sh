#!/bin/bash
set -eux

./kill.sh

cd ..
python3 -m laserharp
cp cap_*.jpg laserharp # store tmp captures
cd -
