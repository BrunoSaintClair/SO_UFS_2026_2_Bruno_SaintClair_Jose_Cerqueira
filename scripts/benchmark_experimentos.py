#!/usr/bin/env python3
"""
Benchmark automatizado — Parte C: Experimentos Comparativos
============================================================
Sistemas Operacionais — Atividade 1 (AV1) | 2026.2

Executa três configurações de teste sobre o pipeline RAG (ollama_pdf_rag):
  - Configuração 1: Execução padrão (1 requisição sequencial)
  - Configuração 2: Concorrência controlada (N requisições simultâneas)
  - Configuração 3: Ajuste de execução local (GPU vs CPU)

Coleta métricas de: tempo total, tempo até 1ª resposta, tokens/s, CPU, RAM,
VRAM, processos, threads, erros e avaliação da resposta.

Uso:
    python3 scripts/benchmark_experimentos.py [--repeticoes N] [--output DIR]
"""

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# ─── Configuração Global ─────────────────────────────────────────────────────

API_BASE = "http://localhost:8001/api/v1"
OLLAMA_BASE = "http://localhost:11434"
MODELO_LLM = "hf.co/LiquidAI/LFM2.5-2.6B-GGUF:Q4_0"

# Perguntas de teste: curta e longa (dois tamanhos de entrada)
PERGUNTA_CURTA = "Qual é o tema principal do documento?"
PERGUNTA_LONGA = (
    "Analise detalhadamente o conteúdo do documento, identificando os principais "
    "argumentos apresentados pelo autor, as conclusões tiradas, e como os dados "
    "apresentados sustentam as afirmações feitas ao longo do texto. Inclua também "
    "quaisquer referências a outros trabalhos ou fontes externas mencionadas."
)

# Níveis de concorrência para Configuração 2
NIVEIS_CONCORRENCIA = [1, 4]

# Repetições padrão por configuração
REPETICOES_PADRAO = 3


# ─── Funções Utilitárias ─────────────────────────────────────────────────────

def timestamp_iso():
    """Retorna timestamp ISO 8601 atual."""
    return datetime.now().isoformat()


def coletar_metricas_sistema():
    """Coleta CPU, RAM, VRAM, processos e threads do sistema."""
    metricas = {}

    # CPU e RAM via /proc e free
    try:
        result = subprocess.run(
            ["free", "-b"], capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.strip().split("\n"):
            if line.startswith("Mem:"):
                parts = line.split()
                metricas["ram_total_bytes"] = int(parts[1])
                metricas["ram_usada_bytes"] = int(parts[2])
                metricas["ram_disponivel_bytes"] = int(parts[6]) if len(parts) > 6 else 0
    except Exception:
        pass

    # VRAM via nvidia-smi
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        parts = result.stdout.strip().split(",")
        if len(parts) >= 3:
            metricas["vram_usada_mib"] = int(parts[0].strip())
            metricas["vram_total_mib"] = int(parts[1].strip())
            metricas["gpu_utilizacao_pct"] = int(parts[2].strip())
    except Exception:
        pass

    # CPU utilizada (snapshot rápido via top)
    try:
        result = subprocess.run(
            ["grep", "-c", "^processor", "/proc/cpuinfo"],
            capture_output=True, text=True, timeout=5
        )
        metricas["cpu_nucleos_logicos"] = int(result.stdout.strip())

        # Load average
        with open("/proc/loadavg") as f:
            parts = f.read().split()
            metricas["load_avg_1m"] = float(parts[0])
            metricas["load_avg_5m"] = float(parts[1])
    except Exception:
        pass

    # Processos e threads dos componentes da aplicação
    try:
        result = subprocess.run(
            ["ps", "-eo", "pid,nlwp,rss,pcpu,comm", "--no-headers"],
            capture_output=True, text=True, timeout=5
        )
        total_threads = 0
        total_procs = 0
        componentes = {}
        for line in result.stdout.strip().split("\n"):
            parts = line.split()
            if len(parts) >= 5:
                comm = parts[4]
                if any(k in comm for k in ["ollama", "llama-server", "python3", "node", "next-server", "uvicorn"]):
                    pid = parts[0]
                    nlwp = int(parts[1])
                    rss_kb = int(parts[2])
                    pcpu = float(parts[3])
                    total_threads += nlwp
                    total_procs += 1
                    if comm not in componentes:
                        componentes[comm] = {"pids": 0, "threads": 0, "rss_kb": 0, "cpu_pct": 0.0}
                    componentes[comm]["pids"] += 1
                    componentes[comm]["threads"] += nlwp
                    componentes[comm]["rss_kb"] += rss_kb
                    componentes[comm]["cpu_pct"] += pcpu

        metricas["total_processos_app"] = total_procs
        metricas["total_threads_app"] = total_threads
        metricas["componentes"] = componentes
    except Exception:
        pass

    return metricas


def coletar_metricas_cpu_durante(duracao_s=2):
    """Coleta utilização média de CPU durante um período usando mpstat ou /proc/stat."""
    try:
        # Ler /proc/stat antes
        with open("/proc/stat") as f:
            line1 = f.readline()
        parts1 = [int(x) for x in line1.split()[1:]]

        time.sleep(duracao_s)

        with open("/proc/stat") as f:
            line2 = f.readline()
        parts2 = [int(x) for x in line2.split()[1:]]

        delta = [b - a for a, b in zip(parts1, parts2)]
        total = sum(delta)
        idle = delta[3] + (delta[4] if len(delta) > 4 else 0)  # idle + iowait
        cpu_pct = ((total - idle) / total * 100) if total > 0 else 0.0
        return round(cpu_pct, 2)
    except Exception:
        return None


def query_rag(pergunta, modelo=MODELO_LLM):
    """Envia query ao pipeline RAG e retorna resposta + métricas de tempo."""
    import urllib.request
    import urllib.error

    payload = json.dumps({
        "question": pergunta,
        "model": modelo
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{API_BASE}/query",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    t_inicio = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            t_primeira_resposta = time.perf_counter()
            body = resp.read()
            t_fim = time.perf_counter()
            data = json.loads(body)
            return {
                "sucesso": True,
                "tempo_total_s": round(t_fim - t_inicio, 4),
                "tempo_primeira_resposta_s": round(t_primeira_resposta - t_inicio, 4),
                "resposta_tamanho": len(data.get("answer", "")),
                "resposta_preview": data.get("answer", "")[:300],
                "fontes": len(data.get("sources", [])),
                "chunks_recuperados": data.get("metadata", {}).get("chunks_retrieved", 0),
                "passos_raciocinio": len(data.get("metadata", {}).get("reasoning_steps", [])),
                "erro": None
            }
    except urllib.error.HTTPError as e:
        t_fim = time.perf_counter()
        return {
            "sucesso": False,
            "tempo_total_s": round(t_fim - t_inicio, 4),
            "tempo_primeira_resposta_s": None,
            "resposta_tamanho": 0,
            "resposta_preview": "",
            "fontes": 0,
            "chunks_recuperados": 0,
            "passos_raciocinio": 0,
            "erro": f"HTTP {e.code}: {e.reason}"
        }
    except Exception as e:
        t_fim = time.perf_counter()
        return {
            "sucesso": False,
            "tempo_total_s": round(t_fim - t_inicio, 4),
            "tempo_primeira_resposta_s": None,
            "resposta_tamanho": 0,
            "resposta_preview": "",
            "fontes": 0,
            "chunks_recuperados": 0,
            "passos_raciocinio": 0,
            "erro": str(e)
        }


def query_ollama_direto(prompt, modelo=MODELO_LLM, num_ctx=4096):
    """Query direta ao Ollama para medir tokens/s com precisão."""
    import urllib.request

    payload = json.dumps({
        "model": modelo,
        "prompt": prompt,
        "stream": False,
        "options": {"num_ctx": num_ctx}
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{OLLAMA_BASE}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    t_inicio = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            body = resp.read()
            t_fim = time.perf_counter()
            data = json.loads(body)
            eval_count = data.get("eval_count", 0)
            eval_duration_ns = data.get("eval_duration", 1)
            prompt_eval_count = data.get("prompt_eval_count", 0)
            load_duration_ns = data.get("load_duration", 0)
            tokens_por_segundo = (eval_count / (eval_duration_ns / 1e9)) if eval_duration_ns > 0 else 0

            return {
                "sucesso": True,
                "tempo_total_s": round(t_fim - t_inicio, 4),
                "tokens_gerados": eval_count,
                "tokens_prompt": prompt_eval_count,
                "tokens_por_segundo": round(tokens_por_segundo, 2),
                "tempo_carga_modelo_s": round(load_duration_ns / 1e9, 4),
                "resposta_preview": data.get("response", "")[:300],
                "erro": None
            }
    except Exception as e:
        t_fim = time.perf_counter()
        return {
            "sucesso": False,
            "tempo_total_s": round(t_fim - t_inicio, 4),
            "tokens_gerados": 0,
            "tokens_prompt": 0,
            "tokens_por_segundo": 0,
            "tempo_carga_modelo_s": 0,
            "resposta_preview": "",
            "erro": str(e)
        }


def medir_inicializacao_ollama():
    """Mede tempo de carga do modelo no Ollama (cold start)."""
    import urllib.request

    # Descarregar modelo da memória primeiro
    try:
        payload = json.dumps({"model": MODELO_LLM, "keep_alive": 0}).encode("utf-8")
        req = urllib.request.Request(
            f"{OLLAMA_BASE}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=30)
        time.sleep(3)  # Esperar descarregamento
    except Exception:
        pass

    # Agora medir cold start
    return query_ollama_direto("Olá", modelo=MODELO_LLM)


def avaliar_resposta(resposta_preview, pergunta):
    """Avaliação simples e explícita da qualidade da resposta."""
    if not resposta_preview or len(resposta_preview.strip()) < 10:
        return "INADEQUADA — resposta vazia ou muito curta"

    # Verificar se contém conteúdo relevante (não é apenas tokens de raciocínio)
    texto_limpo = re.sub(r"<think>.*?</think>", "", resposta_preview, flags=re.DOTALL).strip()
    if len(texto_limpo) < 10:
        return "INADEQUADA — apenas bloco de raciocínio sem resposta"

    # Verificar coerência mínima: resposta tem palavras reais
    palavras = texto_limpo.split()
    if len(palavras) < 3:
        return "INADEQUADA — resposta com menos de 3 palavras"

    # Verificar se não é erro/recusa
    recusas = ["não posso", "i cannot", "error", "erro", "sorry", "desculpe"]
    for r in recusas:
        if r.lower() in texto_limpo.lower():
            return f"PARCIAL — possível recusa detectada ('{r}')"

    return "ADEQUADA — resposta coerente e contextualizada"


def configurar_ollama_cpu():
    """Configura Ollama para executar em CPU (CUDA_VISIBLE_DEVICES vazio)."""
    try:
        # Parar o serviço
        subprocess.run(["sudo", "systemctl", "stop", "ollama"], timeout=10, capture_output=True)
        time.sleep(2)

        # Configurar override para CPU-only
        override_dir = "/etc/systemd/system/ollama.service.d"
        override_file = f"{override_dir}/cpu-only.conf"
        subprocess.run(["sudo", "mkdir", "-p", override_dir], timeout=5, capture_output=True)
        subprocess.run(
            ["sudo", "bash", "-c", f'echo -e "[Service]\\nEnvironment=CUDA_VISIBLE_DEVICES=" > {override_file}'],
            timeout=5, capture_output=True
        )
        subprocess.run(["sudo", "systemctl", "daemon-reload"], timeout=10, capture_output=True)
        subprocess.run(["sudo", "systemctl", "start", "ollama"], timeout=10, capture_output=True)
        time.sleep(5)  # Esperar inicialização

        # Verificar se Ollama está respondendo
        import urllib.request
        for _ in range(10):
            try:
                urllib.request.urlopen(f"{OLLAMA_BASE}/api/tags", timeout=5)
                return True
            except Exception:
                time.sleep(2)
        return False
    except Exception as e:
        print(f"  ⚠ Erro ao configurar CPU: {e}")
        return False


def restaurar_ollama_gpu():
    """Restaura Ollama para execução com GPU."""
    try:
        override_file = "/etc/systemd/system/ollama.service.d/cpu-only.conf"
        subprocess.run(["sudo", "rm", "-f", override_file], timeout=5, capture_output=True)
        subprocess.run(["sudo", "systemctl", "daemon-reload"], timeout=10, capture_output=True)
        subprocess.run(["sudo", "systemctl", "restart", "ollama"], timeout=10, capture_output=True)
        time.sleep(5)

        import urllib.request
        for _ in range(10):
            try:
                urllib.request.urlopen(f"{OLLAMA_BASE}/api/tags", timeout=5)
                return True
            except Exception:
                time.sleep(2)
        return False
    except Exception as e:
        print(f"  ⚠ Erro ao restaurar GPU: {e}")
        return False


# ─── Execução dos Experimentos ───────────────────────────────────────────────

def executar_configuracao_1(repeticoes, resultados):
    """Configuração 1 — Execução padrão (sequencial, 1 requisição por vez)."""
    print("\n" + "=" * 70)
    print("📋 CONFIGURAÇÃO 1 — Execução Padrão")
    print("=" * 70)
    print(f"   Modelo: {MODELO_LLM}")
    print(f"   Modo: sequencial, 1 requisição por vez")
    print(f"   Repetições: {repeticoes}")
    print(f"   Perguntas: curta + longa\n")

    # Medir inicialização (cold start)
    print("  ⏱ Medindo cold start do modelo...")
    cold_start = medir_inicializacao_ollama()
    resultados["config_1"]["cold_start"] = cold_start
    print(f"    → Tempo carga: {cold_start['tempo_carga_modelo_s']}s | "
          f"Tokens/s: {cold_start['tokens_por_segundo']}")

    for tipo_pergunta, pergunta in [("curta", PERGUNTA_CURTA), ("longa", PERGUNTA_LONGA)]:
        print(f"\n  📝 Pergunta {tipo_pergunta}: \"{pergunta[:60]}...\"")

        for rep in range(1, repeticoes + 1):
            print(f"    Repetição {rep}/{repeticoes}...", end=" ", flush=True)

            # Coletar métricas ANTES
            metricas_antes = coletar_metricas_sistema()

            # Executar query RAG
            resultado_rag = query_rag(pergunta)

            # Coletar métricas DEPOIS
            metricas_depois = coletar_metricas_sistema()

            # Query direta ao Ollama para tokens/s preciso
            resultado_ollama = query_ollama_direto(pergunta)

            # Avaliar resposta
            avaliacao = avaliar_resposta(resultado_rag["resposta_preview"], pergunta)

            registro = {
                "configuracao": "1_padrao",
                "tipo_pergunta": tipo_pergunta,
                "repeticao": rep,
                "timestamp": timestamp_iso(),
                "rag": resultado_rag,
                "ollama_direto": resultado_ollama,
                "avaliacao": avaliacao,
                "metricas_sistema_antes": metricas_antes,
                "metricas_sistema_depois": metricas_depois,
            }

            resultados["config_1"]["testes"].append(registro)
            status = "✅" if resultado_rag["sucesso"] else "❌"
            print(f"{status} RAG={resultado_rag['tempo_total_s']}s | "
                  f"Ollama={resultado_ollama['tokens_por_segundo']}tok/s | "
                  f"{avaliacao[:30]}")

            time.sleep(2)  # Cooldown entre repetições


def executar_configuracao_2(repeticoes, resultados):
    """Configuração 2 — Concorrência controlada (N requisições simultâneas)."""
    print("\n" + "=" * 70)
    print("📋 CONFIGURAÇÃO 2 — Concorrência Controlada")
    print("=" * 70)
    print(f"   Modelo: {MODELO_LLM}")
    print(f"   Níveis de concorrência: {NIVEIS_CONCORRENCIA}")
    print(f"   Repetições: {repeticoes}")
    print(f"   Perguntas: curta + longa\n")

    for nivel in NIVEIS_CONCORRENCIA:
        for tipo_pergunta, pergunta in [("curta", PERGUNTA_CURTA), ("longa", PERGUNTA_LONGA)]:
            print(f"\n  🔄 Concorrência={nivel} | Pergunta {tipo_pergunta}")

            for rep in range(1, repeticoes + 1):
                print(f"    Repetição {rep}/{repeticoes}...", end=" ", flush=True)

                metricas_antes = coletar_metricas_sistema()
                t_lote_inicio = time.perf_counter()

                # Disparar N requisições simultâneas
                resultados_paralelos = []
                with ThreadPoolExecutor(max_workers=nivel) as executor:
                    futures = {
                        executor.submit(query_rag, pergunta): i
                        for i in range(nivel)
                    }
                    for future in as_completed(futures):
                        resultados_paralelos.append(future.result())

                t_lote_fim = time.perf_counter()
                metricas_depois = coletar_metricas_sistema()

                # Agregar métricas do lote
                tempos = [r["tempo_total_s"] for r in resultados_paralelos if r["sucesso"]]
                sucessos = sum(1 for r in resultados_paralelos if r["sucesso"])
                erros = sum(1 for r in resultados_paralelos if not r["sucesso"])

                registro = {
                    "configuracao": "2_concorrencia",
                    "nivel_concorrencia": nivel,
                    "tipo_pergunta": tipo_pergunta,
                    "repeticao": rep,
                    "timestamp": timestamp_iso(),
                    "tempo_lote_total_s": round(t_lote_fim - t_lote_inicio, 4),
                    "tempo_medio_req_s": round(sum(tempos) / len(tempos), 4) if tempos else 0,
                    "tempo_min_req_s": round(min(tempos), 4) if tempos else 0,
                    "tempo_max_req_s": round(max(tempos), 4) if tempos else 0,
                    "requisicoes_total": nivel,
                    "requisicoes_sucesso": sucessos,
                    "requisicoes_erro": erros,
                    "resultados_individuais": resultados_paralelos,
                    "metricas_sistema_antes": metricas_antes,
                    "metricas_sistema_depois": metricas_depois,
                }

                avaliacoes = [avaliar_resposta(r["resposta_preview"], pergunta)
                              for r in resultados_paralelos if r["sucesso"]]
                registro["avaliacoes"] = avaliacoes

                resultados["config_2"]["testes"].append(registro)
                print(f"{'✅' if erros == 0 else '⚠'} Lote={registro['tempo_lote_total_s']}s | "
                      f"Média={registro['tempo_medio_req_s']}s | "
                      f"Sucesso={sucessos}/{nivel}")

                time.sleep(3)  # Cooldown maior para concorrência


def executar_configuracao_3(repeticoes, resultados):
    """Configuração 3 — GPU vs CPU (ajuste de execução local)."""
    print("\n" + "=" * 70)
    print("📋 CONFIGURAÇÃO 3 — GPU vs CPU")
    print("=" * 70)
    print(f"   Modelo: {MODELO_LLM}")
    print(f"   Comparação: GPU (padrão) vs CPU-only")
    print(f"   Repetições: {repeticoes}")
    print(f"   Perguntas: curta + longa\n")

    for modo, label in [("gpu", "GPU (padrão)"), ("cpu", "CPU-only")]:
        print(f"\n  🖥 Modo: {label}")

        if modo == "cpu":
            print("    Reconfigurando Ollama para CPU-only...")
            ok = configurar_ollama_cpu()
            if not ok:
                print("    ❌ Falha ao configurar CPU-only. Pulando...")
                resultados["config_3"]["erro_cpu"] = "Falha ao reconfigurar para CPU"
                continue
            time.sleep(3)

        # Cold start neste modo
        print("    ⏱ Medindo cold start...")
        cold_start = medir_inicializacao_ollama()
        resultados["config_3"][f"cold_start_{modo}"] = cold_start
        print(f"      → Carga: {cold_start['tempo_carga_modelo_s']}s | "
              f"Tokens/s: {cold_start['tokens_por_segundo']}")

        for tipo_pergunta, pergunta in [("curta", PERGUNTA_CURTA), ("longa", PERGUNTA_LONGA)]:
            print(f"\n    📝 Pergunta {tipo_pergunta}")

            for rep in range(1, repeticoes + 1):
                print(f"      Repetição {rep}/{repeticoes}...", end=" ", flush=True)

                metricas_antes = coletar_metricas_sistema()
                resultado_rag = query_rag(pergunta)
                resultado_ollama = query_ollama_direto(pergunta)
                metricas_depois = coletar_metricas_sistema()
                avaliacao = avaliar_resposta(resultado_rag["resposta_preview"], pergunta)

                registro = {
                    "configuracao": "3_gpu_vs_cpu",
                    "modo": modo,
                    "tipo_pergunta": tipo_pergunta,
                    "repeticao": rep,
                    "timestamp": timestamp_iso(),
                    "rag": resultado_rag,
                    "ollama_direto": resultado_ollama,
                    "avaliacao": avaliacao,
                    "metricas_sistema_antes": metricas_antes,
                    "metricas_sistema_depois": metricas_depois,
                }

                resultados["config_3"]["testes"].append(registro)
                status = "✅" if resultado_rag["sucesso"] else "❌"
                print(f"{status} RAG={resultado_rag['tempo_total_s']}s | "
                      f"Ollama={resultado_ollama['tokens_por_segundo']}tok/s | "
                      f"{avaliacao[:30]}")

                time.sleep(2)

        if modo == "cpu":
            print("\n    🔄 Restaurando Ollama para GPU...")
            restaurar_ollama_gpu()
            time.sleep(5)


def gerar_csv_resumo(resultados, output_dir):
    """Gera CSV resumido com todas as métricas para facilitar tabulação."""
    csv_path = os.path.join(output_dir, "resultados_resumo.csv")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Configuração", "Modo/Concorrência", "Tipo Pergunta", "Repetição",
            "Tempo RAG Total (s)", "Tempo 1ª Resposta (s)", "Tokens/s (Ollama)",
            "Tokens Gerados", "Tempo Carga Modelo (s)",
            "RAM Usada Antes (MiB)", "RAM Usada Depois (MiB)",
            "VRAM Usada Antes (MiB)", "VRAM Usada Depois (MiB)",
            "GPU Util Depois (%)", "Threads App Depois",
            "Sucesso", "Avaliação", "Erro"
        ])

        # Config 1
        for t in resultados["config_1"]["testes"]:
            writer.writerow([
                "1 — Padrão", "Sequencial", t["tipo_pergunta"], t["repeticao"],
                t["rag"]["tempo_total_s"], t["rag"]["tempo_primeira_resposta_s"],
                t["ollama_direto"]["tokens_por_segundo"], t["ollama_direto"]["tokens_gerados"],
                t["ollama_direto"]["tempo_carga_modelo_s"],
                round(t["metricas_sistema_antes"].get("ram_usada_bytes", 0) / 1048576),
                round(t["metricas_sistema_depois"].get("ram_usada_bytes", 0) / 1048576),
                t["metricas_sistema_antes"].get("vram_usada_mib", "N/A"),
                t["metricas_sistema_depois"].get("vram_usada_mib", "N/A"),
                t["metricas_sistema_depois"].get("gpu_utilizacao_pct", "N/A"),
                t["metricas_sistema_depois"].get("total_threads_app", "N/A"),
                t["rag"]["sucesso"], t["avaliacao"], t["rag"]["erro"] or ""
            ])

        # Config 2
        for t in resultados["config_2"]["testes"]:
            writer.writerow([
                "2 — Concorrência", f"N={t['nivel_concorrencia']}", t["tipo_pergunta"], t["repeticao"],
                t["tempo_lote_total_s"], t["tempo_medio_req_s"],
                "N/A (lote)", "N/A",
                "N/A",
                round(t["metricas_sistema_antes"].get("ram_usada_bytes", 0) / 1048576),
                round(t["metricas_sistema_depois"].get("ram_usada_bytes", 0) / 1048576),
                t["metricas_sistema_antes"].get("vram_usada_mib", "N/A"),
                t["metricas_sistema_depois"].get("vram_usada_mib", "N/A"),
                t["metricas_sistema_depois"].get("gpu_utilizacao_pct", "N/A"),
                t["metricas_sistema_depois"].get("total_threads_app", "N/A"),
                f"{t['requisicoes_sucesso']}/{t['requisicoes_total']}",
                "; ".join(t.get("avaliacoes", [])),
                f"{t['requisicoes_erro']} erros" if t['requisicoes_erro'] > 0 else ""
            ])

        # Config 3
        for t in resultados["config_3"]["testes"]:
            writer.writerow([
                "3 — GPU vs CPU", t["modo"].upper(), t["tipo_pergunta"], t["repeticao"],
                t["rag"]["tempo_total_s"], t["rag"]["tempo_primeira_resposta_s"],
                t["ollama_direto"]["tokens_por_segundo"], t["ollama_direto"]["tokens_gerados"],
                t["ollama_direto"]["tempo_carga_modelo_s"],
                round(t["metricas_sistema_antes"].get("ram_usada_bytes", 0) / 1048576),
                round(t["metricas_sistema_depois"].get("ram_usada_bytes", 0) / 1048576),
                t["metricas_sistema_antes"].get("vram_usada_mib", "N/A"),
                t["metricas_sistema_depois"].get("vram_usada_mib", "N/A"),
                t["metricas_sistema_depois"].get("gpu_utilizacao_pct", "N/A"),
                t["metricas_sistema_depois"].get("total_threads_app", "N/A"),
                t["rag"]["sucesso"], t["avaliacao"], t["rag"]["erro"] or ""
            ])

    print(f"\n  📄 CSV gerado: {csv_path}")
    return csv_path


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Benchmark — Parte C: Experimentos Comparativos")
    parser.add_argument("--repeticoes", type=int, default=REPETICOES_PADRAO,
                        help=f"Número de repetições por configuração (padrão: {REPETICOES_PADRAO})")
    parser.add_argument("--output", type=str, default="scripts/resultados",
                        help="Diretório de saída para resultados (padrão: scripts/resultados)")
    parser.add_argument("--skip-config3", action="store_true",
                        help="Pular Configuração 3 (GPU vs CPU, requer sudo)")
    args = parser.parse_args()

    output_dir = os.path.join("/home/bruno/Desktop/trabalho-so", args.output)
    os.makedirs(output_dir, exist_ok=True)

    print("╔" + "═" * 68 + "╗")
    print("║  BENCHMARK — Parte C: Experimentos Comparativos                    ║")
    print("║  Sistemas Operacionais — AV1 | 2026.2                              ║")
    print("╚" + "═" * 68 + "╝")
    print(f"\n  Modelo LLM:    {MODELO_LLM}")
    print(f"  Repetições:    {args.repeticoes}")
    print(f"  Saída:         {output_dir}")
    print(f"  Início:        {timestamp_iso()}")

    resultados = {
        "metadata": {
            "modelo": MODELO_LLM,
            "repeticoes": args.repeticoes,
            "perguntas": {"curta": PERGUNTA_CURTA, "longa": PERGUNTA_LONGA},
            "niveis_concorrencia": NIVEIS_CONCORRENCIA,
            "inicio": timestamp_iso(),
            "maquina": {}
        },
        "config_1": {"testes": []},
        "config_2": {"testes": []},
        "config_3": {"testes": []}
    }

    # Coletar info da máquina
    resultados["metadata"]["maquina"] = coletar_metricas_sistema()

    # Espaço em disco dos modelos
    try:
        result = subprocess.run(
            ["du", "-sh", "/usr/share/ollama/.ollama/models"],
            capture_output=True, text=True, timeout=10
        )
        resultados["metadata"]["espaco_modelos"] = result.stdout.strip().split("\t")[0]
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["du", "-sh", "/home/bruno/Desktop/trabalho-so/ollama_pdf_rag/data/vectors"],
            capture_output=True, text=True, timeout=10
        )
        resultados["metadata"]["espaco_vetores"] = result.stdout.strip().split("\t")[0]
    except Exception:
        pass

    # ── Executar Configurações ────────────────────────────────────────────
    executar_configuracao_1(args.repeticoes, resultados)
    executar_configuracao_2(args.repeticoes, resultados)

    if not args.skip_config3:
        executar_configuracao_3(args.repeticoes, resultados)
    else:
        print("\n⏭ Configuração 3 pulada (--skip-config3)")

    resultados["metadata"]["fim"] = timestamp_iso()

    # ── Salvar Resultados ─────────────────────────────────────────────────
    json_path = os.path.join(output_dir, "resultados_completos.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n  📄 JSON gerado: {json_path}")

    gerar_csv_resumo(resultados, output_dir)

    print(f"\n✅ Benchmark completo! Duração total: {resultados['metadata']['inicio']} → {resultados['metadata']['fim']}")
    print(f"   Resultados em: {output_dir}/")


if __name__ == "__main__":
    main()
