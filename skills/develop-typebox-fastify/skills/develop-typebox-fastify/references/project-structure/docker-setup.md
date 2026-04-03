# Docker Setup for Fastify + TypeBox Projects

## Overview

Multi-stage Docker builds keep production images small and secure. This covers Dockerfile
patterns, docker-compose for development, and container best practices.

## Multi-Stage Dockerfile

```dockerfile
# Stage 1: Dependencies
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

# Stage 2: Build
FROM node:22-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build
# Remove dev dependencies after build
RUN npm prune --production

# Stage 3: Production
FROM node:22-alpine AS production
WORKDIR /app

# Security: Run as non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup

# Copy only what's needed
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./
COPY --from=build /app/drizzle ./drizzle

# Set environment
ENV NODE_ENV=production
ENV PORT=3000

# Use non-root user
USER appuser

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health/live || exit 1

# Start the app (exec form for signal handling)
CMD ["node", "dist/server.js"]
```

## .dockerignore

```
node_modules
dist
.git
.env*
!.env.example
*.md
test
coverage
.vscode
.idea
docker-compose*.yml
Dockerfile
.dockerignore
```

## Docker Compose for Development

```yaml
# docker-compose.yml
services:
  api:
    build:
      context: .
      target: deps  # Use deps stage for development
    volumes:
      - .:/app
      - /app/node_modules  # Prevent overwriting container node_modules
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/myapp_dev
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=dev-secret-at-least-32-characters-long
    command: npx tsx watch src/server.ts
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: myapp_dev
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  # Optional: DB admin UI
  pgadmin:
    image: dpage/pgadmin4
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@local.dev
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"
    profiles:
      - tools

volumes:
  pgdata:
```

## Docker Compose for Production-Like Testing

```yaml
# docker-compose.prod.yml
services:
  api:
    build:
      context: .
      target: production
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/myapp
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
```

## Running Migrations in Docker

```yaml
# docker-compose.yml - add a migration service
services:
  migrate:
    build:
      context: .
      target: build
    command: node dist/db/migrate.js
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/myapp_dev
    depends_on:
      db:
        condition: service_healthy
    profiles:
      - migration
```

```bash
# Run migrations
docker compose --profile migration run --rm migrate
```

## Common Commands

```bash
# Start development environment
docker compose up -d

# View logs
docker compose logs -f api

# Run tests in container
docker compose exec api npm test

# Rebuild after dependency changes
docker compose build --no-cache api

# Production build
docker compose -f docker-compose.prod.yml up -d

# Clean up
docker compose down -v  # Remove volumes too
```

## Key Points

- Use multi-stage builds: deps -> build -> production (small final image)
- Run as non-root user in production containers
- Use `CMD` exec form (`["node", "..."]`) for proper signal handling
- Mount source code as volume in development for hot reload
- Use health checks for container orchestration
- Never copy `.env` files into images -- use environment variables
- Use `docker compose` profiles for optional services (pgadmin, migrations)
- Set memory limits in production to prevent OOM issues
