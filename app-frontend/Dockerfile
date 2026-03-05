FROM node:22-alpine

RUN corepack enable

WORKDIR /app

# Install dependencies (with caching)
COPY package.json pnpm-lock.yaml .npmrc ./
RUN pnpm install --frozen-lockfile

# Copy source code
COPY . .

# Default command (overridden by docker-compose)
CMD ["pnpm", "dev"]
