from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import models
from database import engine, get_db
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pdfplumber
import docx
import io
import httpx
from groq import Groq

models.Base.metadata.create_all(bind=engine)

from dotenv import load_dotenv
import os
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
cliente_ia = Groq(api_key=GROQ_API_KEY)

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/app")
def frontend():
    return FileResponse("index.html")

class CandidaturaCreate(BaseModel):
    empresa: str
    cargo: str
    plataforma: str
    status: Optional[str] = "Enviado"
    observacoes: Optional[str] = None

class VagaTexto(BaseModel):
    texto: str

@app.get("/")
def root():
    return {"message": "CandidaTrack API rodando!"}

@app.get("/candidaturas")
def listar_candidaturas(db: Session = Depends(get_db)):
    return db.query(models.Candidatura).all()

@app.post("/candidaturas")
def criar_candidatura(candidatura: CandidaturaCreate, db: Session = Depends(get_db)):
    nova = models.Candidatura(**candidatura.model_dump())
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova

@app.put("/candidaturas/{candidatura_id}")
def atualizar_candidatura(candidatura_id: int, candidatura: CandidaturaCreate, db: Session = Depends(get_db)):
    existente = db.query(models.Candidatura).filter(models.Candidatura.id == candidatura_id).first()
    if not existente:
        raise HTTPException(status_code=404, detail="Candidatura não encontrada")
    for key, value in candidatura.model_dump().items():
        setattr(existente, key, value)
    db.commit()
    db.refresh(existente)
    return existente

@app.delete("/candidaturas/{candidatura_id}")
def deletar_candidatura(candidatura_id: int, db: Session = Depends(get_db)):
    existente = db.query(models.Candidatura).filter(models.Candidatura.id == candidatura_id).first()
    if not existente:
        raise HTTPException(status_code=404, detail="Candidatura não encontrada")
    db.delete(existente)
    db.commit()
    return {"detail": "Candidatura deletada com sucesso"}

# --- CURRÍCULO ---

def extrair_texto(conteudo: bytes, nome_arquivo: str) -> str:
    if nome_arquivo.endswith(".pdf"):
        with pdfplumber.open(io.BytesIO(conteudo)) as pdf:
            return "\n".join(
                pagina.extract_text() or "" for pagina in pdf.pages
            ).strip()
    elif nome_arquivo.endswith(".docx"):
        doc = docx.Document(io.BytesIO(conteudo))
        return "\n".join(p.text for p in doc.paragraphs).strip()
    else:
        raise HTTPException(status_code=400, detail="Formato não suportado. Envie PDF ou DOCX.")

@app.post("/curriculo/upload")
async def upload_curriculo(arquivo: UploadFile = File(...), db: Session = Depends(get_db)):
    conteudo = await arquivo.read()
    texto = extrair_texto(conteudo, arquivo.filename)
    if not texto:
        raise HTTPException(status_code=422, detail="Não foi possível extrair texto do arquivo.")
    db.query(models.Curriculo).delete()
    novo = models.Curriculo(nome_arquivo=arquivo.filename, texto_extraido=texto)
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return {"nome_arquivo": novo.nome_arquivo, "data_upload": novo.data_upload}

@app.get("/curriculo")
def obter_curriculo(db: Session = Depends(get_db)):
    curriculo = db.query(models.Curriculo).first()
    if not curriculo:
        return None
    return {
        "id": curriculo.id,
        "nome_arquivo": curriculo.nome_arquivo,
        "data_upload": curriculo.data_upload
    }

# --- VAGA ---

async def fetch_texto_url(url: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            headers = {"User-Agent": "Mozilla/5.0"}
            res = await client.get(url, headers=headers)
            if res.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(res.text, "html.parser")
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                return soup.get_text(separator="\n", strip=True)[:4000]
    except Exception:
        pass
    return None

def analisar_texto_vaga(texto: str) -> dict:
    # Trunca o texto para gastar menos tokens
    texto_curto = texto[:3000]
    
    resposta = cliente_ia.chat.completions.create(
        model="llama-3.1-8b-instant",  # modelo leve = menos tokens
        messages=[
            {
                "role": "system",
                "content": "Você extrai dados de vagas de emprego. Responda APENAS com JSON válido, sem markdown."
            },
            {
                "role": "user",
                "content": f'Extraia do texto: {{"titulo":"...","empresa":"...","requisitos_obrigatorios":["..."],"requisitos_desejaveis":["..."],"resumo":"..."}}\n\nTexto:\n{texto_curto}'
            }
        ],
        max_tokens=500,  # limita a resposta
        temperature=0.1  # menos criatividade = mais consistente e barato
    )
    
    import json, re
    texto_resposta = resposta.choices[0].message.content.strip()
    print("=== RESPOSTA IA ===")
    print(texto_resposta)
    print("==================")
    texto_resposta = re.sub(r"```json\s*", "", texto_resposta)
    texto_resposta = re.sub(r"```\s*", "", texto_resposta)
    return json.loads(texto_resposta.strip())

@app.post("/vaga/analisar-url")
async def analisar_url(payload: dict):
    url = payload.get("url", "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL não fornecida.")
    texto = await fetch_texto_url(url)
    if not texto:
        return {"sucesso": False, "motivo": "fetch_falhou"}
    try:
        resultado = analisar_texto_vaga(texto)
        return {"sucesso": True, "dados": resultado}
    except Exception as e:
        print(f"Erro: {e}")
        return {"sucesso": False, "motivo": "parse_falhou"}

@app.post("/vaga/analisar-texto")
async def analisar_texto(payload: VagaTexto):
    if not payload.texto.strip():
        raise HTTPException(status_code=400, detail="Texto vazio.")
    try:
        resultado = analisar_texto_vaga(payload.texto)
        return {"sucesso": True, "dados": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao analisar: {str(e)}")