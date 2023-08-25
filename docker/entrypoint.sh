#!/bin/bash

# PWD = /root (was set in Dockerfile)
# Create venv here and not pollute the mapped volume in the /root/vocabuilder folder
python -m venv .venv
cd vocabuilder
source ../.venv/bin/activate
pip install .
exec bash
