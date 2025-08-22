#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Install system dependencies
apt-get update
apt-get install -y libzbar0

# 2. Install Python dependencies
pip install -r requirements.txt
