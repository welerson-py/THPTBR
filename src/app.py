"""Streamlit UI: Dicionario (search) + Conversa (live mic translation)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import hashlib
import io
import socket
import time
import streamlit as st
import streamlit.components.v1 as components

from embed_store import search, count


@st.cache_data
def _get_local_url():
    """Discover LAN IP for QR code (so phones can scan to connect)."""
    try:
        # Open dummy socket to discover routing IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        # Check if we're running with SSL by looking for cert
        from pathlib import Path
        cert = Path(__file__).resolve().parent.parent / "certs" / "cert.pem"
        scheme = "https" if cert.exists() else "http"
        return f"{scheme}://{ip}:8501"
    except Exception:
        return None


@st.cache_data
def _make_qr_png(url: str) -> bytes:
    """Generate QR code PNG bytes for a URL."""
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#F8C630", back_color="#061224")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return b""


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

/* ---- Background: mural caribenho em 5 camadas + vignette ---- */
.stApp {
  background-color: #061224;
  background-image:
    /* Layer 1: motivos tropicais grandes esparsos (palmeira, sol, folha, bird) */
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='480' height='480' viewBox='0 0 480 480'%3E%3Cg opacity='0.025'%3E%3Cg transform='translate(40,60)'%3E%3Crect x='28' y='40' width='4' height='40' fill='%23F8C630'/%3E%3Cpath d='M30,40 Q12,32 3,17 M30,40 Q48,32 57,17 M30,40 Q40,22 50,3 M30,40 Q20,22 10,3' stroke='%232D9F6A' stroke-width='3' fill='none'/%3E%3C/g%3E%3Cg transform='translate(360,140)'%3E%3Ccircle cx='30' cy='30' r='12' fill='%23F8C630'/%3E%3Cg stroke='%23E55934' stroke-width='2.5'%3E%3Cline x1='30' y1='5' x2='30' y2='14'/%3E%3Cline x1='30' y1='46' x2='30' y2='55'/%3E%3Cline x1='5' y1='30' x2='14' y2='30'/%3E%3Cline x1='46' y1='30' x2='55' y2='30'/%3E%3Cline x1='12' y1='12' x2='18' y2='18'/%3E%3Cline x1='42' y1='42' x2='48' y2='48'/%3E%3Cline x1='12' y1='48' x2='18' y2='42'/%3E%3Cline x1='42' y1='18' x2='48' y2='12'/%3E%3C/g%3E%3C/g%3E%3Cg transform='translate(180,320)'%3E%3Cpath d='M20,5 Q4,15 7,30 Q11,46 20,49 Q29,46 33,30 Q36,15 20,5 Z' fill='%232D9F6A'/%3E%3C/g%3E%3Cg transform='translate(80,380)'%3E%3Cpath d='M8,25 Q14,12 26,12 Q38,12 42,24 L44,30 L42,32 L24,32 Q12,32 8,25 Z' fill='%23A050A0'/%3E%3Ccircle cx='36' cy='20' r='2' fill='%23F8C630'/%3E%3C/g%3E%3Cg transform='translate(380,360)'%3E%3Cellipse cx='20' cy='30' rx='15' ry='18' fill='%23E55934'/%3E%3Cpath d='M20,15 L25,8' stroke='%232D9F6A' stroke-width='2'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E"),
    /* Layer 2: labirinto haitiano (medio) inspirado na ceramica */
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180' viewBox='0 0 180 180'%3E%3Cg fill='none' stroke='%23F8C630' stroke-width='1.5' opacity='0.06'%3E%3Crect x='25' y='25' width='130' height='130'/%3E%3Crect x='40' y='40' width='100' height='100'/%3E%3Crect x='55' y='55' width='70' height='70'/%3E%3Crect x='70' y='70' width='40' height='40' fill='%23E55934' fill-opacity='0.15'/%3E%3Cline x1='90' y1='25' x2='90' y2='40'/%3E%3Cline x1='90' y1='140' x2='90' y2='155'/%3E%3Cline x1='25' y1='90' x2='40' y2='90'/%3E%3Cline x1='140' y1='90' x2='155' y2='90'/%3E%3C/g%3E%3C/svg%3E"),
    /* Layer 3: pontilhado (estilo aborigene-haitiano de pottery) */
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40' viewBox='0 0 40 40'%3E%3Cg fill='%23FAF3DD' opacity='0.04'%3E%3Ccircle cx='5' cy='5' r='0.8'/%3E%3Ccircle cx='15' cy='10' r='0.8'/%3E%3Ccircle cx='25' cy='5' r='0.8'/%3E%3Ccircle cx='35' cy='12' r='0.8'/%3E%3Ccircle cx='10' cy='20' r='0.8'/%3E%3Ccircle cx='20' cy='25' r='0.8'/%3E%3Ccircle cx='30' cy='22' r='0.8'/%3E%3Ccircle cx='5' cy='32' r='0.8'/%3E%3Ccircle cx='18' cy='35' r='0.8'/%3E%3Ccircle cx='28' cy='32' r='0.8'/%3E%3C/g%3E%3C/svg%3E"),
    /* Layer 4: glow quente nos cantos */
    radial-gradient(circle at 8% 12%, rgba(229,89,52,0.18) 0%, transparent 35%),
    radial-gradient(circle at 92% 88%, rgba(45,159,106,0.16) 0%, transparent 35%),
    radial-gradient(circle at 70% 15%, rgba(248,198,48,0.10) 0%, transparent 40%),
    radial-gradient(circle at 20% 85%, rgba(192,50,33,0.10) 0%, transparent 35%);
  background-size:
    480px 480px,    /* motivos tropicais */
    180px 180px,    /* labirinto */
    40px 40px,      /* pontilhado */
    auto, auto, auto, auto;
  background-attachment: fixed;
}

/* Vignette: escurece bordas pra focar conteudo */
.stApp::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(ellipse 80% 80% at 50% 50%, transparent 50%, rgba(0,0,0,0.45) 100%);
  z-index: 0;
}

/* Main container fica acima do vignette */
.main, .stMain, [data-testid="stMain"] {
  position: relative;
  z-index: 2;
}

/* ---- Icones tropicais flutuantes (decoracao fixa nos cantos) ---- */
.tropical-decor {
  position: fixed;
  pointer-events: none;
  z-index: 1;
  opacity: 0.15;
}
.tropical-decor.palm-top-right {
  top: 20px; right: 20px; width: 80px; height: 100px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 80'%3E%3Crect x='28' y='40' width='4' height='40' fill='%23A0522D'/%3E%3Cpath d='M30,40 Q12,32 3,17' stroke='%232D9F6A' stroke-width='3' fill='none' stroke-linecap='round'/%3E%3Cpath d='M30,40 Q48,32 57,17' stroke='%232D9F6A' stroke-width='3' fill='none' stroke-linecap='round'/%3E%3Cpath d='M30,40 Q40,22 50,3' stroke='%232D9F6A' stroke-width='3' fill='none' stroke-linecap='round'/%3E%3Cpath d='M30,40 Q20,22 10,3' stroke='%232D9F6A' stroke-width='3' fill='none' stroke-linecap='round'/%3E%3Cpath d='M30,40 Q30,25 30,5' stroke='%232D9F6A' stroke-width='3' fill='none' stroke-linecap='round'/%3E%3Ccircle cx='28' cy='42' r='2.5' fill='%23E55934'/%3E%3Ccircle cx='32' cy='44' r='2.5' fill='%23F8C630'/%3E%3C/svg%3E");
  background-size: contain;
  background-repeat: no-repeat;
  animation: floatSlow 6s ease-in-out infinite;
}
.tropical-decor.sun-bottom-left {
  bottom: 30px; left: 30px; width: 70px; height: 70px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 60'%3E%3Ccircle cx='30' cy='30' r='12' fill='%23F8C630'/%3E%3Cg stroke='%23E55934' stroke-width='2.5' stroke-linecap='round'%3E%3Cline x1='30' y1='5' x2='30' y2='14'/%3E%3Cline x1='30' y1='46' x2='30' y2='55'/%3E%3Cline x1='5' y1='30' x2='14' y2='30'/%3E%3Cline x1='46' y1='30' x2='55' y2='30'/%3E%3Cline x1='12' y1='12' x2='18' y2='18'/%3E%3Cline x1='42' y1='42' x2='48' y2='48'/%3E%3Cline x1='12' y1='48' x2='18' y2='42'/%3E%3Cline x1='42' y1='18' x2='48' y2='12'/%3E%3C/g%3E%3C/svg%3E");
  background-size: contain;
  background-repeat: no-repeat;
  animation: spinSlow 24s linear infinite, floatSlow 5s ease-in-out infinite;
}
.tropical-decor.leaf-top-left {
  top: 80px; left: 25px; width: 60px; height: 75px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 50'%3E%3Cpath d='M20,5 Q4,15 7,30 Q11,46 20,49 Q29,46 33,30 Q36,15 20,5 Z' fill='%232D9F6A' stroke='%230F2A1D' stroke-width='1'/%3E%3Cpath d='M20,8 L20,46 M13,18 L13,28 M27,18 L27,28 M16,32 L16,40 M24,32 L24,40' stroke='%230F2A1D' stroke-width='1.2' opacity='0.7'/%3E%3Ccircle cx='13' cy='28' r='2' fill='%230F2A1D'/%3E%3Ccircle cx='27' cy='28' r='2' fill='%230F2A1D'/%3E%3Ccircle cx='16' cy='40' r='1.5' fill='%230F2A1D'/%3E%3Ccircle cx='24' cy='40' r='1.5' fill='%230F2A1D'/%3E%3C/svg%3E");
  background-size: contain;
  background-repeat: no-repeat;
  animation: floatSlow 7s ease-in-out infinite;
  animation-delay: -2s;
}
.tropical-decor.bird-bottom-right {
  bottom: 50px; right: 40px; width: 80px; height: 55px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 50 40'%3E%3Cpath d='M8,25 Q14,12 26,12 Q38,12 42,24 L44,30 L42,32 L24,32 Q12,32 8,25 Z' fill='%23A050A0' stroke='%230F2A1D' stroke-width='1'/%3E%3Cpath d='M14,18 Q18,16 22,18 M28,16 Q32,14 36,16' stroke='%23E55934' stroke-width='1.5' fill='none'/%3E%3Ccircle cx='36' cy='20' r='2.5' fill='%23F8C630'/%3E%3Ccircle cx='36' cy='20' r='1' fill='%230F2A1D'/%3E%3Cpath d='M42,22 L50,20 L42,24 Z' fill='%23F8C630'/%3E%3Cpath d='M14,32 L11,38 L18,35 Z' fill='%23A050A0'/%3E%3C/svg%3E");
  background-size: contain;
  background-repeat: no-repeat;
  animation: floatSlow 8s ease-in-out infinite;
  animation-delay: -3s;
}

@keyframes floatSlow {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50%      { transform: translateY(-12px) rotate(3deg); }
}
@keyframes spinSlow {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .tropical-decor { opacity: 0.08; transform: scale(0.7); }
  .tropical-decor.palm-top-right { top: 10px; right: 10px; }
  .tropical-decor.sun-bottom-left { bottom: 60px; left: 10px; }
  .tropical-decor.leaf-top-left, .tropical-decor.bird-bottom-right { display: none; }
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

/* ---- Tabs: card flutuante caribenho, separado do fundo rico ---- */
.stTabs [data-baseweb="tab-list"] {
  gap: 0.5rem !important;
  padding: 0.6rem !important;
  background: linear-gradient(135deg,
    rgba(6,18,36,0.92) 0%,
    rgba(10,22,40,0.92) 100%) !important;
  border-radius: 16px !important;
  border: 1px solid rgba(248,198,48,0.20);
  box-shadow:
    0 8px 32px rgba(0,0,0,0.4),
    inset 0 1px 0 rgba(250,243,221,0.06);
  position: relative;
  overflow: visible;
}
/* Listra de cor no topo das tabs (estilo bandeira) */
.stTabs [data-baseweb="tab-list"]::before {
  content: "";
  position: absolute;
  top: -2px; left: 12px; right: 12px; height: 3px;
  background: linear-gradient(90deg, var(--c-orange), var(--c-yellow), var(--c-green), var(--c-red));
  border-radius: 2px;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 10px !important;
  padding: 0.7rem 1.4rem !important;
  font-weight: 600 !important;
  font-size: 1rem !important;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
  border: 1px solid transparent !important;
  color: rgba(250,243,221,0.7) !important;
}
.stTabs [data-baseweb="tab"]:hover {
  background: rgba(248,198,48,0.08) !important;
  color: var(--c-yellow) !important;
  transform: translateY(-1px);
}
.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg, var(--c-orange) 0%, var(--c-yellow) 100%) !important;
  color: #061224 !important;
  border-color: rgba(250,243,221,0.3) !important;
  box-shadow: 0 4px 16px rgba(229,89,52,0.4);
  font-weight: 700 !important;
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

/* ---- Sidebar: 100% solida em mobile, padrao decorativo em desktop ---- */
[data-testid="stSidebar"],
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #061322 0%, #0a1a2e 50%, #051219 100%) !important;
  border-right: 2px solid var(--c-orange) !important;
  box-shadow: 8px 0 40px rgba(0,0,0,0.6) !important;
  opacity: 1 !important;
  z-index: 999999 !important;
}
[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] > div {
  background: transparent !important;
}
/* Padrao labirinto haitiano dentro da sidebar */
[data-testid="stSidebar"]::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='60' viewBox='0 0 60 60'%3E%3Cg fill='none' stroke='%23F8C630' stroke-width='1' opacity='0.08'%3E%3Crect x='10' y='10' width='40' height='40'/%3E%3Crect x='18' y='18' width='24' height='24'/%3E%3Crect x='25' y='25' width='10' height='10' fill='%23E55934' fill-opacity='0.3'/%3E%3C/g%3E%3C/svg%3E");
  background-repeat: repeat;
  pointer-events: none;
  z-index: -1;
}
/* Borda decorativa colorida no topo da sidebar */
[data-testid="stSidebar"]::after {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0; height: 5px;
  background: linear-gradient(90deg, var(--c-orange) 0%, var(--c-yellow) 33%, var(--c-green) 66%, var(--c-red) 100%);
  z-index: 1000;
}

@media (max-width: 768px) {
  [data-testid="stSidebar"],
  section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #061322, #0a1a2e) !important;
    box-shadow: 6px 0 50px rgba(0,0,0,0.9) !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
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
/* Decoracoes SVG no banner (sol e palmeira) */
.welcome-deco-left, .welcome-deco-right {
  position: absolute;
  width: 80px;
  height: 80px;
  opacity: 0.35;
  pointer-events: none;
}
.welcome-deco-left {
  top: 50%; left: -10px;
  transform: translateY(-50%);
  animation: spinSlow 30s linear infinite;
}
.welcome-deco-right {
  top: 50%; right: -5px;
  transform: translateY(-50%);
  animation: floatSlow 5s ease-in-out infinite;
}
@media (max-width: 768px) {
  .welcome-deco-left, .welcome-deco-right { display: none; }
  .welcome-banner { padding: 1.2rem 1.2rem; }
}

/* ---- Divider decorativo entre secoes (tres variantes) ---- */
.divider-haiti {
  margin: 2rem 0;
  height: 32px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 32'%3E%3Ccircle cx='50' cy='16' r='8' fill='%23F8C630' stroke='%23E55934' stroke-width='2'/%3E%3Cpolygon points='50,8 56,16 50,24 44,16' fill='%23C03221'/%3E%3Cline x1='0' y1='16' x2='38' y2='16' stroke='%23E55934' stroke-width='2'/%3E%3Cline x1='62' y1='16' x2='100' y2='16' stroke='%23E55934' stroke-width='2'/%3E%3Ccircle cx='20' cy='16' r='2.5' fill='%232D9F6A'/%3E%3Ccircle cx='80' cy='16' r='2.5' fill='%232D9F6A'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: center;
  background-size: contain;
  opacity: 0.8;
}
.divider-leaves {
  margin: 1.5rem 0;
  height: 40px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 40'%3E%3Cpath d='M0,20 Q15,5 30,20 T60,20 T90,20 T120,20 T150,20 T180,20 T200,20' stroke='%23E55934' stroke-width='2' fill='none' opacity='0.5'/%3E%3Cpath d='M40,15 Q45,8 50,15 Q55,22 60,15' stroke='%232D9F6A' stroke-width='2' fill='%232D9F6A' fill-opacity='0.3'/%3E%3Cpath d='M140,15 Q145,8 150,15 Q155,22 160,15' stroke='%232D9F6A' stroke-width='2' fill='%232D9F6A' fill-opacity='0.3'/%3E%3Ccircle cx='100' cy='20' r='6' fill='%23F8C630' stroke='%23E55934' stroke-width='1.5'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: center;
  background-size: contain;
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

/* ---- Cards de resultado: estilo SELO POSTAL com bordas tracejadas ---- */
[data-testid="stContainer"] [data-testid="stVerticalBlockBorderWrapper"] {
  position: relative;
  background: linear-gradient(135deg, rgba(10,22,40,0.7), rgba(15,42,29,0.5)) !important;
  border: 2px dashed rgba(248,198,48,0.25) !important;
  border-radius: 12px !important;
  transition: all 0.3s ease;
  padding: 1rem !important;
}
[data-testid="stContainer"] [data-testid="stVerticalBlockBorderWrapper"]:hover {
  border-color: var(--c-yellow) !important;
  box-shadow: var(--shadow-card-hover), 0 0 24px rgba(248,198,48,0.15);
  transform: translateY(-2px);
}
/* Ornamentos nos 4 cantos dos cards (estilo selo) */
[data-testid="stContainer"] [data-testid="stVerticalBlockBorderWrapper"]::before,
[data-testid="stContainer"] [data-testid="stVerticalBlockBorderWrapper"]::after {
  content: "✦";
  position: absolute;
  font-size: 0.9rem;
  color: var(--c-orange);
  opacity: 0.6;
}
[data-testid="stContainer"] [data-testid="stVerticalBlockBorderWrapper"]::before {
  top: 6px; left: 10px;
}
[data-testid="stContainer"] [data-testid="stVerticalBlockBorderWrapper"]::after {
  bottom: 6px; right: 10px;
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

/* ---- Mode Pase Telefon: UI ultra simplificada pro imigrante ---- */
.passa-hero {
  font-size: 2.8rem;
  font-weight: 800;
  text-align: center;
  background: linear-gradient(135deg, var(--c-yellow) 0%, var(--c-orange) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 1rem 0 0.3rem;
  letter-spacing: -0.02em;
  font-family: 'Fraunces', serif !important;
  font-style: italic;
}
.passa-instructions {
  font-size: 1.5rem;
  text-align: center;
  color: var(--c-cream);
  margin-bottom: 1.5rem;
  font-weight: 500;
}
.passa-instructions .pt-translation {
  display: block;
  font-size: 0.95rem;
  opacity: 0.55;
  margin-top: 0.3rem;
  font-style: italic;
}
.passa-result-kr {
  font-size: 3.2rem;
  font-weight: 700;
  text-align: center;
  color: #d1fae5;
  padding: 1.8rem 1.5rem;
  background: linear-gradient(135deg, rgba(45,159,106,0.20), rgba(45,159,106,0.06));
  border-radius: 18px;
  border-left: 8px solid var(--c-green);
  border-right: 8px solid var(--c-green);
  margin: 1.2rem 0;
  animation: slideUpFade 0.5s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: var(--shadow-card);
  line-height: 1.15;
}
.passa-result-pt {
  font-size: 2.5rem;
  font-weight: 700;
  text-align: center;
  color: #fef3c7;
  padding: 1.5rem 1.4rem;
  background: linear-gradient(135deg, rgba(248,198,48,0.15), rgba(248,198,48,0.04));
  border-radius: 18px;
  border: 3px dashed rgba(248,198,48,0.5);
  margin: 1.2rem 0;
  animation: slideUpFade 0.7s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: var(--shadow-card);
  line-height: 1.15;
}
.passa-divider-arrow {
  text-align: center;
  font-size: 2.5rem;
  color: var(--c-yellow);
  margin: 0.3rem 0;
  animation: bounce 2s ease-in-out infinite;
}
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50%      { transform: translateY(6px); }
}
.passa-section-label {
  font-size: 0.95rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  opacity: 0.7;
  margin-top: 0.5rem;
  text-align: center;
}
@media (max-width: 768px) {
  .passa-hero { font-size: 2rem; }
  .passa-instructions { font-size: 1.2rem; }
  .passa-result-kr { font-size: 2.2rem; padding: 1.2rem; }
  .passa-result-pt { font-size: 1.7rem; padding: 1rem; }
  .passa-divider-arrow { font-size: 2rem; }
}
</style>
""", unsafe_allow_html=True)

# Decoracoes tropicais fixas (palm, sol, folha, passaro flutuando nos cantos)
st.markdown("""
<div class="tropical-decor palm-top-right"></div>
<div class="tropical-decor sun-bottom-left"></div>
<div class="tropical-decor leaf-top-left"></div>
<div class="tropical-decor bird-bottom-right"></div>
""", unsafe_allow_html=True)

st.title("🎓 Oficina de Imigrantes")
st.caption("**Kreyòl Ayisyen** ↔ **Português** — dicionário com áudio + conversa ao vivo")

# Banner de boas-vindas BR + Haiti (calor de oficina, decorado caribenho)
st.markdown("""
<div class="welcome-banner">
  <svg class="welcome-deco-left" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
    <circle cx="40" cy="40" r="14" fill="#F8C630"/>
    <g stroke="#E55934" stroke-width="3" stroke-linecap="round">
      <line x1="40" y1="8" x2="40" y2="18"/>
      <line x1="40" y1="62" x2="40" y2="72"/>
      <line x1="8" y1="40" x2="18" y2="40"/>
      <line x1="62" y1="40" x2="72" y2="40"/>
      <line x1="17" y1="17" x2="24" y2="24"/>
      <line x1="56" y1="56" x2="63" y2="63"/>
      <line x1="17" y1="63" x2="24" y2="56"/>
      <line x1="56" y1="24" x2="63" y2="17"/>
    </g>
  </svg>
  <svg class="welcome-deco-right" viewBox="0 0 60 80" xmlns="http://www.w3.org/2000/svg">
    <rect x="28" y="40" width="4" height="40" fill="#A0522D"/>
    <path d="M30,40 Q12,32 3,17" stroke="#2D9F6A" stroke-width="3" fill="none" stroke-linecap="round"/>
    <path d="M30,40 Q48,32 57,17" stroke="#2D9F6A" stroke-width="3" fill="none" stroke-linecap="round"/>
    <path d="M30,40 Q40,22 50,3" stroke="#2D9F6A" stroke-width="3" fill="none" stroke-linecap="round"/>
    <path d="M30,40 Q20,22 10,3" stroke="#2D9F6A" stroke-width="3" fill="none" stroke-linecap="round"/>
    <circle cx="28" cy="42" r="2.5" fill="#E55934"/>
    <circle cx="32" cy="44" r="2.5" fill="#F8C630"/>
  </svg>
  <div class="welcome-pt">🇧🇷 Olá, parceiro! Bem-vindo. Aqui estamos juntos pra aprender. Pode contar comigo, tô junto.</div>
  <div class="welcome-kr">🇭🇹 Bonjou, zanmi m! Byenvini lakay nou. Nou ansanm pou aprann. Konte sou mwen, mwen avèk ou.</div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    # QR code pra celulares na mesma rede conectarem
    local_url = _get_local_url()
    if local_url:
        st.markdown("### 📱 Conecta o celular")
        qr_png = _make_qr_png(local_url)
        if qr_png:
            st.image(qr_png, caption=local_url, use_container_width=True)
        else:
            st.code(local_url)
        st.caption("Mesma WiFi do note. Aceite o aviso de certificado na 1ª vez.")
        st.markdown("---")

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
        "- **Conversa**: microfone pra falar ao vivo com o imigrante\n"
        "- **Mòd Imigran**: passa o celular pro haitiano"
    )

tab_dic, tab_conversa, tab_imigrante, tab_passa = st.tabs([
    "📚 Dicionário",
    "🎙️ Conversa ao vivo",
    "🤝 Mòd Imigran",
    "📱 Pase Telefòn",
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

    # Inicializa estado da sessao
    if "conv_history" not in st.session_state:
        st.session_state.conv_history = []
    if "last_pt_audio_hash" not in st.session_state:
        st.session_state.last_pt_audio_hash = None
    if "last_kr_audio_hash" not in st.session_state:
        st.session_state.last_kr_audio_hash = None

    # ===== HISTORICO RECENTE =====
    if st.session_state.conv_history:
        with st.expander(f"📜 Conversa recente ({len(st.session_state.conv_history)} turnos)", expanded=False):
            for i, turn in enumerate(st.session_state.conv_history[:5]):
                if turn["direction"] == "pt_to_kr":
                    src_flag, tgt_flag, tgt_color = "🇧🇷", "🇭🇹", "var(--c-kr)"
                    src_label, tgt_label = "Você disse", "Em kreyòl"
                else:
                    src_flag, tgt_flag, tgt_color = "🇭🇹", "🇧🇷", "var(--c-pt)"
                    src_label, tgt_label = "Ele/ela disse", "Em português"

                with st.container(border=True):
                    st.markdown(
                        f"<div class='label'>{src_flag} {src_label}</div>"
                        f"<div style='font-size:1.3rem;font-weight:600;margin-bottom:0.4rem'>{turn['src_text'] or '(silêncio)'}</div>"
                        f"<div class='label'>{tgt_flag} {tgt_label}</div>"
                        f"<div style='font-size:1.3rem;font-weight:600;color:{tgt_color}'>{turn['tgt_text'] or '(traduzindo falhou)'}</div>",
                        unsafe_allow_html=True,
                    )
                    if turn.get("wav_bytes"):
                        st.audio(turn["wav_bytes"], format="audio/wav")
                        st.caption("🔁 Clique no play pra ouvir de novo")

            col_clear, _ = st.columns([1, 3])
            with col_clear:
                if st.button("🗑️ Limpar histórico", key="clear_history"):
                    st.session_state.conv_history = []
                    st.session_state.last_pt_audio_hash = None
                    st.session_state.last_kr_audio_hash = None
                    st.rerun()
        st.markdown("<div class='divider-leaves'></div>", unsafe_allow_html=True)

    sub_pt, sub_kr = st.columns(2)

    # ----- 1. Você fala PT, mostra em kreyòl -----
    with sub_pt:
        st.markdown("### 🇧🇷 → 🇭🇹  Você fala em **Português**")
        st.caption("Para o imigrante entender o que você quer dizer")
        pt_audio = st.audio_input("🎙️ Gravar sua voz (PT):", key="pt_input")
        if pt_audio:
            audio_bytes = pt_audio.getvalue()
            audio_hash = hashlib.sha1(audio_bytes).hexdigest()
            # So processa se for uma gravacao NOVA (evita duplicar historico em reruns)
            is_new = audio_hash != st.session_state.last_pt_audio_hash
            if is_new:
                status_slot = st.empty()
                status_slot.markdown(
                    "<div class='status-pill'><span class='status-dot'></span> "
                    "<span>✍️ Transcrevendo e traduzindo…</span></div>",
                    unsafe_allow_html=True,
                )
                from conversa import pt_says_to_kr
                result = pt_says_to_kr(audio_bytes)
                status_slot.empty()

                wav = None
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
                    except Exception as e:
                        st.warning(f"TTS kreyòl indisponível: {e}")
                    tts_slot.empty()

                # Salva no historico (no topo, mais recente primeiro)
                st.session_state.conv_history.insert(0, {
                    "direction": "pt_to_kr",
                    "src_text": result["pt"],
                    "tgt_text": result["kr"],
                    "wav_bytes": wav,
                    "ts": time.time(),
                })
                # Limita historico a 10 entradas
                st.session_state.conv_history = st.session_state.conv_history[:10]
                st.session_state.last_pt_audio_hash = audio_hash

            # Mostra o resultado mais recente (whether just processed or from history)
            if st.session_state.conv_history and st.session_state.conv_history[0]["direction"] == "pt_to_kr":
                latest = st.session_state.conv_history[0]
                st.markdown("<div class='label'>🇧🇷 Você disse</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='big-result'>{latest['src_text'] or '(silêncio)'}</div>", unsafe_allow_html=True)
                st.markdown("<div class='label'>🇭🇹 Em kreyòl (mostre pro imigrante)</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='big-result' style='color:var(--c-kr)'>{latest['tgt_text'] or '(traduzindo falhou)'}</div>", unsafe_allow_html=True)
                if latest.get("wav_bytes"):
                    st.audio(latest["wav_bytes"], format="audio/wav", autoplay=is_new)
                    st.caption("🔊 Toca pra o imigrante ouvir (botão de play repete)")

    # ----- 2. Imigrante fala KR, você lê em PT -----
    with sub_kr:
        st.markdown("### 🇭🇹 → 🇧🇷  Imigrante fala em **Kreyòl**")
        st.caption("Para você entender o que ele/ela está dizendo")
        kr_audio = st.audio_input("🎙️ Pedir pro imigrante falar aqui:", key="kr_input")
        if kr_audio:
            audio_bytes = kr_audio.getvalue()
            audio_hash = hashlib.sha1(audio_bytes).hexdigest()
            is_new = audio_hash != st.session_state.last_kr_audio_hash
            if is_new:
                status_slot2 = st.empty()
                status_slot2.markdown(
                    "<div class='status-pill'><span class='status-dot'></span> "
                    "<span>🎙️ MMS escutando kreyòl…</span></div>",
                    unsafe_allow_html=True,
                )
                from conversa import kr_says_to_pt
                result = kr_says_to_pt(audio_bytes)
                status_slot2.empty()

                st.session_state.conv_history.insert(0, {
                    "direction": "kr_to_pt",
                    "src_text": result["kr"],
                    "tgt_text": result["pt"],
                    "wav_bytes": None,
                    "ts": time.time(),
                })
                st.session_state.conv_history = st.session_state.conv_history[:10]
                st.session_state.last_kr_audio_hash = audio_hash

            # Mostra o KR->PT mais recente
            recent_kr = next((t for t in st.session_state.conv_history if t["direction"] == "kr_to_pt"), None)
            if recent_kr:
                st.markdown("<div class='label'>🇭🇹 Ele/ela disse</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='big-result' style='color:var(--c-kr)'>{recent_kr['src_text'] or '(silêncio)'}</div>", unsafe_allow_html=True)
                st.markdown("<div class='label'>🇧🇷 Em português</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='big-result' style='color:var(--c-pt)'>{recent_kr['tgt_text'] or '(traduzindo falhou)'}</div>", unsafe_allow_html=True)

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

# ----------------- PASE TELEFON (Pass the phone) -----------------
# Tab ultra-simplificada: voluntario passa o celular pro imigrante.
# Imigrante so ve um botao gigante, grava, ve a tradução em letras enormes.
with tab_passa:
    st.markdown("<div class='passa-hero'>📱 Pase telefòn nan</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='passa-instructions'>"
        "Klike sou bouton an pou pale"
        "<span class='pt-translation'>(Clique no botão pra falar)</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Estado especifico desta aba
    if "passa_audio_hash" not in st.session_state:
        st.session_state.passa_audio_hash = None
    if "passa_result" not in st.session_state:
        st.session_state.passa_result = None

    # Mic gigante
    passa_audio = st.audio_input(
        "🎙️ Klike isit la pou pale",
        key="passa_input",
    )

    if passa_audio:
        audio_bytes = passa_audio.getvalue()
        audio_hash = hashlib.sha1(audio_bytes).hexdigest()
        is_new = audio_hash != st.session_state.passa_audio_hash
        if is_new:
            status_passa = st.empty()
            status_passa.markdown(
                "<div class='status-pill' style='margin: 1rem auto; display: flex; justify-content: center'>"
                "<span class='status-dot'></span> <span>MMS ap koute…</span>"
                "</div>",
                unsafe_allow_html=True,
            )
            from conversa import kr_says_to_pt
            result = kr_says_to_pt(audio_bytes)
            status_passa.empty()
            st.session_state.passa_result = result
            st.session_state.passa_audio_hash = audio_hash
            # Tambem registra no historico geral pra voluntario ver na aba Conversa
            st.session_state.conv_history.insert(0, {
                "direction": "kr_to_pt",
                "src_text": result["kr"],
                "tgt_text": result["pt"],
                "wav_bytes": None,
                "ts": time.time(),
            })
            st.session_state.conv_history = st.session_state.conv_history[:10]

    # Mostra resultado mais recente com letras GIGANTES
    if st.session_state.passa_result:
        r = st.session_state.passa_result
        st.markdown("<div class='passa-section-label'>🇭🇹 Sa ou di</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='passa-result-kr'>{r['kr'] or '(silans)'}</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='passa-divider-arrow'>↓</div>", unsafe_allow_html=True)
        st.markdown("<div class='passa-section-label'>🇧🇷 Pwofesè a wè sa</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='passa-result-pt'>{r['pt'] or '(pa ka tradui)'}</div>",
            unsafe_allow_html=True,
        )

        # Botao pra resetar e gravar novamente
        col_reset, _ = st.columns([1, 2])
        with col_reset:
            if st.button("🔄 Pale ankò (Falar de novo)", key="passa_reset", use_container_width=True):
                st.session_state.passa_result = None
                st.session_state.passa_audio_hash = None
                st.rerun()
    else:
        # Estado inicial: instrucao visual destacada
        st.markdown(
            "<div style='text-align:center; opacity:0.5; margin-top:1.5rem; font-size:1.1rem'>"
            "⬆️ Klike sou bouton anwo a pou kòmanse"
            "</div>",
            unsafe_allow_html=True,
        )

# ===== Footer caribenho em todas as paginas =====
st.markdown("""
<div class="caribbean-footer">
  <small>🇧🇷 Oficina de Imigrantes &middot; Kreyòl ↔ Português &middot; 🇭🇹</small><br>
  <small style="opacity:0.6">Konte sou mwen, mwen avèk ou</small>
</div>
""", unsafe_allow_html=True)
