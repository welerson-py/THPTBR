# Oficina de Imigrantes — Kreyòl Ayisyen ↔ Português

Sistema local de IA para workshop de imigrantes haitianos no Brasil. Processa vídeos do YouTube em kreyòl, transcreve, traduz para português, e oferece:

- **📚 Dicionário** vetorial com áudio (clica e ouve a professora nativa dizendo a palavra)
- **🎙️ Conversa ao vivo** via microfone (PT↔KR em tempo real)
- **🤝 Modo Imigrante** com botões grandes em kreyòl pra ele se virar sozinho

Tudo roda local, offline. Sem custos de API, sem dependência de internet durante o workshop.

---

## 🚀 Como usar (3 cliques)

1. **Adicionar vídeos pra processar**: edite `data/queue.txt`. Uma URL por linha (pode ser vídeo ou playlist completa).

2. **Processador batch ("treinar dia e noite")**: dois cliques em **`iniciar_daemon.bat`**. Ele:
   - Lê a `queue.txt`
   - Expande playlists, deduplica
   - Baixa áudio com yt-dlp
   - Transcreve com Whisper-medium (segmenta) + MMS-1B (texto fino em kreyòl)
   - Traduz em batch via NLLB-200 (8 frases por vez)
   - Indexa em ChromaDB com embeddings LaBSE (768d)
   - É **offline-friendly**: se faltar internet, pula downloads e segue processando o que tá no disco

3. **Interface web**: dois cliques em **`iniciar_ui.bat`** → abre `http://localhost:8501` no navegador.

---

## 🏗️ Arquitetura

```
┌──────────────┐
│  queue.txt   │
└──────┬───────┘
       │
       ▼
┌──────────────┐    ┌─────────────────────┐
│  daemon.py   │───►│ download.py (yt-dlp)│
└──────┬───────┘    └─────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────┐
│  pipeline.py  (orquestra os 4 passos)           │
├──────────────────────────────────────────────────┤
│  1. transcribe.py    Whisper-medium + MMS-1B    │
│  2. expand_segment   detecta pares de palavras  │
│  3. translate.py     NLLB batch + 4 camadas     │
│  4. embed_store.py   LaBSE + ChromaDB           │
└──────────────────────────────────────────────────┘
       ▲
       │ search
┌──────┴───────┐    ┌───────────────────────────┐
│   app.py     │───►│ conversa.py (mic ao vivo) │
│  (Streamlit) │───►│ tts.py (voz kreyòl)       │
└──────────────┘    └───────────────────────────┘
```

---

## 🧠 As 4 camadas de tradução (PT → KR)

Cada camada tem prioridade decrescente. A primeira que tiver match dispara, as outras nem rodam:

| # | Camada | O que faz | Onde fica |
|---|---|---|---|
| 1 | **Override exato** | "tansyon = pressão" → forçado pra "swaf = sede" | `data/correcoes.json` (editável!) |
| 2 | **Cultural direto** | "mamão com açúcar" → **"Se dlo kòk"** (água de coco, gíria HT) | `idiomas.py` IDIOMA_CULTURAL |
| 3 | **Reescrita de idiomatismo** | "Esse exercício é mamão com açúcar" → "Esse exercício é muito fácil" → NLLB | `idiomas.py` IDIOMA_REWRITES |
| 4 | **Calor pós-NLLB** | NLLB devolve "se trè fasil" → substitui pra "se dlo kòk" (mais quente) | `idiomas.py` WARMTH_KR |

A camada 4 é o "tempero" — transforma tradução técnica em tradução com alma de oficina.

---

## 🔍 Busca bidirecional (KR↔PT)

Quando o imigrante busca "achte" (kreyòl pra comprar):
1. Sistema procura "achte" direto no banco (vector + fuzzy)
2. **Em paralelo** traduz "achte"→"comprar" via NLLB e procura "comprar" também
3. Merge dos resultados, ranqueado por score combinado

Resultado: imigrante consegue achar coisas mesmo digitando só em kreyòl.

---

## ⚙️ Stack técnica

| Componente | Modelo | Tamanho | Por quê |
|---|---|---|---|
| ASR batch (segmentação) | `faster-whisper` medium int8 | 1.5 GB | VAD timestamps + transcrição PT/KR razoável |
| ASR batch (refino kreyòl) | `facebook/mms-1b-all` | 3.5 GB | Treinado especificamente em 1100+ línguas low-resource, melhor em kreyòl |
| ASR mic PT | `faster-whisper` small int8 | 480 MB | Rápido pra resposta interativa, PT excelente |
| ASR mic KR | MMS-1B | (já carregado) | Melhor qualidade pra fala de haitiano |
| Tradução KR↔PT | `facebook/nllb-200-distilled-600M` | 2.5 GB | Cobre kreyòl haitiano (`hat_Latn`) e PT (`por_Latn`) |
| Embeddings | `sentence-transformers/LaBSE` | 1.8 GB | 109 idiomas incluindo kreyòl. Score 0.7-0.95 em busca cross-lingual |
| TTS kreyòl | `facebook/mms-tts-hat` | 500 MB | Única opção offline com qualidade decente pra kreyòl |
| Vector DB | `chromadb` 1.5+ | ~ | Persistente local, HNSW cosine |
| UI | `streamlit` | ~ | Browser local, fácil de mostrar pra equipe |

**Total disco de modelos**: ~10 GB. CPU: usa todos os cores via torch.set_num_threads.

---

## 📂 Estrutura de pastas

```
oficina-imigrantes-ai/
├── src/
│   ├── config.py            constantes (modelo, paths, threads)
│   ├── download.py          yt-dlp wrapper, ffmpeg auto-detect
│   ├── transcribe.py        Whisper (whisper / mms / hybrid backends)
│   ├── transcribe_mms.py    MMS-1B com adapter kreyol
│   ├── translate.py         NLLB com batch_translate + 4 camadas
│   ├── idiomas.py           dicionario PT BR <-> KR (1k+ entradas)
│   ├── correcoes.py         overrides manuais (PT↔KR), persistente JSON
│   ├── embed_store.py       LaBSE + ChromaDB, busca bidirecional
│   ├── tts.py               MMS-TTS-hat com cache em disco
│   ├── conversa.py          mic ASR + tradução pros 2 sentidos
│   ├── pipeline.py          orquestra batch (download→ASR→NLLB batch→embed)
│   ├── daemon.py            loop que le queue.txt, offline-friendly
│   ├── app.py               Streamlit UI (3 abas: Dicionario, Conversa, Mòd Imigran)
│   ├── precache_phrases.py  pre-gera TTS pra 64 frases PT comuns
│   ├── precache_immigrant.py pre-aquece NLLB pra 46 frases KR
│   ├── round_trip_test.py   TTS→MMS→NLLB validacao end-to-end
│   ├── re_embed.py          re-embedar banco com novo embedder
│   └── reset_chroma.py      limpa o vector DB
├── data/
│   ├── audio/               mp3 baixados (gitignored)
│   ├── transcripts/         JSON com transcrição por vídeo (gitignored)
│   ├── chroma/              vector DB persistente (gitignored)
│   ├── tts_cache/           audio cache do TTS (gitignored)
│   ├── queue.txt            URLs pra processar
│   ├── correcoes.json       overrides PT↔KR (versionado)
│   ├── processed.txt        IDs já feitos
│   └── failed.txt           IDs com falha
├── models/                  cache local de modelos (gitignored, ~4GB)
├── .venv/                   Python venv (gitignored)
├── iniciar_ui.bat           shortcut pra UI
├── iniciar_daemon.bat       shortcut pro processador
├── requirements.txt
└── README.md
```

---

## 🎙️ Os 3 modos da UI

### 📚 Dicionário
Caixa de busca única. Digite em PT ou KR — o sistema busca nos dois.
Cada resultado mostra: kreyòl, português, e o **vídeo do YouTube embedado começando no momento exato** que a professora diz aquela palavra. Audio pronunciation grátis.

### 🎙️ Conversa ao vivo
Duas colunas lado a lado:
- **🇧🇷 → 🇭🇹** Voluntário fala PT → Whisper transcreve → NLLB traduz → mostra texto KR grande **e gera áudio kreyòl** via TTS (cacheado em disco, repetições são instantâneas)
- **🇭🇹 → 🇧🇷** Imigrante fala kreyòl → MMS-1B transcreve → NLLB traduz → voluntário lê PT

### 🤝 Mòd Imigran
Aba dedicada ao imigrante, **toda em kreyòl**. Tem:
- Botão grande "🎙️ Pale isi a" pra ele falar
- **18 frases prontas** ("Mwen pa konprann", "Èske w ka repete?", etc) — clica e mostra PT pro voluntário ler
- **9 sentimentos** ("😟 Mwen pa fin konprann", "💪 Mwen ka fè l") pra expressar estado emocional sem precisar saber PT
- Banner em PT e KR no topo de todas as telas

---

## 🔧 Configurações principais (`src/config.py`)

```python
WHISPER_MODEL = "medium"   # small (rápido) | medium (qualidade) | large-v3 (luxo)
WHISPER_LANG  = "ht"       # forçado pra kreyòl no batch

ASR_BACKEND = "hybrid"     # whisper | mms | hybrid (recomendado)

EMBED_MODEL = "sentence-transformers/LaBSE"   # 109 idiomas, kreyòl incluso
```

CPU é configurado automaticamente pra usar todos os cores lógicos (12 num i7 13gen).

---

## ⚡ Performance

- **Batch processing**: cada vídeo de ~10 min leva 5-10 min pra processar (Whisper medium + MMS + NLLB batch + embed)
- **TTS no UI**: primeira frase ~12s (carrega modelo), seguintes 3-4s. **Cache em disco** zera latência pra frases repetidas (<0.1s)
- **Busca**: <1s mesmo com banco de 5000+ records

---

## ⚠️ Limitações conhecidas (honestas)

1. **Round-trip MMS → NLLB pode errar feio**: testamos com TTS sintético, MMS-1B confundiu "pèdi" (perdido) com "bêbado". Em fala de **humano real** o comportamento pode ser melhor OU pior — **precisa validar com haitiano nativo** antes de ambiente final.

2. **NLLB tem alucinações culturais**: traduz literalmente expressões idiomáticas. Mitigado pelas 4 camadas em `idiomas.py` + `correcoes.json` — quanto mais usarem, mais frases vamos cadastrar.

3. **TTS kreyòl é uma voz só**, qualidade média. Funciona, mas é monotôno. Ideal seria voice cloning de um nativo, fora do escopo atual.

4. **Não suporta diarização** (múltiplos falantes simultâneos). Workshop deve usar push-to-talk.

5. **Vídeo de 48 min trava o pipeline na transcrição**: marcado no `failed.txt` como `skipped_too_long_48min`. Solução futura: chunking de áudio antes do Whisper.

---

## 🧪 Como adicionar correções de tradução

**Caso 1: NLLB traduziu errado uma frase específica**

Edite `data/correcoes.json`:
```json
{
  "pt_to_kr": {
    "minha frase em pt": "Sa mwen vle di an kreyòl"
  },
  "kr_to_pt": {
    "fraz an kreyòl": "Minha frase em português"
  }
}
```

Não precisa reiniciar Streamlit — próxima query já usa.

**Caso 2: Quer adicionar uma gíria nova**

Edite `src/idiomas.py`:
- Se for "PT-idiomático → KR-cultural": adiciona em `IDIOMA_CULTURAL`
- Se for "PT idiomático → reescrever pra PT literal antes do NLLB": adiciona em `IDIOMA_REWRITES`

---

## 📞 Workshop day (cenário ideal)

1. Boot do notebook. Internet ok (apenas pra download de vídeos novos).
2. Roda `iniciar_daemon.bat` se quiser processar mais conteúdo, OU pula esse passo se já estiver tudo no banco.
3. Roda `iniciar_ui.bat`. Aguarda spinner "Carregando modelos (1x, ~30s)".
4. **Para o voluntário**: aba "🎙️ Conversa", coluna esquerda. Segura mic, fala PT, mostra a tela com texto kreyòl + toca áudio TTS pro imigrante ouvir.
5. **Para o imigrante**: aba "🤝 Mòd Imigran". Botões grandes em kreyòl. Clica num sentimento, mostra PT pro voluntário ler.
6. **Pra qualquer um**: aba "📚 Dicionário" pra buscar palavra solta + ver vídeo de professora nativa pronunciando.

---

## 📦 Setup do zero (em outra máquina)

```powershell
# Pre-requisitos: Python 3.12+, Git, winget (Windows 11)
git clone https://github.com/welerson-py/THPTBR.git
cd THPTBR

# ffmpeg
winget install Gyan.FFmpeg

# venv + deps
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Primeira execução baixa modelos automaticamente (~10 GB total)
.\iniciar_ui.bat
```

---

## 🤝 Sobre o projeto

Construído pra workshop de inclusão digital de imigrantes haitianos em São Paulo. Deadline original: maio/2026.

A ideia central: **o sistema só é útil se o imigrante sentir que vocês se deram ao trabalho de entender como ele pensa**. Por isso as 4 camadas, as gírias, o calor humano embutido. Tradução literal é só o ponto de partida — tradução **com alma** é o objetivo.

> "Konte sou mwen, mwen avèk ou."

🇧🇷🤝🇭🇹
