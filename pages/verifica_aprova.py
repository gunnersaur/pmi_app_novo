import streamlit as st
import pandas as pd
import re


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Verifica preenchimento - ALF - Aprova Digital",
    page_icon="images/favicon.png",
    layout="wide"
)


# ============================================================
# FUNÇÃO LIMPAR
# ============================================================

def limpar_campos():
    st.session_state["texto_aprova"] = ""
    st.session_state["texto_cnpj"] = ""


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("Links úteis")

    st.page_link("app.py", label="Início")
    st.page_link("pages/cv_zona.py", label="CV Zona")
    st.page_link(
        "pages/documentacao-complementar-ALF.py",
        label="Documentação Complementar - ALF"
    )
    st.page_link(
        "pages/estudo-de-impacto-de-vizinhanca.py",
        label="Estudo de Impacto de Vizinhança"
    )
    st.page_link(
        "pages/links.py",
        label="Links"
    )
    st.page_link(
        "pages/verifica_aprova.py",
        label="Verifica Aprova"
    )


# ============================================================
# TÍTULO
# ============================================================

st.title("Verifica preenchimento - ALF - Aprova Digital")

st.write(
    "Cole abaixo os textos extraídos do Aprova Digital e do CNPJ "
    "para realizar a conferência."
)


# ============================================================
# ÁREA DE ENTRADA
# ============================================================

col1, col2 = st.columns(2)


with col1:

    st.subheader("📄 Aprova Digital")

    st.text_area(
        "Cole todo o texto da página do processo do Aprova Digital:",
        height=350,
        key="texto_aprova"
    )


with col2:

    st.subheader("🏢 CNPJ")

    st.text_area(
        "Cole todo o texto do CNPJ:",
        height=350,
        key="texto_cnpj"
    )


# ============================================================
# BOTÕES
# ============================================================

col_b1, col_b2 = st.columns([1, 5])

with col_b1:

    st.button(
        "🗑️ Limpar",
        on_click=limpar_campos,
        use_container_width=True
    )


with col_b2:

    analisar = st.button(
        "🔎 Analisar",
        type="primary",
        use_container_width=True
    )


# ============================================================
# NÃO PROCESSAR ENQUANTO NÃO HOUVER DADOS
# ============================================================

texto_aprova = st.session_state.get("texto_aprova", "")
texto_cnpj = st.session_state.get("texto_cnpj", "")


if not analisar:

    st.info(
        "Cole os dois documentos acima e clique em **Analisar**."
    )

    st.stop()


if not texto_aprova.strip():

    st.warning(
        "O texto do **Aprova Digital** não foi preenchido."
    )

    st.stop()


if not texto_cnpj.strip():

    st.warning(
        "O texto do **CNPJ** não foi preenchido."
    )

    st.stop()


# ============================================================
# A PARTIR DAQUI COMEÇA A ANÁLISE
# ============================================================

st.markdown("---")

st.subheader("🔎 Resultado da análise")

# Continue aqui com as funções de extração
# e comparação.
