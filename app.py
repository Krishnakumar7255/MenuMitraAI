
import csv, io, json, os
from typing import List
from html import escape
import ollama
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

APP_NAME = "MenuMitra AI"
MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
app = FastAPI(title=APP_NAME, version="1.0.0")

class MenuItem(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    price: float = Field(ge=0, le=100000)
    allergens: str = Field(default="", max_length=200)

class TranslateRequest(BaseModel):
    restaurant_name: str = Field(default="My Restaurant", max_length=120)
    source_language: str = "English"
    target_language: str = "Hindi"
    items: List[MenuItem] = Field(min_length=1, max_length=50)

class TranslatedItem(BaseModel):
    original_name: str
    translated_name: str
    original_description: str
    translated_description: str
    price: float
    allergens: str
    needs_review: bool = True

class TranslateResponse(BaseModel):
    restaurant_name: str
    source_language: str
    target_language: str
    items: List[TranslatedItem]

def run_translation(req: TranslateRequest) -> TranslateResponse:
    source_items = [item.model_dump() for item in req.items]
    prompt = f"""
Translate this restaurant menu from {req.source_language} to {req.target_language}.
Return a JSON object with an "items" array. Each item must contain
translated_name, translated_description, and needs_review.
Preserve culturally specific dish names where appropriate. Do not invent
ingredients, cooking methods, health claims, or allergen information.
Mark needs_review=true when uncertain. Return valid JSON only.

Restaurant: {req.restaurant_name}
Input menu: {json.dumps(source_items, ensure_ascii=False)}
"""
    try:
        response = ollama.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a careful restaurant menu translator. Never invent facts."},
                {"role": "user", "content": prompt},
            ],
            format="json",
            options={"temperature": 0.1},
        )
        raw = json.loads(response.message.content)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Local Ollama/model error. Run 'ollama pull {MODEL}' and ensure Ollama is running. Details: {str(exc)[:200]}")

    translated = raw.get("items") if isinstance(raw, dict) else raw
    if not isinstance(translated, list) or len(translated) != len(req.items):
        raise HTTPException(status_code=502, detail="The model returned an unexpected result. Try fewer menu items.")

    output = []
    for original, result in zip(req.items, translated):
        if not isinstance(result, dict):
            raise HTTPException(status_code=502, detail="The model returned an invalid menu item.")
        # Critical business data comes from original input, not the model.
        output.append(TranslatedItem(
            original_name=original.name,
            translated_name=str(result.get("translated_name") or original.name)[:120],
            original_description=original.description,
            translated_description=str(result.get("translated_description") or "")[:500],
            price=original.price,
            allergens=original.allergens,
            needs_review=bool(result.get("needs_review", True)),
        ))
    return TranslateResponse(restaurant_name=req.restaurant_name, source_language=req.source_language,
                             target_language=req.target_language, items=output)

@app.get("/api/health")
def health():
    try:
        result = ollama.list()
        models = [m.model for m in result.models]
        available = any(m == MODEL or m.startswith(MODEL + ":") for m in models)
        return {"status": "ok", "model": MODEL, "model_available": available, "installed_models": models}
    except Exception as exc:
        return JSONResponse(status_code=503, content={"status": "ollama_unavailable", "model": MODEL, "detail": str(exc)[:200]})

@app.post("/api/translate", response_model=TranslateResponse)
def translate(req: TranslateRequest):
    return run_translation(req)

@app.post("/api/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file.")
    data = await file.read()
    if len(data) > 1_000_000:
        raise HTTPException(status_code=413, detail="CSV must be smaller than 1 MB.")
    try:
        reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
        if not reader.fieldnames:
            raise ValueError("CSV needs a header row.")
        rows = []
        for row in reader:
            name = (row.get("name") or row.get("dish") or "").strip()
            if not name:
                continue
            rows.append(MenuItem(
                name=name,
                description=(row.get("description") or "").strip(),
                price=float((row.get("price") or "0").replace("₹", "").strip()),
                allergens=(row.get("allergens") or "").strip()
            ).model_dump())
            if len(rows) > 50:
                raise ValueError("Maximum 50 menu items per upload.")
        if not rows:
            raise ValueError("No menu items found. Use columns: name, description, price, allergens.")
        return {"items": rows}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read CSV: {str(exc)[:180]}")

@app.post("/api/export/csv")
def export_csv(data: TranslateResponse):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=["original_name", "translated_name", "original_description",
        "translated_description", "price", "allergens", "needs_review"])
    writer.writeheader()
    for item in data.items:
        writer.writerow(item.model_dump())
    return StreamingResponse(iter([out.getvalue().encode("utf-8-sig")]), media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="menumitra_menu.csv"'})

@app.post("/api/export/print")
def export_print(data: TranslateResponse):
    rows = ""
    for item in data.items:
        review = '<span class="review">Please review translation</span>' if item.needs_review else ""
        rows += f"<article><div><h2>{escape(item.translated_name)}</h2><p>{escape(item.translated_description)}</p>{review}</div><strong>₹{item.price:g}</strong></article>"
    page = f"""<!doctype html><html><head><meta charset="utf-8"><title>Menu</title>
    <style>body{{font-family:Arial,sans-serif;max-width:800px;margin:40px auto;padding:20px;color:#18372b}}
    h1{{text-align:center;color:#174c38}}.sub{{text-align:center;color:#666}}
    article{{display:flex;justify-content:space-between;gap:20px;border-bottom:1px solid #ddd;padding:12px 0}}
    h2{{font-size:19px;margin:0 0 5px}}p{{margin:0;color:#444}}.review{{color:#8a4b00;font-size:12px}}
    @media print{{button{{display:none}}}}</style></head><body>
    <h1>{escape(data.restaurant_name)}</h1><p class="sub">{escape(data.source_language)} → {escape(data.target_language)}</p>
    {rows}<p class="sub">AI translations must be reviewed before publication.</p>
    <button onclick="window.print()">Print / Save as PDF</button></body></html>"""
    return HTMLResponse(page)

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML

HTML = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MenuMitra AI</title><style>
:root{--green:#174c38;--cream:#fffaf0;--orange:#e99b35;--ink:#20332b}*{box-sizing:border-box}
body{margin:0;background:var(--cream);font-family:Segoe UI,Arial,sans-serif;color:var(--ink)}
header{background:var(--green);color:white;padding:28px 20px}header .wrap,main{max-width:1100px;margin:auto}
h1{margin:0;font-size:clamp(28px,5vw,42px)}header p{margin:8px 0 0;color:#e8f1eb}
main{padding:24px 18px 60px}.panel{background:white;border:1px solid #e8e2d6;border-radius:16px;padding:20px;margin-bottom:18px}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}label{font-weight:650;display:block;margin-bottom:6px}
input,select{width:100%;padding:11px;border:1px solid #d4d8d2;border-radius:8px;font:inherit;background:white}
.item{display:grid;grid-template-columns:1.2fr 1.5fr .6fr 1fr auto;gap:8px;align-items:end;margin:12px 0}
button{border:0;border-radius:9px;background:var(--green);color:white;padding:12px 16px;font-weight:700;cursor:pointer}
.secondary{background:#e9efe9;color:var(--green)}.orange{background:var(--orange);color:#2a2418}
.actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:16px}.muted{color:#68756d;font-size:14px}
.status{padding:12px;border-radius:9px;background:#f1f4ef;margin:12px 0;white-space:pre-wrap}.result{border:1px solid #e2e6df;border-radius:12px;padding:14px;margin:10px 0}
.result h3{margin:0 0 8px;color:var(--green)}.result p{margin:5px 0}.flag{font-size:12px;color:#8a4b00;font-weight:700}
footer{text-align:center;color:#69756d;padding:24px}@media(max-width:720px){.grid{grid-template-columns:1fr}.item{grid-template-columns:1fr 1fr}.item button{grid-column:1/-1}}
</style></head><body><header><div class="wrap"><h1>🍽️ MenuMitra AI</h1><p>Local-first AI menu translation for small restaurants and cafés.</p></div></header>
<main><div class="panel"><h2>1. Restaurant details</h2><div class="grid">
<div><label>Restaurant name</label><input id="restaurant" value="Bihar Taste Cafe"></div>
<div><label>Menu language</label><select id="source"><option>English</option><option>Hindi</option></select></div>
<div><label>Translate into</label><select id="target"><option>Hindi</option><option>English</option><option>Bengali</option><option>Marathi</option><option>Tamil</option></select></div>
<div><label>Load menu from CSV</label><input type="file" id="csvfile" accept=".csv"><p class="muted">Columns: name, description, price, allergens</p></div>
</div></div>
<div class="panel"><h2>2. Menu items</h2><div id="items"></div><div class="actions"><button class="secondary" id="add">+ Add item</button><button class="orange" id="sample">Load sample menu</button></div>
<p class="muted">Use restaurant-verified ingredient and allergen information. The AI does not verify food safety.</p></div>
<div class="panel"><h2>3. Translate and review</h2><button id="translate">Translate menu with local AI</button><div id="status" class="status">Checking local Ollama...</div><div id="results"></div>
<div class="actions"><button id="csv" class="secondary" disabled>Download CSV</button><button id="print" class="secondary" disabled>Open printable menu</button></div></div>
<div class="panel"><h2>Privacy by design</h2><p>With a local Ollama model, menu text is processed by the local model service rather than a hosted AI API. The initial model download requires internet.</p>
<p class="muted">Review every translation before publishing. Prices and allergen information should be confirmed by the restaurant.</p></div></main><footer>MenuMitra AI · Python + FastAPI + Ollama</footer>
<script>
const itemsEl=document.getElementById('items'),statusEl=document.getElementById('status'),resultsEl=document.getElementById('results');let translated=null;
function addItem(v={}){const row=document.createElement('div');row.className='item';row.innerHTML='<div><label>Dish name</label><input class="name" placeholder="Sattu Paratha"></div><div><label>Description</label><input class="description" placeholder="Roasted gram flour stuffed flatbread"></div><div><label>Price (₹)</label><input class="price" type="number" min="0" step="0.01" placeholder="80"></div><div><label>Allergens (verified)</label><input class="allergens" placeholder="e.g. wheat"></div><button class="secondary remove">×</button>';
row.querySelector('.name').value=v.name||'';row.querySelector('.description').value=v.description||'';row.querySelector('.price').value=v.price??'';row.querySelector('.allergens').value=v.allergens||'';row.querySelector('.remove').onclick=()=>row.remove();itemsEl.appendChild(row);}
function readItems(){const out=[...itemsEl.querySelectorAll('.item')].map(r=>({name:r.querySelector('.name').value.trim(),description:r.querySelector('.description').value.trim(),price:Number(r.querySelector('.price').value),allergens:r.querySelector('.allergens').value.trim()})).filter(x=>x.name);
if(!out.length)throw Error('Add at least one dish name.');if(out.some(x=>!Number.isFinite(x.price)||x.price<0))throw Error('Enter a valid non-negative price for every dish.');return out;}
document.getElementById('add').onclick=()=>addItem();
document.getElementById('sample').onclick=()=>{itemsEl.innerHTML='';[{name:'Sattu Paratha',description:'Flatbread stuffed with roasted gram flour',price:80,allergens:'wheat'},{name:'Litti Chokha',description:'Roasted wheat dough balls served with mashed vegetables',price:120,allergens:'wheat'},{name:'Paneer Butter Masala',description:'Paneer in a creamy tomato-based gravy',price:180,allergens:'milk'}].forEach(addItem);};
document.getElementById('csvfile').onchange=async e=>{const f=e.target.files[0];if(!f)return;const fd=new FormData();fd.append('file',f);try{const r=await fetch('/api/upload-csv',{method:'POST',body:fd});const d=await r.json();if(!r.ok)throw Error(d.detail||'Upload failed');itemsEl.innerHTML='';d.items.forEach(addItem);statusEl.textContent='CSV loaded. Review values before translating.';}catch(err){statusEl.textContent=err.message;}};
document.getElementById('translate').onclick=async()=>{try{const items=readItems();statusEl.textContent='Translating locally. First request can take longer while the model loads...';resultsEl.innerHTML='';
const payload={restaurant_name:document.getElementById('restaurant').value||'My Restaurant',source_language:document.getElementById('source').value,target_language:document.getElementById('target').value,items};
const r=await fetch('/api/translate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const d=await r.json();if(!r.ok)throw Error(d.detail||'Translation failed');translated=d;
d.items.forEach(x=>{const el=document.createElement('div');el.className='result';const h=document.createElement('h3');h.textContent=x.translated_name+' · ₹'+x.price;el.appendChild(h);
const p1=document.createElement('p');p1.textContent='Original: '+x.original_name+' — '+x.original_description;el.appendChild(p1);const p2=document.createElement('p');p2.textContent='Translation: '+x.translated_description;el.appendChild(p2);
const p3=document.createElement('p');p3.textContent='Allergens (provided): '+(x.allergens||'Not provided');el.appendChild(p3);if(x.needs_review){const f=document.createElement('div');f.className='flag';f.textContent='⚠ Human review required';el.appendChild(f);}resultsEl.appendChild(el);});
statusEl.textContent='Translation complete. Review all items before publishing.';document.getElementById('csv').disabled=false;document.getElementById('print').disabled=false;
}catch(err){statusEl.textContent='Error: '+err.message;}};
document.getElementById('csv').onclick=async()=>{if(!translated)return;const r=await fetch('/api/export/csv',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(translated)});if(!r.ok){statusEl.textContent='CSV export failed';return;}const a=document.createElement('a');a.href=URL.createObjectURL(await r.blob());a.download='menumitra_menu.csv';a.click();URL.revokeObjectURL(a.href);};
document.getElementById('print').onclick=async()=>{if(!translated)return;const r=await fetch('/api/export/print',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(translated)});const html=await r.text();const w=window.open('','_blank');if(!w){statusEl.textContent='Allow pop-ups to open printable menu.';return;}w.document.open();w.document.write(html);w.document.close();};
document.getElementById('sample').click();fetch('/api/health').then(r=>r.json()).then(d=>statusEl.textContent=d.model_available?'Ollama ready. Model: '+d.model:'Model not detected: '+d.model+'. Run: ollama pull '+d.model).catch(()=>statusEl.textContent='Could not reach Ollama yet. Start Ollama and install the model.');
</script></body></html>"""
