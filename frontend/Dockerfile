FROM node:20-slim AS build-stage

WORKDIR /app

COPY package*.json ./
RUN rm -f package-lock.json && npm install

COPY . .

RUN npm run build

FROM nginx:stable-alpine AS production-stage

# Configurar permissões para rodar como usuário não-root (nginx)
# Criamos o arquivo pid e damos permissão nas pastas de cache e log
RUN touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid /var/cache/nginx /var/log/nginx /etc/nginx/conf.d

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build-stage --chown=nginx:nginx /app/dist /usr/share/nginx/html

USER nginx

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]