# Node 24 to match @types/node ^24 and Vite 8.
FROM node:24-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# `npm run build` is `vue-tsc -b && vite build`, so a type error fails the image build.
# No VITE_API_BASE_URL: unset, the app falls back to window.location.origin, which is
# what single-origin nginx serving needs (see src/lib/api.ts).
RUN npm run build


FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
