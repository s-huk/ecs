#!/bin/bash

. .venv/bin/activate && python src/genutil.py -a gen-doc -p "pipelines/*/*.conf"
