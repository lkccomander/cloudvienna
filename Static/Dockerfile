FROM nginx:alpine
COPY Static/ /usr/share/nginx/html
COPY Static/nginx.conf.template /etc/nginx/templates/default.conf.template
CMD ["/bin/sh", "-c", "envsubst '${API_BASE_URL}' < /usr/share/nginx/html/config.js.template > /usr/share/nginx/html/config.js && exec nginx -g 'daemon off;'"]
EXPOSE 8080
