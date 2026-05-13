# Oficina de Imigrantes — Kreyòl Ayisyen ↔ Português

Sistema local que assiste vídeos do YouTube em kreyòl haitiano, transcreve, traduz para português e guarda num banco vetorial pesquisável.

## Como usar

1. **Adicionar vídeos pra processar**: edite `data/queue.txt` e coloque uma URL por linha (vídeo ou playlist).

2. **Rodar o processador (dia e noite)**: clique duas vezes em `iniciar_daemon.bat`. Ele varre a fila, baixa o áudio, transcreve com Whisper (kreyòl), traduz com NLLB-200 e indexa no ChromaDB. Roda em loop a cada 5 minutos.

3. **Abrir a interface de busca**: clique duas vezes em `iniciar_ui.bat`. Abre o navegador em `http://localhost:8501`.

## Arquitetura

```
queue.txt ──> daemon.py ──> pipeline.py ──┬─> download.py   (yt-dlp -> mp3)
                                          ├─> transcribe.py (faster-whisper, language=ht)
                                          ├─> translate.py  (NLLB-200, hat -> por)
                                          └─> embed_store.py (MiniLM + ChromaDB)
                                                       ▲
                                                       │ search
                                                  app.py (Streamlit UI)
```

## Stack

- **Python 3.14**
- **faster-whisper** (small, int8 CPU) — transcrição forçada em kreyòl
- **facebook/nllb-200-distilled-600M** — tradução kreyòl→português
- **paraphrase-multilingual-MiniLM-L12-v2** — embeddings multilíngues
- **ChromaDB** — banco vetorial persistente local
- **Streamlit** — UI web

## Estrutura de pastas

- `src/` — código Python
- `data/audio/` — mp3 baixados
- `data/transcripts/` — JSON com transcrições por vídeo
- `data/chroma/` — banco vetorial persistente
- `data/queue.txt` — URLs pra processar
- `data/processed.txt` — IDs já feitos (não reprocessa)
- `data/failed.txt` — IDs com falha

## Limitações conhecidas

- Whisper `small` tem ortografia kreyòl imperfeita. Upgrade para `medium` (`config.py: WHISPER_MODEL`) melhora mas é 3x mais lento.
- NLLB às vezes alucina em listas longas; o pipeline tenta mitigar splittando por vírgula.
- Busca por palavra em kreyòl puro ainda dá scores baixos (limitação do embedder multilíngue). Pesquisar em português dá resultados muito melhores.
