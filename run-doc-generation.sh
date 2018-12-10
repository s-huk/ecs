#!/bin/bash

cat doc/intro.md > ./README.md
echo >> ./README.md
echo "## Felder" >> ./README.md
echo >> ./README.md
. .venv/bin/activate && python doc/doc.py >> ./README.md