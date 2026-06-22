from sqlalchemy import Column, Integer, String, DateTime
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