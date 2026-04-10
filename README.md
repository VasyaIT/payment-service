# Payment Processing Service

Асинхронный микросервис для обработки платежей с использованием FastAPI, RabbitMQ и PostgreSQL.

## Архитектура

- **API** — FastAPI-сервис, принимает запросы на создание и получение платежей
- **Consumer** — FastStream-воркер, обрабатывает платежи из очереди RabbitMQ
- **Outbox Pattern** — гарантированная доставка событий через таблицу outbox
- **DLQ** — Dead Letter Queue для сообщений, которые не удалось обработать после 3 попыток

## Запуск

```bash
docker compose up --build
```

Сервисы:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- RabbitMQ Management: http://localhost:15672 (guest/guest)

## API

### Создание платежа

```bash
curl -X POST http://localhost:8000/api/v1/payments \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -H "Idempotency-Key: unique-key-123" \
  -d '{
    "amount": 100.50,
    "currency": "RUB",
    "description": "Test payment",
    "metadata": {"order_id": "ord-001"},
    "webhook_url": "https://httpbin.org/post"
  }'
```

Ответ (202 Accepted):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2026-04-09T12:00:00Z"
}
```

### Получение платежа

```bash
curl http://localhost:8000/api/v1/payments/{payment_id} \
  -H "X-API-Key: test-api-key"
```

## Стек

- FastAPI + Pydantic v2
- SQLAlchemy 2.0 (async)
- PostgreSQL
- RabbitMQ (FastStream)
- Alembic
- Docker Compose
