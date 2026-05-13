FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json ./
COPY apps/web/package.json apps/web/package.json
COPY apps/web/package-lock.json apps/web/package-lock.json
RUN npm ci --prefix apps/web

FROM node:20-alpine AS build
WORKDIR /app
ENV NODE_ENV=production
ARG SITE_URL=http://localhost:4321
ENV SITE_URL=${SITE_URL}
COPY --from=deps /app/apps/web/node_modules apps/web/node_modules
COPY . .
RUN npm run build --prefix apps/web

FROM caddy:2.8-alpine AS runtime
COPY infra/caddy/Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/apps/web/dist /srv
EXPOSE 80 443
