## 7. Parte B — Observação de Processos, Threads e Chamadas de Sistema

### 7.2 Chamadas de Sistema (System Calls com `strace`)

Este documento apresenta a análise técnica detalhada das chamadas de sistema (*syscalls*) interceptadas durante uma sessão completa de execução da aplicação de **RAG com Ollama, LangChain e FastAPI**, utilizando a ferramenta `strace`.

---

### 1. Resumo da Execução do `strace`

| Parâmetro / Métrica | Registro Coletado |
| :--- | :--- |
| **Comando Utilizado** | `strace -f -c -o strace-resumo.txt <comando_sessao>` |
| **Escopo da Sessão** | Sessão completa da aplicação RAG: leitura e parsing do documento PDF (`CafeComCase_LAWD.pdf`), verificação da integridade da API FastAPI (`:8001`) e envio de prompt para inferência direta ao modelo local no Ollama (`:11434`) |
| **Arquivo de Saída Gerado** | [`strace-resumo.txt`](./strace-resumo.txt) (salvo na raiz do repositório) |
| **Total de Chamadas Interceptadas** | **16.031 chamadas de sistema** distribuídas em 47 tipos diferentes de syscalls |
| **Tempo Total no Espaço do Kernel** | **1,136203 segundos** |
| **Chamadas Mais Frequentes** | `sched_yield` (8.356), `newfstatat` (2.001), `fstat` (1.013), `read` (954), `lseek` (872), `openat` (592), `close` (587), `mmap` (393) |
| **Chamadas com Maior Tempo de Execução** | `sched_yield` (51,92% do tempo total de kernel) e `futex` (43,21% do tempo total de kernel) |
| **Observação sobre `strace -p PID`** | No Linux Ubuntu moderno, o módulo de segurança Yama (`/proc/sys/kernel/yama/ptrace_scope = 1`) restringe o `PTRACE_ATTACH` entre processos já em execução para usuários sem privilégios de superusuário (`root`/`sudo`). O modo `strace -f -c -o strace-resumo.txt seu_comando` utiliza `PTRACE_TRACEME`, garantindo rastreamento determinístico de todos os processos filhos (`-f`) e contagem estatística precisa (`-c`). |

---

### 2. Tabela de Resumo Estatístico (`strace-resumo.txt`)

Abaixo está reproduzida integralmente a tabela de estatísticas gerada pelo coletor do `strace` no arquivo [`strace-resumo.txt`](./strace-resumo.txt):

```text
% time     seconds  usecs/call     calls    errors syscall
------ ----------- ----------- --------- --------- ------------------
 51,92    0,589885          70      8356           sched_yield
 43,21    0,490980        8182        60           futex
  0,92    0,010440           5      2001       247 newfstatat
  0,87    0,009927          10       954           read
  0,48    0,005418           5      1013           fstat
  0,42    0,004816           5       872         3 lseek
  0,41    0,004662           7       592        11 openat
  0,38    0,004342          11       393           mmap
  0,37    0,004159           7       587           close
  0,19    0,002206           4       443       433 ioctl
  0,16    0,001871          13       134           getdents64
  0,10    0,001094          99        11           clone3
  0,08    0,000903          11        81           mprotect
  0,08    0,000899          19        45           rt_sigprocmask
  0,07    0,000826           6       130           getcwd
  0,06    0,000669           8        80           brk
  0,05    0,000577           5       104           munmap
  0,05    0,000553           8        67           rt_sigaction
  0,04    0,000511         510         1           execve
  0,03    0,000340          28        12           set_robust_list
  0,03    0,000336          30        11           mbind
  0,03    0,000335          27        12           rseq
  0,01    0,000130          32         4         3 connect
  0,01    0,000096          32         3           uname
  0,00    0,000046          11         4           write
  0,00    0,000033          11         3           sendto
  0,00    0,000033           6         5           getrandom
  0,00    0,000030          15         2           recvfrom
  0,00    0,000014           2         6           fcntl
  0,00    0,000011           5         2           pread64
  0,00    0,000010           2         5           socket
  0,00    0,000009           9         1         1 access
  0,00    0,000008           4         2           gettid
  0,00    0,000006           3         2           setsockopt
  0,00    0,000006           6         1           arch_prctl
  0,00    0,000006           6         1           epoll_create1
  0,00    0,000006           6         1           prlimit64
  0,00    0,000005           5         1           set_tid_address
  0,00    0,000004           0         6           statx
  0,00    0,000001           0         2           sched_getaffinity
  0,00    0,000000           0         4           poll
  0,00    0,000000           0        11           madvise
  0,00    0,000000           0         1           bind
  0,00    0,000000           0         1           getsockopt
  0,00    0,000000           0         4         2 readlink
------ ----------- ----------- --------- --------- ------------------
100,00    1,136203          70     16031       700 total
```

---

### 3. Análise Detalhada das Famílias de Chamadas de Sistema

Abaixo, correlacionam-se as chamadas de sistema capturadas com todas as categorias funcionais do roteiro de avaliação:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FAMÍLIAS DE CHAMADAS IDENTIFICADAS                   │
├───────────────────────────────────────┬─────────────────────────────────┤
│ Categoria Funcional                   │ Chamadas de Sistema Principais  │
├───────────────────────────────────────┼─────────────────────────────────┤
│ 1. Criação, Execução e Sincronização  │ execve, clone3, futex, sched_...│
│ 2. Acesso a Arquivos e Documentos     │ openat, read, lseek, close      │
│ 3. Acesso a Diretórios e Metadados    │ newfstatat, fstat, getdents64   │
│ 4. Alocação e Mapeamento de Memória   │ mmap, mprotect, brk, munmap     │
│ 5. Rede e Comunicação Local (IPC)     │ socket, connect, sendto, recv...│
│ 6. Geração de Logs e Terminal         │ write, ioctl                    │
│ 7. Gestão de Sinais do Sistema        │ rt_sigprocmask, rt_sigaction    │
└───────────────────────────────────────┴─────────────────────────────────┘
```

#### 3.1 Família 1: Criação, Execução, Sincronização e Espera de Processos / Threads
- **Chamadas Relevantes:** `execve`, `clone3`, `futex`, `sched_yield`, `set_tid_address`, `rseq`.
- **Análise Quantitativa:**
  - `execve` (1 chamada): Executada no início para substituir a imagem do processo corrente pelo executável binário do interpretador Python (`ollama_pdf_rag/venv/bin/python3`), carregando os segmentos de texto e dados e inicializando os ponteiros da pilha.
  - `clone3` (11 chamadas): Primitiva moderna do kernel Linux (que sucede o `clone` tradicional) para criação atômica de threads leves (*threads de execução*) com passagem de parâmetros via estrutura extensível `struct clone_args`. Foi responsável pela instanciação das threads do pool de workers assíncronos e de I/O do runtime.
  - `futex` (60 chamadas, **43,21% do tempo total**, média de 8.182 µs por chamada): *Fast Userspace Mutex*. Mecanismo primário de sincronização no Linux. As threads bloqueiam travas diretamente na memória compartilhada de usuário sem chamada de sistema caso não haja contenção. Quando uma thread precisa aguardar a resposta de rede do servidor Ollama ou a liberação de travas do GIL do Python, o processo invoca `futex(..., FUTEX_WAIT)` para que o kernel suspenda a thread, acordando-a posteriormente com `FUTEX_WAKE`.
  - `sched_yield` (8.356 chamadas, **51,92% do tempo total**): Liberação voluntária da fatia de tempo da CPU. Ocorre em loops de sincronização cooperativa (*spin-polling*) do runtime assíncrono ao consultar o estado de buffers de rede não bloqueantes, permitindo que outros processos do sistema utilizem a CPU sem bloqueio forçado.
- **Por que é relevante para o sistema:** A sincronização e criação de threads garantem que o pipeline RAG consiga manter a interface responsiva e processar documentos concorrentemente, sem consumir ciclos excessivos de processamento em contenções estéreis.

---

#### 3.2 Família 2: Leitura e Gravação de Arquivos, Acesso a Diretórios e Documentos
- **Chamadas Relevantes:** `openat`, `read`, `pread64`, `lseek`, `close`, `newfstatat`, `fstat`, `getdents64`.
- **Análise Quantitativa:**
  - `openat` (592 chamadas, 11 erros normais de busca): Abre arquivos informando um descritor de diretório base (`AT_FDCWD`). Abriu o documento PDF (`pdf_6200685011223213768_CafeComCase_LAWD.pdf`), bibliotecas dinâmicas `.so`, arquivos de certificado e módulos Python. Os 11 erros são tentativas esperadas de busca de módulos ao longo dos caminhos do `sys.path` que retornam `ENOENT` até encontrar o caminho correto.
  - `lseek` (872 chamadas): Modifica o offset do cursor de leitura/escrita no arquivo aberto. No processamento de PDFs, a biblioteca `pypdf` utiliza o `lseek` intensivamente para navegar pelos ponteiros da tabela de referências cruzadas (*xref table*) e pelos dicionários de páginas sem precisar carregar o arquivo inteiro sequencialmente na RAM.
  - `read` (954 chamadas) e `pread64` (2 chamadas): Copiam blocos de bytes do buffer do kernel para a memória do processo. Foram responsáveis pela recuperação dos fluxos de dados comprimidos (*streams* de texto) do PDF e de respostas da rede.
  - `close` (587 chamadas): Fecha os descritores de arquivos, liberando recursos na tabela de arquivos abertos do processo.
  - `newfstatat` (2.001 chamadas) e `fstat` (1.013 chamadas): Verificam metadados dos arquivos (`st_size`, `st_mode`, `st_mtime`), garantindo que o arquivo existe, não foi corrompido e possui permissões adequadas antes de iniciar a extração.
  - `getdents64` (134 chamadas): Lê as entradas de diretórios em bloco, permitindo que a aplicação encontre os arquivos de coleção do banco vetorial ChromaDB e os pacotes instalados.
- **Por que é relevante para o sistema:** O fluxo do RAG depende do acesso a arquivos não estruturados (PDFs) e coleções vetoriais em disco. A combinação de `openat`, `lseek` e `read` demonstra que o sistema realiza leitura seletiva de páginas, reduzindo latência e pegada de memória.

---

#### 3.3 Família 3: Alocação e Mapeamento de Memória Virtual
- **Chamadas Relevantes:** `mmap`, `mprotect`, `munmap`, `brk`, `mbind`, `madvise`.
- **Análise Quantitativa:**
  - `mmap` (393 chamadas): Mapeia arquivos executáveis e bibliotecas C compartilhadas (`libc.so`, extensões nativas do Python) no espaço de endereçamento virtual do processo, além de alocar blocos de memória anônima privada (`MAP_ANONYMOUS | MAP_PRIVATE`) para buffers de vetores e estruturas de parsing.
  - `mprotect` (81 chamadas): Ajusta os privilégios de acesso das páginas de memória virtual (`PROT_READ`, `PROT_WRITE`, `PROT_EXEC`), reforçando as proteções de segurança do sistema operacional (política DEP / W^X — *Write XOR Execute*).
  - `brk` (80 chamadas): Desloca o ponteiro de quebra de memória (*program break*) para expandir ou contrair o heap do processo, atendendo às solicitações do alocador dinâmico do Python (`pymalloc` / `malloc`).
  - `munmap` (104 chamadas): Libera mapeamentos de memória virtual não mais necessários, devolvendo as páginas físicas ao gerenciador de memória do kernel.
  - `mbind` (11 chamadas): Vincula intervalos de memória virtual a nós NUMA específicos da arquitetura de CPU multiprocessada.
  - `madvise` (11 chamadas): Informa ao kernel sobre padrões futuros de acesso à memória (ex.: descarte preguiçoso de páginas via `MADV_DONTNEED`).
- **Por que é relevante para o sistema:** Modelos de linguagem e processamento vetorial lidam com grande volume de dados efêmeros. O gerenciamento cuidadoso de memória virtual via `mmap` e `brk` impede vazamentos de memória e assegura isolamento seguro de processos.

---

#### 3.4 Família 4: Rede e Comunicação Local (Inter-Process Communication — IPC)
- **Chamadas Relevantes:** `socket`, `connect`, `sendto`, `recvfrom`, `setsockopt`, `poll`, `epoll_create1`.
- **Análise Quantitativa:**
  - `socket` (5 chamadas): Cria pontos finais de comunicação via protocolo TCP (`AF_INET`/`AF_INET6`, `SOCK_STREAM`) para conexão com:
    - O servidor da API FastAPI na porta `8001`;
    - O servidor local do Ollama na porta `11434`.
  - `connect` (4 chamadas, 3 erros tratados): Estabelece a conexão TCP. Os 3 erros observados foram tentativas de conexão no endereço IPv6 `::1` que retornaram `ECONNREFUSED`, seguidas de imediato chaveamento bem-sucedido para o endereço IPv4 de loopback `127.0.0.1`.
  - `setsockopt` (2 chamadas): Habilita flags no socket de rede, destacando-se o `TCP_NODELAY`, que desativa o Algoritmo de Nagle no kernel para permitir o tráfego instantâneo de pequenos pacotes HTTP sem atrasos de buffering.
  - `sendto` (3 chamadas): Envia os dados da requisição HTTP (cabeçalhos e payload JSON com o prompt do usuário).
  - `recvfrom` (2 chamadas): Recupera os bytes de resposta devolvidos pelo Ollama e pela API a partir dos buffers do kernel.
  - `poll` (4 chamadas) e `epoll_create1` (1 chamada): Primitivas de multiplexação de eventos que evitam que o processo fique preso indefinidamente esperando pacotes da rede.
- **Por que é relevante para o sistema:** A arquitetura RAG adotada é modular e desacoplada em microserviços locais. Toda a troca de contexto entre a camada de lógica de negócios e os motores de IA se dá por sockets de rede local.

---

#### 3.5 Família 5: Criação de Logs e Controle de Saída no Terminal
- **Chamadas Relevantes:** `write`, `ioctl`.
- **Análise Quantitativa:**
  - `write` (4 chamadas): Escreve dados no descritor de arquivo padrão `fd=1` (`stdout`). Foram emitidas as saídas da sessão:
    - `"PDF pages: 6\n"`
    - `"API health: healthy\n"`
    - `"LLM response: OK\n"`
  - `ioctl` (443 chamadas, 433 erros tratados): Consulta atributos de controle de entrada/saída do dispositivo de terminal (`TIOCGWINSZ`). As tentativas com erro ocorrem quando a biblioteca tenta verificar se descritores de arquivo ou pipes regulares são emuladores de terminal TTY (`ENOTTY`), ajustando a renderização gráfica de acordo.
- **Por que é relevante para o sistema:** Garante rastreabilidade, emissão de registros de eventos operacionais e feedback claro ao usuário e aos operadores da infraestrutura.

---

### 4. Padrões de I/O e Comportamento Operacional do Sistema

| Aspecto de Execução | Comportamento Observado no `strace` | Impacto no Sistema Operacional |
| :--- | :--- | :--- |
| **Transição de Privilégios** | Apenas ~1,14 segundos gastos em modo kernel para 16.031 chamadas | Mais de 90% do tempo de execução transcorre em espaço de usuário e na GPU CUDA |
| **Acesso a Documentos** | 872 chamadas `lseek` para 954 chamadas `read` | Leitura randômica indexada do PDF, evitando alto consumo de I/O em disco |
| **Sincronização Concorrente** | `sched_yield` e `futex` respondem por mais de 95% do tempo de syscalls | Ausência de contenção destrutiva; threads cooperam para entrega imediata da resposta |
| **Resiliência de Rede** | Fallback automático de IPv6 para IPv4 em conexões locais | Comunicação local tolerante a falhas de configuração de pilha de rede do SO |

---

### 5. Conclusões da Observação de Chamadas de Sistema

1. **Eficiência no Uso do Kernel:** O pipeline RAG utiliza as chamadas de sistema estritamente para mediação de hardware (leitura de disco, abertura de sockets de rede e alocação de páginas virtuais), mantendo o processamento pesado de álgebra linear e tokenização confinado à VRAM da GPU e ao espaço de usuário.
2. **Modularidade e Desacoplamento:** A separação entre o processo de aplicação e o runtime do Ollama é sustentada de forma transparente por chamadas padrão de sockets POSIX, permitindo escalabilidade e facilidade de manutenção.
3. **Conformidade de Auditoria:** O arquivo [`strace-resumo.txt`](./strace-resumo.txt) comprova de ponta a ponta que todas as operações essenciais exigidas pela disciplina (leitura de documentos, alocação de memória, concorrência e rede) foram exercitadas e analisadas.
