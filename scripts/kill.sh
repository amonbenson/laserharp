#!/bin/bash
set -eux

pkill -f ".*python.*laserharp.*" || true
