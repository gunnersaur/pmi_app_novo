import re
import unicodedata
import streamlit as st


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Verifica preenchimento - Cadastro - Legalização",
    page_icon="🔎",
    layout="wide"
)


# ============================================================
# MENU LATERAL
# ============================================================

st.sidebar.title("Aplicações")

st.sidebar.markdown(
    """
    - [App](https://pmiappnovo-copia.streamlit.app/)
    - [CV Zona](https://pmiappnovo-copia.streamlit.app/cv_zona)
    - [Documentação Complementar - ALF](https://pmiappnovo-copia.streamlit.app/documentacao-complementar-ALF)
    - [Estudo de Impacto de Vizinhança](https://pmiappnovo-copia.streamlit.app/estudo-de-impacto-de-vizinhanca)
    - [Links](https://pmiappnovo-copia.streamlit.app/links)
    - [Verifica Aprova](https://pmiappnovo-copia.streamlit.app/verifica-aprova)
    """
)


# ============================================================
# FUNÇÕES DE NORMALIZAÇÃO
# ============================================================

def normalizar_texto(valor):

    if valor is None:
        return ""

    valor = str(valor)

    valor = unicodedata.normalize(
        "NFKC",
        valor
    )

    valor = re.sub(
        r"\s+",
        " ",
        valor
    )

    return valor.strip().upper()


def normalizar_sem_acentos(valor):

    valor = normalizar_texto(valor)

    valor = unicodedata.normalize(
        "NFD",
        valor
    )

    return "".join(
        c
        for c in valor
        if unicodedata.category(c) != "Mn"
    )


def normalizar_razao_social(valor):

    valor = normalizar_sem_acentos(valor)

    return re.sub(
        r"[^A-Z0-9]",
        "",
        valor
    )


def normalizar_natureza_juridica(valor):

    valor = normalizar_sem_acentos(valor)

    return re.sub(
        r"[^A-Z0-9]",
        "",
        valor
    )
