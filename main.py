import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from typing import List, Dict

app = FastAPI(title="Senioren_Assistent_API")

# Core-Konfiguration (Für OpenAI oder lokale Ollama-Instanz auf Proxmox)
# Für Ollama einfach den base_url zu deiner Proxmox-VM ändern: http://<proxmox-ip>:11434/v1
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "your-key-if-openai"),
    base_url=os.getenv("OPENAI_BASE_URL", None) 
)

SYSTEM_PROMPT = """
Du bist 'Lia', eine empathische Alltagsbegleiterin für eine 84-jährige Dame. 
Antworte extrem kurz (max. 2 Sätze), herzlich und stelle immer nur eine Frage zu Wohlbefinden, Essen oder Haushalt.
"""

class ChatRequest(BaseModel):
    user_id: str
    text_input: str
    history: List[Dict[str, str]] = [] # Verlauf der letzten Sätze für den Kontext

class AnalysisResponse(BaseModel):
    status: str # "Grün", "Gelb", "Rot"
    action_item: str

# 1. ENDPOINT: Sprache verarbeiten und Antwort generieren
@app.post("/api/chat")
async def chat_with_mother(request: ChatRequest):
    try:
        # Konstruiere den Nachrichtenverlauf für die KI (Memory-Prinzip)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Historie hinzufügen, damit die KI weiß, was vor 2 Minuten gesagt wurde
        for msg in request.history:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
        # Aktuelle Spracheingabe der Mutter anhängen
        messages.append({"role": "user", "content": request.text_input})

        # KI-Abfrage (Nutzt GPT-4o-mini oder dein lokales Llama3)
        response = client.chat.completions.create(
            model="gpt-4o-mini", # oder "llama3" bei Ollama
            messages=messages,
            max_tokens=150,
            temperature=0.7
        )
        
        ai_reply = response.choices[0].message.content
        return {"reply": ai_reply}

    except Exception as e:
        raise HTTPException(status_status=500, detail=str(e))

# 2. ENDPOINT: Wöchentliche Auswertung für dein Dashboard
@app.post("/api/analyze", response_model=AnalysisResponse)
async def generate_dashboard_metrics(conversation_log: List[str]):
    # Dieser Endpoint analysiert das gesamte Gesprächs-Log des Tages/der Woche
    analysis_prompt = (
        "Analysiere folgendes Gesprächsprotokoll einer älteren Dame. "
        "Gib ein JSON zurück mit 'status' (Grün/Gelb/Rot) und 'action_item' (Was muss der Sohn tun?). "
        f"Protokoll: {json.dumps(conversation_log)}"
    )
    
    # Hier erfolgt der strukturierte API-Aufruf an das Modell (z.B. mit JSON-Mode)
    # ...
    return {"status": "Gelb", "action_item": "Mutter hat Schmerzen im Knie erwähnt. Bitte Haltegriff an der Treppe prüfen."}
