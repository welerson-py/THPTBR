"""Streamlit UI: Dicionario (search) + Conversa (live mic translation)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import streamlit.components.v1 as components

from embed_store import search, count

st.set_page_config(
    page_title="Oficina de Imigrantes — Kreyòl ↔ Português",
    page_icon="🎓",
    layout="wide",
)

# Big readable text for the workshop room
st.markdown("""
<style>
.big-result { font-size: 2.5rem; font-weight: 700; line-height: 1.2; margin: 0.5rem 0; }
.label { font-size: 0.9rem; opacity: 0.7; text-transform: uppercase; letter-spacing: 0.1em; }
.context-text { font-size: 0.9rem; opacity: 0.6; font-style: italic; }
</style>
""", unsafe_allow_html=True)

st.title("🎓 Oficina de Imigrantes")
st.caption("**Kreyòl Ayisyen** ↔ **Português** — dicionário com áudio + conversa ao vivo")

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

tab_dic, tab_conversa = st.tabs(["📚 Dicionário", "🎙️ Conversa ao vivo"])

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
        pt_audio = st.audio_input("Gravar sua voz (PT):", key="pt_input")
        if pt_audio:
            with st.spinner("Transcrevendo + traduzindo..."):
                from conversa import pt_says_to_kr
                result = pt_says_to_kr(pt_audio.getvalue())
            st.markdown("<div class='label'>🇧🇷 Você disse:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='big-result'>{result['pt'] or '(silêncio)'}</div>", unsafe_allow_html=True)
            st.markdown("<div class='label'>🇭🇹 Em kreyòl (mostre pro imigrante):</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='big-result' style='color:#4ade80'>{result['kr'] or '(traduzindo falhou)'}</div>", unsafe_allow_html=True)

            if result["kr"]:
                with st.spinner("Gerando áudio em kreyòl..."):
                    try:
                        from tts import synth_kreyol_wav_bytes
                        wav = synth_kreyol_wav_bytes(result["kr"])
                        st.audio(wav, format="audio/wav")
                        st.caption("🔊 Toque pra o imigrante ouvir")
                    except Exception as e:
                        st.warning(f"TTS kreyòl indisponível: {e}")

    # ----- 2. Imigrante fala KR, você lê em PT -----
    with sub_kr:
        st.markdown("### 🇭🇹 → 🇧🇷  Imigrante fala em **Kreyòl**")
        st.caption("Para você entender o que ele/ela está dizendo")
        kr_audio = st.audio_input("Pedir pro imigrante falar aqui:", key="kr_input")
        if kr_audio:
            with st.spinner("Transcrevendo kreyòl com MMS + traduzindo..."):
                from conversa import kr_says_to_pt
                result = kr_says_to_pt(kr_audio.getvalue())
            st.markdown("<div class='label'>🇭🇹 Ele/ela disse:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='big-result'>{result['kr'] or '(silêncio)'}</div>", unsafe_allow_html=True)
            st.markdown("<div class='label'>🇧🇷 Em português:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='big-result' style='color:#60a5fa'>{result['pt'] or '(traduzindo falhou)'}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.info(
        "💡 **Dica:** quanto mais perto o microfone, melhor. Headset USB ajuda muito em sala cheia. "
        "Primeira gravação demora ~30s (carrega modelo). Depois fica rápido (3-6s por turno)."
    )
