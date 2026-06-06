# Build
FROM node:22-alpine AS builder
WORKDIR /app

# Install Node dependencies
COPY package.json package-lock.json ./
RUN npm ci

COPY svelte.config.js vite.config.ts tsconfig.json ./
COPY src ./src
COPY static ./static

RUN npm run build

# Production stage
FROM node:22-alpine AS runner
WORKDIR /app

# Copy only runtime dependencies and build output
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY --from=builder /app/build ./build
COPY index.cjs ./index.cjs

ENV NODE_ENV=production
ENV PORT=3000
EXPOSE 3000

CMD ["node", "index.cjs"]
