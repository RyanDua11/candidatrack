from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import models
from database import engine, get_db
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
models.Base.metadata.create_all(bind=engine)

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
