# app.py
import os, tempfile, json
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from ai_logic import analyze_pitchdeck

app = FastAPI(title="Pitch Deck Analyzer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"ok": True, "msg": "POST a PDF/PPTX to /analyze_file OR send a local path to /analyze_path (dev-only - from docker)."}

@app.post("/analyze_file")
async def analyze_file(file: UploadFile = File(...)):
    """
    Upload a .pdf or .pptx. We save it to a temp file (to get a real file path),
    pass that path into analyzer.analyze_pitchdeck(), return JSON.
    """
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in {".pdf", ".pptx"}:
        raise HTTPException(status_code=415, detail="Only .pdf and .pptx supported.")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file.")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        result = analyze_pitchdeck(tmp_path)   # <-- pass file path to your function
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Analyze error: {e}")
    finally:
        try:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass

@app.post("/analyze_path")
def analyze_path(path: str = Body(..., embed=True)):
    """
    DEV-ONLY: pass a local file path that the server can access.
    Body: {"path": "C:\\Users\\...\\deck.pdf"}
    """
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    ext = os.path.splitext(path)[1].lower()
    if ext not in {".pdf", ".pptx"}:
        raise HTTPException(status_code=415, detail="Only .pdf and .pptx supported.")
    try:
        return analyze_pitchdeck(path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Analyze error: {e}")
