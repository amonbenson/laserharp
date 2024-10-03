#!/bin/sh
set -eux

# install imagemagick convert tool
if ! command -v convert >/dev/null 2>&1; then
    echo "convert command could not be found. Installing via apt-get"
    sudo apt-get install imagemagick -y
fi

# create icons
mkdir -p output
convert -background transparent -density 256x256 -resize 256x256 icon.svg output/icon_256.png
convert -background transparent -define 'icon:auto-resize=16,24,32,64' icon.svg output/favicon.ico

# move favicon.ico to the frontend directory
cp output/favicon.ico ../frontend/public/favicon.ico
