# Reasoning: node:20-slim gives prebuilt better-sqlite3 binaries (no compiler
# needed in-image). Multi-stage isn't worth it at this size; a named volume
# carries the SQLite file so the container stays disposable.
FROM node:20-slim

ENV NODE_ENV=production
WORKDIR /app

# Install deps first for layer caching: package.json changes far less often than code.
COPY package.json package-lock.json* ./
RUN npm ci --omit=dev

COPY server ./server
COPY public ./public

# Single non-root user; the data dir must be writable for the SQLite file.
RUN mkdir -p /app/data && chown -R node:node /app
USER node

ENV PORT=3000
EXPOSE 3000
CMD ["node", "server/index.js"]
