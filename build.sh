#!/usr/bin/env bash
# Build all sites (or: bash build.sh spring). Output: dist/<site>/
set -e
python3 build.py "$@"
(cd tools && npx tailwindcss -c tailwind.config.js -i input.css -o ../shared/site.css --minify 2>&1 | tail -1)
python3 build.py "$@" >/dev/null   # second pass so the ?v= on site.css matches the finished stylesheet
for d in dist/*/; do cp shared/site.css "$d/assets/site.css"; done
