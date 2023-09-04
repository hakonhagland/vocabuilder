#!/bin/bash

# PWD = /root/vocabuilder (was set in Dockerfile)
python -m venv .venv
source .venv/bin/activate
pip install .
exec bash
