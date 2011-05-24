#!/bin/bash

# Publishes the results of the last run: copies ../../public_html_nonlive to ../../public_html, and ../../judgmental_nonlive.db to ../../judgmental.db

echo "Copying to judgmental.db"
cp -f ../../judgmental_nonlive.db ../../judgmental.db

echo "Copying to public_html"
rsync -ru ../../public_html_nonlive ../../public_html_live