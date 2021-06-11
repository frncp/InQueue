# Dockerfile-nginx
FROM nginx:latest

EXPOSE 5000
EXPOSE 80

RUN rm /etc/nginx/conf.d/default.conf

COPY app.conf /etc/nginx/conf.d
