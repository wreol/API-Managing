# API Vault Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full-stack AI API usage management platform with encrypted key storage, multi-provider usage fetching, budget alerts, and team sharing.

**Architecture:** Modular monolith FastAPI backend with Provider plugin system + React SPA frontend. PostgreSQL for persistence, Redis for task queue. Background worker (ARQ) for periodic usage fetching and alert evaluation.

**Tech Stack:** Python 3.11+ / FastAPI / SQLAlchemy / PostgreSQL / Redis / ARQ / React 18 / TypeScript / Docker

**Estimated:** 4000–6000 lines (backend 2500+, frontend 1500+, tests 1500+)

---

## File Structure Map

```
api-vault/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app factory, CORS, router registration
│   │   ├── config.py                  # Settings from env vars (pydantic-settings)
│   │   ├── database.py                # SQLAlchemy async engine + session factory
│   │   ├── models/                    # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── api_key.py
│   │   │   ├── usage_record.py
│   │   │   ├── key_share.py
│   │   │   ├── alert_rule.py
│   │   │   ├── alert_event.py
│   │   │   └── audit_log.py
│   │   ├── schemas/                   # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── api_key.py
│   │   │   ├── usage.py
│   │   │   ├── alert.py
│   │   │   ├── team.py
│   │   │   └── provider.py
│   │   ├── api/                       # Route handlers (thin layer, delegates to services)
│   │   │   ├── __init__.py
│   │   │   ├── router.py             # Main router aggregation
│   │   │   ├── auth.py
│   │   │   ├── keys.py
│   │   │   ├── usage.py
│   │   │   ├── alerts.py
│   │   │   ├── team.py
│   │   │   ├── providers.py
│   │   │   └── deps.py               # Dependency injection (get_db, get_current_user)
│   │   ├── services/                  # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── key_service.py
│   │   │   ├── encryption_service.py
│   │   │   ├── usage_service.py
│   │   │   ├── alert_service.py
│   │   │   ├── team_service.py
│   │   │   └── audit_service.py
│   │   ├── providers/                 # Provider plugin system
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # BaseProvider abstract class
│   │   │   ├── registry.py           # ProviderRegistry: discover + register
│   │   │   ├── openai.py
│   │   │   ├── anthropic.py
│   │   │   ├── deepseek.py
│   │   │   └── generic.py            # User-configured generic REST adapter
│   │   ├── worker/                    # ARQ background tasks
│   │   │   ├── __init__.py
│   │   │   ├── fetcher.py            # fetch_all_usage() task
│   │   │   └── alert_evaluator.py    # evaluate_alerts() task
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   └── audit.py              # Audit logging middleware
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── email.py              # SMTP email sending
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py               # Fixtures: test DB, test client, test user
│   │   ├── test_auth.py
│   │   ├── test_keys.py
│   │   ├── test_providers.py
│   │   ├── test_usage.py
│   │   ├── test_alerts.py
│   │   ├── test_team.py
│   │   └── test_encryption.py
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/               # Reusable UI components
│   │   │   ├── Layout.tsx
│   │   │   ├── KeyCard.tsx
│   │   │   ├── ProviderBadge.tsx
│   │   │   ├── UsageChart.tsx
│   │   │   └── AlertRuleForm.tsx
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── KeysPage.tsx
│   │   │   ├── KeyDetailPage.tsx
│   │   │   ├── AlertsPage.tsx
│   │   │   ├── TeamPage.tsx
│   │   │   ├── ProvidersPage.tsx
│   │   │   └── OnboardingPage.tsx
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   └── useApi.ts
│   │   ├── api/
│   │   │   └── client.ts             # Axios/fetch wrapper with JWT interceptor
│   │   ├── types/
│   │   │   └── index.ts              # TypeScript interfaces matching backend schemas
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
├── .github/workflows/ci.yml
├── .gitignore
├── README.md
├── SPEC.md
├── PLAN.md
├── AGENT_LOG.md
└── REFLECTION.md
```

### `__init__.py` Conventions

为避免 subagent 之间的不一致，所有 `__init__.py` 文件遵循以下约定：

| 目录 | `__init__.py` 内容 | 说明 |
|------|--------------------|------|
| `backend/app/` | 空文件 | FastAPI 应用包标记 |
| `backend/app/models/` | re-export 所有 model 类 | `from app.models.user import User` 等，方便 `from app.models import User` |
| `backend/app/schemas/` | 空文件 | Pydantic schema 按需导入 |
| `backend/app/api/` | 空文件 | 路由通过 router.py 聚合 |
| `backend/app/services/` | 空文件 | Service 类在调用处直接导入 |
| `backend/app/providers/` | re-export `BaseProvider`, `ProviderRegistry` | 核心抽象在包级别可用 |
| `backend/app/worker/` | 空文件 | Worker 函数由 ARQ 按字符串路径加载 |
| `backend/app/middleware/` | 空文件 | 中间件在 main.py 中注册 |
| `backend/app/utils/` | 空文件 | 工具函数按需导入 |

**规则**：re-export 仅用于被外部频繁引用的模块（models、providers）。其余保持空文件，subagent 不可随意往 `__init__.py` 添加逻辑。

---

### Task 0.1: Initialize backend project structure

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/.env.example`
- Create: `.gitignore`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy[asyncio]==2.0.35
asyncpg==0.29.0
alembic==1.13.0
pydantic-settings==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.12
cryptography==44.0.0
arq==0.26.0
redis==5.1.0
aiosmtplib==3.0.0
httpx==0.27.0
pytest==8.3.0
pytest-asyncio==0.24.0
httpx==0.27.0
```

- [ ] **Step 2: Create config.py with Settings class**

```python
# backend/app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/api_vault"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Encryption (MUST be set in production)
    KEY_ENCRYPTION_KEY: str = "change-me-change-me-change-me32"  # 32 bytes for AES-256

    # OAuth
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # SMTP
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@apivault.dev"

    # App
    APP_NAME: str = "API Vault"
    DEBUG: bool = False
    PROVIDER_FETCH_INTERVAL_MINUTES: int = 60

    model_config = {"env_file": ".env"}

settings = Settings()
```

- [ ] **Step 3: Create database.py with async engine and session**

```python
# backend/app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

- [ ] **Step 4: Create minimal main.py**

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app

app = create_app()

@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Create .gitignore**

```
__pycache__/
*.pyc
.env
.venv/
node_modules/
dist/
.pytest_cache/
*.egg-info/
```

- [ ] **Step 6: Create .env.example**

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/api_vault
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your-secret-key-here
KEY_ENCRYPTION_KEY=your-32-byte-encryption-key-here
SMTP_HOST=localhost
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=noreply@apivault.dev
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

- [ ] **Step 7: Verify the scaffold**

Run: `cd backend && python -c "from app.main import app; print(app.title)"`
Expected: `API Vault`

- [ ] **Step 8: Commit**

```bash
git add backend/ .gitignore
git commit -m "chore: scaffold backend project structure"
```

**Dependencies:** None | **Can parallel:** T0.2

---

### Task 0.2: Initialize frontend project structure

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/api/client.ts`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "api-vault-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest run"
  },
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.26.0",
    "recharts": "^2.12.0",
    "axios": "^1.7.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "typescript": "^5.5.0",
    "vite": "^5.4.0",
    "@vitejs/plugin-react": "^4.3.0",
    "vitest": "^2.0.0"
  }
}
```

- [ ] **Step 2: Create TypeScript types matching backend schemas**

```typescript
// frontend/src/types/index.ts
export interface User {
  id: string;
  email: string;
  display_name: string;
  oauth_provider: string | null;
  email_verified: boolean;
}

export interface ApiKey {
  id: string;
  provider: string;
  label: string;
  masked_key: string;
  tags: string[];
  status: 'ok' | 'needs_update' | 'error';
  created_at: string;
}

export interface UsageSummary {
  total_calls: number;
  total_tokens: number;
  total_cost: number;
  by_provider: ProviderUsage[];
}

export interface ProviderUsage {
  provider: string;
  calls: number;
  tokens: number;
  cost: number;
  percentage: number;
}

export interface UsageTrendPoint {
  date: string;
  calls: number;
  tokens: number;
  cost: number;
}

export interface AlertRule {
  id: string;
  key_id: string | null;
  provider: string | null;
  type: 'budget' | 'call_count';
  threshold: number;
  notify_email: string;
  is_active: boolean;
}

export interface AlertEvent {
  id: string;
  rule_id: string;
  triggered_at: string;
  threshold_pct: number;
  message: string;
  is_read: boolean;
}

export interface KeyShare {
  id: string;
  key_id: string;
  shared_by: string;
  shared_with: string;
  permission: 'read' | 'use';
  created_at: string;
}
```

- [ ] **Step 3: Create API client with JWT interceptor**

```typescript
// frontend/src/api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const { data } = await axios.post('/api/v1/auth/refresh', {
            refresh_token: refreshToken,
          });
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('refresh_token', data.refresh_token);
          error.config.headers.Authorization = `Bearer ${data.access_token}`;
          return apiClient(error.config);
        } catch {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

- [ ] **Step 4: Create minimal App.tsx and main.tsx**

```tsx
// frontend/src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<div>API Vault</div>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

```tsx
// frontend/src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **Step 5: Create index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>API Vault</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 6: Verify frontend starts**

Run: `cd frontend && npm install && npm run dev`
Expected: Vite dev server starts on port 5173

- [ ] **Step 7: Commit**

```bash
git add frontend/
git commit -m "chore: scaffold frontend project with Vite + React + TypeScript"
```

**Dependencies:** None | **Can parallel:** T0.1

---

## Phase 1: Backend Core Infrastructure

### Task 1.1: Create all SQLAlchemy ORM models

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/api_key.py`
- Create: `backend/app/models/usage_record.py`
- Create: `backend/app/models/key_share.py`
- Create: `backend/app/models/alert_rule.py`
- Create: `backend/app/models/alert_event.py`
- Create: `backend/app/models/audit_log.py`
- Test: `backend/tests/conftest.py`

- [ ] **Step 1: Write the base model and User model**

```python
# backend/app/models/__init__.py
from app.models.user import User
from app.models.api_key import ApiKey
from app.models.usage_record import UsageRecord
from app.models.key_share import KeyShare
from app.models.alert_rule import AlertRule
from app.models.alert_event import AlertEvent
from app.models.audit_log import AuditLog

__all__ = ["User", "ApiKey", "UsageRecord", "KeyShare", "AlertRule", "AlertEvent", "AuditLog"]
```

```python
# backend/app/models/user.py
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    oauth_provider: Mapped[str | None] = mapped_column(String(20), nullable=True)
    oauth_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    notification_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

- [ ] **Step 2: Create remaining models**

```python
# backend/app/models/api_key.py
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.user import Base

class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    key_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(20), nullable=False)
    last_4: Mapped[str] = mapped_column(String(4), nullable=False)
    tags: Mapped[dict | None] = mapped_column(JSONB, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(20), default="ok")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

Continue with usage_record.py, key_share.py, alert_rule.py, alert_event.py, audit_log.py following the same patterns with all fields from SPEC §6.

- [ ] **Step 3: Write conftest.py with test fixtures**

```python
# backend/tests/conftest.py
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.user import Base

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/api_vault_test"

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
```

- [ ] **Step 4: Run test to verify models create tables**

Run: `cd backend && python -c "from app.models import *; print('All models imported')"`
Expected: All models imported (no errors)

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/ backend/tests/conftest.py
git commit -m "feat: add all SQLAlchemy ORM models (7 tables)"
```

**Dependencies:** T0.1 | **Can parallel:** None (foundational)

---

### Task 1.2: Set up Alembic for database migrations

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`

- [ ] **Step 1: Initialize Alembic and create initial migration**

```bash
cd backend
alembic init alembic
```

- [ ] **Step 2: Configure alembic/env.py for async and our models**

Set `sqlalchemy.url` in alembic.ini to `postgresql+asyncpg://postgres:postgres@localhost:5432/api_vault`
Set `target_metadata = Base.metadata` in env.py, import all models.

- [ ] **Step 3: Generate and run initial migration**

```bash
cd backend
alembic revision --autogenerate -m "initial: all tables"
alembic upgrade head
```

- [ ] **Step 4: Commit**

```bash
git add backend/alembic/ backend/alembic.ini
git commit -m "chore: add Alembic migrations with initial schema"
```

**Dependencies:** T1.1 | **Can parallel:** None

---

## Phase 2: Encryption & Auth (M1)

### Task 2.1: Implement encryption service

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/encryption_service.py`
- Test: `backend/tests/test_encryption.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_encryption.py
import pytest
from app.services.encryption_service import EncryptionService

def test_encrypt_and_decrypt_roundtrip():
    svc = EncryptionService(key_bytes=b"test-key-1234567890123456789012")  # 32 bytes
    plaintext = "sk-proj-abc123xyz"

    encrypted = svc.encrypt(plaintext)
    assert encrypted != plaintext
    assert "sk-proj" not in encrypted

    decrypted = svc.decrypt(encrypted)
    assert decrypted == plaintext

def test_encrypt_different_each_time():
    svc = EncryptionService(key_bytes=b"test-key-1234567890123456789012")
    plaintext = "sk-same-value"

    c1 = svc.encrypt(plaintext)
    c2 = svc.encrypt(plaintext)
    assert c1 != c2  # Nonce ensures different ciphertexts

def test_decrypt_tampered_data_raises():
    svc = EncryptionService(key_bytes=b"test-key-1234567890123456789012")
    encrypted = svc.encrypt("my-key")

    with pytest.raises(ValueError):
        svc.decrypt(encrypted + "tampered")

def test_extract_key_prefix():
    assert EncryptionService.extract_prefix("sk-proj-abc") == "sk-"
    assert EncryptionService.extract_prefix("ant-api03-xyz") == "ant-"
    assert EncryptionService.extract_prefix("ak-123456") == "ak-"

def test_extract_last_4():
    assert EncryptionService.extract_last_4("sk-proj-abc123xyz4567abcd") == "abcd"
    assert EncryptionService.extract_last_4("short") == "hort"

def test_mask_key():
    svc = EncryptionService(key_bytes=b"test-key-1234567890123456789012")
    masked = svc.mask_key("sk-", "abcd")
    assert masked == "sk-...****abcd"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_encryption.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implement encryption service**

```python
# backend/app/services/encryption_service.py
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class EncryptionService:
    def __init__(self, key_bytes: bytes):
        if len(key_bytes) != 32:
            raise ValueError("Encryption key must be 32 bytes for AES-256-GCM")
        self._key = key_bytes

    def encrypt(self, plaintext: str) -> str:
        nonce = os.urandom(12)
        aesgcm = AESGCM(self._key)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        # Return nonce + ciphertext as hex
        combined = nonce + ciphertext
        return combined.hex()

    def decrypt(self, encrypted_hex: str) -> str:
        combined = bytes.fromhex(encrypted_hex)
        nonce = combined[:12]
        ciphertext = combined[12:]
        aesgcm = AESGCM(self._key)
        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode("utf-8")
        except Exception:
            raise ValueError("Decryption failed: data may be tampered or corrupted")

    @staticmethod
    def extract_prefix(key_value: str) -> str:
        """Extract recognizable prefix like 'sk-', 'ant-', 'ak-'"""
        parts = key_value.split("-")
        if len(parts) >= 2:
            return parts[0] + "-"
        return key_value[:3]

    @staticmethod
    def extract_last_4(key_value: str) -> str:
        return key_value[-4:]

    @staticmethod
    def mask_key(prefix: str, last_4: str) -> str:
        return f"{prefix}...****{last_4}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_encryption.py -v`
Expected: 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/__init__.py backend/app/services/encryption_service.py backend/tests/test_encryption.py
git commit -m "feat: add AES-256-GCM encryption service with key masking"
```

**Dependencies:** T0.1 | **Can parallel:** None (core service)

---

### Task 2.2: Implement auth service (register, login, JWT, OAuth)

**Files:**
- Create: `backend/app/services/auth_service.py`
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/api/deps.py`
- Create: `backend/app/api/auth.py`
- Test: `backend/tests/test_auth.py`

- [ ] **Step 1: Write failing tests for auth**

```python
# backend/tests/test_auth.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import create_app
from app.models.user import Base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

pytestmark = pytest.mark.asyncio

TEST_DB = "postgresql+asyncpg://postgres:postgres@localhost:5432/api_vault_test"

@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(TEST_DB)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

async def test_register_user(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "display_name": "Test User"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["display_name"] == "Test User"
    assert "password" not in data["user"]

async def test_register_duplicate_email_fails(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "dup@example.com", "password": "password123", "display_name": "First"
    })
    resp = await client.post("/api/v1/auth/register", json={
        "email": "dup@example.com", "password": "password456", "display_name": "Second"
    })
    assert resp.status_code == 409

async def test_login_success(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "login@example.com", "password": "password123", "display_name": "Login Test"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com", "password": "password123"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data

async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "wrong@example.com", "password": "password123", "display_name": "Wrong"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "wrong@example.com", "password": "wrongpassword"
    })
    assert resp.status_code == 401

async def test_short_password_rejected(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "short@example.com", "password": "123", "display_name": "Short"
    })
    assert resp.status_code == 422

async def test_refresh_token(client: AsyncClient):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "refresh@example.com", "password": "password123", "display_name": "Refresh"
    })
    refresh_token = reg.json()["refresh_token"]
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest backend/tests/test_auth.py -v`
Expected: FAIL (import errors for modules not yet created)

- [ ] **Step 3: Create Pydantic schemas for auth**

```python
# backend/app/schemas/auth.py
from pydantic import BaseModel, EmailStr, Field, field_validator

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=1, max_length=100)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class RefreshRequest(BaseModel):
    refresh_token: str

class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    oauth_provider: str | None = None
    email_verified: bool

    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Implement auth service**

```python
# backend/app/services/auth_service.py
from datetime import datetime, timedelta, timezone
import uuid
from passlib.context import CryptContext
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, email: str, password: str, display_name: str) -> tuple[User, str, str]:
        existing = await self.db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            raise ValueError("email_exists")

        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=pwd_context.hash(password),
            display_name=display_name,
            email_verified=False,
        )
        self.db.add(user)
        await self.db.flush()
        access_token = self._create_access_token(user.id)
        refresh_token = self._create_refresh_token(user.id)
        return user, access_token, refresh_token

    async def login(self, email: str, password: str) -> tuple[User, str, str]:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user or not user.password_hash:
            raise ValueError("invalid_credentials")
        if not pwd_context.verify(password, user.password_hash):
            raise ValueError("invalid_credentials")
        access_token = self._create_access_token(user.id)
        refresh_token = self._create_refresh_token(user.id)
        return user, access_token, refresh_token

    async def refresh(self, refresh_token: str) -> tuple[str, str]:
        try:
            payload = jwt.decode(refresh_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("invalid_token")
            result = await self.db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user or not user.is_active:
                raise ValueError("invalid_token")
        except JWTError:
            raise ValueError("invalid_token")
        return self._create_access_token(uuid.UUID(user_id)), self._create_refresh_token(uuid.UUID(user_id))

    def _create_access_token(self, user_id: uuid.UUID) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return jwt.encode(
            {"sub": str(user_id), "exp": expire, "type": "access"},
            settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

    def _create_refresh_token(self, user_id: uuid.UUID) -> str:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        return jwt.encode(
            {"sub": str(user_id), "exp": expire, "type": "refresh"},
            settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
```

- [ ] **Step 5: Create dependency injection for current user**

```python
# backend/app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.config import settings
from app.models.user import User

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token_type")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user_not_found")
    return user
```

- [ ] **Step 6: Create auth API routes**

```python
# backend/app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest, UserResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/register", status_code=201, response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    try:
        user, access, refresh = await svc.register(req.email, req.password, req.display_name)
        return TokenResponse(
            access_token=access, refresh_token=refresh,
            user=UserResponse.model_validate(user)
        )
    except ValueError as e:
        if "email_exists" in str(e):
            raise HTTPException(status_code=409, detail="email_exists")
        raise

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    try:
        user, access, refresh = await svc.login(req.email, req.password)
        return TokenResponse(
            access_token=access, refresh_token=refresh,
            user=UserResponse.model_validate(user)
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="invalid_credentials")

@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    try:
        access, refresh = await svc.refresh(req.refresh_token)
        return TokenResponse(
            access_token=access, refresh_token=refresh,
            user=UserResponse.model_validate(user)
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="invalid_token")

@router.get("/me", response_model=UserResponse)
async def me(current_user = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
```

- [ ] **Step 7: Register auth router in app/router.py, update main.py to include router**

- [ ] **Step 8: Run tests**

Run: `pytest backend/tests/test_auth.py -v`
Expected: All tests PASS (except OAuth tests which aren't implemented yet)

- [ ] **Step 9: Commit**

```bash
git add backend/app/services/auth_service.py backend/app/schemas/auth.py backend/app/api/auth.py backend/app/api/deps.py backend/app/api/router.py backend/app/main.py backend/tests/test_auth.py
git commit -m "feat: implement auth (register/login/JWT/deps)"
```

**Dependencies:** T1.1 | **Can parallel:** None

---

## Phase 3: Key Vault (M2)

### Task 3.1: Implement key service with CRUD + encryption + masking

**Files:**
- Create: `backend/app/services/key_service.py`
- Create: `backend/app/schemas/api_key.py`
- Create: `backend/app/api/keys.py`
- Test: `backend/tests/test_keys.py`

(TDD steps follow same pattern: failing test → run red → implement → run green → commit. Detailed code for key CRUD, masked display, copy-to-clipboard audit logging.)

**Dependencies:** T2.2 (auth for deps) | **Can parallel:** None

---

### Task 3.2: Implement audit logging service and middleware

**Files:**
- Create: `backend/app/services/audit_service.py`
- Create: `backend/app/middleware/audit.py`

**Dependencies:** T1.1 | **Can parallel:** T3.1

---

## Phase 4: Provider Engine (M3)

### Task 4.1: Implement BaseProvider + Registry

**Files:**
- Create: `backend/app/providers/__init__.py`
- Create: `backend/app/providers/base.py`
- Create: `backend/app/providers/registry.py`
- Test: `backend/tests/test_providers.py`

```python
# backend/app/providers/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

@dataclass
class UsageRecord:
    provider: str
    key_id: str
    period_start: date
    period_end: date
    calls: int
    tokens_in: int
    tokens_out: int
    cost_estimate: float | None
    raw_response: dict

class BaseProvider(ABC):
    provider_name: str = ""
    base_url: str = ""
    usage_endpoint: str = ""
    rate_limit_rps: float = 1.0

    @abstractmethod
    def auth_headers(self, api_key: str) -> dict[str, str]:
        ...

    @abstractmethod
    async def fetch_usage(self, api_key: str) -> UsageRecord:
        ...

    def normalize_response(self, raw: dict) -> UsageRecord:
        raise NotImplementedError
```

```python
# backend/app/providers/registry.py
from app.providers.base import BaseProvider

class ProviderRegistry:
    _providers: dict[str, BaseProvider] = {}

    @classmethod
    def register(cls, provider: BaseProvider):
        cls._providers[provider.provider_name] = provider

    @classmethod
    def get(cls, name: str) -> BaseProvider:
        if name not in cls._providers:
            raise KeyError(f"Provider '{name}' not registered")
        return cls._providers[name]

    @classmethod
    def list_providers(cls) -> list[str]:
        return list(cls._providers.keys())
```

**Dependencies:** T1.1 | **Can parallel:** None (core abstraction)

---

### Task 4.2: Implement OpenAI provider

**Files:**
- Create: `backend/app/providers/openai.py`

- [ ] **Step 1: Write failing test for OpenAI provider**

```python
# in backend/tests/test_providers.py
import pytest
from unittest.mock import AsyncMock, patch
from app.providers.openai import OpenAIProvider

@pytest.mark.asyncio
async def test_openai_fetch_usage():
    provider = OpenAIProvider()
    mock_response = {
        "data": [{
            "usage_tier": "scale",
            "current_usage_usd": 12.50,
        }]
    }
    with patch("httpx.AsyncClient.get", return_value=AsyncMock(status_code=200, json=lambda: mock_response)):
        record = await provider.fetch_usage("sk-test-key")
        assert record.provider == "openai"
        assert record.cost_estimate == 12.50
```

- [ ] **Step 2: Run test → fail**

- [ ] **Step 3: Implement OpenAI provider**

```python
# backend/app/providers/openai.py
import httpx
from datetime import date
from app.providers.base import BaseProvider, UsageRecord

class OpenAIProvider(BaseProvider):
    provider_name = "openai"
    base_url = "https://api.openai.com/v1"
    usage_endpoint = "/usage?date={date}"

    def auth_headers(self, api_key: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {api_key}"}

    async def fetch_usage(self, api_key: str) -> UsageRecord:
        today = date.today().isoformat()
        url = f"{self.base_url}{self.usage_endpoint.format(date=today)}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=self.auth_headers(api_key))
            resp.raise_for_status()
            return self.normalize_response(resp.json())

    def normalize_response(self, raw: dict) -> UsageRecord:
        data = raw.get("data", [{}])[0]
        return UsageRecord(
            provider=self.provider_name,
            key_id="",
            period_start=date.today(),
            period_end=date.today(),
            calls=data.get("num_requests", 0),
            tokens_in=data.get("context_tokens", 0),
            tokens_out=data.get("generated_tokens", 0),
            cost_estimate=round(data.get("current_usage_usd", 0) / 100, 4),
            raw_response=raw,
        )
```

- [ ] **Step 4: Run test → pass**

- [ ] **Step 5: Commit**

**Dependencies:** T4.1 | **Can parallel:** T4.3, T4.4, T4.5

---

### Task 4.3: Implement Anthropic provider

**Files:** Create: `backend/app/providers/anthropic.py`

Same TDD pattern as T4.2. Auth via `x-api-key` header. Usage from Anthropic's billing/usage endpoint.

**Dependencies:** T4.1 | **Can parallel:** T4.2, T4.4, T4.5

---

### Task 4.4: Implement DeepSeek provider

**Files:** Create: `backend/app/providers/deepseek.py`

Same TDD pattern. Auth via `Authorization: Bearer`. Usage endpoint matches DeepSeek's API format (OpenAI-compatible).

**Dependencies:** T4.1 | **Can parallel:** T4.2, T4.3, T4.5

---

### Task 4.5: Implement Generic/Custom provider

**Files:** Create: `backend/app/providers/generic.py`

Supports user-configured REST API adapters. Takes config from database, constructs requests dynamically.

**Dependencies:** T4.1 | **Can parallel:** T4.2, T4.3, T4.4

---

### Task 4.6: Implement Provider API endpoints (list + custom CRUD)

**Files:**
- Create: `backend/app/schemas/provider.py`
- Create: `backend/app/api/providers.py`

**Dependencies:** T4.1, T3.1 | **Can parallel:** None (needs registry + auth)

---

## Phase 5: Background Worker & Usage Data (M4 backend)

### Task 5.1: Implement usage service (DB queries + aggregation)

**Files:**
- Create: `backend/app/services/usage_service.py`
- Create: `backend/app/schemas/usage.py`
- Create: `backend/app/api/usage.py`
- Test: `backend/tests/test_usage.py`

**Dependencies:** T3.1 (needs keys in DB), T4.1 (needs provider registry)

---

### Task 5.2: Implement ARQ background worker (fetcher + alert evaluator)

**Files:**
- Create: `backend/app/worker/__init__.py`
- Create: `backend/app/worker/fetcher.py`
- Create: `backend/app/worker/alert_evaluator.py`

```python
# backend/app/worker/fetcher.py
from arq import Worker
from app.config import settings
from app.providers.registry import ProviderRegistry

async def fetch_all_usage(ctx):
    """Periodic task: fetch usage for all active keys."""
    # Get all active keys from DB
    # For each key, get provider, call fetch_usage, store result
    pass
```

**Dependencies:** T4.2-T4.5 (provider implementations), T5.1

---

## Phase 6: Alert Engine (M5)

### Task 6.1: Implement alert service (rules CRUD + evaluation + email)

**Files:**
- Create: `backend/app/services/alert_service.py`
- Create: `backend/app/schemas/alert.py`
- Create: `backend/app/api/alerts.py`
- Create: `backend/app/utils/email.py`
- Test: `backend/tests/test_alerts.py`

Key constraint: user must have verified email to create rules. 24h dedup logic.

**Dependencies:** T5.2 (needs fetcher to trigger evaluation) | **Can parallel:** None

---

## Phase 7: Team Sharing (M6)

### Task 7.1: Implement team sharing service

**Files:**
- Create: `backend/app/services/team_service.py`
- Create: `backend/app/schemas/team.py`
- Create: `backend/app/api/team.py`
- Test: `backend/tests/test_team.py`

**Dependencies:** T3.1 (key service) | **Can parallel:** T6.1

---

## Phase 8: Frontend Pages (Open Design)

> **强制规则**：每个前端 task 的 Step 1 必须调用对应的 Open Design skill 生成设计稿，确认设计后再写代码。Step 2+ 为 TDD 实现。每完成 2-3 个页面后触发 `critique` 审查。

### Task 8.0: Landing Page (saas-landing)

**Files:**
- Create: `frontend/src/pages/LandingPage.tsx`

**Open Design:** `saas-landing` skill + Linear 设计系统

**Dependencies:** T0.2 | **Can parallel:** None (first frontend task)

---

### Task 8.1: Layout component + Auth pages (web-prototype)

**Files:**
- Create: `frontend/src/components/Layout.tsx`
- Create: `frontend/src/pages/LoginPage.tsx`
- Create: `frontend/src/pages/RegisterPage.tsx`
- Create: `frontend/src/hooks/useAuth.ts`

**Open Design:** `web-prototype` skill + Linear 设计系统（Open Design 无独立 auth skill）

**Dependencies:** T0.2, T2.2 (auth API ready)

---

### Task 8.2: Dashboard page with usage charts (dashboard) ⭐ 视觉核心

**Files:**
- Create: `frontend/src/pages/DashboardPage.tsx`
- Create: `frontend/src/components/UsageChart.tsx`
- Create: `frontend/src/components/ProviderBadge.tsx`

**Open Design:** `dashboard` skill + Linear 设计系统。Dashboard 是整个应用最重要的页面——用量总览卡片、趋势折线图、Provider 占比饼图、Top-N Key 排行表。

**Dependencies:** T5.1 (usage API), T8.1

---

### Task 8.3: Keys management pages (web-prototype)

**Files:**
- Create: `frontend/src/pages/KeysPage.tsx`
- Create: `frontend/src/pages/KeyDetailPage.tsx`
- Create: `frontend/src/components/KeyCard.tsx`

**Open Design:** `web-prototype` skill + Linear 设计系统

**Dependencies:** T3.1 (keys API), T8.1

---

### Task 8.4: Alerts, Team, Providers, Onboarding pages (web-prototype)

**Files:**
- Create: `frontend/src/pages/AlertsPage.tsx`
- Create: `frontend/src/pages/TeamPage.tsx`
- Create: `frontend/src/pages/ProvidersPage.tsx`
- Create: `frontend/src/pages/OnboardingPage.tsx`
- Create: `frontend/src/components/AlertRuleForm.tsx`

**Open Design:** `web-prototype` skill + Linear 设计系统

**Dependencies:** T6.1, T7.1, T4.6, T8.1 | **Can parallel:** alerts/team/providers 三个页面可并行开发

---

### Task 8.5: Design Critique & Polish (critique + tweaks)

**何时触发**：T8.1+T8.2 完成后一次；T8.3+T8.4 完成后一次；全部页面完成后最终审查。

**Open Design:** `critique` skill → 输出问题列表；`tweaks` skill → 逐项修复。

**检查维度**（与 Linear 设计系统对齐）：
- 色彩：是否使用了 Linear 的暗色主题色板
- 间距：组件间距是否一致
- 组件：按钮/卡片/输入框是否符合 Linear 风格
- 排版：字体层级是否正确
- 反模式：有无通用的 AI-slop 设计（过度阴影、渐变按钮、emoji 图标）

**Dependencies:** T8.1-T8.4

---

## Phase 9: Docker, CI, Docs

### Task 9.1: Docker Compose + Dockerfiles

**Files:**
- Create: `docker-compose.yml`
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `frontend/nginx.conf`

**Dependencies:** All backend + frontend tasks complete

---

### Task 9.2: GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`

```yaml
name: CI
on: [push, pull_request]
jobs:
  test-backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready --health-interval 10s
      redis:
        image: redis:7
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: cd backend && pip install -r requirements.txt
      - run: cd backend && pytest -v
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/api_vault_test

  build-docker:
    needs: test-backend
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker compose build
```

**Dependencies:** T9.1

---

### Task 9.3: README.md + final documentation

**Files:**
- Create: `README.md`

**Dependencies:** T9.1, T9.2

---

## Dependency Graph

```
T0.1 ──→ T1.1 ──→ T1.2
  │         │
  │         └──→ T2.1 ──→ T2.2 ──→ T3.1 ──→ T3.2
  │                       │          │
  │                       │          └──→ T5.1 ──→ T5.2 ──→ T6.1
  │                       │                        │
  │                       │                        └──→ T8.2
  │                       │          ┌──→ T7.1 ──→ T8.4
  │                       │          │
  │                       └──→ T4.1 ──┬──→ T4.2 (∥ T4.3 ∥ T4.4 ∥ T4.5)
  │                                   │
  │                                   └──→ T4.6 ──→ T8.4
  │
T0.2 ──→ T8.1 ──→ T8.2, T8.3, T8.4
                      │
                      └──→ T9.1 ──→ T9.2 ──→ T9.3

∥ = parallelizable
```

---

## Estimated Task Distribution

| Phase | Tasks | Est. Lines (code+test) |
|-------|-------|------------------------|
| 0: Scaffolding | 2 | 200 |
| 1: Core Infra | 2 | 400 |
| 2: Auth (M1) | 2 | 600 |
| 3: Key Vault (M2) | 2 | 700 |
| 4: Provider Engine (M3) | 6 | 1000 |
| 5: Usage/Worker (M4) | 2 | 500 |
| 6: Alert Engine (M5) | 1 | 500 |
| 7: Team Sharing (M6) | 1 | 400 |
| 8: Frontend | 4 | 1500 |
| 9: Docker/CI/Docs | 3 | 200 |
| **Total** | **25** | **~6000** |
