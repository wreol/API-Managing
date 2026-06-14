from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    return app


app = create_app()


# Register built-in providers on import
from app.providers.openai import OpenAIProvider
from app.providers.anthropic import AnthropicProvider
from app.providers.deepseek import DeepSeekProvider
from app.providers.registry import ProviderRegistry

ProviderRegistry.register(OpenAIProvider())
ProviderRegistry.register(AnthropicProvider())
ProviderRegistry.register(DeepSeekProvider())


@app.get("/health")
async def health():
    return {"status": "ok"}
