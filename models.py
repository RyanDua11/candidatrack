from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from database import Base

class Candidatura(Base):
    __tablename__ = "candidaturas"

    id = Column(Integer, primary_key=True, index=True)
    empresa = Column(String, nullable=False)
    cargo = Column(String, nullable=False)
    plataforma = Column(String, nullable=False)
    status = Column(String, default="Enviado")
    data_candidatura = Column(DateTime, default=datetime.now)
    observacoes = Column(String, nullable=True)

class Curriculo(Base):
    __tablename__ = "curriculo"

    id = Column(Integer, primary_key=True, index=True)
    nome_arquivo = Column(String, nullable=False)
    texto_extraido = Column(Text, nullable=False)
    complemento = Column(Text, nullable=True)
    data_upload = Column(DateTime, default=datetime.now)
    github_url = Column(String, nullable=True)

class HistoricoVaga(Base):
    __tablename__ = "historico_vagas"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=True)
    empresa = Column(String, nullable=True)
    requisitos_obrigatorios = Column(Text, nullable=True)  # JSON string
    requisitos_desejaveis = Column(Text, nullable=True)    # JSON string
    score = Column(Integer, nullable=True)
    data_analise = Column(DateTime, default=datetime.now)