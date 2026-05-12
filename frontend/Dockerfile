# ---- 本地已构建版：服务器直接 COPY 产物，无需 Node ----
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY dist /usr/share/nginx/html
EXPOSE 80
