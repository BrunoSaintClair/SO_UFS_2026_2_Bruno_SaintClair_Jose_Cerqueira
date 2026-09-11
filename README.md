# Ollama PDF RAG

Aplicação de RAG (Retrieval-Augmented Generation) local para conversar com documentos PDF utilizando Ollama, LangChain, FastAPI e Next.js.

---

## 📋 Pré-requisitos

1. **Ollama instalado e em execução**:
   ```bash
   ollama serve
   ```
2. **Modelos baixados no Ollama**:
   - Modelo base (**LiquidAI/LFM2.5-2.6B**):
     ```bash
     ollama pull hf.co/LiquidAI/LFM2.5-2.6B-GGUF:Q4_0
     ```
   - Modelo para embeddings:
     ```bash
     ollama pull nomic-embed-text
     ```
3. **Python 3.10+**
4. **Node.js (18+) e pnpm** (instale via `npm install -g pnpm` caso necessário)

---

## ⚙️ Instalação e Configuração

Entre na pasta do projeto:
```bash
cd ollama_pdf_rag
```

### 1. Configurar ambiente Python (Backend / Streamlit)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar frontend (Next.js)
```bash
cd web-ui
pnpm install
pnpm db:migrate
cd ..
```

---

## 🚀 Como Rodar

### Opção 1: Iniciar tudo de uma vez
Na pasta `ollama_pdf_rag` com o ambiente virtual ativado:
```bash
chmod +x start_all.sh
./start_all.sh
```

---

### Opção 2: Iniciar serviços individualmente

- **Backend FastAPI** (porta `8001`):
  ```bash
  cd ollama_pdf_rag
  source venv/bin/activate
  python3 run_api.py
  ```

- **Frontend Next.js** (porta `3000`):
  ```bash
  cd ollama_pdf_rag/web-ui
  pnpm dev
  ```

- **Interface Streamlit (Opcional)** (porta `8501`):
  ```bash
  cd ollama_pdf_rag
  source venv/bin/activate
  python3 run.py
  ```

---

## 🌐 URLs de Acesso

- **Web UI (Next.js):** [http://localhost:3000](http://localhost:3000)
- **API FastAPI (Docs):** [http://localhost:8001/docs](http://localhost:8001/docs)
- **Streamlit Admin:** [http://localhost:8501](http://localhost:8501)
