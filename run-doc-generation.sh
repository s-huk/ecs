#!/bin/bash

. .venv/bin/activate && python doc/genutil.py -a gen-doc -p "pipelines/*/*.conf"
