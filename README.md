# CandidaTrack

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat&logo=sqlalchemy&logoColor=white)
![Groq](https://img.shields.io/badge/Groq_API-LLaMA-F55036?style=flat)
![HTML CSS JS](https://img.shields.io/badge/Frontend-HTML%20%2B%20CSS%20%2B%20JS-E34F26?style=flat&logo=html5&logoColor=white)
![Status](https://img.shields.io/badge/status-em%20uso%20ativo-brightgreen?style=flat)

> **Projeto pessoal** — sistema completo de rastreamento de candidaturas de emprego com análise inteligente de currículo e vagas via IA, construído do zero para uso real no dia a dia da minha transição de carreira para TI.

![Preview 1](screenshots/image.png)
![Preview 2](screenshots/image-1.png)
![Preview 3](screenshots/image-2.png)
![Preview 4](screenshots/image-3.png)
![Preview 5](screenshots/image-5.png)
![Preview 6](screenshots/image-6.png)
![Preview 7](screenshots/image-7.png)
---

## Contexto e motivação

Este é o meu **segundo projeto** de desenvolvimento. O primeiro foi uma [To-Do List API](https://github.com/RyanDua11/todolist-spring-postgres) construída com Java 21 + Spring Boot + PostgreSQL, onde aprendi na prática os fundamentos de backend, persistência de dados e resolução de bugs reais.

O CandidaTrack nasceu de uma necessidade real: eu estava me candidatando a várias vagas de emprego ao mesmo tempo e perdi o controle de onde tinha aplicado, em qual status estava cada processo, e não tinha como comparar meu currículo com os requisitos de cada vaga de forma rápida e inteligente. Planilha não era suficiente. Então construí a solução.

A ideia é simples: um sistema que centraliza todas as candidaturas, analisa vagas com IA, compara automaticamente com o meu currículo e ainda oferece um chat consultivo para perguntar sobre cada vaga diretamente. Tudo rodando localmente, sem custo, sem dado nenhum saindo pra nuvem além das chamadas de API.

---

## O que o sistema faz

### Gestão de Candidaturas
- Registra candidaturas com empresa, cargo, plataforma (LinkedIn, Gupy, etc.), status e observações
- Atualiza status em tempo real — Enviado, Em Andamento, Aprovado, Reprovado
- Cards expansíveis com edição inline, sem reload de página
- Modal de confirmação antes de deletar

### Currículo Inteligente
- Upload de currículo em PDF ou DOCX com extração automática de texto via `pdfplumber` e `python-docx`
- Campo de certificações e cursos extras para complementar o que não está no PDF
- Campo de link do GitHub — entra automaticamente no contexto de todas as análises de IA
- Tudo carrega automaticamente ao abrir a página

### Análise de Vagas
- Analisa vagas diretamente pela URL — faz scraping automático com `httpx` + `BeautifulSoup4`
- Fallback inteligente: se o scraping falhar (sites bloqueados, SPAs, etc.), o campo de texto aparece automaticamente para colar o conteúdo manualmente
- Extrai título, empresa, requisitos obrigatórios, requisitos desejáveis e resumo da vaga via IA
- Requisitos com alternativas (`"ou"`, vírgulas) são mantidos como item único — não fragmentados incorretamente

### Comparador Currículo × Vaga
- Compara o currículo extraído + certificações + GitHub com todos os requisitos da vaga
- Classifica cada requisito em "tenho" ou "falta" com equivalência semântica real (ex: "cursando ADS" atende "Superior em andamento em SI ou afins")
- Score de compatibilidade com peso diferente para obrigatórios (×2) e desejáveis (×1)
- Barra de progresso visual + recomendação em texto gerada pela IA
- Score salvo automaticamente no histórico

### Chat Consultivo de Vaga
- Abre automaticamente após analisar qualquer vaga
- Chat em tempo real com IA sobre aquela vaga específica — contexto completo: currículo, certificações, GitHub, requisitos da vaga
- Responde perguntas como "Vale a pena me candidatar?", "O que reforçar no currículo?", "Esse requisito me elimina?"
- Modelo maior (`llama-3.3-70b-versatile`) exclusivamente no chat para respostas mais elaboradas
- Histórico das últimas 6 mensagens mantido por vaga, reseta ao analisar nova vaga
- Suporte a markdown — **negrito** renderizado corretamente no chat

### Histórico de Análises
- Todas as vagas analisadas ficam salvas com título, empresa, data e score
- Carrega automaticamente ao abrir a página
- Delete individual com botão ✕

---

## Stack completa

### Backend
| Tecnologia | Uso |
|---|---|
| Python 3.11+ | Linguagem principal |
| FastAPI | Framework web e API REST |
| PostgreSQL | Banco de dados relacional |
| SQLAlchemy | ORM — models e queries |
| pdfplumber | Extração de texto de PDFs |
| python-docx | Extração de texto de arquivos DOCX |
| httpx | Requisições HTTP assíncronas (scraping de URL) |
| BeautifulSoup4 | Parse de HTML das páginas de vaga |
| python-dotenv | Carregamento seguro de variáveis de ambiente |
| Groq SDK | Chamadas à API de IA (LLaMA via Groq) |

### IA — Modelos utilizados
| Modelo | Onde é usado |
|---|---|
| `llama-3.1-8b-instant` | Extração de dados da vaga e comparação currículo×vaga |
| `llama-3.3-70b-versatile` | Chat consultivo (respostas mais elaboradas e contextuais) |

### Frontend
| Tecnologia | Uso |
|---|---|
| HTML5 + CSS3 + JavaScript puro | Frontend completo, sem frameworks |
| Cormorant Garamond | Tipografia serif para títulos |
| Space Grotesk | Tipografia sans-serif para corpo |
| Google Fonts | Carregamento das fontes |

### Visual — Tema "Antique Parian"
- Fundo principal: `#0d0b08`
- Dourado: `#c9a84c`
- Cards com bordas duplas e cantos ornamentais em CSS puro
- Orbs com gradiente animados ao movimento do mouse
- Scrollbars dourados finos customizados (webkit + Firefox)
- Select com seta customizada em SVG inline

---

## Arquitetura

```
candidatrack/
├── main.py          # FastAPI — todas as rotas e lógica de negócio
├── models.py        # Modelos SQLAlchemy: Candidatura, Curriculo, HistoricoVaga
├── database.py      # Conexão com PostgreSQL e sessão do SQLAlchemy
├── index.html       # Frontend completo (HTML + CSS + JS em arquivo único)
├── .env             # Chave de API Groq (nunca commitar)
└── .gitignore       # Inclui .env, venv/, __pycache__/
```

### Models do banco

**Candidatura** — empresa, cargo, plataforma, status, data, observações

**Curriculo** — nome do arquivo, texto extraído, complemento (certificações), github_url, data de upload

**HistoricoVaga** — título, empresa, requisitos obrigatórios (JSON), requisitos desejáveis (JSON), score, data da análise

---

## Como rodar localmente

### Pré-requisitos
- Python 3.11+
- PostgreSQL rodando localmente
- Conta na [Groq](https://console.groq.com) com chave de API gratuita
- Live Server (extensão do VS Code) ou qualquer servidor local para o frontend

### 1. Clonar o repositório

```bash
git clone https://github.com/RyanDua11/candidatrack.git
cd candidatrack
```

### 2. Criar e ativar o ambiente virtual

```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary pdfplumber python-docx httpx beautifulsoup4 python-dotenv groq
```

### 4. Configurar o banco de dados

Crie um banco PostgreSQL local e configure a string de conexão em `database.py`:

```python
SQLALCHEMY_DATABASE_URL = "postgresql://usuario:senha@localhost/candidatrack"
```

As tabelas são criadas automaticamente na primeira execução. As colunas `complemento` e `github_url` também são adicionadas automaticamente via migration simples no startup caso não existam.

### 5. Configurar a chave de API

Crie um arquivo `.env` na raiz:

```
GROQ_API_KEY=gsk_sua_chave_aqui
```

> O `.env` está no `.gitignore`. Nunca commitar a chave.

### 6. Rodar o backend

```bash
uvicorn main:app --reload
```

O backend sobe em `http://127.0.0.1:8000`.

### 7. Abrir o frontend

Abra o `index.html` com o Live Server do VS Code (porta 5500) ou qualquer servidor local. Não abrir direto como arquivo — a API precisa do CORS configurado para `localhost`.

---

## Rotas da API

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/candidaturas` | Lista todas as candidaturas |
| POST | `/candidaturas` | Cria nova candidatura |
| PUT | `/candidaturas/{id}` | Atualiza candidatura existente |
| DELETE | `/candidaturas/{id}` | Deleta candidatura |
| POST | `/curriculo/upload` | Upload de currículo PDF ou DOCX |
| GET | `/curriculo` | Retorna currículo salvo |
| PUT | `/curriculo/complemento` | Salva certificações e cursos extras |
| PUT | `/curriculo/github` | Salva link do GitHub |
| POST | `/vaga/analisar-url` | Analisa vaga a partir de URL (scraping) |
| POST | `/vaga/analisar-texto` | Analisa vaga a partir de texto colado |
| POST | `/vaga/comparar` | Compara currículo com requisitos da vaga |
| POST | `/vaga/consultar` | Chat consultivo sobre a vaga |
| GET | `/historico` | Lista histórico de vagas analisadas |
| DELETE | `/historico/{id}` | Deleta entrada do histórico |

---

## Dificuldades reais enfrentadas e como foram resolvidas

### 1. Scraping de vagas bloqueadas
Muitos sites de vaga (Gupy, LinkedIn, portais corporativos) bloqueiam scraping ou retornam SPAs que não têm conteúdo no HTML estático. A solução foi implementar um fallback automático: se o fetch da URL falhar ou retornar conteúdo inútil, o frontend exibe um textarea para o usuário colar o texto manualmente — sem mensagem de erro genérica, sem travar o fluxo.

### 2. IA fragmentando requisitos compostos incorretamente
A IA tinha o hábito de quebrar requisitos como "Sistemas de Informação, Ciência da Computação ou afins" em três itens separados. Isso distorcia o score e poluía a interface. Resolvido com instrução explícita no prompt: requisitos com "ou"/vírgulas são uma única exigência e devem ser mantidos como item único. Testado e validado com vários formatos de vaga reais.

### 3. Score impreciso por falta de equivalência semântica
O comparador inicial marcava "falta" para tudo que não fosse menção textual exata. "Cursando ADS" não atendia "Superior em andamento em SI ou afins". Resolvido com instrução de equivalência semântica no prompt do comparador, com exemplos concretos de mapeamento.

### 4. Rotas sumindo ao editar o main.py
Durante o desenvolvimento, ao colar blocos grandes de código no arquivo, algumas rotas desapareciam silenciosamente por erros de indentação ou colagem incorreta. Lição aprendida: sempre confirmar as rotas ativas com um print ou via `/docs` do FastAPI antes de seguir.

### 5. Reload automático do uvicorn não pegando mudanças grandes
O `--reload` do uvicorn às vezes não detectava mudanças em arquivos grandes ou alterações de configuração. Solução: reiniciar manualmente o processo após qualquer mudança estrutural relevante.

### 6. CSS do select no Chrome
O highlight azul nativo do sistema operacional ao abrir um `<select>` não pode ser sobrescrito por CSS — é comportamento nativo do Chrome/Edge. Tentativas com `appearance: none`, `background`, `color` nas options funcionaram parcialmente mas o highlight de seleção ativa é controlado pelo SO. Decisão final: aceitar o comportamento e focar no que é controlável.

### 7. Histórico não carregando ao abrir a página
O `carregarHistorico()` estava sendo chamado apenas após analisar uma vaga. Ao abrir a página pela primeira vez, o histórico ficava vazio mesmo com dados no banco. Corrigido chamando a função no init da página junto com `carregarCandidaturas()` e `carregarCurriculo()`.

### 8. Markdown no chat aparecendo como texto puro
As respostas da IA vinham com `**negrito**` literal no texto. Resolvido com um `.replace()` simples no JavaScript antes de inserir a mensagem no DOM: `` resposta.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') ``.

---

## Decisões técnicas documentadas

- **Chat sem persistência no banco** — o histórico do chat vive em memória no frontend e reseta a cada nova vaga. Decisão consciente: o chat é contextual por sessão de análise, não faz sentido persistir.
- **Modelo maior só no chat** — `llama-3.3-70b-versatile` é usado exclusivamente no chat consultivo onde respostas elaboradas importam. Extração e comparação usam `llama-3.1-8b-instant` que é mais rápido e suficiente para tarefas estruturadas.
- **Currículo truncado em 1500 chars no chat** — o contexto do chat já inclui vaga + histórico de mensagens + system prompt. Truncar o currículo evita estourar o contexto sem perder as informações mais relevantes.
- **Histórico limitado a 6 mensagens no chat** — equivale a 3 trocas completas (usuário + assistente). Suficiente para manter continuidade sem acumular tokens desnecessários.
- **GitHub como link de perfil** — apenas o link do perfil entra no contexto da IA. Leitura de repositórios via API do GitHub foi descartada intencionalmente para manter o projeto simples e sem autenticação adicional.
- **Requisito rígido = ALERTA, nunca eliminação automática** — a IA é instruída a nunca descartar uma candidatura por um requisito que não seja atendido. Ela avalia o contexto (empresa grande com ATS vs recrutador humano) e alerta, sem decidir pelo candidato.
- **Migrations automáticas no startup** — colunas novas (`complemento`, `github_url`) são adicionadas automaticamente com `ALTER TABLE` no startup do backend, sem ferramenta de migration externa. Simples e suficiente para projeto pessoal.

---

## Futuro do projeto

Este é meu segundo projeto de desenvolvimento. Após finalizá-lo, vou iniciar um **curso de design web** (UI/UX, tipografia, composição visual, design systems). Quando concluir, voltarei ao CandidaTrack para aplicar esse conhecimento diretamente aqui — redesenhando a interface com fundamentos sólidos de design, não só intuição.

Possíveis evoluções futuras:
- Redesign da interface com base em fundamentos de UI/UX aprendidos no curso
- Filtro e busca no histórico de vagas analisadas
- Suporte a múltiplos usuários (autenticação)
- Deploy em nuvem (Railway, Render ou similar)
- Leitura de repositórios do GitHub via API para contexto mais rico na análise

---

## Sobre o autor

**Ryan Duarte Quintão**
Cursando ADS na Multivix, Serra-ES (2026–2028) — em transição de carreira para TI.

Competências em desenvolvimento: Python, SQL, PostgreSQL, FastAPI, Java, Spring Boot, HTML/CSS/JS, Linux, Power BI, IA aplicada.

- GitHub: [RyanDua11](https://github.com/RyanDua11)
- LinkedIn: [ryan-duarte-39028a2a1](https://linkedin.com/in/ryan-duarte-39028a2a1)
- Primeiro projeto: [todolist-spring-postgres](https://github.com/RyanDua11/todolist-spring-postgres) — To-Do List API com Java 21 + Spring Boot + PostgreSQL + Docker

---

> Projeto desenvolvido com pesquisa ativa e documentação técnica, com todo código escrito e entendido manualmente, cada bug debugado na raça e cada decisão técnica consciente e documentada.