from dotenv import load_dotenv
import os
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import models
import json
import re
from database import engine, get_db
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pdfplumber
import docx
import io
import httpx
from groq import Groq

models.Base.metadata.create_all(bind=engine)

# Adiciona coluna complemento se não existir (migration simples)
from sqlalchemy import text
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE curriculo ADD COLUMN complemento TEXT"))
        conn.commit()
    except Exception:
        pass  # coluna já existe

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE curriculo ADD COLUMN github_url VARCHAR"))
        conn.commit()
    except Exception:
        pass  # coluna já existe

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
cliente_ia = Groq(api_key=GROQ_API_KEY)

# Contexto fixo de projetos práticos do Ryan (fora do currículo formal)
PROJETOS_PRATICOS = """
PROJETO PRÁTICO (GitHub público, prova de aplicação real — não é só teoria de curso):

To-Do List API (Java 21 + Spring Boot 4.1.0 + Hibernate ORM + PostgreSQL + Docker):
- Backend Java com Spring Boot, persistência real em PostgreSQL containerizado 
  via Docker Compose (volume nomeado, restart automático configurado)
- Persistência validada na prática: dados confirmados intactos após restart 
  do container (não é só "configurei e funcionou uma vez")
- CRUD completo (POST, GET, PUT, DELETE) testado manualmente
- Frontend próprio em HTML/CSS/JS vanilla, tema dark, com feedback visual
- 3 bugs reais resolvidos com causa raiz documentada: erro de digitação em 
  dependência Maven, incompatibilidade de volume Docker com versão do Postgres, 
  cascata de erro de sintaxe em edição manual de CSS
- Ambiente 100% reproduzível via docker-compose up
- Projeto teve orientação conceitual por IA, mas todo código foi escrito 
  manualmente pelo candidato, com aprendizado documentado em caderno físico
"""

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

def salvar_historico(db: Session, resultado: dict, score: Optional[int] = None):
    entrada = models.HistoricoVaga(
        titulo=resultado.get("titulo"),
        empresa=resultado.get("empresa"),
        requisitos_obrigatorios=json.dumps(resultado.get("requisitos_obrigatorios", [])),
        requisitos_desejaveis=json.dumps(resultado.get("requisitos_desejaveis", [])),
        score=score
    )
    db.add(entrada)
    db.commit()
    db.refresh(entrada)
    return entrada

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
        "complemento": curriculo.complemento or "",
        "github_url": curriculo.github_url or "",
        "data_upload": curriculo.data_upload
    }

class ComplementoPayload(BaseModel):
    complemento: str

class GitHubPayload(BaseModel):
    github_url: str

@app.put("/curriculo/github")
def salvar_github(payload: GitHubPayload, db: Session = Depends(get_db)):
    curriculo = db.query(models.Curriculo).first()
    if not curriculo:
        raise HTTPException(status_code=404, detail="Nenhum currículo encontrado.")
    curriculo.github_url = payload.github_url
    db.commit()
    return {"ok": True}

@app.put("/curriculo/complemento")
def salvar_complemento(payload: ComplementoPayload, db: Session = Depends(get_db)):
    curriculo = db.query(models.Curriculo).first()
    if not curriculo:
        raise HTTPException(status_code=404, detail="Nenhum currículo encontrado.")
    curriculo.complemento = payload.complemento
    db.commit()
    return {"ok": True}

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
    texto_curto = texto[:3000]

    resposta = cliente_ia.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "Você extrai dados de vagas de emprego. Responda APENAS com JSON válido, sem markdown."
            },
            {
                "role": "user",
                "content": f"""Extraia os dados da vaga abaixo.

SEÇÕES QUE CONTÊM REQUISITOS (extrair):
- Requisitos, Pré-requisitos, Qualificações, Perfil desejado, Diferenciais, Desejável

SEÇÕES QUE NÃO SÃO REQUISITOS (ignorar completamente):
- Benefícios, Atribuições, Responsabilidades, Atividades, O que você vai fazer, Local de trabalho, Regime, Jornada

REGRA CRÍTICA — NÃO FATIAR:
- Se uma frase tem "ou", vírgulas ou "e" listando alternativas de UMA MESMA exigência, mantenha como UM ÚNICO item.
- ERRADO: separar "Sistemas de Informação, Ciência da Computação ou afins" em 3 itens.
- CERTO: manter como "Sistemas de Informação, Ciência da Computação ou afins" — 1 item só.
- Só separe quando forem exigências INDEPENDENTES (ex: "Inglês intermediário" e "Excel avançado" são 2 itens distintos).
Responda com este JSON:
{{"titulo":"...","empresa":"...","requisitos_obrigatorios":["..."],"requisitos_desejaveis":["..."],"resumo":"..."}}

Texto da vaga:
{texto_curto}"""
            }
        ],
        max_tokens=500,
        temperature=0.1
    )

    import json, re
    texto_resposta = resposta.choices[0].message.content.strip()
    print("=== RESPOSTA IA ===")
    print(texto_resposta)
    print("==================")
    texto_resposta = re.sub(r"```json\s*", "", texto_resposta)
    texto_resposta = re.sub(r"```\s*", "", texto_resposta)
    resultado = json.loads(texto_resposta.strip())
    for chave in ["requisitos_obrigatorios", "requisitos_desejaveis"]:  
        resultado[chave] = [r.rstrip(";,. ") for r in resultado.get(chave, [])]
    return resultado

@app.post("/vaga/analisar-url")
async def analisar_url(payload: dict, db: Session = Depends(get_db)):
    url = payload.get("url", "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL não fornecida.")
    texto = await fetch_texto_url(url)
    if not texto:
        return {"sucesso": False, "motivo": "fetch_falhou"}
    try:
        resultado = analisar_texto_vaga(texto)
        historico = salvar_historico(db, resultado)
        resultado["historico_id"] = historico.id
        return {"sucesso": True, "dados": resultado}
    except Exception as e:
        print(f"Erro: {e}")
        return {"sucesso": False, "motivo": "parse_falhou"}

@app.post("/vaga/analisar-texto")
async def analisar_texto(payload: VagaTexto, db: Session = Depends(get_db)):
    if not payload.texto.strip():
        raise HTTPException(status_code=400, detail="Texto vazio.")
    try:
        resultado = analisar_texto_vaga(payload.texto)
        historico = salvar_historico(db, resultado)
        resultado["historico_id"] = historico.id
        return {"sucesso": True, "dados": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao analisar: {str(e)}")

class VagaComparar(BaseModel):
    requisitos_obrigatorios: list
    requisitos_desejaveis: list
    titulo: str
    empresa: str
    historico_id: Optional[int] = None

@app.post("/vaga/comparar")
def comparar_curriculo_vaga(payload: VagaComparar, db: Session = Depends(get_db)):
    curriculo = db.query(models.Curriculo).first()
    if not curriculo:
        raise HTTPException(status_code=404, detail="Nenhum currículo encontrado. Faça upload primeiro.")

    complemento = curriculo.complemento or ""
    github_url = curriculo.github_url or ""
    github_linha = f"\n\nGitHub: {github_url}" if github_url else ""
    texto_curriculo = (curriculo.texto_extraido + "\n\nCERTIFICAÇÕES CONCLUÍDAS PELO CANDIDATO:\n" + complemento + github_linha)[:2000]
    obrigatorios = payload.requisitos_obrigatorios[:8]
    desejaveis = payload.requisitos_desejaveis[:5]
    obrigatorios_str = "\n".join(f"- {r}" for r in obrigatorios)
    desejaveis_str = "\n".join(f"- {r}" for r in desejaveis)

    resposta = cliente_ia.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "Você compara currículos com vagas. Responda APENAS com JSON válido, sem markdown."
            },
            {
                "role": "user",
                "content": f"""Leia o currículo abaixo com atenção total antes de classificar qualquer requisito.

CURRÍCULO:
{texto_curriculo}

VAGA: {payload.titulo} em {payload.empresa}

REQUISITOS OBRIGATÓRIOS (classifique cada um como "tenho" ou "falta"):
{obrigatorios_str}

REQUISITOS DESEJÁVEIS (classifique cada um como "tenho" ou "falta"):
{desejaveis_str}

INSTRUÇÕES:
1. Procure equivalência semântica: "cursando ADS" atende "Superior em andamento em Sistemas de Informação ou afins". "Python" atende "linguagem de programação". "Power BI" atende "Dashboards/BI".
2. Para requisitos com "ou"/alternativas, basta o currículo atender QUALQUER uma das opções para marcar como "tenho".
3. Para localização: procure explicitamente a cidade no currículo antes de marcar como "falta".
4. Use o texto EXATO de cada requisito ao colocá-lo em "tenho" ou "falta". Não invente novos requisitos.
5. TODOS os requisitos listados acima devem aparecer em "tenho" ou "falta" — nenhum pode sumir.

Responda APENAS com este JSON:
{{"tenho":["requisito exato"],"falta":["requisito exato"],"recomendacao":"1 frase direta sobre o alinhamento do candidato"}}"""
            }
        ],
        max_tokens=500,
        temperature=0.1
    )

    texto_resposta = resposta.choices[0].message.content.strip()
    print("=== COMPARADOR ===")
    print(texto_resposta)
    print("==================")
    texto_resposta = re.sub(r"```json\s*", "", texto_resposta)
    texto_resposta = re.sub(r"```\s*", "", texto_resposta)
    resultado = json.loads(texto_resposta.strip())

    tenho = resultado.get("tenho", [])
    falta = resultado.get("falta", [])

    PESO_OBRIGATORIO = 2
    PESO_DESEJAVEL = 1
    pontos_totais = (len(obrigatorios) * PESO_OBRIGATORIO) + (len(desejaveis) * PESO_DESEJAVEL)

    if pontos_totais == 0:
        score = 0
    else:
        pontos_obtidos = 0
        for req in obrigatorios:
            if req in tenho:
                pontos_obtidos += PESO_OBRIGATORIO
        for req in desejaveis:
            if req in tenho:
                pontos_obtidos += PESO_DESEJAVEL
        score = round((pontos_obtidos / pontos_totais) * 100)

    if payload.historico_id:
        entrada = db.query(models.HistoricoVaga).filter(models.HistoricoVaga.id == payload.historico_id).first()
        if entrada:
            entrada.score = score
            db.commit()

    return {
        "score": score,
        "tenho": tenho,
        "falta": falta,
        "recomendacao": resultado.get("recomendacao", "")
    }


# --- CHAT CONSULTIVO DE VAGA ---

class MensagemChat(BaseModel):
    role: str  # "user" ou "assistant"
    content: str

class VagaConsultar(BaseModel):
    titulo: str
    empresa: str
    requisitos_obrigatorios: list
    requisitos_desejaveis: list
    resumo: Optional[str] = ""
    pergunta: str
    historico_chat: list[MensagemChat] = []

def montar_system_prompt_consultivo(curriculo_texto: str, github_url: str = "") -> str:
    return f"""Você é um consultor de RH sênior e especialista em estratégia de candidaturas, analisando vagas para Ryan Duarte Quintão.

CONTEXTO PESSOAL DO RYAN:
- Cursando ADS (Análise e Desenvolvimento de Sistemas) na Multivix, Serra-ES, 2026-2028, atualmente no 1º período (adiantando matérias)
- Em transição de carreira para TI
- Localização: Serra - ES

CURRÍCULO FORMAL E CERTIFICAÇÕES:
{curriculo_texto}

{PROJETOS_PRATICOS}

{f"GitHub público do candidato: {github_url}" if github_url else ""}

COMO VOCÊ DEVE ANALISAR:
1. Nunca trate requisito rígido (período, formação exata) como eliminação automática — trate como ALERTA, e avalie se é o tipo de empresa/vaga onde isso provavelmente é flexível (recrutador humano lendo currículo) ou rígido (ATS corporativo de multinacional, grande volume de candidatos).
2. Sempre que um requisito técnico aparecer, verifique se o Ryan tem PROVA PRÁTICA (projeto, certificação) e não só menção solta de competência genérica.
3. Aponte equivalência semântica quando fizer sentido (ex: "cursando ADS" atende "Sistemas de Informação ou afins"; "Postgres no projeto" atende "noções de SQL").
4. Quando um requisito for um ponto fraco real, SEMPRE sugira como ele pode reforçar isso no currículo: uma frase ou palavra-chave pronta pra colar, sem inventar experiência que ele não tem.
5. Responda em linguagem natural, como uma conversa franca de consultor, não como lista robótica de score.
6. Seja honesto: se a vaga não for um bom encaixe, diga isso claramente, sem inflar otimismo só para agradar.
7. Não acrescente seções fora do que foi pedido na pergunta do Ryan — responda diretamente ao que ele perguntou, sem repetir a análise completa do zero a cada mensagem."""

@app.post("/vaga/consultar")
def consultar_vaga(payload: VagaConsultar, db: Session = Depends(get_db)):
    curriculo = db.query(models.Curriculo).first()
    if not curriculo:
        raise HTTPException(status_code=404, detail="Nenhum currículo encontrado. Faça upload primeiro.")

    complemento = curriculo.complemento or ""
    curriculo_texto = (curriculo.texto_extraido + "\n\nCERTIFICAÇÕES CONCLUÍDAS:\n" + complemento)[:1500]
    system_prompt = montar_system_prompt_consultivo(curriculo_texto, curriculo.github_url or "")
    obrigatorios_str = "\n".join(f"- {r}" for r in payload.requisitos_obrigatorios[:8])
    desejaveis_str = "\n".join(f"- {r}" for r in payload.requisitos_desejaveis[:5])

    contexto_vaga = f"""VAGA ANALISADA AGORA:
Título: {payload.titulo}
Empresa: {payload.empresa}

Requisitos obrigatórios:
{obrigatorios_str}

Requisitos desejáveis:
{desejaveis_str}

Resumo da vaga: {payload.resumo}"""

    mensagens = [{"role": "system", "content": system_prompt}]
    mensagens.append({"role": "user", "content": contexto_vaga})

    historico_limitado = payload.historico_chat[-6:]
    for msg in historico_limitado:
        mensagens.append({"role": msg.role, "content": msg.content})

    mensagens.append({"role": "user", "content": payload.pergunta})

    try:
        resposta = cliente_ia.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=mensagens,
            max_tokens=700,
            temperature=0.4
        )
        texto_resposta = resposta.choices[0].message.content.strip()
        return {"resposta": texto_resposta}
    except Exception as e:
        print(f"Erro no chat consultivo: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao consultar: {str(e)}")

@app.get("/historico")
def listar_historico(db: Session = Depends(get_db)):
    registros = db.query(models.HistoricoVaga).order_by(models.HistoricoVaga.data_analise.desc()).all()
    return [
        {
            "id": r.id,
            "titulo": r.titulo,
            "empresa": r.empresa,
            "score": r.score,
            "data_analise": r.data_analise,
            "requisitos_obrigatorios": json.loads(r.requisitos_obrigatorios) if r.requisitos_obrigatorios else [],
            "requisitos_desejaveis": json.loads(r.requisitos_desejaveis) if r.requisitos_desejaveis else []
        }
        for r in registros
    ]

@app.delete("/historico/{historico_id}")
def deletar_historico(historico_id: int, db: Session = Depends(get_db)):
    entrada = db.query(models.HistoricoVaga).filter(models.HistoricoVaga.id == historico_id).first()
    if not entrada:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    db.delete(entrada)
    db.commit()
    return {"detail": "Deletado com sucesso"}