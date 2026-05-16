# Escopo do Projeto

**Oficina de Imigrantes — Sistema de Tradução Local Português ↔ Kreyòl Ayisyen**

---

| | |
|---|---|
| **Autor** | Welerson dos Anjos |
| **Contato** | welerson.anjos1@hotmail.com · linkedin.com/in/welersondosanjos |
| **Repositório** | https://github.com/welerson-py/THPTBR |
| **Status** | Concluído (v1) |
| **Local de Aplicação** | Canoas, RS — Workshop de inclusão digital |

---

## 1. Sumário Executivo

Sistema de inteligência artificial local que viabiliza comunicação bidirecional entre **voluntários brasileiros** e **imigrantes haitianos** durante workshops de inclusão digital. Toda a inferência (transcrição de voz, tradução e síntese de fala) executa offline no notebook do operador, sem dependência de APIs pagas, sem custos recorrentes e sem dados sensíveis trafegando pela internet.

O sistema combina cinco modelos de aprendizado profundo open-source em um pipeline coeso, distribui o conteúdo de aprendizado por uma interface multi-modal (dicionário com áudio, conversa por microfone e modo simplificado para o imigrante) e incorpora um sistema de **cinco camadas de tradução** que vai além da equivalência literal — entregando traduções culturalmente adequadas (ex.: *"mamão com açúcar"* → *"se dlo kòk"*, gíria equivalente em kreyòl).

---

## 2. Contexto e Justificativa

Imigrantes haitianos no Brasil enfrentam barreiras linguísticas significativas, especialmente em iniciativas de inclusão digital, onde o vocabulário técnico é específico e a fluidez da comunicação é crítica para o aprendizado. Ferramentas de tradução online tradicionais (Google Translate, etc.) apresentam três limitações:

1. **Dependência de internet** — workshops em centros comunitários frequentemente não têm WiFi estável
2. **Tradução literal** — gírias e expressões idiomáticas brasileiras são traduzidas palavra a palavra, perdendo sentido cultural
3. **Privacidade** — dados de voz e texto sensíveis são enviados a servidores de terceiros

Este projeto resolve as três limitações entregando uma solução **local, contextual e privada**.

---

## 3. Objetivos

### 3.1 Objetivo Geral

Reduzir a barreira linguística PT ↔ Kreyòl em workshops presenciais de inclusão digital, oferecendo ferramenta de tradução com qualidade culturalmente adequada e zero custo operacional.

### 3.2 Objetivos Específicos

- Construir banco vetorial com vocabulário extraído de material audiovisual real (aulas de YouTube)
- Disponibilizar tradução por voz bidirecional em tempo quase real (<10 segundos por turno)
- Garantir operação 100% offline após instalação inicial
- Permitir múltiplos dispositivos (celulares dos voluntários) conectados simultaneamente ao mesmo servidor (notebook)
- Embutir vocabulário cultural específico (gírias, expressões idiomáticas, equivalências culturais)
- Entregar interface adaptada para diferentes perfis: voluntário técnico e imigrante sem familiaridade digital

---

## 4. Escopo

### 4.1 Está incluído (in-scope)

- Pipeline de ingestão de vídeos do YouTube (download, segmentação, transcrição, tradução, indexação)
- Quatro modos de interação na interface (Dicionário, Conversa, Modo Imigrante, Passa o Telefone)
- Sistema de cinco camadas de tradução com correções manuais editáveis
- Glossário curado de 289 termos de inclusão digital
- Setup HTTPS local com certificado auto-assinado (mkcert) para uso de microfone em celulares
- QR Code para conexão simplificada
- Documentação completa (README, scripts de inicialização, transparência sobre IA)
- Banco vetorial portável (12 MB versionado no Git, auto-import em ~5 segundos)

### 4.2 Não está incluído (out-of-scope)

- Aplicativo nativo Android/iOS (clientes acessam via navegador)
- Hospedagem em nuvem (sistema é local por desenho)
- Suporte a outros idiomas além de PT e Kreyòl Ayisyen
- Sincronização entre múltiplos servidores
- Painel administrativo para coordenador da oficina
- Reconhecimento de múltiplos falantes simultâneos (diarização)

---

## 5. Stack Tecnológica

### 5.1 Modelos de IA

| Componente | Modelo | Tamanho | Justificativa |
|---|---|---|---|
| Transcrição (segmentação) | faster-whisper medium int8 | 1.5 GB | VAD timestamps confiáveis, melhor para fala estruturada |
| Transcrição (kreyòl refinado) | facebook/mms-1b-all | 3.5 GB | Treinado em 1100+ línguas low-resource, melhor para kreyòl |
| Tradução bidirecional | facebook/nllb-200-distilled-600M | 2.5 GB | Suporta `por_Latn` e `hat_Latn` nativamente |
| Embeddings (busca) | sentence-transformers/LaBSE | 1.8 GB | 109 idiomas incluindo kreyòl; score 0.7-0.95 em busca cross-lingual |
| Síntese de voz kreyòl | facebook/mms-tts-hat | 500 MB | Único TTS offline com qualidade aceitável para kreyòl |

### 5.2 Stack de Aplicação

- **Linguagem:** Python 3.14
- **Banco vetorial:** ChromaDB com índice HNSW (cosine similarity)
- **Framework UI:** Streamlit (HTTPS local via mkcert)
- **Inferência:** PyTorch + Transformers (Hugging Face), CPU multi-threaded (12 cores)
- **Ingestão de áudio:** yt-dlp + ffmpeg
- **Manipulação de áudio:** librosa, soundfile
- **Versionamento:** Git + GitHub

---

## 6. Arquitetura

### 6.1 Fluxo de Dados (Pipeline Batch)

```
queue.txt (URLs) → daemon.py
    ├─ download.py     (yt-dlp → mp3)
    ├─ transcribe.py   (Whisper: segmenta; MMS: refina texto kreyòl)
    ├─ pipeline.py     (expand_segment: detecta pares de palavras)
    ├─ translate.py    (NLLB batch: 8 traduções por chamada)
    └─ embed_store.py  (LaBSE → ChromaDB persistente)
```

### 6.2 Sistema de Cinco Camadas de Tradução (PT → KR)

Cada camada tem precedência sobre as seguintes. A primeira que casa retorna o resultado:

1. **Override manual** (`data/correcoes.json`) — correções específicas registradas
2. **Glossário de informática** (`data/glossario_informatica.json`) — 289 termos técnicos curados
3. **Equivalência cultural direta** (`idiomas.IDIOMA_CULTURAL`) — expressões idiomáticas inteiras
4. **Reescrita de idiomatismo** + NLLB — frases longas têm gírias substituídas por equivalentes literais antes da tradução automática
5. **Calor pós-NLLB** (`idiomas.WARMTH_KR`) — substituições no output do NLLB para humanizar o resultado

### 6.3 Interface Web (Streamlit, 4 abas)

- **📚 Dicionário** — busca textual com embedding LaBSE; resultados incluem áudio do YouTube original começando no timestamp exato
- **🎙️ Conversa ao vivo** — microfone, transcrição, tradução, TTS, com histórico das 10 últimas falas e botão de repetir áudio
- **🤝 Mòd Imigran** — interface em kreyòl com 18 frases prontas + 9 expressões emocionais; voluntário entrega o celular ao imigrante
- **📱 Pase Telefòn** — modo ultra-simplificado: 1 botão de microfone, texto em letras enormes para ambos os lados lerem

### 6.4 Distribuição Multi-dispositivo

- Servidor único (notebook do operador)
- Clientes (celulares + outros PCs) acessam via WiFi local em `https://[ip-local]:8501`
- Certificado HTTPS gerado por `mkcert` (CA local) — necessário para acesso ao microfone via navegador
- QR Code embutido na sidebar para conexão sem digitação de URL

---

## 7. Funcionalidades Entregues

| ID | Funcionalidade | Status |
|---|---|---|
| F01 | Download em lote de playlists do YouTube | ✅ |
| F02 | Transcrição automática (Whisper + MMS híbrido) | ✅ |
| F03 | Tradução em batch via NLLB (8 frases/chamada) | ✅ |
| F04 | Banco vetorial persistente com 7.021 frases | ✅ |
| F05 | Busca textual bidirecional (vetorial + fuzzy) | ✅ |
| F06 | Reprodução de áudio nativo das aulas originais | ✅ |
| F07 | Microfone com transcrição PT em tempo real | ✅ |
| F08 | Microfone com transcrição kreyòl em tempo real | ✅ |
| F09 | Síntese de voz em kreyòl com cache em disco | ✅ |
| F10 | Histórico de conversas com replay | ✅ |
| F11 | Sistema de correções manuais editável | ✅ |
| F12 | Glossário de informática (289 termos) | ✅ |
| F13 | Detecção de idiomatismos com substituição contextual | ✅ |
| F14 | Pós-processamento cultural ("calor humano") | ✅ |
| F15 | HTTPS local com mkcert | ✅ |
| F16 | QR Code para conexão de celulares | ✅ |
| F17 | Banco vetorial portável (12 MB versionável) | ✅ |
| F18 | Auto-import na primeira execução (~5s) | ✅ |
| F19 | Daemon resiliente a falhas de rede | ✅ |
| F20 | Bundle exportável (.zip de 30 MB) | ✅ |

---

## 8. Cronograma (Realizado)

| Período | Etapa |
|---|---|
| Dia 1 | Definição de arquitetura, instalação de dependências, primeiro pipeline funcional |
| Dia 2 | Integração de Whisper + NLLB; primeiros 5 vídeos processados |
| Dia 3 | Sistema de idiomatismos culturais, glossário, busca bidirecional |
| Dia 4 | Modo Conversa com microfone; TTS em kreyòl com cache |
| Dia 5 | Upgrade para LaBSE; reprocessamento do banco; UI rica com identidade visual caribenha |
| Dia 6 | HTTPS local, QR Code, bundle exportável, modo "Passa o Telefone" |
| Dia 7 | Banco vetorial portável, glossário de informática (289 termos), polimento |

---

## 9. Resultados Quantificáveis

- **7.021 frases** indexadas no banco vetorial (~37 vídeos processados)
- **289 termos** de inclusão digital com tradução curada
- **100+ expressões idiomáticas BR** com equivalentes culturais haitianos
- **64 frases de workshop** com áudio TTS pré-gerado (latência <100ms para frases repetidas)
- **46 frases de imigrante** pré-cacheadas no NLLB (resposta KR→PT <2s)
- **12 MB** de tamanho do banco vetorial versionado no Git (vs ~10 GB de modelos brutos)
- **~5 segundos** para um novo clone do repositório ter o banco completo funcional
- **4 modos de interação** atendendo voluntário, imigrante e situações de uso compartilhado

---

## 10. Limitações Conhecidas

1. **Qualidade do MMS em fala espontânea** — testado com áudio sintético (TTS); fala real de haitiano com sotaque ainda precisa validação
2. **TTS kreyòl monotônico** — voz única, qualidade aceitável mas sem prosódia natural
3. **Sem diarização** — múltiplos falantes simultâneos não são distinguidos; workshop deve usar push-to-talk
4. **Memória RAM** — uso completo dos modelos exige 8-16 GB; PCs mais fracos podem usar apenas o modo Dicionário (~4 GB suficientes)
5. **Certificados HTTPS** — primeira conexão de cada celular exige aceitar aviso de certificado (auto-assinado)

---

## 11. Próximos Passos (Roadmap)

- Validação com falante nativo de kreyòl em fala espontânea
- Dry-run com equipe de voluntários antes do workshop
- Coleta de feedback em uso real para ampliar `correcoes.json`
- Possível integração com LLM local (Phi-3.5 ou Llama 3.2) para correção contextual avançada
- Versão Android nativa (médio prazo, fora do escopo atual)

---

## 12. Considerações Finais

O sistema entrega uma solução técnica robusta para um problema social específico, combinando engenharia de software moderna com sensibilidade cultural. A arquitetura modular permite que componentes individuais (modelos, camadas de tradução, interface) sejam evoluídos ou substituídos sem refatoração ampla. O versionamento do banco vetorial portável garante que a inteligência acumulada seja reproduzível em qualquer máquina sem necessidade de reprocessamento.

O projeto demonstra capacidade de levar um problema complexo — comunicação multilíngue, processamento de áudio, modelos de IA, distribuição multi-dispositivo, identidade visual e usabilidade — da concepção ao deploy funcional, em uma escala compatível com uma única pessoa desenvolvendo de forma autônoma.

---

*Documento gerado em maio de 2026 · Repositório: https://github.com/welerson-py/THPTBR*
