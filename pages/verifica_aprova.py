import streamlit as st
import pandas as pd
import re
import unicodedata


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Verifica preenchimento - ALF - Aprova Digital",
    page_icon="images/favicon.png",
    layout="wide"
)


# ============================================================
# FUNÇÕES DE NORMALIZAÇÃO
# ============================================================

def normalizar_texto(valor):
    """
    Normaliza texto para comparação:
    - transforma em string
    - remove acentos
    - coloca em maiúsculas
    - remove pontuação desnecessária
    - reduz espaços
    """
    if valor is None:
        return ""

    valor = str(valor).strip().upper()

    valor = unicodedata.normalize("NFKD", valor)
    valor = "".join(
        c for c in valor
        if not unicodedata.combining(c)
    )

    valor = re.sub(r"[^\w\s./-]", " ", valor)
    valor = re.sub(r"\s+", " ", valor)

    return valor.strip()


def normalizar_numero(valor):
    if valor is None:
        return ""

    return re.sub(r"\D", "", str(valor))


def normalizar_cnpj(valor):
    return normalizar_numero(valor)


def normalizar_cep(valor):
    return normalizar_numero(valor)


def normalizar_cnae(valor):
    """
    Transforma:
    47.89-0-04
    4789-0-04
    4789004

    em uma representação numérica comparável.
    """
    if not valor:
        return ""

    return re.sub(r"\D", "", str(valor))


def formatar_cnae(valor):
    """
    Formata CNAE para XX.XX-X-XX
    """
    numeros = normalizar_cnae(valor)

    if len(numeros) == 7:
        return (
            numeros[:2]
            + "."
            + numeros[2:4]
            + "-"
            + numeros[4]
            + "-"
            + numeros[5:]
        )

    return valor


# ============================================================
# EXTRAÇÃO DE CNPJ
# ============================================================

def extrair_cnpj(texto):

    padroes = [
        r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b"
    ]

    for padrao in padroes:

        resultado = re.search(
            padrao,
            texto
        )

        if resultado:
            return resultado.group(0)

    return ""


# ============================================================
# EXTRAÇÃO DE CNAEs
# ============================================================

def extrair_cnaes(texto):

    padrao = r"\b\d{2}\.\d{2}-\d-\d{2}\b"

    encontrados = re.findall(
        padrao,
        texto
    )

    resultado = []

    for cnae in encontrados:

        cnae_formatado = formatar_cnae(cnae)

        if cnae_formatado not in resultado:
            resultado.append(cnae_formatado)

    return resultado


# ============================================================
# EXTRAÇÃO DO CNPJ
# ============================================================

def extrair_dados_cnpj(texto):

    dados = {
        "cnpj": "",
        "razao_social": "",
        "nome_fantasia": "",
        "natureza_juridica": "",
        "logradouro": "",
        "numero": "",
        "complemento": "",
        "bairro": "",
        "cep": "",
        "municipio": "",
        "cnaes": [],
        "cnae_principal": "",
    }

    # --------------------------------------------------------
    # CNPJ
    # --------------------------------------------------------

    dados["cnpj"] = extrair_cnpj(texto)

    # --------------------------------------------------------
    # RAZÃO SOCIAL
    # --------------------------------------------------------

    padroes_razao = [
        r"RAZÃO SOCIAL\s*[:\-]?\s*(.*?)\s+(?:NOME FANTASIA|TÍTULO DO ESTABELECIMENTO)",
        r"RAZAO SOCIAL\s*[:\-]?\s*(.*?)\s+(?:NOME FANTASIA|TITULO DO ESTABELECIMENTO)",
        r"NOME EMPRESARIAL\s*[:\-]?\s*(.*?)\s+(?:NOME FANTASIA|TÍTULO)",
        r"NOME EMPRESARIAL\s*[:\-]?\s*(.*?)\s+(?:NOME FANTASIA|TITULO)",
    ]

    for padrao in padroes_razao:

        match = re.search(
            padrao,
            texto,
            flags=re.IGNORECASE | re.DOTALL
        )

        if match:
            dados["razao_social"] = match.group(1).strip()
            break

    # --------------------------------------------------------
    # NOME FANTASIA
    # --------------------------------------------------------

    padroes_fantasia = [
        r"NOME FANTASIA\s*[:\-]?\s*(.*?)\s+(?:SITUAÇÃO|SITUACAO|NATUREZA)",
        r"TÍTULO DO ESTABELECIMENTO\s*[:\-]?\s*(.*?)\s+(?:SITUAÇÃO|SITUACAO|NATUREZA)",
        r"TITULO DO ESTABELECIMENTO\s*[:\-]?\s*(.*?)\s+(?:SITUACAO|SITUACAO|NATUREZA)",
    ]

    for padrao in padroes_fantasia:

        match = re.search(
            padrao,
            texto,
            flags=re.IGNORECASE | re.DOTALL
        )

        if match:
            dados["nome_fantasia"] = match.group(1).strip()
            break

    # --------------------------------------------------------
    # NATUREZA JURÍDICA
    # --------------------------------------------------------

    match = re.search(
        r"NATUREZA JUR[IÍ]DICA\s*[:\-]?\s*(.*?)(?=\n|QUALIFICA|ATIVIDADE)",
        texto,
        flags=re.IGNORECASE
    )

    if match:
        dados["natureza_juridica"] = match.group(1).strip()

    # --------------------------------------------------------
    # LOGRADOURO
    # --------------------------------------------------------

    match = re.search(
        r"LOGRADOURO\s*[:\-]?\s*(.*?)(?=\s+N[ÚU]MERO|\s+COMPLEMENTO|\s+CEP)",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    if match:
        dados["logradouro"] = match.group(1).strip()

    # --------------------------------------------------------
    # NÚMERO
    # --------------------------------------------------------

    match = re.search(
        r"N[ÚU]MERO\s*[:\-]?\s*([^\s\n]+)",
        texto,
        flags=re.IGNORECASE
    )

    if match:
        dados["numero"] = match.group(1).strip()

    # --------------------------------------------------------
    # COMPLEMENTO
    # --------------------------------------------------------

    match = re.search(
        r"COMPLEMENTO\s*[:\-]?\s*(.*?)(?=\s+CEP|\s+BAIRRO|\s+MUNIC[IÍ]PIO)",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    if match:
        dados["complemento"] = match.group(1).strip()

    # --------------------------------------------------------
    # CEP
    # --------------------------------------------------------

    match = re.search(
        r"CEP\s*[:\-]?\s*(\d{5}-?\d{3})",
        texto,
        flags=re.IGNORECASE
    )

    if match:
        dados["cep"] = match.group(1)

    # --------------------------------------------------------
    # BAIRRO
    # --------------------------------------------------------

    match = re.search(
        r"BAIRRO/?DISTRITO\s*[:\-]?\s*(.*?)(?=\s+MUNIC[IÍ]PIO|\s+ENDERE[CÇ]O|\n)",
        texto,
        flags=re.IGNORECASE
    )

    if match:
        dados["bairro"] = match.group(1).strip()

    # --------------------------------------------------------
    # MUNICÍPIO
    # --------------------------------------------------------

    match = re.search(
        r"MUNIC[IÍ]PIO\s*[:\-]?\s*(.*?)(?=\s+UF|\s+CEP|\n)",
        texto,
        flags=re.IGNORECASE
    )

    if match:
        dados["municipio"] = match.group(1).strip()

    # --------------------------------------------------------
    # CNAEs
    # --------------------------------------------------------

    dados["cnaes"] = extrair_cnaes(texto)

    if dados["cnaes"]:
        dados["cnae_principal"] = dados["cnaes"][0]

    return dados


# ============================================================
# EXTRAÇÃO DO APROVA DIGITAL
# ============================================================

def extrair_dados_aprova(texto):

    dados = {
        "cnpj": "",
        "razao_social": "",
        "nome_fantasia": "",
        "natureza_juridica": "",
        "inscricao_imobiliaria": "",
        "logradouro": "",
        "numero": "",
        "complemento": "",
        "bairro": "",
        "cep": "",
        "cnaes": [],
        "cnae_principal": "",
        "zoneamento": "",
        "classificacao_uso": "",
        "area": "",
    }

    # --------------------------------------------------------
    # CNPJ
    # --------------------------------------------------------

    dados["cnpj"] = extrair_cnpj(texto)

    # --------------------------------------------------------
    # RAZÃO SOCIAL
    # --------------------------------------------------------

    padroes = [
        r"Raz[aã]o\s+Social\s+(.*?)\s+Nome\s+Fantasia",
        r"RAZ[AÃ]O\s+SOCIAL\s+(.*?)\s+NOME\s+FANTASIA",
    ]

    for padrao in padroes:

        match = re.search(
            padrao,
            texto,
            flags=re.IGNORECASE | re.DOTALL
        )

        if match:
            dados["razao_social"] = match.group(1).strip()
            break

    # --------------------------------------------------------
    # NOME FANTASIA
    # --------------------------------------------------------

    padroes = [
        r"Nome\s+Fantasia\s+(.*?)\s+(?:Natureza|REGIN|CNPJ)",
        r"NOME\s+FANTASIA\s+(.*?)\s+(?:NATUREZA|REGIN|CNPJ)",
    ]

    for padrao in padroes:

        match = re.search(
            padrao,
            texto,
            flags=re.IGNORECASE | re.DOTALL
        )

        if match:
            dados["nome_fantasia"] = match.group(1).strip()
            break

    # --------------------------------------------------------
    # NATUREZA JURÍDICA
    # --------------------------------------------------------

    match = re.search(
        r"(?:Natureza\s+Jur[ií]dica|NATUREZA\s+JUR[IÍ]DICA)"
        r"\s*[:\-]?\s*(.*?)(?=\s+(?:CNPJ|REGIN|Bairro|Logradouro)|\n)",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    if match:
        dados["natureza_juridica"] = match.group(1).strip()

    # --------------------------------------------------------
    # INSCRIÇÃO IMOBILIÁRIA
    # --------------------------------------------------------

    padroes = [
        r"Inscri[cç][aã]o\s+Imobili[aá]ria\s*[:\-]?\s*([^\s\n]+)",
        r"INSCRI[CÇ][AÃ]O\s+IMOBILI[AÁ]RIA\s*[:\-]?\s*([^\s\n]+)",
    ]

    for padrao in padroes:

        match = re.search(
            padrao,
            texto,
            flags=re.IGNORECASE
        )

        if match:
            dados["inscricao_imobiliaria"] = match.group(1).strip()
            break

    # --------------------------------------------------------
    # LOGRADOURO
    # --------------------------------------------------------

    match = re.search(
        r"Logradouro\s*[:\-]?\s*(.*?)(?=\s+N[uú]mero|\s+Predial|\s+Bairro|\s+CEP|\n)",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    if match:
        dados["logradouro"] = match.group(1).strip()

    # --------------------------------------------------------
    # NÚMERO
    # --------------------------------------------------------

    match = re.search(
        r"(?:N[uú]mero|N[uú]mero\s+Predial)\s*[:\-]?\s*([^\s\n]+)",
        texto,
        flags=re.IGNORECASE
    )

    if match:
        dados["numero"] = match.group(1).strip()

    # --------------------------------------------------------
    # BAIRRO
    # --------------------------------------------------------

    match = re.search(
        r"Bairro\s*[:\-]?\s*(.*?)(?=\s+Logradouro|\s+CEP|\s+N[uú]mero|\n)",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    if match:
        dados["bairro"] = match.group(1).strip()

    # --------------------------------------------------------
    # CEP
    # --------------------------------------------------------

    match = re.search(
        r"CEP\s*[:\-]?\s*(\d{5}-?\d{3})",
        texto,
        flags=re.IGNORECASE
    )

    if match:
        dados["cep"] = match.group(1)

    # --------------------------------------------------------
    # COMPLEMENTO
    # --------------------------------------------------------

    complementos = []

    # Sala
    match = re.search(
        r"(?:Sala|SALA\))\s*[:\-]?\s*([A-Za-z0-9\-]+)",
        texto,
        flags=re.IGNORECASE
    )

    if match:
        complementos.append("SALA " + match.group(1))

    # Box
    match = re.search(
        r"(?:Box|BOX\))\s*[:\-]?\s*([A-Za-z0-9\-]+)",
        texto,
        flags=re.IGNORECASE
    )

    if match:
        complementos.append("BOX " + match.group(1))

    # Lote
    match = re.search(
        r"LOTE\s*[:\-]?\s*([A-Za-z0-9\-]+)",
        texto,
        flags=re.IGNORECASE
    )

    if match:
        complementos.insert(
            0,
            "LOTE " + match.group(1)
        )

    dados["complemento"] = " ".join(complementos)

    # --------------------------------------------------------
    # CNAEs
    # --------------------------------------------------------

    dados["cnaes"] = extrair_cnaes(texto)

    if dados["cnaes"]:
        dados["cnae_principal"] = dados["cnaes"][0]

    # --------------------------------------------------------
    # ZONEAMENTO
    # --------------------------------------------------------

    match = re.search(
        r"Zoneamento\s*[:\-]?\s*(.*?)(?=\s+Classifica|\s+Uso|\n)",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    if match:
        dados["zoneamento"] = match.group(1).strip()

    # --------------------------------------------------------
    # CLASSIFICAÇÃO DE USO
    # --------------------------------------------------------

    match = re.search(
        r"(?:Classifica[cç][aã]o\s+de\s+Uso|Classifica[cç][aã]o)\s*"
        r"[:\-]?\s*(.*?)(?=\n|$)",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    if match:
        dados["classificacao_uso"] = match.group(1).strip()

    # --------------------------------------------------------
    # ÁREA
    # --------------------------------------------------------

    match = re.search(
        r"[ÁA]rea\s*[:\-]?\s*([\d.,]+\s*m[²2]?)",
        texto,
        flags=re.IGNORECASE
    )

    if match:
        dados["area"] = match.group(1).strip()

    return dados


# ============================================================
# COMPARAÇÃO DE CAMPOS
# ============================================================

def comparar_valores(
    campo,
    aprova,
    cnpj,
    tipo="texto"
):

    if not str(aprova).strip() or not str(cnpj).strip():

        return {
            "Campo": campo,
            "Aprova Digital": aprova,
            "CNPJ": cnpj,
            "Resultado": "NÃO LOCALIZADO",
            "Observação": "Informação ausente em uma das fontes."
        }

    # --------------------------------------------------------
    # CNPJ
    # --------------------------------------------------------

    if tipo == "cnpj":

        a = normalizar_cnpj(aprova)
        b = normalizar_cnpj(cnpj)

        if a == b:

            return {
                "Campo": campo,
                "Aprova Digital": aprova,
                "CNPJ": cnpj,
                "Resultado": "OK",
                "Observação": ""
            }

        return {
            "Campo": campo,
            "Aprova Digital": aprova,
            "CNPJ": cnpj,
            "Resultado": "VERIFICAR",
            "Observação": "CNPJ divergente."
        }

    # --------------------------------------------------------
    # NÚMERO
    # --------------------------------------------------------

    if tipo == "numero":

        a = normalizar_numero(aprova)
        b = normalizar_numero(cnpj)

        if a == b:

            return {
                "Campo": campo,
                "Aprova Digital": aprova,
                "CNPJ": cnpj,
                "Resultado": "OK",
                "Observação": ""
            }

        return {
            "Campo": campo,
            "Aprova Digital": aprova,
            "CNPJ": cnpj,
            "Resultado": "VERIFICAR",
            "Observação": "Número divergente."
        }

    # --------------------------------------------------------
    # CEP
    # --------------------------------------------------------

    if tipo == "cep":

        a = normalizar_cep(aprova)
        b = normalizar_cep(cnpj)

        if a == b:

            return {
                "Campo": campo,
                "Aprova Digital": aprova,
                "CNPJ": cnpj,
                "Resultado": "OK",
                "Observação": ""
            }

        return {
            "Campo": campo,
            "Aprova Digital": aprova,
            "CNPJ": cnpj,
            "Resultado": "VERIFICAR",
            "Observação": "CEP divergente."
        }

    # --------------------------------------------------------
    # TEXTO
    # --------------------------------------------------------

    a = normalizar_texto(aprova)
    b = normalizar_texto(cnpj)

    if a == b:

        return {
            "Campo": campo,
            "Aprova Digital": aprova,
            "CNPJ": cnpj,
            "Resultado": "OK",
            "Observação": ""
        }

    # --------------------------------------------------------
    # DIFERENÇA DE FORMATAÇÃO
    # --------------------------------------------------------

    if tipo == "endereco":

        # Remove prefixos comuns
        prefixos = [
            "RUA ",
            "AV ",
            "AVENIDA ",
            "RODOVIA ",
            "ESTRADA ",
            "TRAVESSA ",
            "ALAMEDA "
        ]

        aa = a
        bb = b

        for prefixo in prefixos:

            aa = aa.replace(prefixo, "")
            bb = bb.replace(prefixo, "")

        if aa == bb:

            return {
                "Campo": campo,
                "Aprova Digital": aprova,
                "CNPJ": cnpj,
                "Resultado": "ATENÇÃO",
                "Observação": "Diferença apenas na forma de apresentação."
            }

    return {
        "Campo": campo,
        "Aprova Digital": aprova,
        "CNPJ": cnpj,
        "Resultado": "VERIFICAR",
        "Observação": "Informações diferentes."
    }


# ============================================================
# COMPARAÇÃO DOS CNAEs
# ============================================================

def comparar_cnaes(cnaes_aprova, cnaes_cnpj):

    aprova = {
        normalizar_cnae(cnae)
        for cnae in cnaes_aprova
    }

    cnpj = {
        normalizar_cnae(cnae)
        for cnae in cnaes_cnpj
    }

    if aprova == cnpj:

        return {
            "Campo": "CNAEs",
            "Aprova Digital": ", ".join(cnaes_aprova),
            "CNPJ": ", ".join(cnaes_cnpj),
            "Resultado": "OK",
            "Observação": "Todos os CNAEs são compatíveis."
        }

    if aprova and cnpj:

        somente_aprova = aprova - cnpj
        somente_cnpj = cnpj - aprova

        observacao = []

        if somente_aprova:
            observacao.append(
                "Somente Aprova: "
                + ", ".join(
                    formatar_cnae(x)
                    for x in somente_aprova
                )
            )

        if somente_cnpj:
            observacao.append(
                "Somente CNPJ: "
                + ", ".join(
                    formatar_cnae(x)
                    for x in somente_cnpj
                )
            )

        return {
            "Campo": "CNAEs",
            "Aprova Digital": ", ".join(cnaes_aprova),
            "CNPJ": ", ".join(cnaes_cnpj),
            "Resultado": "VERIFICAR",
            "Observação": " | ".join(observacao)
        }

    return {
        "Campo": "CNAEs",
        "Aprova Digital": ", ".join(cnaes_aprova),
        "CNPJ": ", ".join(cnaes_cnpj),
        "Resultado": "NÃO LOCALIZADO",
        "Observação": "Não foi possível localizar todos os CNAEs."
    }


# ============================================================
# LIMPAR
# ============================================================

def limpar_campos():

    st.session_state["texto_aprova"] = ""
    st.session_state["texto_cnpj"] = ""
    st.session_state["analisar"] = False


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("Links úteis")

    st.page_link(
        "app.py",
        label="Início"
    )

    st.page_link(
        "pages/cv_zona.py",
        label="CV Zona"
    )

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
# INICIALIZA SESSION STATE
# ============================================================

if "texto_aprova" not in st.session_state:
    st.session_state["texto_aprova"] = ""

if "texto_cnpj" not in st.session_state:
    st.session_state["texto_cnpj"] = ""

if "analisar" not in st.session_state:
    st.session_state["analisar"] = False


# ============================================================
# TÍTULO
# ============================================================

st.title(
    "Verifica preenchimento - ALF - Aprova Digital"
)

st.write(
    "Cole os dados do processo do Aprova Digital e do CNPJ "
    "para realizar a conferência automática."
)


# ============================================================
# INPUTS
# ============================================================

col1, col2 = st.columns(2)

with col1:

    st.subheader("📄 Aprova Digital")

    st.text_area(
        "Cole todo o texto da página do processo:",
        key="texto_aprova",
        height=400,
        placeholder="Cole aqui o texto copiado do Aprova Digital..."
    )


with col2:

    st.subheader("🏢 CNPJ")

    st.text_area(
        "Cole todo o texto do CNPJ:",
        key="texto_cnpj",
        height=400,
        placeholder="Cole aqui o texto do CNPJ..."
    )


# ============================================================
# BOTÕES
# ============================================================

col_btn1, col_btn2, col_btn3 = st.columns(
    [1, 1, 4]
)

with col_btn1:

    st.button(
        "🗑️ Limpar",
        on_click=limpar_campos,
        use_container_width=True
    )


with col_btn2:

    if st.button(
        "🔎 Analisar",
        type="primary",
        use_container_width=True
    ):
        st.session_state["analisar"] = True


# ============================================================
# RECUPERA TEXTO
# ============================================================

texto_aprova = st.session_state.get(
    "texto_aprova",
    ""
)

texto_cnpj = st.session_state.get(
    "texto_cnpj",
    "")


# ============================================================
# VALIDAÇÃO
# ============================================================

if not st.session_state.get("analisar", False):

    st.info(
        "Cole os dois documentos e clique em **Analisar**."
    )

    st.stop()


if not texto_aprova.strip():

    st.warning(
        "⚠️ O texto do Aprova Digital não foi preenchido."
    )

    st.stop()


if not texto_cnpj.strip():

    st.warning(
        "⚠️ O texto do CNPJ não foi preenchido."
    )

    st.stop()


# ============================================================
# EXTRAÇÃO
# ============================================================

try:

    dados_aprova = extrair_dados_aprova(
        texto_aprova
    )

    dados_cnpj = extrair_dados_cnpj(
        texto_cnpj
    )

except Exception as erro:

    st.error(
        "Ocorreu um erro durante a leitura dos documentos."
    )

    st.exception(erro)

    st.stop()


# ============================================================
# RESUMO DA EXTRAÇÃO
# ============================================================

st.markdown("---")

st.subheader("📊 Dados identificados")

col1, col2 = st.columns(2)

with col1:

    st.markdown("### Aprova Digital")

    st.write(
        "**CNPJ:**",
        dados_aprova["cnpj"] or "Não localizado"
    )

    st.write(
        "**Razão Social:**",
        dados_aprova["razao_social"] or "Não localizada"
    )

    st.write(
        "**Nome Fantasia:**",
        dados_aprova["nome_fantasia"] or "Não localizado"
    )

    st.write(
        "**Inscrição Imobiliária:**",
        dados_aprova["inscricao_imobiliaria"] or "Não localizada"
    )

with col2:

    st.markdown("### CNPJ")

    st.write(
        "**CNPJ:**",
        dados_cnpj["cnpj"] or "Não localizado"
    )

    st.write(
        "**Razão Social:**",
        dados_cnpj["razao_social"] or "Não localizada"
    )

    st.write(
        "**Nome Fantasia:**",
        dados_cnpj["nome_fantasia"] or "Não localizado"
    )

    st.write(
        "**Natureza Jurídica:**",
        dados_cnpj["natureza_juridica"] or "Não localizada"
    )


# ============================================================
# COMPARAÇÕES
# ============================================================

resultados = []


# ------------------------------------------------------------
# CNPJ
# ------------------------------------------------------------

resultados.append(
    comparar_valores(
        "CNPJ",
        dados_aprova["cnpj"],
        dados_cnpj["cnpj"],
        "cnpj"
    )
)


# ------------------------------------------------------------
# RAZÃO SOCIAL
# ------------------------------------------------------------

resultados.append(
    comparar_valores(
        "Razão Social",
        dados_aprova["razao_social"],
        dados_cnpj["razao_social"]
    )
)


# ------------------------------------------------------------
# NOME FANTASIA
# ------------------------------------------------------------

resultados.append(
    comparar_valores(
        "Nome Fantasia",
        dados_aprova["nome_fantasia"],
        dados_cnpj["nome_fantasia"]
    )
)


# ------------------------------------------------------------
# NATUREZA JURÍDICA
# ------------------------------------------------------------

resultados.append(
    comparar_valores(
        "Natureza Jurídica",
        dados_aprova["natureza_juridica"],
        dados_cnpj["natureza_juridica"]
    )
)


# ------------------------------------------------------------
# LOGRADOURO
# ------------------------------------------------------------

resultados.append(
    comparar_valores(
        "Logradouro",
        dados_aprova["logradouro"],
        dados_cnpj["logradouro"],
        "endereco"
    )
)


# ------------------------------------------------------------
# NÚMERO
# ------------------------------------------------------------

resultados.append(
    comparar_valores(
        "Número",
        dados_aprova["numero"],
        dados_cnpj["numero"],
        "numero"
    )
)


# ------------------------------------------------------------
# COMPLEMENTO
# ------------------------------------------------------------

resultados.append(
    comparar_valores(
        "Complemento",
        dados_aprova["complemento"],
        dados_cnpj["complemento"],
        "endereco"
    )
)


# ------------------------------------------------------------
# BAIRRO
# ------------------------------------------------------------

resultados.append(
    comparar_valores(
        "Bairro",
        dados_aprova["bairro"],
        dados_cnpj["bairro"],
        "endereco"
    )
)


# ------------------------------------------------------------
# CEP
# ------------------------------------------------------------

resultados.append(
    comparar_valores(
        "CEP",
        dados_aprova["cep"],
        dados_cnpj["cep"],
        "cep"
    )
)


# ------------------------------------------------------------
# CNAEs
# ------------------------------------------------------------

resultados.append(
    comparar_cnaes(
        dados_aprova["cnaes"],
        dados_cnpj["cnaes"]
    )
)


# ------------------------------------------------------------
# INSCRIÇÃO IMOBILIÁRIA
# ------------------------------------------------------------

resultados.append(
    {
        "Campo": "Inscrição Imobiliária",
        "Aprova Digital": dados_aprova["inscricao_imobiliaria"],
        "CNPJ": "Não se aplica",
        "Resultado": "OK"
        if dados_aprova["inscricao_imobiliaria"]
        else "NÃO LOCALIZADO",
        "Observação":
            ""
            if dados_aprova["inscricao_imobiliaria"]
            else "Não localizada no Aprova Digital."
    }
)


# ------------------------------------------------------------
# ZONEAMENTO
# ------------------------------------------------------------

resultados.append(
    {
        "Campo": "Zoneamento",
        "Aprova Digital": dados_aprova["zoneamento"],
        "CNPJ": "Não se aplica",
        "Resultado": "OK"
        if dados_aprova["zoneamento"]
        else "NÃO LOCALIZADO",
        "Observação":
            ""
            if dados_aprova["zoneamento"]
            else "Zoneamento não localizado."
    }
)


# ------------------------------------------------------------
# CLASSIFICAÇÃO DE USO
# ------------------------------------------------------------

resultados.append(
    {
        "Campo": "Classificação de Uso",
        "Aprova Digital": dados_aprova["classificacao_uso"],
        "CNPJ": "Não se aplica",
        "Resultado": "OK"
        if dados_aprova["classificacao_uso"]
        else "NÃO LOCALIZADO",
        "Observação":
            ""
            if dados_aprova["classificacao_uso"]
            else "Classificação de uso não localizada."
    }
)


# ------------------------------------------------------------
# ÁREA
# ------------------------------------------------------------

resultados.append(
    {
        "Campo": "Área",
        "Aprova Digital": dados_aprova["area"],
        "CNPJ": "Não se aplica",
        "Resultado": "OK"
        if dados_aprova["area"]
        else "NÃO LOCALIZADO",
        "Observação":
            ""
            if dados_aprova["area"]
            else "Área não localizada."
    }
)


# ============================================================
# DATAFRAME
# ============================================================

df_resultados = pd.DataFrame(
    resultados
)


# ============================================================
# FUNÇÃO DE COR
# ============================================================

def cor_linha(resultado):

    resultado = str(resultado).upper()

    if resultado == "OK":
        return (
            "background-color: #d4edda;"
            "color: #155724;"
        )

    if "ATENÇÃO" in resultado:
        return (
            "background-color: #fff3cd;"
            "color: #856404;"
        )

    if "VERIFICAR" in resultado:
        return (
            "background-color: #f8d7da;"
            "color: #721c24;"
        )

    if "NÃO LOCALIZADO" in resultado:
        return (
            "background-color: #e2e3e5;"
            "color: #383d41;"
        )

    return ""


def aplicar_cor(row):

    cor = cor_linha(
        row["Resultado"]
    )

    return [
        cor
        for _ in row
    ]


# ============================================================
# TABELA DE COMPARAÇÃO
# ============================================================

st.markdown("---")

st.subheader(
    "🔍 Comparação Aprova Digital × CNPJ"
)

st.dataframe(
    df_resultados.style.apply(
        aplicar_cor,
        axis=1
    ),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# CHECKLIST
# ============================================================

st.markdown("---")

st.subheader(
    "📋 Checklist Final"
)


# Contagens

total = len(df_resultados)

qtd_ok = sum(
    df_resultados["Resultado"]
    .astype(str)
    .str.upper()
    .eq("OK")
)

qtd_atencao = sum(
    df_resultados["Resultado"]
    .astype(str)
    .str.upper()
    .str.contains("ATENÇÃO|ATENCAO", regex=True)
)

qtd_verificar = sum(
    df_resultados["Resultado"]
    .astype(str)
    .str.upper()
    .str.contains(
        "VERIFICAR|DIVERGÊNCIA|DIVERGENCIA",
        regex=True
    )
)

qtd_nao_localizado = sum(
    df_resultados["Resultado"]
    .astype(str)
    .str.upper()
    .str.contains(
        "NÃO LOCALIZADO|NAO LOCALIZADO",
        regex=True
    )
)


# ============================================================
# INDICADORES
# ============================================================

c1, c2, c3, c4 = st.columns(4)

with c1:

    st.metric(
        "🟢 OK",
        qtd_ok
    )

with c2:

    st.metric(
        "🟡 Atenção",
        qtd_atencao
    )

with c3:

    st.metric(
        "🔴 Verificar",
        qtd_verificar
    )

with c4:

    st.metric(
        "⚪ Não localizado",
        qtd_nao_localizado
    )


# ============================================================
# CHECKLIST ITEM A ITEM
# ============================================================

st.markdown(
    "### Conferência campo a campo"
)

for _, linha in df_resultados.iterrows():

    campo = linha["Campo"]
    resultado = str(
        linha["Resultado"]
    ).upper()

    observacao = str(
        linha.get("Observação", "")
    )

    if resultado == "OK":

        st.success(
            f"✅ **{campo}** — OK"
        )

    elif "ATENÇÃO" in resultado:

        mensagem = (
            f"⚠️ **{campo}** — Atenção"
        )

        if observacao:
            mensagem += f" — {observacao}"

        st.warning(mensagem)

    elif "VERIFICAR" in resultado:

        mensagem = (
            f"❌ **{campo}** — Verificar"
        )

        if observacao:
            mensagem += f" — {observacao}"

        st.error(mensagem)

    elif "NÃO LOCALIZADO" in resultado:

        mensagem = (
            f"⚪ **{campo}** — Não localizado"
        )

        if observacao:
            mensagem += f" — {observacao}"

        st.info(mensagem)


# ============================================================
# RESULTADO FINAL
# ============================================================

st.markdown("---")

st.subheader(
    "🚦 Resultado Final da Conferência"
)


if qtd_verificar > 0:

    st.error(
        f"🔴 **VERIFICAR DOCUMENTAÇÃO**\n\n"
        f"Foram identificadas **{qtd_verificar} "
        f"divergência(s)** que precisam ser conferidas."
    )

elif qtd_nao_localizado > 0:

    st.warning(
        f"🟡 **CONFERÊNCIA INCOMPLETA**\n\n"
        f"{qtd_nao_localizado} campo(s) "
        f"não foram localizados."
    )

elif qtd_atencao > 0:

    st.warning(
        f"🟡 **CONFERÊNCIA COM ATENÇÕES**\n\n"
        f"Não foram encontradas divergências diretas, "
        f"mas existem {qtd_atencao} diferença(s) "
        f"de apresentação/formatação."
    )

else:

    st.success(
        "🟢 **CONFERÊNCIA CONCLUÍDA**\n\n"
        "Todos os campos analisados estão compatíveis."
    )


# ============================================================
# LEGENDA
# ============================================================

st.markdown("---")

st.markdown(
    """
### Legenda

🟢 **OK** — informações compatíveis.

🟡 **ATENÇÃO** — diferença de apresentação/formatação
que merece conferência, mas não necessariamente representa
uma divergência cadastral.

🔴 **VERIFICAR** — informações efetivamente diferentes.

⚪ **NÃO LOCALIZADO** — informação não encontrada
na fonte analisada.
"""
)
