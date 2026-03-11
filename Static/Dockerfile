FROM nginx:alpine
COPY Static/ /usr/share/nginx/html
COPY Static/nginx.conf.template /etc/nginx/templates/default.conf.template
COPY Static/docker-entrypoint.d/40-env-config.sh /docker-entrypoint.d/40-env-config.sh
EXPOSE 8080
