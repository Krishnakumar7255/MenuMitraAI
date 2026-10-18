# MenuMitra AI 🍽️

A local-first AI menu translator prototype for small restaurants and cafés. Built with Python, FastAPI and Ollama.

## Features
- Translate menu item names/descriptions into supported languages.
- Preserve original dish names, prices and restaurant-provided allergen fields in application code.
- Load CSV menus, export translated CSV, and open a printable menu page.
- Local inference; no hosted AI API is configured.
- Human-review flags for uncertain translations.

## Setup (Windows PowerShell)

1. Install Ollama: https://ollama.com/download
2. Download a model:
   ```powershell
   ollama pull qwen2.5:7b
   ```
3. In this project folder:
   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   uvicorn app:app --reload
   ```
4. Open http://127.0.0.1:8000

If 7B is too demanding, try `ollama pull qwen2.5:3b` and set:
```powershell
$env:OLLAMA_MODEL="qwen2.5:3b"
uvicorn app:app --reload
```

Check the exact model's license before commercial use: https://ollama.com/library/qwen2.5

## CSV format
Headers: `name,description,price,allergens`. Only `name` is required.

## Tests
```powershell
pytest
```

## Limitations and privacy
- Model downloads initially require internet; local inference can then run offline.
- Translation quality varies; review every item before publishing.
- Allergen values are copied from user input and not independently verified. Never use the model as a food-safety authority.
- This is a local prototype, not hardened for public deployment. It has no authentication, persistent database, OCR or production access controls.
- The application is configured for local Ollama inference; check your machine and network configuration before entering sensitive data.

## Open innovation
Local inference offers control over processing, model choice and recurring hosted API usage, while still requiring hardware, power and maintenance.

## License
Original app code: MIT. Models and dependencies have separate licenses.
