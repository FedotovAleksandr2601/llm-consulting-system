# LLM Consulting System

## Описание проекта

**LLM Consulting System** — это учебная двухсервисная распределённая система для безопасного доступа к LLM-консультациям через Telegram-бота.

Архитектура проекта построена по принципу разделения ответственности:

- **Auth Service** отвечает только за регистрацию пользователей, логин и выпуск JWT-токенов;
- **Bot Service** предоставляет доступ к LLM через Telegram-бота и допускает пользователя к функциональности только при наличии валидного JWT.

Такой подход приближает проект к реальной микросервисной архитектуре: сервис авторизации изолирован от прикладного сервиса, а Telegram-бот не знает ничего о пользователях, паролях и механизмах регистрации.

## Архитектура системы

В проекте используются следующие компоненты:

- **auth_service** — FastAPI-сервис авторизации;
- **bot_api** — FastAPI API для Bot Service;
- **bot_worker** — Celery worker для фоновой обработки LLM-запросов;
- **telegram_bot** — Telegram-бот на aiogram;
- **redis** — хранение состояний и/или backend результатов;
- **rabbitmq** — брокер задач Celery;
- **OpenRouter** — внешний API для генерации ответов LLM.

### Сценарий работы

1. Пользователь регистрируется через **Auth Service**.
2. Пользователь выполняет логин и получает **JWT-токен**.
3. Пользователь отправляет токен Telegram-боту командой:

```text
/token <JWT>
```

4. Бот сохраняет токен, привязанный к Telegram user_id.
5. Пользователь отправляет обычное сообщение боту.
6. Bot Service валидирует JWT.
7. При валидном токене Bot Service публикует задачу в **RabbitMQ**.
8. **Celery worker** обрабатывает задачу, обращается к **OpenRouter** и получает ответ LLM.
9. Ответ отправляется пользователю в Telegram.
10. **Redis** используется в прикладной логике сервиса.

## Ключевые свойства реализации

- JWT создаётся **только в Auth Service**.
- Bot Service **не хранит пользователей** и **не обращается напрямую к базе Auth Service**.
- Telegram-бот **не выполняет регистрацию и логин**.
- Запросы к LLM **не выполняются напрямую в Telegram-handler**, а отправляются в очередь.
- **RabbitMQ** и **Redis** реально участвуют в обработке, а не подключены формально.

## Технологический стек

### Auth Service

- Python 3.11+
- FastAPI
- SQLAlchemy 2.0
- aiosqlite
- pydantic / pydantic-settings
- python-jose
- passlib + bcrypt
- uvicorn
- pytest / pytest-asyncio / httpx / respx

### Bot Service

- Python 3.11+
- FastAPI
- aiogram
- Celery
- RabbitMQ
- Redis
- httpx
- pydantic-settings
- python-jose
- pytest / pytest-asyncio / pytest-mock / fakeredis / respx

### Инфраструктура

- Docker
- Docker Compose
- uv
- OpenRouter API

Зависимости и виртуальное окружение в проекте управляются через **uv**; спецификация зависимостей хранится в `pyproject.toml`, а зафиксированные версии — в `uv.lock`.

## Структура проекта

```text
llm-consulting-system/
├── auth_service/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py
│   │   │   ├── router.py
│   │   │   └── routes_auth.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── exceptions.py
│   │   │   └── security.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── models.py
│   │   │   └── session.py
│   │   ├── repositories/
│   │   │   └── users.py
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   └── user.py
│   │   ├── usecases/
│   │   │   └── auth.py
│   │   └── main.py
│   ├── tests/
│   │   ├── test_auth_integration.py
│   │   └── test_security.py
│   ├── .env.example
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── pytest.ini
├── bot_service/
│   ├── app/
│   │   ├── bot/
│   │   │   ├── dispatcher.py
│   │   │   └── handlers.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── jwt.py
│   │   ├── infra/
│   │   │   ├── celery_app.py
│   │   │   └── redis.py
│   │   ├── services/
│   │   │   └── openrouter_client.py
│   │   ├── tasks/
│   │   │   └── llm_tasks.py
│   │   └── main.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_handlers.py
│   │   ├── test_jwt.py
│   │   └── test_openrouter_client.py
│   ├── .env.example
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── pytest.ini
│   └── run_bot.py
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Docker Compose

Проект запускается в виде нескольких контейнеров:

- `auth_service` — FastAPI Auth Service, порт `8000`;
- `bot_api` — FastAPI Bot API, порт `8001`;
- `bot_worker` — Celery worker;
- `telegram_bot` — Telegram bot process;
- `redis` — порт `6379`;
- `rabbitmq` — порты `5672` и `15672`.

### Используемые порты

- `8000:8000` — Auth Service Swagger/API
- `8001:8001` — Bot API
- `6379:6379` — Redis
- `5672:5672` — RabbitMQ broker
- `15672:15672` — RabbitMQ management UI

## Переменные окружения

### Auth Service

Пример `.env`:

```env
APP_NAME=auth-service
ENV=local

JWT_SECRET=change_me_super_secret
JWT_ALG=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

SQLITE_PATH=./auth.db
```

### Bot Service

Пример `.env`:

```env
APP_NAME=bot-service
ENV=local

TELEGRAM_BOT_TOKEN=

JWT_SECRET=change_me_super_secret
JWT_ALG=HS256

REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672//

OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=stepfun/step-3.5-flash:free
OPENROUTER_SITE_URL=https://example.com
OPENROUTER_APP_NAME=bot-service
```

> Важно: `JWT_SECRET` в `auth_service` и `bot_service` должен совпадать, потому что Bot Service валидирует токен, выданный Auth Service.

## Запуск проекта

### 1. Клонирование репозитория

```bash
git clone <repo_url>
cd llm-consulting-system
```

### 2. Подготовка окружения

Заполнить `.env` файлы для обоих сервисов:

- `auth_service/.env`
- `bot_service/.env`

Необходимо указать:
- `TELEGRAM_BOT_TOKEN`
- `OPENROUTER_API_KEY`
- `JWT_SECRET`

### 3. Запуск контейнеров

```bash
docker compose up --build
```

### 4. Проверка сервисов

После запуска должны быть доступны:

- Auth Service Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
- Bot API: [http://localhost:8001/docs](http://localhost:8001/docs)
- RabbitMQ UI: [http://localhost:15672](http://localhost:15672)

## Использование

### Регистрация пользователя

В Swagger Auth Service вызвать:

```text
POST /auth/register
```

При регистрации использовать email в требуемом формате, например:

```text
Surname@domain.com
```

### Логин и получение JWT

Вызвать endpoint:

```text
POST /auth/login
```

После успешного логина сервис возвращает JWT-токен.

### Проверка профиля

Для проверки токена можно вызвать:

```text
GET /auth/me
```

с заголовком:

```text
Authorization: Bearer <JWT>
```

### Авторизация в Telegram-боте

Отправить боту:

```text
/token <JWT>
```

После этого бот должен подтвердить, что токен принят и сохранён.

### Получение ответа от LLM

После сохранения токена пользователь отправляет обычное сообщение боту.  
Bot Service валидирует JWT, отправляет задачу в очередь и после обработки возвращает ответ, полученный через OpenRouter.

## Реализация Auth Service

Auth Service реализует основные endpoint-ы:

- `POST /auth/register` — регистрация пользователя;
- `POST /auth/login` — логин и выдача JWT;
- `GET /auth/me` — получение профиля по валидному JWT.

Особенности реализации:

- пароль хранится только в виде хеша;
- JWT содержит `sub`, `role`, `iat`, `exp`;
- бизнес-логика вынесена в usecase-слой;
- доступ к данным вынесен в repository-слой;
- ошибки оформлены через собственные исключения.

## Реализация Bot Service

Bot Service разделён на несколько слоёв:

- `bot/` — aiogram dispatcher и handlers;
- `core/` — конфигурация и валидация JWT;
- `infra/` — Redis и Celery;
- `services/` — клиент OpenRouter;
- `tasks/` — Celery-задачи.

Основная логика:

- `/token <jwt>` сохраняет JWT в Redis;
- обычный текстовый запрос допускается только при валидном токене;
- запрос к LLM отправляется в Celery;
- worker обрабатывает задачу и формирует ответ пользователю.

## Асинхронная обработка

Для асинхронной обработки запросов используются:

- **RabbitMQ** как брокер задач;
- **Celery** как механизм фонового выполнения;
- **Redis** как backend результата и/или хранилище состояния.

Такой подход позволяет Telegram-боту не блокироваться во время ожидания ответа LLM.

## Тестирование

Тестирование разделено на **unit**, **integration** и **mock** тесты.

### Auth Service

#### Unit tests

Проверяются функции безопасности:

- хеширование пароля;
- проверка пароля;
- создание JWT;
- декодирование JWT;
- наличие полей `sub`, `role`, `iat`, `exp`.

Файл:
- `auth_service/tests/test_security.py`

#### Integration tests

Проверяется пользовательский сценарий через HTTP:

- регистрация пользователя;
- логин через form-data;
- доступ к `/auth/me` по Bearer token.

Также проверяются негативные сценарии:

- повторная регистрация -> `409`;
- неверный пароль -> `401`;
- запрос без токена или с неверным токеном -> `401`.

Файл:
- `auth_service/tests/test_auth_integration.py`

### Bot Service

#### Unit tests

Проверяется валидация JWT:

- корректное извлечение `sub`;
- ошибка при невалидном токене.

Файл:
- `bot_service/tests/test_jwt.py`

#### Mock tests

Проверяется логика Telegram-handlers без реального Redis и RabbitMQ:

- сохранение токена по команде `/token <jwt>`;
- отказ в доступе при отсутствии токена;
- вызов `llm_request.delay(...)` при наличии валидного токена.

Используются:
- `fakeredis`;
- `pytest-mock`.

Файл:
- `bot_service/tests/test_handlers.py`

#### Integration tests

Проверяется клиент OpenRouter без реального доступа в интернет:

- мокается endpoint `POST /chat/completions`;
- проверяется корректность payload;
- проверяется извлечение `choices[0].message.content`.

Используется:
- `respx`.

Файл:
- `bot_service/tests/test_openrouter_client.py`

### Запуск тестов

#### Auth Service

```bash
cd auth_service
pytest -v
```

#### Bot Service

```bash
cd bot_service
pytest -v
```

## Скриншоты для сдачи

Для демонстрации проекта необходимы следующие скриншоты. Они находятся в папке screenshots/:

- Swagger Auth Service:
  - регистрация;
  - логин;
  - `/auth/me`;
- Telegram-бот:
  - команда `/token <jwt>`;
  - подтверждение сохранения токена;
  - запрос пользователя;
  - ответ от LLM;
- RabbitMQ UI:
  - очереди;
  - consumers;
  - сообщения;
- результаты тестов:
  - `auth_service`;
  - `bot_service`.

## Быстрая проверка проекта

1. Запустить `docker compose up --build`
2. Открыть Swagger Auth Service
3. Зарегистрировать пользователя и получить JWT
4. Отправить токен в Telegram через `/token <JWT>`
5. Отправить сообщение боту и получить ответ от LLM
6. Проверить RabbitMQ UI и результаты тестов

## Соответствие требованиям задания

Проект удовлетворяет ключевым требованиям задания:

- система разделена на два независимых сервиса;
- JWT выпускается только в Auth Service;
- Bot Service только валидирует JWT;
- запросы к LLM выполняются асинхронно;
- RabbitMQ и Redis участвуют в реальной обработке;
- реализованы unit, integration и mock тесты;
- присутствует документация и демонстрационные материалы.

## Быстрый старт

```bash
docker compose up --build
```

После запуска:
- Auth Service Swagger: http://localhost:8000/docs
- Bot API: http://localhost:8001/docs
- RabbitMQ UI: http://localhost:15672