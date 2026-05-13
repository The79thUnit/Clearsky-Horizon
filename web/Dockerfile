# HORIZON web (Vite dev server for Phase 1 local-first).
# Production build (nginx multi-stage) is a Phase 2 concern.

FROM node:22-alpine
WORKDIR /app

# Install deps first for layer caching
COPY package.json ./
RUN npm install --no-audit --no-fund

# Copy source
COPY index.html ./
COPY vite.config.ts tsconfig.json tsconfig.node.json ./
COPY src ./src

EXPOSE 5173

# Vite dev server is fine for Phase 1 local-first
CMD ["npm", "run", "dev"]
