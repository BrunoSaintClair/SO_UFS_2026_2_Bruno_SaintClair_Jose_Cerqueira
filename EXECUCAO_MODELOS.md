## 6.3 Instalação e Execução de Modelos e Serviços

### 1. Resumo da Execução

| Métrica / Parâmetro | Registro Coletado |
| :--- | :--- |
| **Serviço de LLM Local** | **Ollama v0.32.0** (serviço systemd `ollama.service`, daemon `ollama serve`) |
| **Modelo Reservado (LLM)** | `hf.co/LiquidAI/LFM2.5-2.6B-GGUF:Q4_0` (1.59 GB, 2.7B parâmetros, 4096 ctx) |
| **Modelo de Embeddings** | `nomic-embed-text:latest` (274 MB, 137M parâmetros, 768 dim) |
| **Tempo de Download (Reservado)** | **1m 44s** (104 s) — 16 partes de 100 MB via streaming HTTP |
| **Tempo de Download (Embeddings)**| **22.96s** (~23 s) — 3 partes de 100 MB |
| **Espaço em Disco (Modelos)** | **3.6 GB** em `/usr/share/ollama/.ollama/models` (blobs) |
| **Espaço em Disco (Ollama)** | **38 MB** (binário) + **2.1 GB** (runners e CUDA libraries em `/usr/local/lib/ollama`) |
| **Espaço em Disco (Aplicação)** | **3.6 GB** em `ollama_pdf_rag` (1.9 GB `venv`, 1.8 GB `web-ui`, 14 MB `data/`) |
| **Tempo de Inicialização (Ollama)**| **~15 ms** (abertura socket 11434) + **~5.9 s** (descoberta de GPU CUDA) |
| **Tempo de Inicialização (Modelo)**| **4.03 s a 4.13 s** (carga na VRAM pelo `llama-server`) \| **6.36 s** total na API |
| **Tempo de Inicialização (App)** | **6.18 s** (FastAPI/LangChain backend) \| **~2.8 s** (Next.js Turbopack frontend) |
| **Processos Criados** | `ollama` (PID 5102) -> `llama-server` (PID 139562, 100% GPU VRAM); `start_all.sh` -> `python3 run_api.py` + workers (PID 137714, 137717) e `next-server` (PID 137835) |
| **Portas de Rede em Escuta** | **11434** (Ollama API), **36727** (llama-server IPC interno), **8001** (FastAPI), **3000** (Next.js Web UI) |
| **Uso de GPU / VRAM** | **1754 MiB VRAM** alocados na **NVIDIA GeForce RTX 3050 6GB Laptop GPU** |
| **Taxa de Inferência Atingida** | **61.04 tokens/s** na geração (`eval_duration`: 1146 ms / 70 tokens) |

---

### 2. Detalhamento dos Componentes e Execução

#### 2.1 Comandos Utilizados

##### 2.1.1 Servidor Ollama e Gestão de Modelos
- **Instalação do Ollama:**
  ```bash
  curl -fsSL https://ollama.com/install.sh | sh
  ```
  Instala o executável em `/usr/local/bin/ollama`, módulos de aceleração em `/usr/local/lib/ollama/`, provisiona a conta de sistema `ollama` e registra a unidade systemd `/etc/systemd/system/ollama.service`.

- **Ativação e Consulta do Serviço:**
  ```bash
  sudo systemctl enable --now ollama
  systemctl status ollama --no-pager
  ollama --version
  ```

- **Download dos Modelos Locais:**
  ```bash
  # Download do modelo reservado (LFM2.5-2.6B quantizado em Q4_0)
  ollama pull hf.co/LiquidAI/LFM2.5-2.6B-GGUF:Q4_0

  # Download do modelo para representação vetorial
  ollama pull nomic-embed-text
  ```

- **Inspeção de Modelos e Teste de Inferência:**
  ```bash
  # Listar modelos locais persistidos
  ollama list

  # Monitorar modelos carregados na VRAM/RAM
  ollama ps

  # Teste direto de inferência via API REST local
  curl -s http://localhost:11434/api/generate \
    -d '{"model": "hf.co/LiquidAI/LFM2.5-2.6B-GGUF:Q4_0", "prompt": "Ola", "stream": false}' | jq .
  ```

##### 2.1.2 Camada de Aplicação (Backend FastAPI + Frontend Next.js)
- **Instalação do Backend Python:**
  ```bash
  cd /home/bruno/Desktop/trabalho-so/ollama_pdf_rag
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

- **Instalação do Frontend Next.js:**
  ```bash
  cd web-ui
  pnpm install
  pnpm db:migrate
  cd ..
  ```

- **Execução Orquestrada de Todos os Serviços:**
  ```bash
  chmod +x start_all.sh
  ./start_all.sh
  ```

- **Execução dos Serviços em Terminais Individuais (Alternativa):**
  ```bash
  # 1. Backend FastAPI (porta 8001)
  cd ollama_pdf_rag && source venv/bin/activate && python3 run_api.py

  # 2. Frontend Next.js (porta 3000)
  cd ollama_pdf_rag/web-ui && pnpm dev

  # 3. Interface Administrativa Streamlit (porta 8501, opcional)
  cd ollama_pdf_rag && source venv/bin/activate && python3 run.py
  ```

---

#### 2.2 Tempo de Download dos Modelos

Os tempos e taxas foram extraídos diretamente do log de transações do serviço Ollama via `journalctl`:

1. **Modelo Reservado — `hf.co/LiquidAI/LFM2.5-2.6B-GGUF:Q4_0`:**
   - **Tamanho transferido:** 1.593.906.453 bytes (~1.59 GB).
   - **Início:** `16:02:26` (download de 16 partes de 100 MB).
   - **Término:** `16:04:09` (status HTTP 200 na rota `/api/pull`).
   - **Duração Total:** **1m 44s** (104 segundos).
   - **Taxa Média de Transferência:** ~15.3 MB/s.

2. **Modelo de Embeddings — `nomic-embed-text:latest`:**
   - **Tamanho transferido:** 274.302.450 bytes (~274 MB).
   - **Início:** `16:05:11` (download de 3 partes de 100 MB).
   - **Término:** `16:05:28` (status HTTP 200 na rota `/api/pull`).
   - **Duração Total:** **22.96 segundos**.
   - **Taxa Média de Transferência:** ~11.9 MB/s.

---

#### 2.3 Espaço Ocupado pelos Arquivos

- **Ollama e Dependências do Servidor:**
  - `/usr/local/bin/ollama`: **38 MB** (executável estático principal).
  - `/usr/local/lib/ollama`: **2.1 GB** (runners compilados para arquiteturas CUDA `compute_75` a `compute_90` e bibliotecas dinâmicas do runtime).
  - `/usr/share/ollama/.ollama/models`: **3.6 GB**
    - `blobs/`: 3.6 GB (pesos e tensores dos modelos salvos por hash SHA-256).
    - `manifests/`: 44 KB (arquivos de configuração, template e camadas).

- **Aplicação RAG (`/home/bruno/Desktop/trabalho-so/ollama_pdf_rag`): 3.6 GB Total**
  - `venv/` (Python Virtual Environment): **1.9 GB**
    - Pacotes instalados: LangChain, ChromaDB, PyTorch/ONNX, FastAPI, Uvicorn, Pydantic, Unstructured, PDFPlumber.
  - `web-ui/` (Frontend Node.js / React 19): **1.8 GB**
    - `web-ui/node_modules/`: 1.2 GB (dependências de interface e SDK AI).
    - `web-ui/.next/`: 578 MB (cache de build incremental Turbopack).
  - `data/` (Bancos e Arquivos): **14 MB**
    - `data/vectors/`: Base vetorial do ChromaDB (banco SQLite + índices Parquet).
    - `data/api.db`: Base de dados relacional SQLite do backend.
    - `data/pdfs/`: Diretório de armazenamento de documentos PDF indexados.
  - `src/` e `docs/`: **~4.5 MB** (código-fonte e documentação técnica).

---

#### 2.4 Tempo de Inicialização

1. **Servidor Ollama (`ollama serve`):**
   - **Abertura do socket de rede:** **~15 ms** (`10:32:40.489` a `10:32:40.503`).
   - **Descoberta de aceleradores de hardware:** **~5.9 s** (`10:32:40.508` a `10:32:46.456`). O Ollama escaneou a interface Vulkan/CUDA e selecionou a GPU dedicada RTX 3050.

2. **Carregamento do Modelo Reservado na GPU (`llama-server`):**
   - **Alocação de Tensores na VRAM:** **4.03 s a 4.13 s** (tempo medido internamente pelo `llama-server` para carregar o arquivo GGUF e warm-up dos tensores na VRAM).
   - **Duração Total até primeiro token (`load_duration`):** **6.36 s** (6.358.764.843 ns reportados na resposta JSON da API).

3. **Backend FastAPI (`run_api.py`):**
   - **Tempo de importação e setup de rotas:** **6.18 s** (inicialização do framework FastAPI, ChromaDB client e importação dos pipelines do LangChain).

4. **Frontend Next.js (`pnpm dev` com Turbopack):**
   - **Tempo de prontidão do servidor:** **~2.8 s** (execução do Node.js, compilação dos componentes React 19 e escuta na porta 3000).

---

#### 2.5 Processos Criados

A topologia de processos ativos no sistema operacional durante a execução da aplicação e do modelo é estruturada da seguinte forma:

```text
systemd (PID 1)
 ├── ollama.service
 │    └── ollama serve (PID 5102, usuário: ollama, 16 threads)
 │         └── llama-server (PID 139562, usuário: ollama)
 │              ├── Tensores alocados: 100% GPU VRAM (1754 MiB na RTX 3050)
 │              └── Canal IPC: porta TCP local 127.0.0.1:36727
 │
 └── bash -> ./start_all.sh (PID 137713)
      ├── python3 run_api.py (PID 137714)
      │    ├── python3 ... resource_tracker (PID 137716)
      │    └── python3 ... spawn_main (PID 137717, worker Uvicorn/FastAPI na porta 8001)
      │
      └── pnpm dev (PID 137795)
           └── node ... next dev --turbo (PID 137819)
                ├── next-server (v16.0.10) (PID 137835, porta 3000, 25 threads)
                └── node ... postcss.js (PID 137951)
```

- **`ollama serve` (PID 5102):** Processo daemon que gerencia o ciclo de vida dos modelos, pooling de VRAM e requisições HTTP na porta 11434.
- **`llama-server` (PID 139562):** Instância dedicada do runtime *llama.cpp*, invocada pelo Ollama para processar a inferência do modelo `LiquidAI/LFM2.5-2.6B`.
  - Argumentos: `--model .../sha256-e1a61bf9... --port 36727 --host 127.0.0.1 -c 4096 -np 1 --flash-attn auto -b 512 -ub 512`.
- **`python3 run_api.py` (PID 137714, 137717):** Processos do backend REST baseados em Starlette/Uvicorn, gerenciando upload de PDFs, persistência no ChromaDB e geração de respostas aumentadas por recuperação.
- **`next-server` (PID 137835):** Servidor HTTP do Next.js responsável pela renderização da interface web e streaming SSE de respostas para o cliente.

---

#### 2.6 Portas e Serviços Utilizados

| Porta | Protocolo | Endereço de Escuta | Serviço / Aplicação | Processo Associado (PID) | Finalidade no Ecossistema |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **11434** | TCP | `127.0.0.1:11434` | Ollama REST API | `ollama` (PID 5102) | Interface externa do servidor Ollama para geração de texto, embeddings e controle de modelos. |
| **36727** | TCP | `127.0.0.1:36727` | llama-server IPC | `llama-server` (PID 139562) | Porta de alta velocidade efêmera para troca de mensagens entre o daemon Ollama e o motor llama.cpp. |
| **8001** | TCP | `0.0.0.0:8001` | FastAPI Backend | `python3` (PID 137714/137717) | API REST principal do RAG, com documentação Swagger interativa em `/docs`. |
| **3000** | TCP | `:::3000` (IPv4/IPv6) | Next.js Frontend | `next-server` (PID 137835) | Interface gráfica com o usuário, chat com histórico e visualização de documentos. |
| **8501** | TCP | `0.0.0.0:8501` | Streamlit Admin | *(opcional)* `python3` | Interface administrativa complementar para testes de chunks e embeddings. |

---

#### 2.7 Logs, Erros e Avisos Relevantes

1. **Detecção e Seleção Automática de Hardware (Ollama):**
   - *Log:* `msg="dropping integrated GPU; to enable, set OLLAMA_IGPU_ENABLE=1" id=0 library=Vulkan compute=0.0 name=Vulkan0 description="Intel(R) Graphics (RPL-P)"`
   - *Log:* `msg="inference compute" id=0 library=CUDA compute=8.6 name=CUDA0 description="NVIDIA GeForce RTX 3050 6GB Laptop GPU" driver=13.2 total="5.7 GiB" available="5.5 GiB"`
   - *Interpretação:* O Ollama identificou a GPU integrada Intel Iris Xe e a desabilitou automaticamente para priorizar a GPU dedicada NVIDIA RTX 3050 (6GB GDDR6, arquitetura Ampere compute 8.6, CUDA 13.2).

2. **Alocação de Camadas e Desempenho de Inferência:**
   - *Log:* `msg="llama-server started in 4.13 seconds"`
   - *Log:* `prompt eval time = 17211.33 ms / 12 tokens`
   - *Log:* `eval time = 1146.86 ms / 70 tokens (61.04 tokens/s)`
   - *Interpretação:* Com 100% das camadas carregadas na VRAM, o modelo alcançou uma taxa de **61.04 tokens por segundo** na etapa de decodificação.

3. **Compatibilidade de Chat Template e Reasoning:**
   - *Log:* `srv init: chat template supports preserving reasoning, consider enabling it via --reasoning-preserve`
   - *Log:* `cmn common_conte: the context does not support partial sequence removal`
   - *Interpretação:* O modelo LFM2.5 possui suporte a blocos especiais de raciocínio interno (`<think>...<\think>`), formato mapeado pelo chat template do Ollama.

4. **Verificação de Saúde do Backend (`GET /api/v1/health`):**
   - *Resposta:* `{"status":"healthy","ollama_connected":true,"chromadb_collections":3,"total_pdfs":1}`
   - *Interpretação:* O backend conectou com êxito ao Ollama na porta 11434 e validou a integridade das 3 coleções ativas do ChromaDB.

5. **Aviso de Redirecionamento no Next.js:**
   - *Log:* `NEXT_REDIRECT ... Switched to client rendering because the server rendering errored: Error: NEXT_REDIRECT`
   - *Interpretação:* Mecanismo padrão do Next.js App Router ao redirecionar a rota `/` para uma nova sessão `/chat/[uuid]`.

---

### 3. Evidências dos Comandos Executados

<details>
<summary><strong>systemctl status ollama</strong></summary>

```text
● ollama.service - Ollama Service
     Loaded: loaded (/etc/systemd/system/ollama.service; enabled; preset: enabled)
     Active: active (running) since Sat 2026-09-12 10:32:40 -03; 24h ago
   Main PID: 5102 (ollama)
      Tasks: 16 (limit: 25579)
     Memory: 432.9M (peak: 685.7M)
        CPU: 11.323s
     CGroup: /system.slice/ollama.service
             └─5102 /usr/local/bin/ollama serve
```
</details>

<details>
<summary><strong>ollama list</strong></summary>

```text
$ ollama list
NAME                                    ID              SIZE      MODIFIED   
nomic-embed-text:latest                 0a109f422b47    274 MB    2 days ago    
hf.co/LiquidAI/LFM2.5-2.6B-GGUF:Q4_0    11e60e11c1d7    1.6 GB    2 days ago    
```
</details>

<details>
<summary><strong>ollama ps</strong></summary>

```text
$ ollama ps
NAME                                    ID              SIZE      PROCESSOR    CONTEXT    UNTIL              
hf.co/LiquidAI/LFM2.5-2.6B-GGUF:Q4_0    11e60e11c1d7    1.7 GB    100% GPU     4096       4 minutes from now
```
</details>

<details>
<summary><strong>nvidia-smi</strong></summary>

```text
$ nvidia-smi
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 595.84                 Driver Version: 595.84         CUDA Version: 13.2     |
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 3050 ...    Off |   00000000:01:00.0  On |                  N/A |
| N/A   49C    P0             10W /   50W |    1833MiB /   6144MiB |      3%      Default |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|    0   N/A  N/A          130866      G   /usr/lib/xorg/Xorg                       53MiB |
|    0   N/A  N/A          139562      C   ...local/lib/ollama/llama-server       1754MiB |
+-----------------------------------------------------------------------------------------+
```
</details>

<details>
<summary><strong>ss -tulpn (Portas e Serviços Ativos)</strong></summary>

```text
$ ss -tulpn | grep -E "11434|8001|3000|8501"
tcp   LISTEN 0      2048                       0.0.0.0:8001       0.0.0.0:*    users:(("python3",pid=137717,fd=3),("python3",pid=137714,fd=3))
tcp   LISTEN 0      4096                     127.0.0.1:11434      0.0.0.0:*    users:(("ollama",pid=5102,fd=3))
tcp   LISTEN 0      511                              *:3000             *:*    users:(("next-server (v1",pid=137835,fd=24))
```
</details>

<details>
<summary><strong>journalctl -u ollama (Download dos Modelos)</strong></summary>

```text
$ journalctl -u ollama --since "2026-09-10 16:02:20" --until "2026-09-10 16:05:35" --no-pager
set 10 16:02:26 bruno-Nitro-ANV15-51 ollama[4666]: time=2026-09-10T16:02:26.051-03:00 level=INFO source=download.go:179 msg="downloading e1a61bf937bc in 16 100 MB part(s)"
set 10 16:03:59 bruno-Nitro-ANV15-51 ollama[4666]: time=2026-09-10T16:03:59.920-03:00 level=INFO source=download.go:179 msg="downloading 30adf9d64781 in 1 10 KB part(s)"
set 10 16:04:01 bruno-Nitro-ANV15-51 ollama[4666]: time=2026-09-10T16:04:01.437-03:00 level=INFO source=download.go:179 msg="downloading a776233427f3 in 1 197 B part(s)"
set 10 16:04:02 bruno-Nitro-ANV15-51 ollama[4666]: time=2026-09-10T16:04:02.733-03:00 level=INFO source=download.go:179 msg="downloading d7ca051a8aac in 1 75 B part(s)"
set 10 16:04:04 bruno-Nitro-ANV15-51 ollama[4666]: time=2026-09-10T16:04:04.038-03:00 level=INFO source=download.go:179 msg="downloading 8d96ec5edf20 in 1 695 B part(s)"
set 10 16:04:09 bruno-Nitro-ANV15-51 ollama[4666]: [GIN] 2026/09/10 - 16:04:09 | 200 |         1m44s |       127.0.0.1 | POST     "/api/pull"
set 10 16:05:11 bruno-Nitro-ANV15-51 ollama[4666]: time=2026-09-10T16:05:11.980-03:00 level=INFO source=download.go:179 msg="downloading 970aa74c0a90 in 3 100 MB part(s)"
set 10 16:05:23 bruno-Nitro-ANV15-51 ollama[4666]: time=2026-09-10T16:05:23.526-03:00 level=INFO source=download.go:179 msg="downloading c71d239df917 in 1 11 KB part(s)"
set 10 16:05:25 bruno-Nitro-ANV15-51 ollama[4666]: time=2026-09-10T16:05:25.035-03:00 level=INFO source=download.go:179 msg="downloading ce4a164fc046 in 1 17 B part(s)"
set 10 16:05:26 bruno-Nitro-ANV15-51 ollama[4666]: time=2026-09-10T16:05:26.534-03:00 level=INFO source=download.go:179 msg="downloading 31df23ea7daa in 1 420 B part(s)"
set 10 16:05:28 bruno-Nitro-ANV15-51 ollama[4666]: [GIN] 2026/09/10 - 16:05:28 | 200 | 22.957278659s |       127.0.0.1 | POST     "/api/pull"
```
</details>

<details>
<summary><strong>du -sh (Espaço em Disco de Modelos e Aplicação)</strong></summary>

```text
$ du -sh /usr/local/bin/ollama /usr/local/lib/ollama /usr/share/ollama/.ollama/models
38M	/usr/local/bin/ollama
2,1G	/usr/local/lib/ollama
3,6G	/usr/share/ollama/.ollama/models

$ du -h --max-depth=1 /home/bruno/Desktop/trabalho-so/ollama_pdf_rag | sort -hr
3,6G	/home/bruno/Desktop/trabalho-so/ollama_pdf_rag
1,9G	/home/bruno/Desktop/trabalho-so/ollama_pdf_rag/venv
1,8G	/home/bruno/Desktop/trabalho-so/ollama_pdf_rag/web-ui
14M	/home/bruno/Desktop/trabalho-so/ollama_pdf_rag/data
2,4M	/home/bruno/Desktop/trabalho-so/ollama_pdf_rag/docs
312K	/home/bruno/Desktop/trabalho-so/ollama_pdf_rag/src
```
</details>

<details>
<summary><strong>curl /api/generate (Métricas de Carga e Inferência do Modelo Reservado)</strong></summary>

```json
$ curl -s http://localhost:11434/api/generate -d '{"model": "hf.co/LiquidAI/LFM2.5-2.6B-GGUF:Q4_0", "prompt": "Ola", "stream": false}'
{
  "model": "hf.co/LiquidAI/LFM2.5-2.6B-GGUF:Q4_0",
  "created_at": "2026-09-13T13:54:08.35247534Z",
  "response": "<think>...</think>Olá! Tudo bem? Como posso ajudar você hoje?",
  "done": true,
  "done_reason": "stop",
  "total_duration": 24725356923,
  "load_duration": 6358764843,
  "prompt_eval_count": 12,
  "prompt_eval_duration": 17211329000,
  "eval_count": 70,
  "eval_duration": 1146862000
}
```
</details>
