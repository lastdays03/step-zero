
FROM node:20-alpine

WORKDIR /app

# Install dependencies (with caching)
COPY package.json package-lock.json* ./
RUN npm install

# Copy source code
COPY . .

# Build step is optional for dev, but good to have ready
# RUN npm run build

# Default command (overridden by docker-compose)
CMD ["npm", "run", "dev"]
