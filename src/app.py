"""Streamlit UI: search Kreyòl <-> Português with YouTube audio playback."""
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

st.title("🎓 Oficina de Imigrantes")
st.caption("Busca de palavras em **Kreyòl Ayisyen** ↔ **Português**")

with st.sidebar:
    st.header("Configurações")
    n_results = st.slider("Quantidade de resultados", 3, 20, 8)
    show_score = st.checkbox("Mostrar score de similaridade", value=False)
    try:
        db_size = count()
        st.metric("Frases no banco", db_size)
    except Exception as e:
        st.error(f"Erro ao ler banco: {e}")
    st.markdown("---")
    st.markdown("**Como usar:**")
    st.markdown(
        "- **Equipe (PT→KR):** digite em português (`comprar`, `comer`, `casa`)\n"
        "- **Aprendiz (KR→PT):** digite em kreyòl (`manje`, `achte`)\n"
        "- Clique no vídeo pra ouvir a professora dizer"
    )

query = st.text_input(
    "🔍 Buscar:",
    placeholder="ex.: 'comprar' ou 'manje'",
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

        for i, r in enumerate(results):
            with st.container(border=True):
                c1, c2 = st.columns([1, 1])
                with c1:
                    st.markdown("**🇭🇹 Kreyòl**")
                    st.markdown(f"### {r['kreyol']}")
                    if r.get("context") and r["context"].strip() != r["kreyol"].strip():
                        st.caption(f"contexto: _{r['context'][:120]}_")
                with c2:
                    st.markdown("**🇧🇷 Português**")
                    st.markdown(f"### {r['portuguese'] or '(sem tradução)'}")

                # YouTube embed with timestamp
                start_s = max(0, int(r["start"]) - 1)
                embed_url = (
                    f"https://www.youtube.com/embed/{r['video_id']}"
                    f"?start={start_s}&rel=0"
                )
                components.iframe(embed_url, height=220)

                meta_bits = [f"@ {r['start']:.1f}s"]
                if show_score:
                    meta_bits.append(f"score={r['score']:.2f}")
                st.caption(" • ".join(meta_bits))

else:
    st.info("Digite uma palavra para começar a buscar.")
