import io
import re
import unicodedata

import fitz  # PyMuPDF
import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURAÇÕES
# ============================================================

st.set_page_config(
    page_title="Verifica Cadastro Econômico x Prefeitura",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.sidebar.title("Verificação cadastral")
st.sidebar.divider()
st.sidebar.markdown(
    """
    **Comparação automática**

    Extrato do Cadastro Econômico × Prefeitura / Alvará
    """
)

st.subheader("Verifica Cadastro Econômico × Prefeitura")


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def extrair_texto_pdf(arquivo):
    """Extrai todo o texto de um PDF."""
    if arquivo is None:
        return ""

    dados = arquivo.read()
    doc = fitz.open(stream=dados, filetype="pdf")

    paginas = []
    for pagina in doc:
        paginas.append(pagina.get_text())

    return "\n".join(paginas)


def normalizar(texto):
    """
    Normaliza texto para comparação:
    - maiúsculas
    - remove acentos
    - reduz espaços
    - remove espaços antes/depois de pontuação
    """
    if texto is None:
        return ""

    texto = str(texto).strip().upper()

    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        c for c in texto
        if not unicodedata.combining(c)
    )

    texto = re.sub(r"\s+", " ", texto)

    texto = re.sub(r"\s*[,;]\s*", ",", texto)
    texto = re.sub(r"\s*-\s*", "-", texto)

    return texto.strip()


def normalizar_cnpj(texto):
    numeros = re.sub(r"\D", "", str(texto or ""))
    return numeros


def normalizar_numero(texto):
    numeros = re.sub(r"\D", "", str(texto or ""))
    return numeros


def normalizar_cep(texto):
    numeros = re.sub(r"\D", "", str(texto or ""))
    return numeros


def extrair_primeiro(padrao, texto, flags=re.IGNORECASE):
    resultado = re.search(padrao, texto, flags)
    if resultado:
        return resultado.group(1).strip()
    return ""


# ============================================================
# PARSER - EXTRATO DO CADASTRO ECONÔMICO
# ============================================================

def extrair_cadastro_economico(texto):
    """
    Extrai os campos relevantes do Extrato do Cadastro Econômico.
    A estrutura foi feita com base no documento fornecido.
    """

    dados = {}

    # CNPJ
    dados["cnpj"] = extrair_primeiro(
        r"CPF/CNPJ:\s*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})",
        texto
    )

    # Razão social
    dados["razao_social"] = extrair_primeiro(
        r"Nome:\s*\n?\s*(.*?)\s*\n\s*Nome Fantasia:",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    # Nome fantasia
    dados["nome_fantasia"] = extrair_primeiro(
        r"Nome Fantasia:\s*\n?\s*(.*?)\s*\n\s*Desc\. Natureza Jurídica:",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    # Natureza jurídica
    dados["natureza_juridica"] = extrair_primeiro(
        r"Desc\. Natureza Jurídica:\s*\n?\s*(.*?)\s*\n\s*Correio Eletrônico:",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    # Endereço
    dados["logradouro"] = extrair_primeiro(
        r"Endereço\s+Logradouro:\s*\n?\s*(.*?)\s*\n\s*Número:",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    dados["numero"] = extrair_primeiro(
        r"Endereço\s+.*?Número:\s*\n?\s*(.*?)\s*\n\s*Bairro:",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    dados["bairro"] = extrair_primeiro(
        r"Endereço\s+.*?Bairro:\s*\n?\s*(.*?)\s*\n\s*Complemento:",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    dados["complemento"] = extrair_primeiro(
        r"Endereço\s+.*?Complemento:\s*\n?\s*(.*?)\s*\n\s*CEP:",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    dados["cep"] = extrair_primeiro(
        r"Endereço\s+.*?CEP:\s*\n?\s*(\d{5}[-.]?\d{3})",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    # Todos os CNAEs do cadastro econômico.
    # O documento apresenta códigos sem pontuação.
    dados["cnaes"] = re.findall(
        r"(?<!\d)(\d{7})(?!\d)",
        texto
    )

    # Remove códigos que não são atividades econômicas caso apareçam
    # em outras partes do documento.
    inicio = texto.find("Atividade Econômica CNAE")
    fim = texto.find("Atividade Econômica Atual")

    if inicio >= 0:
        bloco_cnaes = texto[
            inicio:fim if fim > inicio else len(texto)
        ]

        dados["cnaes"] = re.findall(
            r"(?<!\d)(\d{7})(?!\d)",
            bloco_cnaes
        )

    dados["cnaes"] = list(dict.fromkeys(dados["cnaes"]))

    # Situação
    dados["situacao"] = extrair_primeiro(
        r"Nº CMC:\s*Situação:\s*\n?\s*(.*?)\s*\n\s*Horário Funcionamento:",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    # Inscrição municipal
    dados["inscricao_municipal"] = ""

    # No documento, o número aparece associado à inscrição municipal,
    # mas a extração textual pode não preservar a posição visual.
    # Mantemos vazio quando não houver marcador inequívoco.

    return dados


# ============================================================
# PARSER - PREFEITURA / ALVARÁ
# ============================================================

def extrair_prefeitura(texto):
    """
    Extrai os campos relevantes do PDF da Prefeitura.
    """

    dados = {}

    dados["protocolo"] = extrair_primeiro(
        r"Protocolo:\s*(\d+)",
        texto
    )

    dados["data_protocolo"] = extrair_primeiro(
        r"Data do Protocolo:\s*(\d{2}/\d{2}/\d{4})",
        texto
    )

    dados["acao"] = extrair_primeiro(
        r"Ação:\s*(.*?)\s*\n\s*Situação do Protocolo:",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    dados["natureza_juridica"] = extrair_primeiro(
        r"Natureza Jurídica:\s*(.*?)\s*\n\s*Nome Empresarial:",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    dados["razao_social"] = extrair_primeiro(
        r"Nome Empresarial:\s*(.*?)\s*\n\s*Nome Fantasia:",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    dados["nome_fantasia"] = extrair_primeiro(
        r"Nome Fantasia:\s*(.*?)\s*\n\s*Capital Social:",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    dados["capital_social"] = extrair_primeiro(
        r"Capital Social:\s*(.*?)\s*\n\s*Tipo de Estabelecimento:",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    dados["cnpj"] = extrair_primeiro(
        r"CNPJ:\s*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})",
        texto
    )

    dados["logradouro"] = extrair_primeiro(
        r"Logradouro:\s*(.*?)\s*\n\s*Nº",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    dados["numero"] = extrair_primeiro(
        r"Nº\s*(\d+)",
        texto
    )

    dados["complemento"] = extrair_primeiro(
        r"Complemento:\s*(.*?)\s*\n\s*Referência:",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    dados["bairro"] = extrair_primeiro(
        r"Bairro:\s*(.*?)\s*\n\s*Município:",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    dados["municipio"] = extrair_primeiro(
        r"Município:\s*(.*?)\s*\n\s*Estado:",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    dados["estado"] = extrair_primeiro(
        r"Estado:\s*(.*?)\s*\n\s*CEP:",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    dados["cep"] = extrair_primeiro(
        r"CEP:\s*(\d{2}\.?\d{3}[-.]?\d{3})",
        texto
    )

    dados["area_construida"] = extrair_primeiro(
        r"Área Construída\(m2\):\s*(.*?)\s*\n",
        texto,
        flags=re.IGNORECASE
    )

    dados["evento"] = extrair_primeiro(
        r"Eventos:\s*(.*?)(?:\nCNPJ:)",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    return dados


# ============================================================
# COMPARAÇÕES
# ============================================================

def comparar_exato(campo, descricao, cadastro, prefeitura):
    valor1 = cadastro.get(campo, "")
    valor2 = prefeitura.get(campo, "")

    n1 = normalizar(valor1)
    n2 = normalizar(valor2)

    if not n1 or not n2:
        return {
            "Item": descricao,
            "Cadastro Econômico": valor1 or "Não localizado",
            "Prefeitura": valor2 or "Não localizado",
            "Status": "⚪ NÃO LOCALIZADO"
        }

    if n1 == n2:
        status = "🟢 OK"
    else:
        status = "🔴 VERIFICAR"

    return {
        "Item": descricao,
        "Cadastro Econômico": valor1,
        "Prefeitura": valor2,
        "Status": status
    }


def comparar_cnpj(cadastro, prefeitura):
    v1 = normalizar_cnpj(cadastro.get("cnpj"))
    v2 = normalizar_cnpj(prefeitura.get("cnpj"))

    if not v1 or not v2:
        status = "⚪ NÃO LOCALIZADO"
    elif v1 == v2:
        status = "🟢 OK"
    else:
        status = "🔴 VERIFICAR"

    return {
        "Item": "CNPJ",
        "Cadastro Econômico": cadastro.get("cnpj", "") or "Não localizado",
        "Prefeitura": prefeitura.get("cnpj", "") or "Não localizado",
        "Status": status
    }


def comparar_numero(cadastro, prefeitura):
    v1 = normalizar_numero(cadastro.get("numero"))
    v2 = normalizar_numero(prefeitura.get("numero"))

    if not v1 or not v2:
        status = "⚪ NÃO LOCALIZADO"
    elif v1 == v2:
        status = "🟢 OK"
    else:
        status = "🔴 VERIFICAR"

    return {
        "Item": "Número",
        "Cadastro Econômico": cadastro.get("numero", "") or "Não localizado",
        "Prefeitura": prefeitura.get("numero", "") or "Não localizado",
        "Status": status
    }


def comparar_cep(cadastro, prefeitura):
    v1 = normalizar_cep(cadastro.get("cep"))
    v2 = normalizar_cep(prefeitura.get("cep"))

    if not v1 or not v2:
        status = "⚪ NÃO LOCALIZADO"
    elif v1 == v2:
        status = "🟢 OK"
    else:
        status = "🔴 VERIFICAR"

    return {
        "Item": "CEP",
        "Cadastro Econômico": cadastro.get("cep", "") or "Não localizado",
        "Prefeitura": prefeitura.get("cep", "") or "Não localizado",
        "Status": status
    }


def comparar_natureza(cadastro, prefeitura):
    """
    Trata como equivalentes formatos como:
    205-4 Sociedade Anônima Fechada
    2054 - Sociedade Anônima Fechada
    """
    v1 = normalizar(cadastro.get("natureza_juridica"))
    v2 = normalizar(prefeitura.get("natureza_juridica"))

    if not v1 or not v2:
        status = "⚪ NÃO LOCALIZADO"
    else:
        codigo1 = re.search(r"\b(\d{3})[- ]?(\d)\b", v1)
        codigo2 = re.search(r"\b(\d{4})\b", v2)

        nome1 = re.sub(r"[^A-Z ]", " ", v1)
        nome2 = re.sub(r"[^A-Z ]", " ", v2)

        nome1 = re.sub(r"\s+", " ", nome1).strip()
        nome2 = re.sub(r"\s+", " ", nome2).strip()

        equivalente = False

        if codigo1 and codigo2:
            codigo_cadastro = codigo1.group(1) + codigo1.group(2)
            codigo_prefeitura = codigo2.group(1)

            if codigo_cadastro == codigo_prefeitura:
                equivalente = True

        if (
            "SOCIEDADE ANONIMA FECHADA" in nome1
            and "SOCIEDADE ANONIMA FECHADA" in nome2
        ):
            equivalente = True

        status = "🟢 OK" if equivalente else "🔴 VERIFICAR"

    return {
        "Item": "Natureza jurídica",
        "Cadastro Econômico": cadastro.get("natureza_juridica", "") or "Não localizado",
        "Prefeitura": prefeitura.get("natureza_juridica", "") or "Não localizado",
        "Status": status
    }


def comparar_endereco(cadastro, prefeitura):
    campos = [
        ("logradouro", "Logradouro"),
        ("numero", "Número"),
        ("bairro", "Bairro"),
        ("complemento", "Complemento"),
        ("cep", "CEP"),
    ]

    resultados = []

    for campo, descricao in campos:
        if campo == "numero":
            resultados.append(comparar_numero(cadastro, prefeitura))
        elif campo == "cep":
            resultados.append(comparar_cep(cadastro, prefeitura))
        else:
            resultados.append(
                comparar_exato(
                    campo,
                    descricao,
                    cadastro,
                    prefeitura
                )
            )

    return resultados


def comparar_cnaes(cadastro, prefeitura):
    """
    O documento da Prefeitura fornecido não apresenta a relação
    de CNAEs. Portanto, não se faz uma comparação artificial.
    """
    cnaes = cadastro.get("cnaes", [])

    if cnaes:
        texto_cadastro = ", ".join(cnaes)
    else:
        texto_cadastro = "Não localizado"

    return {
        "Item": "CNAEs",
        "Cadastro Econômico": texto_cadastro,
        "Prefeitura": "Não informado no documento",
        "Status": "🟡 CONFERÊNCIA MANUAL"
    }


# ============================================================
# TABELA VISUAL
# ============================================================

def tabela_colorida(df):
    def cor_linha(row):
        status = row["Status"]

        if "🟢" in status:
            cor = "#d9ead3"
        elif "🔴" in status:
            cor = "#f4cccc"
        elif "🟡" in status:
            cor = "#fff2cc"
        else:
            cor = "#eeeeee"

        return [f"background-color: {cor}"] * len(row)

    return df.style.apply(cor_linha, axis=1)


# ============================================================
# CHECKLIST
# ============================================================

def checklist_final(df):
    st.subheader("Checklist Final")

    qtd_ok = int(df["Status"].str.contains("🟢").sum())
    qtd_atencao = int(df["Status"].str.contains("🟡").sum())
    qtd_verificar = int(df["Status"].str.contains("🔴").sum())
    qtd_nao_localizado = int(
        df["Status"].str.contains("⚪").sum()
    )

    st.markdown(f"🟢 **OK:** {qtd_ok}")
    st.markdown(f"🟡 **Conferência manual:** {qtd_atencao}")
    st.markdown(f"🔴 **Verificar:** {qtd_verificar}")
    st.markdown(f"⚪ **Não localizado:** {qtd_nao_localizado}")

    st.divider()

    itens_verificar = df[
        df["Status"].str.contains("🔴|🟡|⚪", regex=True)
    ]

    if itens_verificar.empty:
        st.success("Todos os itens automáticos foram conferidos.")
    else:
        st.warning(
            "Antes de concluir o processo, confira os itens abaixo:"
        )

        for _, linha in itens_verificar.iterrows():
            st.markdown(
                f"- **{linha['Item']}** — {linha['Status']}"
            )


# ============================================================
# INTERFACE
# ============================================================

st.markdown(
    """
    Faça o upload dos dois documentos que serão comparados.
    """
)

col1, col2 = st.columns(2)

with col1:
    arquivo_cadastro = st.file_uploader(
        "Extrato do Cadastro Econômico",
        type=["pdf"],
        key="arquivo_cadastro"
    )

with col2:
    arquivo_prefeitura = st.file_uploader(
        "Documento da Prefeitura / Alvará",
        type=["pdf"],
        key="arquivo_prefeitura"
    )


if st.button("Limpar"):
    st.rerun()


if arquivo_cadastro and arquivo_prefeitura:

    try:
        texto_cadastro = extrair_texto_pdf(arquivo_cadastro)
        texto_prefeitura = extrair_texto_pdf(arquivo_prefeitura)

        cadastro = extrair_cadastro_economico(texto_cadastro)
        prefeitura = extrair_prefeitura(texto_prefeitura)

        # ----------------------------------------------------
        # RESUMO
        # ----------------------------------------------------

        st.divider()
        st.subheader("Resumo da análise")

        st.markdown(
            f"**Empresa:** {cadastro.get('razao_social', 'Não localizado')}"
        )

        st.markdown(
            f"**CNPJ:** {cadastro.get('cnpj', 'Não localizado')}"
        )

        st.markdown(
            f"**Protocolo Prefeitura:** "
            f"{prefeitura.get('protocolo', 'Não localizado')}"
        )

        st.markdown(
            f"**Ação:** "
            f"{prefeitura.get('acao', 'Não localizado')}"
        )

        # ----------------------------------------------------
        # COMPARAÇÃO
        # ----------------------------------------------------

        resultados = []

        resultados.append(
            comparar_cnpj(cadastro, prefeitura)
        )

        resultados.append(
            comparar_exato(
                "razao_social",
                "Razão social / Nome empresarial",
                cadastro,
                prefeitura
            )
        )

        resultados.append(
            comparar_exato(
                "nome_fantasia",
                "Nome fantasia",
                cadastro,
                prefeitura
            )
        )

        resultados.append(
            comparar_natureza(cadastro, prefeitura)
        )

        resultados.extend(
            comparar_endereco(cadastro, prefeitura)
        )

        resultados.append(
            comparar_cnaes(cadastro, prefeitura)
        )

        df = pd.DataFrame(resultados)

        # ----------------------------------------------------
        # TABELA
        # ----------------------------------------------------

        st.divider()
        st.subheader("Tabela de conferência")

        st.dataframe(
            tabela_colorida(df),
            use_container_width=True,
            hide_index=True
        )

        # ----------------------------------------------------
        # DETALHAMENTO
        # ----------------------------------------------------

        st.divider()
        st.subheader("Endereço")

        st.markdown(
            "**Cadastro Econômico:** "
            + ", ".join(
                filter(
                    None,
                    [
                        cadastro.get("logradouro"),
                        cadastro.get("numero"),
                        cadastro.get("bairro"),
                        cadastro.get("complemento"),
                        cadastro.get("cep"),
                    ]
                )
            )
        )

        st.markdown(
            "**Prefeitura:** "
            + ", ".join(
                filter(
                    None,
                    [
                        prefeitura.get("logradouro"),
                        prefeitura.get("numero"),
                        prefeitura.get("bairro"),
                        prefeitura.get("complemento"),
                        prefeitura.get("cep"),
                    ]
                )
            )
        )

        st.divider()
        st.subheader("CNAEs do Cadastro Econômico")

        if cadastro.get("cnaes"):
            tabela_cnaes = pd.DataFrame(
                {"CNAE": cadastro["cnaes"]}
            )
            st.dataframe(
                tabela_cnaes,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Nenhum CNAE localizado.")

        # ----------------------------------------------------
        # CHECKLIST
        # ----------------------------------------------------

        checklist_final(df)

    except Exception as erro:
        st.error(
            "Não foi possível concluir a análise automática."
        )

        with st.expander("Detalhes técnicos"):
            st.exception(erro)

else:
    st.info(
        "Envie os dois PDFs para iniciar a análise."
    )
