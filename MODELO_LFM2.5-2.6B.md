# Modelo LFM2.5-2.6B

## Identificação

**Nome completo:** LiquidAI/LFM2.5-2.6B

**Model Card:** https://huggingface.co/LiquidAI/LFM2.5-2.6B

**Repositório GGUF:** https://huggingface.co/LiquidAI/LFM2.5-2.6B-GGUF

## Especificações

| Característica | Informação |
|---|---|
| Família / arquitetura | LFM2.5 / LFM2 |
| Parâmetros | 2,69 bilhões (2.69B) |
| Variante utilizada | GGUF Q4_0 |
| Formato | GGUF |
| Quantização | Q4_0 (4 bits) |
| Licença | LFM Open License v1.0 |
| Janela de contexto | 131.072 tokens (128K) |
| Tamanho aproximado | 1,59 GB |
| Execução | Ollama |

## Utilização no projeto

O modelo LiquidAI/LFM2.5-2.6B foi utilizado como modelo de linguagem
(LLM) para geração das respostas do sistema RAG.

Para reduzir o consumo de memória e otimizar a execução local,
foi utilizada a versão quantizada Q4_0, no formato GGUF.

O modelo é executado localmente através do Ollama.

## Instalação

```bash
ollama pull hf.co/LiquidAI/LFM2.5-2.6B-GGUF:Q4_0

## Para executar

ollama run hf.co/LiquidAI/LFM2.5-2.6B-GGUF:Q4_0