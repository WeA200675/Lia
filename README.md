# Lia

Experimentelles Python-Backend für eine Alltagsbegleiterin. Keine medizinische Überwachung oder Notruflösung.

## Lokaler Start (Python 3.12)

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt httpx
export LIA_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export OPENAI_BASE_URL=http://127.0.0.1:11434/v1
export LIA_MODEL=llama3
uvicorn main:app --host 127.0.0.1 --port 8000
```

Das Modell muss lokal installiert sein. Kein automatischer Cloud-Fallback. Für einen externen Anbieter sind eine bewusste Konfiguration und Datenschutzprüfung erforderlich. API-Aufrufe benötigen Authorization: Bearer mit dem konfigurierten Token. Nicht öffentlich exponieren; für Netzwerkzugriff TLS und zusätzliche Zugriffskontrollen vorsehen. Keine echten Gesprächsdaten in Tests verwenden.

`GET /health` prüft nur den Prozess. `POST /api/chat` liefert bei fehlender Konfiguration oder Provider-Ausfall 503. `POST /api/analyze` liefert bewusst 501 statt erfundener Beobachtungen.

## Tests

`python -m unittest discover -s tests -v`

## Abnahme

CI, reproduzierbare Abhängigkeiten, Provider-Integration, Datenschutz und Geräteabnahme stehen noch aus. Keine Produktivfreigabe. Rücknahme über Schließen des PR; main bleibt unverändert.
