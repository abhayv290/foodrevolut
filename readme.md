# FoodRevolut API

Django REST backend for a food delivery app with auth, restaurants, orders, payments, reviews, search, and live tracking.

## Stack

- Django 6, DRF, SimpleJWT
- PostgreSQL
- Redis, Celery, Channels (WebSocket)
- Nginx, Docker, Docker Compose
- drf-spectacular for API docs

## Project structure

- apps/users: auth, profiles, addresses, email flows
- apps/restaurants: restaurants, categories, menu items
- apps/orders: cart, checkout, orders, order status history
- apps/payments: payment initiation and verification
- apps/reviews: restaurant and delivery reviews
- apps/search: search and autocomplete
- apps/tracking: websocket consumer and routing
- config/settings: base, local, prod settings
- docker/nginx: Nginx config for proxying

## Local run (Docker)

1. Create local env file.

```powershell
Copy-Item .env.example .env
```

2. Update `.env` values (DB, Redis, mail, payment keys).

3. Start services.

```powershell
docker compose -f docker-compose.yaml up --build
```

Local services:
- web: Daphne on port 8000
- worker: Celery worker
- beat: Celery beat
- db: PostgreSQL
- nginx: reverse proxy on port 80

## Production run

- Compose file: `docker-compose.prod.yaml`
- Env file: `.env.prod`
- Settings module: `config.settings.prod`
- Image source: `${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}`

## API and docs

- Health: `/api/health/`
- API base: `/api/v1/`
- Swagger: `/api/docs/`
- ReDoc: `/api/redoc/`
- Schema: `/api/schema`

## WebSocket

- Tracking endpoint:

```text
ws://<host>/ws/tracking/<order_id>/?token=<access_token>
```

