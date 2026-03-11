#!/bin/sh
set -eu

: "${API_BASE_URL:=}"

envsubst '${API_BASE_URL}' \
  < /usr/share/nginx/html/config.js.template \
  > /usr/share/nginx/html/config.js
