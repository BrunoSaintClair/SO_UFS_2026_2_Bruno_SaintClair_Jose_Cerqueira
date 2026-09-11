## 6.1 Inventário do Ambiente

### 1. Resumo do Inventário

| Componente | Especificação Coletada |
| :--- | :--- |
| **Ambiente de Execução** | **Nativo (Bare-metal)** — Laptop Acer Nitro ANV15-51 |
| **Sistema Operacional** | **Ubuntu 24.04.3 LTS (Noble Numbat)** |
| **Versão do Kernel** | **Linux 7.0.0-31-generic** (x86_64) |
| **Processador (CPU)** | **13th Gen Intel(R) Core(TM) i5-13420H** |
| **Núcleos / Threads** | **8 núcleos físicos** (4 P-Cores + 4 E-Cores) / **12 threads** |
| **Memória RAM** | **23 GiB Total** (~12 GiB disponíveis, 4.0 GiB Swap) |
| **GPU Dedicada** | **NVIDIA GeForce RTX 3050 6GB Laptop GPU** |
| **VRAM** | **6144 MiB (6 GiB GDDR6)** \| Driver 595.84 \| CUDA 13.2 |
| **Armazenamento** | SSD NVMe 512 GB (5.3GB livres) |
| **Versão do Ollama** | **v0.32.0** |
| **Modelos de IA Locais** | `hf.co/LiquidAI/LFM2.5-2.6B-GGUF:Q4_0` (1.6 GB), `nomic-embed-text:latest` (274 MB)  |
| **Linguagens de Aplicação** | **Python 3.12.3** (Backend/RAG) e **Node.js v22.18.0 / pnpm 10.12.2** (Frontend Next.js) |

---

### 2. Detalhamento dos Componentes

#### 2.1 Sistema Operacional e Kernel
- **Distribuição:** Ubuntu 24.04.3 LTS (Noble Numbat)
- **ID / Base:** Debian-like (`ubuntu`)
- **Versão do Kernel:** `7.0.0-31-generic`
- **Compilação do Kernel:** `#31~24.04.1-Ubuntu SMP PREEMPT_DYNAMIC Mon Aug 10 09:38:02 UTC 2026`
- **Arquitetura:** `x86_64` (64 bits)

#### 2.2 Processador (CPU)
- **Modelo:** 13th Gen Intel(R) Core(TM) i5-13420H (Raptor Lake)
- **Arquitetura:** x86_64, Little Endian
- **Topologia de Núcleos:**
  - 8 núcleos físicos (4 núcleos de performance *P-cores* com Hyper-Threading + 4 núcleos de eficiência *E-cores*)
  - 12 threads lógicas no total (`nproc` = 12)
  - 1 socket
- **Frequências:** Mínima de 400 MHz, Máxima de até 4600 MHz (4.6 GHz)
- **Caches:**
  - L1d: 320 KiB (8 instâncias)
  - L1i: 384 KiB (8 instâncias)
  - L2: 7 MiB (5 instâncias)
  - L3: 12 MiB (1 instância compartilhada)
- **Virtualização de CPU:** Suporte a Intel VT-x ativo

#### 2.3 Memória RAM e Swap
- **Memória RAM Total:** 23 GiB (~24.5 GB)
- **Memória Usada:** ~10 GiB
- **Memória Livre:** ~1.2 GiB
- **Buffer / Cache:** ~12 GiB
- **Memória Disponível:** ~12 GiB
- **Swap Total:** 4.0 GiB (0 B em uso)

#### 2.4 GPU e VRAM
- **GPU Dedicada:** NVIDIA GeForce RTX 3050 6GB Laptop GPU
- **VRAM Total:** 6144 MiB (6 GiB GDDR6)
- **Versão do Driver NVIDIA:** 595.84
- **Versão da API CUDA:** 13.2
- **GPU Integrada:** Intel Corporation Raptor Lake-P [Iris Xe / UHD Graphics]

#### 2.5 Armazenamento em Disco
- **Dispositivo de Armazenamento Principal:** NVMe SSD de ~512 GB (`/dev/nvme0n1` com 476.9 GiB)
- **Partição Raiz do Sistema (`/dev/nvme0n1p5` montada em `/`):**
  - Capacidade: 111 GiB (112.4 GiB de partição)
  - Espaço Usado: 100 GiB (95% de ocupação)
  - Espaço Disponível: 5.3 GiB
- **Partição de Boot EFI (`/boot/efi` em `/dev/nvme0n1p1`):** 96 MiB (59 MiB livres)

#### 2.6 Ambiente de Execução
- **Tipo de Ambiente:** **Nativo (Bare-metal)**
- **Verificação:** Execução direta no hardware sem camada de virtualização ou contêiner (`systemd-detect-virt` retorna `none`).
- **Dispositivo Hospedeiro:** Notebook Acer Nitro ANV15-51 (BIOS/Firmware v1.60).

#### 2.7 Servidor Local de LLM (Ollama)
- **Versão do Ollama:** `0.32.0`
- **Modelos Locais Baixados:**
  - `hf.co/LiquidAI/LFM2.5-2.6B-GGUF:Q4_0` (1.6 GB) — Modelo principal de linguagem para tarefas de RAG
  - `nomic-embed-text:latest` (274 MB) — Modelo para geração de embeddings vetoriais
  - `qwen2.5-coder:3b` (1.9 GB) — Modelo adicional para tarefas de código

#### 2.8 Camada de Aplicação e Dependências

##### Backend (Python)
- **Versão da Linguagem:** Python 3.12.3
- **Ambiente Virtual:** Python Virtual Environment (`venv`) localizado em `ollama_pdf_rag/venv`
- **Principais Bibliotecas e Frameworks:**
  - **Framework Web / API:** `fastapi` (0.104.0+), `uvicorn` (0.52.4), `starlette` (1.6.0)
  - **Orquestração LLM / RAG:** `langchain` (1.0.0), `langchain-core` (1.6.2), `langchain-ollama` (1.0.1), `langchain-chroma` (1.1.0), `langchain-community` (0.4.1)
  - **Banco de Dados Vetorial & Relacional:** `chromadb` (0.4.22+), `sqlalchemy` (2.0.52), `aiosqlite` (0.19.0)
  - **Processamento de Documentos:** `pdfplumber` (0.11.8), `pdfminer.six` (20251107), `unstructured` (0.27.5), `pypdf` (6.18.0)
  - **Interface Administrativa Opcional:** `streamlit` (1.40.0)
  - **Validação de Dados:** `pydantic` (2.10.4)

##### Frontend (Next.js / Node.js)
- **Runtime:** Node.js v22.18.0
- **Gerenciador de Pacotes:** pnpm 10.12.2
- **Framework:** Next.js 16.0.10 (Turbopack)
- **Principais Dependências:**
  - `react` / `react-dom` (19.0.1)
  - `ai` (5.0.108), `@ai-sdk/react` (2.0.109)
  - `tailwindcss` (4.1.16)
  - `drizzle-orm` (0.34.1)

---

### 3. Evidências dos Comandos Executados

<details>
<summary><strong>uname -a</strong></summary>

```bash
$ uname -a
Linux bruno-Nitro-ANV15-51 7.0.0-31-generic #31~24.04.1-Ubuntu SMP PREEMPT_DYNAMIC Mon Aug 10 09:38:02 UTC 2 x86_64 x86_64 x86_64 GNU/Linux
```
</details>

<details>
<summary><strong>cat /etc/os-release</strong></summary>

```bash
$ cat /etc/os-release
PRETTY_NAME="Ubuntu 24.04.3 LTS"
NAME="Ubuntu"
VERSION_ID="24.04"
VERSION="24.04.3 LTS (Noble Numbat)"
VERSION_CODENAME=noble
ID=ubuntu
ID_LIKE=debian
HOME_URL="https://www.ubuntu.com/"
SUPPORT_URL="https://help.ubuntu.com/"
BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"
UBUNTU_CODENAME=noble
LOGO=ubuntu-logo
```
</details>

<details>
<summary><strong>lscpu</strong></summary>

```text
$ lscpu
Architecture:                x86_64
  CPU op-mode(s):            32-bit, 64-bit
  Address sizes:             39 bits physical, 48 bits virtual
  Byte Order:                Little Endian
CPU(s):                      12
  On-line CPU(s) list:       0-11
Vendor ID:                   GenuineIntel
  Model name:                13th Gen Intel(R) Core(TM) i5-13420H
    CPU family:              6
    Model:                   186
    Thread(s) per core:      2
    Core(s) per socket:      8
    Socket(s):               1
    Stepping:                2
    CPU(s) scaling MHz:      29%
    CPU max MHz:             4600,0000
    CPU min MHz:             400,0000
    BogoMIPS:                5222,40
Virtualization features:     
  Virtualization:            VT-x
Caches (sum of all):         
  L1d:                       320 KiB (8 instances)
  L1i:                       384 KiB (8 instances)
  L2:                        7 MiB (5 instances)
  L3:                        12 MiB (1 instance)
```
</details>

<details>
<summary><strong>nproc</strong></summary>

```bash
$ nproc
12
```
</details>

<details>
<summary><strong>free -h</strong></summary>

```text
$ free -h
               total        used        free      shared  buff/cache   available
Mem:            23Gi        10Gi       1,2Gi       915Mi        12Gi        12Gi
Swap:          4,0Gi          0B       4,0Gi
```
</details>

<details>
<summary><strong>df -h</strong></summary>

```text
$ df -h
Filesystem      Size  Used Avail Use% Mounted on
tmpfs           2,4G  3,7M  2,4G   1% /run
/dev/nvme0n1p5  111G  100G  5,3G  95% /
tmpfs            12G  110M   12G   1% /dev/shm
tmpfs           5,0M   12K  5,0M   1% /run/lock
efivarfs        268K  246K   18K  94% /sys/firmware/efi/efivars
tmpfs            12G     0   12G   0% /run/qemu
/dev/nvme0n1p1   96M   38M   59M  40% /boot/efi
tmpfs           2,4G  148K  2,4G   1% /run/user/1000
```
</details>

<details>
<summary><strong>lsblk</strong></summary>

```text
$ lsblk
NAME        MAJ:MIN RM   SIZE RO TYPE MOUNTPOINTS
nvme0n1     259:0    0 476,9G  0 disk 
├─nvme0n1p1 259:1    0   100M  0 part /boot/efi
├─nvme0n1p2 259:2    0    16M  0 part 
├─nvme0n1p3 259:3    0 342,7G  0 part 
├─nvme0n1p4 259:4    0   943M  0 part 
├─nvme0n1p5 259:5    0 112,4G  0 part /
└─nvme0n1p6 259:6    0    20G  0 part 
```
</details>

<details>
<summary><strong>nvidia-smi</strong></summary>

```text
$ nvidia-smi
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 595.84                 Driver Version: 595.84         CUDA Version: 13.2     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 3050 ...    Off |   00000000:01:00.0 Off |                  N/A |
| N/A   51C    P0             10W /   50W |       1MiB /   6144MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+
```
</details>

<details>
<summary><strong>ollama --version && ollama list</strong></summary>

```text
$ ollama --version
ollama version is 0.32.0

$ ollama list
NAME                                    ID              SIZE      MODIFIED     
nomic-embed-text:latest                 0a109f422b47    274 MB    23 hours ago    
hf.co/LiquidAI/LFM2.5-2.6B-GGUF:Q4_0    11e60e11c1d7    1.6 GB    23 hours ago    
qwen2.5-coder:3b                        f72c60cabf62    1.9 GB    5 days ago      
```
</details>

<details>
<summary><strong>systemd-detect-virt && hostnamectl</strong></summary>

```text
$ systemd-detect-virt
none

$ hostnamectl
 Static hostname: bruno-Nitro-ANV15-51
       Icon name: computer-laptop
         Chassis: laptop 💻
 Operating System: Ubuntu 24.04.3 LTS
          Kernel: Linux 7.0.0-31-generic
    Architecture: x86-64
 Hardware Vendor: Acer
  Hardware Model: Nitro ANV15-51
Firmware Version: V1.60
```
</details>
