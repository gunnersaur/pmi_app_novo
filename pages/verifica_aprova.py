import re
import unicodedata
import pandas as pd
import streamlit as st
from urllib.parse import quote_plus

st.set_page_config(
    page_title="Verifica preenchimento - Cadastro - Legalização",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# FUNÇÕES DE NORMALIZAÇÃO
# ============================================================
def limpar_texto(texto):
    return (texto or "").replace("\xa0", " ").replace("\r", "\n")


def normalizar_espacos(texto):
    return re.sub(r"\s+", " ", limpar_texto(texto)).strip()


def normalizar_comparacao(texto):
    texto = normalizar_espacos(texto).upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]", "", texto)


def somente_digitos(texto):
    return re.sub(r"\D", "", texto or "")


def extrair_cnpj(texto):
    m = re.search(r"(?<!\d)(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})(?!\d)", texto or "")
    if m:
        return m.group(1)
    m = re.search(r"(?<!\d)(\d{14})(?!\d)", texto or "")
    if m:
        n = m.group(1)
        return f"{n[:2]}.{n[2:5]}.{n[5:8]}/{n[8:12]}-{n[12:]}"
    return None


def extrair_cep(texto):
    # Prefere CEP de endereço do contribuinte; exclui CEP do cabeçalho municipal quando possível.
    linhas = [normalizar_espacos(x) for x in limpar_texto(texto).splitlines() if normalizar_espacos(x)]
    candidatos = []
    for i, linha in enumerate(linhas):
        m = re.search(r"\b(\d{2}\.?\d{3}-?\d{3})\b", linha)
        if not m:
            continue
        cep = re.sub(r"\D", "", m.group(1))
        if len(cep) == 8:
            contexto = " ".join(linhas[max(0, i-2):min(len(linhas), i+2)]).upper()
            prioridade = 3 if "CEP:" in linha.upper() else 1
            if "RUA ALBERTO WERNER" in contexto or "SECRETARIA MUNICIPAL" in contexto:
                prioridade -= 3
            candidatos.append((prioridade, cep))
    if candidatos:
        cep = sorted(candidatos, key=lambda x: x[0], reverse=True)[0][1]
        return f"{cep[:5]}-{cep[5:]}"
    return None


def extrair_cnaes(texto):
    """Extrai CNAEs tanto em formato 46.87-7/01 como em formato 4687701."""
    texto = limpar_texto(texto)
    encontrados = set()
    # Formato com pontuação: 46.87-7/01 ou 49.30-2/02
    for m in re.finditer(r"(?<!\d)(\d{2})\.(\d{2})-(\d)/(\d{2})(?!\d)", texto):
        encontrados.add("".join(m.groups()))
    # Código de sete dígitos em linhas de atividade, evitando números de endereço/CEP.
    for linha in texto.splitlines():
        ln = normalizar_espacos(linha)
        if not ln:
            continue
        if re.search(r"CNAE|ATIVIDADE|COMERCIO|COMÉRCIO|TRANSPORTE|SERVIÇOS|SERVICOS", ln, re.I):
            for m in re.finditer(r"(?<!\d)(\d{7})(?!\d)", ln):
                encontrados.add(m.group(1))
        # Cadastro municipal pode pôr código e atividade em linhas separadas.
        elif re.fullmatch(r"\d{7}", ln):
            encontrados.add(ln)
    return sorted(encontrados)


def formatar_cnae(codigo):
    c = somente_digitos(codigo)
    if len(c) != 7:
        return codigo
    return f"{c[:2]}.{c[2:4]}-{c[4]}/{c[5:]}"


def obter_valor_rotulo(texto, rotulos, max_chars=160):
    """Procura rótulos no texto em formato 'Rótulo: valor' ou 'Rótulo valor'."""
