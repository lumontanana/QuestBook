import streamlit as st

from questbook.qa import ask
from questbook.settings import get_settings

settings = get_settings()

st.set_page_config(page_title=settings.app_name, page_icon="QB", layout="centered")
st.title(settings.app_name)
st.caption("Pregunta sobre los libros ya indexados en Milvus.")

with st.form("question-form"):
    question = st.text_area("Pregunta", placeholder="Escribe aqui tu pregunta sobre el libro...")
    submitted = st.form_submit_button("Enviar", type="primary")

if submitted:
    if not question.strip():
        st.warning("Escribe una pregunta antes de enviar.")
    else:
        with st.spinner("Buscando en tus libros..."):
            answer, sources = ask(question, settings=settings)

        st.subheader("Respuesta")
        st.write(answer)

        with st.expander("Fuentes consultadas"):
            for source in sources:
                st.markdown(f"**{source.source}** pagina `{source.page}`")
                st.caption(source.content[:700])
