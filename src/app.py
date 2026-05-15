"""Streamlit UI: Dicionario (search) + Conversa (live mic translation)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import streamlit.components.v1 as components

from embed_store import search, count


@st.cache_resource(show_spinner="Carregando modelos (1x, ~30s)...")
def warmup_models():
    """Pre-load all models so first user interaction is fast."""
    from tts import warmup as tts_warmup
    from conversa import _whisper_pt
    from translate import get_model as nllb_model
    # Order matters: lightest first so something's ready ASAP
    nllb_model()
    _whisper_pt()
    tts_warmup()
    return True


warmup_models()

st.set_page_config(
    page_title="Oficina de Imigrantes — Kreyòl ↔ Português",
    page_icon="🎓",
    layout="wide",
)

# ===== Estilo global: caribenho/haitiano, moderno, mobile-friendly =====
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&family=Fraunces:wght@600;700;800;900&display=swap" rel="stylesheet">

<style>
/* ---- Paleta caribenha (inspirada em arte haitiana folk) ---- */
:root {
  --c-orange:   #E55934;    /* laranja vivo - alegria caribenha */
  --c-yellow:   #F8C630;    /* amarelo sol */
  --c-green:    #2D9F6A;    /* verde Haiti */
  --c-red:      #C03221;    /* vermelho profundo */
  --c-cream:    #FAF3DD;    /* creme/areia */
  --c-deep:     #0F2A1D;    /* verde escuro folha */

  --c-pt:       var(--c-yellow);
  --c-kr:       var(--c-green);
  --c-warm:     var(--c-orange);

  --c-bg-soft:  rgba(248,198,48,0.04);
  --c-border:   rgba(250,243,221,0.10);
  --shadow-card: 0 6px 24px rgba(15,42,29,0.35), 0 1px 0 rgba(250,243,221,0.04) inset;
  --shadow-card-hover: 0 10px 32px rgba(15,42,29,0.45);
}

/* ---- Padroes SVG decorativos como data-URI ---- */
.pattern-waves {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 80 20'%3E%3Cpath d='M0,10 Q10,0 20,10 T40,10 T60,10 T80,10' stroke='%23E55934' stroke-width='3' fill='none'/%3E%3C/svg%3E");
  background-repeat: repeat-x;
  background-size: 80px 20px;
  height: 20px;
}
.pattern-diamonds {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 30 30'%3E%3Cpolygon points='15,2 28,15 15,28 2,15' fill='none' stroke='%23F8C630' stroke-width='2'/%3E%3Cpolygon points='15,8 22,15 15,22 8,15' fill='%23E55934'/%3E%3C/svg%3E");
  background-repeat: repeat-x;
  background-size: 30px 30px;
  height: 30px;
}
.pattern-triangles {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 20'%3E%3Cpolygon points='0,20 10,0 20,20' fill='%232D9F6A'/%3E%3Cpolygon points='20,20 30,0 40,20' fill='%23C03221'/%3E%3C/svg%3E");
  background-repeat: repeat-x;
  background-size: 40px 20px;
  height: 20px;
}

/* ---- Background sutil de toda a pagina ---- */
.stApp {
  background-image:
    radial-gradient(circle at 15% 20%, rgba(229,89,52,0.05) 0%, transparent 40%),
    radial-gradient(circle at 85% 80%, rgba(45,159,106,0.05) 0%, transparent 40%),
    radial-gradient(circle at 50% 50%, rgba(248,198,48,0.03) 0%, transparent 60%);
}
html, body, [class*="css"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
h1, h2, h3, .title {
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  letter-spacing: -0.02em;
}
h1 {
  font-family: 'Fraunces', serif !important;
  font-weight: 800 !important;
  font-style: italic;
}

/* ---- Tipografia das traduções ---- */
.big-result {
  font-size: 2.5rem;
  font-weight: 700;
  line-height: 1.2;
  margin: 0.5rem 0;
  letter-spacing: -0.01em;
  animation: slideUpFade 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.label {
  font-size: 0.85rem;
  opacity: 0.65;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-weight: 600;
}
.context-text {
  font-size: 0.9rem;
  opacity: 0.55;
  font-style: italic;
  margin-top: 0.3rem;
}

/* ---- Animações ---- */
@keyframes slideUpFade {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50%      { transform: scale(1.05); opacity: 0.85; }
}
@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
.pulse-record { animation: pulse 1.5s ease-in-out infinite; display: inline-block; }
.shimmer {
  background: linear-gradient(90deg, var(--c-bg-soft) 0%, rgba(255,255,255,0.1) 50%, var(--c-bg-soft) 100%);
  background-size: 200% 100%;
  animation: shimmer 1.5s linear infinite;
  border-radius: 8px;
}

/* ---- Cards de resultado ---- */
[data-testid="stContainer"]:has(> [data-testid="stVerticalBlock"]) {
  transition: all 0.2s ease;
}
div[data-testid="stContainer"] {
  border-radius: 12px !important;
}

/* ---- Botões: gigantes e tateáveis ---- */
.stButton > button {
  font-size: 1.1rem !important;
  font-weight: 600 !important;
  padding: 0.85rem 1.2rem !important;
  height: auto !important;
  min-height: 3.2rem !important;
  border-radius: 10px !important;
  transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1) !important;
  border: 1px solid var(--c-border) !important;
}
.stButton > button:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-card-hover);
}
.stButton > button:active {
  transform: translateY(0px) scale(0.98);
}

/* ---- Mic input: destacado ---- */
[data-testid="stAudioInput"] {
  border-radius: 14px;
  padding: 0.5rem;
  background: linear-gradient(135deg, rgba(74,222,128,0.08), rgba(96,165,250,0.08));
  border: 1px solid var(--c-border);
}

/* ---- Tabs: estilo app, não browser ---- */
.stTabs [data-baseweb="tab-list"] {
  gap: 0.5rem;
  padding: 0.3rem;
  background: var(--c-bg-soft);
  border-radius: 12px;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 8px !important;
  padding: 0.6rem 1.2rem !important;
  font-weight: 600 !important;
  transition: all 0.15s ease !important;
}
.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg, var(--c-pt), var(--c-kr)) !important;
  color: white !important;
}

/* ---- Inputs: respiráveis ---- */
.stTextInput input, .stTextArea textarea {
  border-radius: 10px !important;
  font-size: 1.05rem !important;
  padding: 0.7rem 1rem !important;
  transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: var(--c-warm) !important;
  box-shadow: 0 0 0 3px rgba(251,146,60,0.15) !important;
}

/* ---- Mobile-first: telas até 768px ---- */
@media (max-width: 768px) {
  .big-result { font-size: 1.8rem; }
  .stButton > button {
    font-size: 1rem !important;
    min-height: 3.5rem !important;
  }
  [data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; }
  .stTabs [data-baseweb="tab"] { padding: 0.5rem 0.8rem !important; font-size: 0.9rem !important; }
  h1 { font-size: 1.6rem !important; }
  iframe { height: 180px !important; }
}

/* ---- Sidebar: solida no mobile (fix da transparencia) e bonita no desktop ---- */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0F2A1D 0%, #112d24 100%) !important;
  border-right: 1px solid var(--c-border);
  box-shadow: 8px 0 30px rgba(0,0,0,0.4);
}
[data-testid="stSidebar"] > div {
  background: transparent !important;
}
@media (max-width: 768px) {
  [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F2A1D, #1a3d2e) !important;
    box-shadow: 6px 0 40px rgba(0,0,0,0.7) !important;
    backdrop-filter: none !important;
  }
  [data-testid="stSidebar"]::before {
    content: "";
    position: absolute;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40' viewBox='0 0 40 40'%3E%3Cpath d='M0,20 Q10,10 20,20 T40,20' stroke='%23E55934' stroke-width='1' fill='none' opacity='0.05'/%3E%3C/svg%3E");
    pointer-events: none;
  }
}

/* ---- Banner welcome: arte caribenha ---- */
.welcome-banner {
  position: relative;
  background:
    linear-gradient(135deg,
      rgba(229,89,52,0.18) 0%,
      rgba(248,198,48,0.10) 30%,
      rgba(45,159,106,0.10) 70%,
      rgba(192,50,33,0.15) 100%);
  border: 1px solid var(--c-border);
  border-radius: 16px;
  padding: 1.6rem 1.5rem 1.4rem;
  margin: 1rem 0;
  box-shadow: var(--shadow-card);
  animation: slideUpFade 0.6s cubic-bezier(0.16, 1, 0.3, 1);
  overflow: hidden;
}
.welcome-banner::before {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0; height: 6px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 6'%3E%3Crect width='10' height='6' fill='%23E55934'/%3E%3Crect x='10' width='10' height='6' fill='%23F8C630'/%3E%3Crect x='20' width='10' height='6' fill='%232D9F6A'/%3E%3Crect x='30' width='10' height='6' fill='%23C03221'/%3E%3C/svg%3E");
  background-size: 40px 6px;
}
.welcome-banner::after {
  content: "";
  position: absolute;
  bottom: 0; left: 0; right: 0; height: 8px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 80 8'%3E%3Cpath d='M0,4 Q10,0 20,4 T40,4 T60,4 T80,4' stroke='%23F8C630' stroke-width='1.5' fill='none' opacity='0.6'/%3E%3C/svg%3E");
  background-size: 80px 8px;
  background-repeat: repeat-x;
}
.welcome-pt {
  font-size: 1.3rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #FAF3DD;
  position: relative;
  padding-left: 1.8rem;
}
.welcome-pt::before {
  content: "🇧🇷";
  position: absolute;
  left: 0;
  top: 0;
}
.welcome-kr {
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--c-yellow);
  position: relative;
  padding-left: 1.8rem;
}
.welcome-kr::before {
  content: "🇭🇹";
  position: absolute;
  left: 0;
  top: 0;
}

/* ---- Divider decorativo entre secoes ---- */
.divider-haiti {
  margin: 2rem 0;
  height: 24px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 24'%3E%3Cpolygon points='30,4 36,12 30,20 24,12' fill='%23F8C630' stroke='%23E55934' stroke-width='1.5'/%3E%3Cline x1='0' y1='12' x2='22' y2='12' stroke='%23E55934' stroke-width='1.5'/%3E%3Cline x1='38' y1='12' x2='60' y2='12' stroke='%23E55934' stroke-width='1.5'/%3E%3C/svg%3E");
  background-repeat: repeat-x;
  background-position: center;
  background-size: 60px 24px;
  opacity: 0.7;
}

/* ---- Decoracao do titulo principal ---- */
h1 {
  position: relative;
  padding-bottom: 0.4rem;
  margin-bottom: 0.2rem !important;
}
h1::after {
  content: "";
  display: block;
  height: 6px;
  width: 80px;
  margin-top: 0.6rem;
  border-radius: 3px;
  background: linear-gradient(90deg, var(--c-orange), var(--c-yellow), var(--c-green), var(--c-red));
}

/* ---- Cards de resultado: borda decorativa ---- */
[data-testid="stContainer"] [data-testid="stVerticalBlockBorderWrapper"] {
  position: relative;
  background: linear-gradient(135deg, rgba(15,42,29,0.4), rgba(15,42,29,0.2)) !important;
  border-color: var(--c-border) !important;
  transition: all 0.2s ease;
}
[data-testid="stContainer"] [data-testid="stVerticalBlockBorderWrapper"]:hover {
  border-color: rgba(248,198,48,0.3) !important;
  box-shadow: var(--shadow-card-hover);
}

/* ---- Status pill (durante processamento) ---- */
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.5rem 1rem;
  border-radius: 999px;
  font-size: 0.95rem;
  font-weight: 600;
  background: linear-gradient(135deg, rgba(229,89,52,0.15), rgba(248,198,48,0.10));
  border: 1px solid rgba(248,198,48,0.25);
  color: var(--c-cream);
  animation: slideUpFade 0.3s ease;
}
.status-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  background: var(--c-orange);
  box-shadow: 0 0 12px var(--c-orange);
  animation: pulse 1s ease-in-out infinite;
}

/* ---- Footer com motivo Caribbean ---- */
.caribbean-footer {
  margin-top: 2.5rem;
  padding: 1rem 0 0.5rem;
  text-align: center;
  opacity: 0.7;
}
.caribbean-footer::before {
  content: "";
  display: block;
  height: 18px;
  margin: 0 auto 0.5rem;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 18'%3E%3Ccircle cx='10' cy='9' r='4' fill='%23E55934'/%3E%3Ccircle cx='30' cy='9' r='4' fill='%23F8C630'/%3E%3Ccircle cx='50' cy='9' r='4' fill='%232D9F6A'/%3E%3Ccircle cx='70' cy='9' r='4' fill='%23C03221'/%3E%3Ccircle cx='90' cy='9' r='4' fill='%23FAF3DD'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: center;
  background-size: 100px 18px;
}

/* ---- Sentimentos / botoes em modo imigrante: cores rotativas caribenhas ---- */
.stTabs [data-baseweb="tab-panel"] .stButton:nth-child(3n+1) > button {
  border-left: 3px solid var(--c-orange) !important;
}
.stTabs [data-baseweb="tab-panel"] .stButton:nth-child(3n+2) > button {
  border-left: 3px solid var(--c-yellow) !important;
}
.stTabs [data-baseweb="tab-panel"] .stButton:nth-child(3n+3) > button {
  border-left: 3px solid var(--c-green) !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🎓 Oficina de Imigrantes")
st.caption("**Kreyòl Ayisyen** ↔ **Português** — dicionário com áudio + conversa ao vivo")

# Banner de boas-vindas BR + Haiti (calor de oficina)
st.markdown("""
<div class="welcome-banner">
  <div class="welcome-pt">🇧🇷 Olá, parceiro! Bem-vindo. Aqui estamos juntos pra aprender. Pode contar comigo, tô junto.</div>
  <div class="welcome-kr">🇭🇹 Bonjou, zanmi m! Byenvini lakay nou. Nou ansanm pou aprann. Konte sou mwen, mwen avèk ou.</div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Configurações")
    n_results = st.slider("Resultados por busca", 3, 20, 8)
    show_score = st.checkbox("Mostrar score técnico", value=False)
    try:
        db_size = count()
        st.metric("Frases no banco", db_size)
    except Exception as e:
        st.error(f"Erro ao ler banco: {e}")
    st.markdown("---")
    st.markdown("**Atalhos de uso:**")
    st.markdown(
        "- **Dicionário**: busca rápida de palavras\n"
        "- **Conversa**: microfone pra falar ao vivo com o imigrante"
    )

tab_dic, tab_conversa, tab_imigrante = st.tabs([
    "📚 Dicionário",
    "🎙️ Conversa ao vivo",
    "🤝 Mòd Imigran",
])

# ----------------- DICIONÁRIO -----------------
with tab_dic:
    st.subheader("Busca de palavras / frases")
    query = st.text_input(
        "🔍 Digite em português OU kreyòl:",
        placeholder="ex.: 'comprar' ou 'manje'",
        key="dic_query",
    )

    if query:
        with st.spinner("Buscando..."):
            try:
                results = search(query.strip(), n=n_results)
            except Exception as e:
                st.error(f"Erro: {e}")
                results = []

        if not results:
            st.warning("Nenhum resultado.")
        else:
            st.caption(f"{len(results)} resultados para **{query}**")
            for r in results:
                with st.container(border=True):
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        st.markdown("<div class='label'>🇭🇹 Kreyòl</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='big-result'>{r['kreyol']}</div>", unsafe_allow_html=True)
                        if r.get("context") and r["context"].strip() != r["kreyol"].strip():
                            st.markdown(f"<div class='context-text'>contexto: {r['context'][:140]}</div>", unsafe_allow_html=True)
                    with c2:
                        st.markdown("<div class='label'>🇧🇷 Português</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='big-result'>{r['portuguese'] or '(sem tradução)'}</div>", unsafe_allow_html=True)

                    start_s = max(0, int(r["start"]) - 1)
                    embed_url = (
                        f"https://www.youtube.com/embed/{r['video_id']}"
                        f"?start={start_s}&rel=0"
                    )
                    components.iframe(embed_url, height=220)

                    bits = [f"@ {r['start']:.1f}s"]
                    if show_score:
                        bits.append(f"score={r['score']:.2f} (vec={r['vec_score']:.2f}, fuzzy={r['fuzzy_score']:.2f})")
                    st.caption(" • ".join(bits))
    else:
        st.info("Digite uma palavra acima para começar.")

# ----------------- CONVERSA -----------------
with tab_conversa:
    st.subheader("Tradução ao vivo via microfone")
    st.caption(
        "🎙️ Grave sua fala, o sistema transcreve e traduz. Mostre a tela pro outro lado ler."
    )

    sub_pt, sub_kr = st.columns(2)

    # ----- 1. Você fala PT, mostra em kreyòl -----
    with sub_pt:
        st.markdown("### 🇧🇷 → 🇭🇹  Você fala em **Português**")
        st.caption("Para o imigrante entender o que você quer dizer")
        pt_audio = st.audio_input("🎙️ Gravar sua voz (PT):", key="pt_input")
        if pt_audio:
            # Status pill com 3 estagios visuais
            status_slot = st.empty()
            status_slot.markdown(
                "<div class='status-pill'><span class='status-dot'></span> "
                "<span>✍️ Transcrevendo e traduzindo…</span></div>",
                unsafe_allow_html=True,
            )
            from conversa import pt_says_to_kr
            result = pt_says_to_kr(pt_audio.getvalue())
            status_slot.empty()

            st.markdown("<div class='label'>🇧🇷 Você disse</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='big-result'>{result['pt'] or '(silêncio)'}</div>", unsafe_allow_html=True)
            st.markdown("<div class='label'>🇭🇹 Em kreyòl (mostre pro imigrante)</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='big-result' style='color:var(--c-kr)'>{result['kr'] or '(traduzindo falhou)'}</div>", unsafe_allow_html=True)

            if result["kr"]:
                tts_slot = st.empty()
                tts_slot.markdown(
                    "<div class='status-pill'><span class='status-dot'></span> "
                    "<span>🔊 Gerando áudio em kreyòl…</span></div>",
                    unsafe_allow_html=True,
                )
                try:
                    from tts import synth_kreyol_wav_bytes
                    wav = synth_kreyol_wav_bytes(result["kr"])
                    tts_slot.empty()
                    st.audio(wav, format="audio/wav", autoplay=True)
                    st.caption("🔊 Áudio pra o imigrante ouvir")
                except Exception as e:
                    tts_slot.empty()
                    st.warning(f"TTS kreyòl indisponível: {e}")

    # ----- 2. Imigrante fala KR, você lê em PT -----
    with sub_kr:
        st.markdown("### 🇭🇹 → 🇧🇷  Imigrante fala em **Kreyòl**")
        st.caption("Para você entender o que ele/ela está dizendo")
        kr_audio = st.audio_input("🎙️ Pedir pro imigrante falar aqui:", key="kr_input")
        if kr_audio:
            status_slot2 = st.empty()
            status_slot2.markdown(
                "<div class='status-pill'><span class='status-dot'></span> "
                "<span>🎙️ MMS escutando kreyòl…</span></div>",
                unsafe_allow_html=True,
            )
            from conversa import kr_says_to_pt
            result = kr_says_to_pt(kr_audio.getvalue())
            status_slot2.empty()

            st.markdown("<div class='label'>🇭🇹 Ele/ela disse</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='big-result' style='color:var(--c-kr)'>{result['kr'] or '(silêncio)'}</div>", unsafe_allow_html=True)
            st.markdown("<div class='label'>🇧🇷 Em português</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='big-result' style='color:var(--c-pt)'>{result['pt'] or '(traduzindo falhou)'}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.info(
        "💡 **Dica:** quanto mais perto o microfone, melhor. Headset USB ajuda muito em sala cheia. "
        "Primeira gravação demora ~30s (carrega modelo). Depois fica rápido (3-6s por turno)."
    )

# ----------------- MODO IMIGRANTE -----------------
# Tab dedicada pro imigrante haitiano. Idioma de UI = kreyòl.
# Botão grande pra falar, frases comuns prontas pra mostrar pro voluntário.
with tab_imigrante:
    st.markdown("""
    <style>
    .imigrante-title {
      font-size: 2.2rem;
      font-weight: 800;
      background: linear-gradient(135deg, #4ade80, #60a5fa);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      letter-spacing: -0.02em;
    }
    .imigrante-display {
      font-size: 2.8rem;
      font-weight: 700;
      line-height: 1.2;
      padding: 1.2rem 1.4rem;
      border-radius: 12px;
      margin: 0.6rem 0;
      animation: slideUpFade 0.4s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: var(--shadow-card);
    }
    .imigrante-kr {
      background: linear-gradient(135deg, rgba(74,222,128,0.15), rgba(74,222,128,0.05));
      border-left: 6px solid var(--c-kr);
      color: #d1fae5;
    }
    .imigrante-pt {
      background: linear-gradient(135deg, rgba(96,165,250,0.15), rgba(96,165,250,0.05));
      border-left: 6px solid var(--c-pt);
      color: #dbeafe;
    }
    @media (max-width: 768px) {
      .imigrante-display { font-size: 1.8rem; padding: 1rem; }
      .imigrante-title { font-size: 1.6rem; }
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='imigrante-title'>🤝 Bonjou! Klike pou pale</div>", unsafe_allow_html=True)
    st.caption("Pale an kreyòl, n ap ekri sa ou di an pòtigè pou pwofesè a")

    kr_audio_im = st.audio_input("🎙️ Pale isi a:", key="im_input")
    if kr_audio_im:
        with st.spinner("Tande... (MMS + tradiksyon)"):
            from conversa import kr_says_to_pt
            result = kr_says_to_pt(kr_audio_im.getvalue())
        st.markdown(
            f"<div class='imigrante-display imigrante-kr'>🇭🇹 {result['kr'] or '(silans)'}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='imigrante-display imigrante-pt'>🇧🇷 {result['pt'] or '(pa ka tradui)'}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div class='divider-haiti'></div>", unsafe_allow_html=True)
    st.markdown("### 🔘 Fraz ki itil")
    st.caption("Klike sou youn pou montre pwofesè a sa w vle di")

    # Frases pré-mapeadas pra mostrar PT direto sem precisar gravar
    QUICK_PHRASES = [
        ("Mwen pa konprann", "Eu não entendo"),
        ("Èske w ka repete?", "Pode repetir?"),
        ("Pale pi dousman", "Fale mais devagar"),
        ("Mwen pa konnen", "Eu não sei"),
        ("Èd mwen tanpri", "Me ajude por favor"),
        ("Mwen vle aprann", "Eu quero aprender"),
        ("Mwen pèdi", "Estou perdido"),
        ("Klike kote?", "Onde clico?"),
        ("Ki bouton?", "Qual botão?"),
        ("Mwen pa wè", "Eu não vejo"),
        ("Mèsi anpil", "Muito obrigado"),
        ("Pi vit tanpri", "Mais rápido por favor"),
        ("Mwen pare", "Estou pronto"),
        ("Mwen fini", "Eu terminei"),
        ("Mwen grangou", "Estou com fome"),
        ("Mwen swaf", "Estou com sede"),
        ("Ki kote twalèt?", "Onde é o banheiro?"),
        ("Ki lè li ye?", "Que horas são?"),
    ]

    if "im_selected" not in st.session_state:
        st.session_state.im_selected = None

    cols = st.columns(3)
    for i, (kr, pt) in enumerate(QUICK_PHRASES):
        with cols[i % 3]:
            if st.button(kr, key=f"qp_{i}", use_container_width=True):
                st.session_state.im_selected = (kr, pt)

    if st.session_state.im_selected:
        kr_sel, pt_sel = st.session_state.im_selected
        st.markdown("---")
        st.markdown("### 👉 Montre sa pwofesè a:")
        st.markdown(
            f"<div class='imigrante-display imigrante-pt'>🇧🇷 {pt_sel}</div>",
            unsafe_allow_html=True,
        )
        st.caption(f"🇭🇹 {kr_sel}")

    # ----- Seção "Sentimentos" pro imigrante expressar sem precisar saber PT -----
    st.markdown("<div class='divider-haiti'></div>", unsafe_allow_html=True)
    st.markdown("### 💚 Kòman ou santi ou? (Como você está se sentindo?)")
    st.caption("Klike yon sa a pou di pwofesè a ki jan ou ye")

    SENTIMENTOS = [
        ("😊 Mwen kontan", "Estou feliz"),
        ("😟 Mwen pa fin konprann", "Não estou entendendo bem"),
        ("😰 Mwen pè", "Estou com medo"),
        ("😣 Mwen fatige", "Estou cansado"),
        ("🤔 M ap reflechi", "Estou pensando"),
        ("👍 M pare", "Estou pronto"),
        ("🙏 Tanpri pi dousman", "Por favor, mais devagar"),
        ("✋ Mwen vle pran yon ti repo", "Quero fazer uma pausa"),
        ("💪 Mwen ka fè l", "Eu consigo fazer"),
    ]
    cols_s = st.columns(3)
    for i, (kr, pt) in enumerate(SENTIMENTOS):
        with cols_s[i % 3]:
            if st.button(kr, key=f"sent_{i}", use_container_width=True):
                st.session_state.im_selected = (kr, pt)
                st.rerun()

# ===== Footer caribenho em todas as paginas =====
st.markdown("""
<div class="caribbean-footer">
  <small>🇧🇷 Oficina de Imigrantes &middot; Kreyòl ↔ Português &middot; 🇭🇹</small><br>
  <small style="opacity:0.6">Konte sou mwen, mwen avèk ou</small>
</div>
""", unsafe_allow_html=True)
