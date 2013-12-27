#!/bin/bash

echo "Copying judgmental.db"
cp -f ../judgmental_nonlive.db ../judgmental.db

echo "Copying index.html"
cp -f ../public_html/index_nonlive.html ../public_html/index.html

echo "Copying judgments"
if [ ! -d ../public_html/judgments ]; then
    mkdir ../public_html/judgments;
fi
rsync -ru --delete ../public_html/judgments_nonlive/* ../public_html/judgments/
