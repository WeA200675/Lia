import os
import secrets
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from openai import OpenAI, OpenAIError
from pydantic import BaseModel, Field

app = FastAPI(title="Senioren_Assistent_API")
SYSTEM_PROMPT = (
    "Du bist Lia, eine empathische Alltagsbegleiterin. "
    "Antworte kurz und herzlich. Stelle höchstens eine Frage. "
    "Erfinde keine Beobachtungen und stelle keine Diagnosen."
)


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    text_input: str = Field(min_length=1, max_length=4000)
    history: list[Message] = Field(default_factory=list, max_length=20)


class AnalysisResponse(BaseModel):
    status: str
    action_item: str


def authorize(authorization: str = Header(default="")):
    token = os.getenv("LIA_API_TOKEN")
    if not token:
        raise HTTPException(503, "Zugriffsschutz nicht konfiguriert")
    if not secrets.compare_digest(authorization.encode(), ("Bearer " + token).encode()):
        raise HTTPException(401, "Nicht autorisiert")


@app.get("/health")
def health():
    return {"status": "alive"}


@app.post("/api/chat", dependencies=[Depends(authorize)])
def chat_with_mother(request: ChatRequest):
    base = os.getenv("OPENAI_BASE_URL")
    key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("LIA_MODEL")
    if not model or not (base or key):
        raise HTTPException(503, "KI nicht konfiguriert")
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(msg.model_dump() for msg in request.history)
    messages.append({"role": "user", "content": request.text_input})
    try:
        with OpenAI(api_key=key or "local", base_url=base, timeout=15.0, max_retries=0) as client:
            response = client.chat.completions.create(
                model=model, messages=messages, max_tokens=150, temperature=0.7
            )
        reply = response.choices[0].message.content if response.choices else None
        if not reply or not reply.strip():
            raise HTTPException(502, "Keine KI-Antwort verfügbar")
        return {"reply": reply}
    except OpenAIError:
        raise HTTPException(503, "KI derzeit nicht erreichbar") from None


@app.post("/api/analyze", response_model=AnalysisResponse, dependencies=[Depends(authorize)])
def generate_dashboard_metrics(conversation_log: list[str]):
    # Never present fabricated observations as a real assessment.
    raise HTTPException(501, "Auswertung noch nicht implementiert")
