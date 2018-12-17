#!/bin/bash

. .venv/bin/activate && python doc/genutil.py -a doc -p "pipelines/*/*.conf"
