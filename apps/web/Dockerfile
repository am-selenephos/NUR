FROM node:22-slim AS build
WORKDIR /srv/web
COPY package.json ./
COPY apps/web/package.json apps/web/
COPY packages/shared-types/package.json packages/shared-types/
RUN npm install
COPY packages/shared-types packages/shared-types
COPY apps/web apps/web
WORKDIR /srv/web/apps/web
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
