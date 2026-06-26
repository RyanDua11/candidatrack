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
    data_upload = Column(DateTime, default=datetime.now)