#!/bin/bash
set -eux

pkill -f ".*python3.*laserharp.*" || true
