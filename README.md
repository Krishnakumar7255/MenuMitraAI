# 🍽️ MenuMitra AI

**A local-first AI menu translator for restaurants, cafés, and small food businesses.**

MenuMitra AI helps small businesses translate restaurant menus, improve dish descriptions, preserve original dish names and prices, and prepare printable menus using locally run AI.

Built with Python, FastAPI, Ollama, and an open-weight language model, MenuMitra AI explores how open AI tools can make useful business automation more accessible.

## ✨ Features

- 🌐 **AI-powered menu translation** — translate menu content into supported languages.
- 🍛 **Regional dish awareness** — preserve culturally specific names such as Litti Chokha and Sattu Paratha.
- ✍️ **Description improvement** — generate clearer descriptions without intentionally inventing ingredients.
- 💰 **Price preservation** — keep prices from the original menu unchanged.
- ⚠️ **Human review** — flag generated translations that need checking.
- 📄 **CSV import and export** — manage menu items in a familiar format.
- 🖨️ **Printable menus** — open a printable page and save it as PDF using your browser.
- 🔒 **Local AI inference** — process menu text through a locally running Ollama model instead of a hosted AI API.

## 🛠️ Tech Stack

- **Language:** Python
- **Backend:** FastAPI
- **AI runtime:** Ollama
- **Model:** Qwen2.5 7B Instruct by default
- **Validation:** Pydantic
- **Interface:** HTML, CSS, and JavaScript served by FastAPI
- **Testing:** Pytest

## 🚀 Getting Started

### Prerequisites

- Python 3.11 recommended
- Ollama installed
- Sufficient RAM and disk space for the selected model

### 1. Download the model

Install Ollama from https://ollama.com/download and run:

```bash
ollama pull qwen2.5:7b
```

### 2. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/MenuMitraAI.git
cd MenuMitraAI
```

Replace `YOUR_USERNAME` with your GitHub username.

### 3. Create a virtual environment

**Windows PowerShell:**

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux/macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Start the application

```bash
uvicorn app:app --reload
```

Open http://127.0.0.1:8000 in your browser.

### Optional: Use a smaller model

If your computer struggles with the 7B model, install a smaller variant:

```bash
ollama pull qwen2.5:3b
```

Then configure the model before starting the application.

**Windows PowerShell:**

```powershell
$env:OLLAMA_MODEL="qwen2.5:3b"
uvicorn app:app --reload
```

## 📋 CSV Format

Prepare a CSV file with these columns:

```csv
name,description,price,allergens
Sattu Paratha,Flatbread stuffed with roasted gram flour,80,wheat
Litti Chokha,Roasted wheat dough balls served with mashed vegetables,120,wheat
Paneer Butter Masala,Paneer in a creamy tomato-based gravy,180,milk
```

The `name` column is required. Review all imported values before translating.

## 🧪 Run Tests

```bash
pytest
```

## 💡 Why Open-Source AI?

Open-weight models and local inference provide greater control over model selection and where data is processed. After downloading the model, the core AI workflow can run without sending menu text to a hosted AI API.

This approach can reduce dependence on per-request API pricing, although local hardware, electricity, and maintenance still have costs.

## 🔐 Privacy and Food Safety

- Menu text is processed using the configured local Ollama service.
- Model downloads require internet initially; local inference can work offline afterward.
- AI-generated translations may be inaccurate and must be reviewed.
- Allergen data must be verified by the restaurant. The AI does not certify food safety.
- Do not expose the development server publicly without appropriate security hardening.

## 🗺️ Roadmap

- [x] Local AI integration
- [x] Menu translation endpoint
- [x] CSV import and export
- [x] Printable menu view
- [ ] PDF and image OCR
- [ ] More robust multilingual evaluation
- [ ] Restaurant branding and menu themes
- [ ] Feedback from real restaurant users
- [ ] Improved error handling and production security

## 🤝 Contributing

Contributions, bug reports, and suggestions are welcome. Open an issue before making a large change.

## 📜 License

The original application code is licensed under the MIT License. The AI model and third-party dependencies have their own licenses and terms.

## 🏆 Challenge

Created for the Hacktoberfest Open-Source AI Challenge — Week 2: Side Hustle.

Project status: prototype; features and translation quality should be verified locally before production use.
