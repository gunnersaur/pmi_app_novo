import re
import streamlit as st


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Verifica preenchimento - ALF - Aprova Digital",
    page_icon="🏢",
    layout="wide"
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>
        .resultado {
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 8px;
            border: 1px solid #ddd;
        }

        .igual {
            background-color: #eaf7ea;
            border-left: 5px solid #2e8b57;
        }

        .diferente {
            background-color: #fdecec;
            border-left: 5px solid #d9534f;
        }

        .atencao {
            background-color: #fff8df;
            border-left: 5px solid #e0a800;
        }

        .info {
            background-color: #eef5ff;
            border-left: 5px solid #4285f4;
        }

        .titulo-secao {
            margin-top: 15px;
            margin-bottom: 10px;
        }

        .codigo {
            font-family: monospace;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# FUNÇÕES DE NORMALIZAÇÃO
# ============================================================

def normalizar_texto(texto):
    """
    Normaliza texto para comparação:
    - remove acentos
    - transforma em maiúsculas
    - remove espaços duplicados
    """
    if texto is None:
        return ""

    texto = str(texto).strip().upper()

    substituicoes = {
        "Á": "A",
        "À": "A",
        "Â": "A",
        "Ã": "A",
        "Ä": "A",
        "É": "E",
        "È": "E",
        "Ê": "E",
        "Ë": "E",
        "Í": "I",
        "Ì": "I",
        "Î": "I",
        "Ï": "I",
        "Ó": "O",
        "Ò": "O",
        "Ô": "O",
        "Õ": "O",
        "Ö": "O",
        "Ú": "U",
        "Ù": "U",
        "Û": "U",
        "Ü": "U",
        "Ç": "C",
    }

    for origem, destino in substituicoes.items():
        texto = texto.replace(origem, destino)

    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def normalizar_cnpj(texto):
    """Retorna somente os 14 dígitos do CNPJ."""
    if not texto:
        return ""

    return re.sub(r"\D", "", texto)


def normalizar_cep(texto):
    """Retorna somente os 8 dígitos do CEP."""
    if not texto:
        return ""

    return re.sub(r"\D", "", texto)


def normalizar_cnae(texto):
    """
    Normaliza CNAE para 7 dígitos.

    Exemplos:
    46.93-1/00 -> 4693100
    4693100    -> 4693100
    """
    if not texto:
        return ""

    codigo = re.sub(r"\D", "", str(texto))

    if len(codigo) == 7:
        return codigo

    return ""


def formatar_cnae(cnae):
    """Formata CNAE no padrão 46.93-1/00."""
    cnae = normalizar_cnae(cnae)

    if len(cnae) != 7:
        return cnae

    return (
        f"{cnae[0:2]}."
        f"{cnae[2:4]}-"
        f"{cnae[4]}/"
        f"{cnae[5:7]}"
    )


# ============================================================
# NORMALIZAÇÃO DE ENDEREÇO
# ============================================================

PREFIXOS_LOGRADOURO = [
    "RUA ",
    "R. ",
    "AVENIDA ",
    "AV. ",
    "RODOVIA ",
    "ROD. ",
    "ESTRADA ",
    "EST. ",
    "TRAVESSA ",
    "TRAV. ",
    "ALAMEDA ",
    "AL. ",
    "PRACA ",
    "PRAÇA ",
    "LARGO ",
    "SERVIDAO ",
    "SERVIDÃO ",
]


def normalizar_logradouro(texto):
    """
    Normaliza logradouro para comparação.

    Exemplo:
    RUA JOAO THOMAZ PINTO
    JOAO THOMAZ PINTO

    tornam-se equivalentes.
    """
    texto = normalizar_texto(texto)

    # Remove número que eventualmente tenha vindo junto
    texto = re.sub(
        r",?\s*N[º°]?\s*\d+.*$",
        "",
        texto
    ).strip()

    for prefixo in PREFIXOS_LOGRADOURO:
        prefixo_norm = normalizar_texto(prefixo)

        if texto.startswith(prefixo_norm):
            texto = texto[len(prefixo_norm):].strip()
            break

    return texto


def normalizar_complemento(texto):
    return normalizar_texto(texto)


def normalizar_bairro(texto):
    return normalizar_texto(texto)


# ============================================================
# EXTRAÇÃO DO CADASTRO MUNICIPAL
# ============================================================

def extrair_cadastro_municipal(texto):
    """
    Extrai informações do:

    Extrato do Cadastro de Contribuinte Pessoa Jurídica
    Município de Itajaí
    Secretaria Municipal da Fazenda
    """

    dados = {
        "cnpj": "",
        "razao_social": "",
        "nome_fantasia": "",
        "natureza_juridica": "",
        "logradouro": "",
        "numero": "",
        "bairro": "",
        "complemento": "",
        "cep": "",
        "cnaes": [],
    }

    if not texto:
        return dados

    linhas = [
        linha.strip()
        for linha in texto.splitlines()
        if linha.strip()
    ]

    # --------------------------------------------------------
    # CNPJ
    # --------------------------------------------------------

    for linha in linhas:
        if re.search(r"\bCNPJ\b", linha, re.IGNORECASE):
            match = re.search(
                r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}",
                linha
            )

            if match:
                dados["cnpj"] = normalizar_cnpj(match.group())
                break

    # Caso não tenha sido encontrado pelo rótulo
    if not dados["cnpj"]:
        match = re.search(
            r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b",
            texto
        )

        if match:
            dados["cnpj"] = normalizar_cnpj(match.group())

    # --------------------------------------------------------
    # NOME
    # --------------------------------------------------------

    for i, linha in enumerate(linhas):

        if re.match(
            r"^Nome\s*:",
            linha,
            re.IGNORECASE
        ):
            valor = linha.split(":", 1)[1].strip()

            if valor:
                dados["razao_social"] = valor

        elif re.match(
            r"^Nome Fantasia\s*:",
            linha,
            re.IGNORECASE
        ):
            valor = linha.split(":", 1)[1].strip()

            if valor:
                dados["nome_fantasia"] = valor

        elif re.match(
            r"^Natureza Jurídica\s*:",
            linha,
            re.IGNORECASE
        ):
            valor = linha.split(":", 1)[1].strip()

            if valor:
                dados["natureza_juridica"] = valor

    # --------------------------------------------------------
    # ENDEREÇO
    # --------------------------------------------------------

    for linha in linhas:

        if re.match(
            r"^Logradouro\s*:",
            linha,
            re.IGNORECASE
        ):
            valor = linha.split(":", 1)[1].strip()
            dados["logradouro"] = valor

        elif re.match(
            r"^Número\s*:",
            linha,
            re.IGNORECASE
        ):
            valor = linha.split(":", 1)[1].strip()
            dados["numero"] = valor

        elif re.match(
            r"^Bairro\s*:",
            linha,
            re.IGNORECASE
        ):
            valor = linha.split(":", 1)[1].strip()
            dados["bairro"] = valor

        elif re.match(
            r"^Complemento\s*:",
            linha,
            re.IGNORECASE
        ):
            valor = linha.split(":", 1)[1].strip()
            dados["complemento"] = valor

        elif re.match(
            r"^CEP\s*:",
            linha,
            re.IGNORECASE
        ):
            valor = linha.split(":", 1)[1].strip()
            dados["cep"] = normalizar_cep(valor)

    # --------------------------------------------------------
    # CNAEs
    # --------------------------------------------------------

    # O Cadastro Municipal apresenta CNAEs no formato:
    # 4693100
    # 2599302
    # etc.
    #
    # Procuramos linhas que sejam exatamente um código de 7
    # dígitos.

    cnaes = []

    for linha in linhas:

        codigo = normalizar_cnae(linha)

        if codigo:
            cnaes.append(codigo)

    # Remove duplicidades preservando a ordem
    dados["cnaes"] = list(dict.fromkeys(cnaes))

    return dados


# ============================================================
# EXTRAÇÃO DO APROVA DIGITAL
# ============================================================

def extrair_aprova(texto):
    """
    Extrai informações do documento da Análise do Alvará
    do Aprova Digital.
    """

    dados = {
        "protocolo": "",
        "cnpj": "",
        "razao_social": "",
        "natureza_juridica": "",
        "logradouro": "",
        "numero": "",
        "bairro": "",
        "complemento": "",
        "cep": "",
        "cnae_principal": "",
        "cnaes_secundarios": [],
        "cnaes": [],
    }

    if not texto:
        return dados

    linhas = [
        linha.strip()
        for linha in texto.splitlines()
        if linha.strip()
    ]

    # --------------------------------------------------------
    # CAMPOS PRINCIPAIS
    # --------------------------------------------------------

    for linha in linhas:

        if re.match(
            r"^Protocolo\s*:",
            linha,
            re.IGNORECASE
        ):
            dados["protocolo"] = linha.split(":", 1)[1].strip()

        elif re.match(
            r"^CNPJ\s*:",
            linha,
            re.IGNORECASE
        ):
            valor = linha.split(":", 1)[1].strip()
            dados["cnpj"] = normalizar_cnpj(valor)

        elif re.match(
            r"^Nome Empresarial\s*:",
            linha,
            re.IGNORECASE
        ):
            dados["razao_social"] = linha.split(
                ":",
                1
            )[1].strip()

        elif re.match(
            r"^Natureza Jurídica\s*:",
            linha,
            re.IGNORECASE
        ):
            dados["natureza_juridica"] = linha.split(
                ":",
                1
            )[1].strip()

        elif re.match(
            r"^Logradouro\s*:",
            linha,
            re.IGNORECASE
        ):
            valor = linha.split(":", 1)[1].strip()

            # Exemplo:
            # RUA JOAO THOMAZ PINTO, Nº1570

            match = re.search(
                r"^(.*?),?\s*N[º°]?\s*(\d+)\s*$",
                valor,
                re.IGNORECASE
            )

            if match:
                dados["logradouro"] = match.group(1).strip()
                dados["numero"] = match.group(2).strip()
            else:
                dados["logradouro"] = valor

        elif re.match(
            r"^Complemento\s*:",
            linha,
            re.IGNORECASE
        ):
            dados["complemento"] = linha.split(
                ":",
                1
            )[1].strip()

        elif re.match(
            r"^Bairro\s*:",
            linha,
            re.IGNORECASE
        ):
            dados["bairro"] = linha.split(
                ":",
                1
            )[1].strip()

        elif re.match(
            r"^CEP\s*:",
            linha,
            re.IGNORECASE
        ):
            valor = linha.split(":", 1)[1].strip()
            dados["cep"] = normalizar_cep(valor)

    # --------------------------------------------------------
    # CNAEs
    # --------------------------------------------------------

    # CNAE principal:
    #
    # Atividade Econômica Principal
    # ...
    # 46.93-1/00 - ...

    encontrou_principal = False
    encontrou_secundarias = False

    cnaes_secundarios = []

    for i, linha in enumerate(linhas):

        # Identificação das seções
        if normalizar_texto(
            linha
        ) == "ATIVIDADE ECONOMICA PRINCIPAL":

            encontrou_principal = True
            encontrou_secundarias = False
            continue

        if normalizar_texto(
            linha
        ) == "ATIVIDADES ECONOMICAS SECUNDARIAS":

            encontrou_principal = False
            encontrou_secundarias = True
            continue

        # ----------------------------------------------------
        # CNAE com descrição
        # ----------------------------------------------------

        match = re.match(
            r"^(\d{2}\.\d{2}-\d/\d{2})\s*-\s*(.*)$",
            linha
        )

        if not match:
            continue

        codigo = normalizar_cnae(match.group(1))

        if not codigo:
            continue

        if encontrou_principal and not dados["cnae_principal"]:
            dados["cnae_principal"] = codigo

        elif encontrou_secundarias:
            cnaes_secundarios.append(codigo)

    dados["cnaes_secundarios"] = list(
        dict.fromkeys(cnaes_secundarios)
    )

    # Todos os CNAEs, mantendo principal primeiro
    todos = []

    if dados["cnae_principal"]:
        todos.append(dados["cnae_principal"])

    todos.extend(dados["cnaes_secundarios"])

    dados["cnaes"] = list(dict.fromkeys(todos))

    return dados


# ============================================================
# COMPARAÇÕES
# ============================================================

def comparar_valores(valor1, valor2, normalizador=None):

    if normalizador:
        v1 = normalizador(valor1)
        v2 = normalizador(valor2)
    else:
        v1 = valor1
        v2 = valor2

    if not v1 and not v2:
        return "nao_informado"

    if not v1 or not v2:
        return "nao_informado"

    if v1 == v2:
        return "igual"

    return "diferente"


def mostrar_comparacao(
    campo,
    valor_cadastro,
    valor_aprova,
    normalizador=None,
    formatador=None
):

    status = comparar_valores(
        valor_cadastro,
        valor_aprova,
        normalizador
    )

    if formatador:
        exibicao_cadastro = formatador(valor_cadastro)
        exibicao_aprova = formatador(valor_aprova)
    else:
        exibicao_cadastro = valor_cadastro or "—"
        exibicao_aprova = valor_aprova or "—"

    if status == "igual":

        st.success(
            f"🟢 **{campo}: IGUAL**  \n"
            f"Cadastro: `{exibicao_cadastro}`  \n"
            f"Aprova Digital: `{exibicao_aprova}`"
        )

    elif status == "diferente":

        st.error(
            f"🔴 **{campo}: DIVERGENTE**  \n"
            f"Cadastro: `{exibicao_cadastro}`  \n"
            f"Aprova Digital: `{exibicao_aprova}`"
        )

    else:

        st.warning(
            f"⚪ **{campo}: NÃO INFORMADO NOS DOIS DOCUMENTOS**  \n"
            f"Cadastro: `{exibicao_cadastro}`  \n"
            f"Aprova Digital: `{exibicao_aprova}`"
        )


# ============================================================
# COMPARAÇÃO DE CNAEs
# ============================================================

def comparar_cnaes(cadastro, aprova):

    cnaes_cadastro = cadastro["cnaes"]
    cnae_principal = aprova["cnae_principal"]
    cnaes_secundarios = aprova["cnaes_secundarios"]

    cnaes_aprova = aprova["cnaes"]

    st.subheader("📊 Comparação dos CNAEs")

    # --------------------------------------------------------
    # RESUMO
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "CNAEs no Cadastro",
            len(cnaes_cadastro)
        )

    with col2:
        st.metric(
            "CNAEs no Aprova",
            len(cnaes_aprova)
        )

    with col3:
        st.metric(
            "CNAE principal no Aprova",
            formatar_cnae(cnae_principal)
            if cnae_principal
            else "Não informado"
        )

    # --------------------------------------------------------
    # CONJUNTOS
    # --------------------------------------------------------

    set_cadastro = set(cnaes_cadastro)
    set_aprova = set(cnaes_aprova)

    somente_cadastro = [
        cnae
        for cnae in cnaes_cadastro
        if cnae not in set_aprova
    ]

    somente_aprova = [
        cnae
        for cnae in cnaes_aprova
        if cnae not in set_cadastro
    ]

    iguais = [
        cnae
        for cnae in cnaes_cadastro
        if cnae in set_aprova
    ]

    # --------------------------------------------------------
    # CNAE PRINCIPAL
    # --------------------------------------------------------

    if cnae_principal:

        if cnae_principal in set_cadastro:

            st.success(
                "🟢 **CNAE principal: encontrado no Cadastro**\n\n"
                f"`{formatar_cnae(cnae_principal)}`"
            )

        else:

            st.error(
                "🔴 **CNAE principal do Aprova não foi encontrado "
                "no Cadastro**\n\n"
                f"`{formatar_cnae(cnae_principal)}`"
            )

    else:

        st.warning(
            "⚪ O CNAE principal não foi identificado no Aprova Digital."
        )

    # --------------------------------------------------------
    # CNAEs AUSENTES NO APROVA
    # --------------------------------------------------------

    st.markdown("### CNAEs do Cadastro que NÃO estão no Aprova")

    if somente_cadastro:

        for cnae in somente_cadastro:
            st.error(
                f"🔴 `{formatar_cnae(cnae)}`"
            )

    else:

        st.success(
            "🟢 Todos os CNAEs do Cadastro foram encontrados no Aprova."
        )

    # --------------------------------------------------------
    # CNAEs EXTRAS NO APROVA
    # --------------------------------------------------------

    st.markdown("### CNAEs do Aprova que NÃO estão no Cadastro")

    if somente_aprova:

        for cnae in somente_aprova:
            st.error(
                f"🔴 `{formatar_cnae(cnae)}`"
            )

    else:

        st.success(
            "🟢 Não existem CNAEs adicionais no Aprova."
        )

    # --------------------------------------------------------
    # CNAEs IGUAIS
    # --------------------------------------------------------

    with st.expander(
        f"Ver CNAEs encontrados nos dois documentos ({len(iguais)})"
    ):

        for cnae in iguais:

            if cnae == cnae_principal:
                identificacao = " — **PRINCIPAL NO APROVA**"
            elif cnae in cnaes_secundarios:
                identificacao = " — secundário no Aprova"
            else:
                identificacao = ""

            st.write(
                f"🟢 `{formatar_cnae(cnae)}`{identificacao}"
            )

    # --------------------------------------------------------
    # LISTA COMPLETA DO APROVA
    # --------------------------------------------------------

    with st.expander(
        "Ver lista completa dos CNAEs do Aprova Digital"
    ):

        if cnae_principal:

            st.write(
                f"**Principal:** `{formatar_cnae(cnae_principal)}`"
            )

        if cnaes_secundarios:

            st.write("**Secundários:**")

            for cnae in cnaes_secundarios:

                st.write(
                    f"- `{formatar_cnae(cnae)}`"
                )

    return {
        "iguais": iguais,
        "somente_cadastro": somente_cadastro,
        "somente_aprova": somente_aprova,
    }


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("📂 Processos")

    st.markdown(
        """
        - [App](https://pmiappnovo-copia.streamlit.app/)
        - [CV Zona](https://pmiappnovo-copia.streamlit.app/cv_zona)
        - [Documentação Complementar - ALF](https://pmiappnovo-copia.streamlit.app/documentacao-complementar-ALF)
        - [Estudo de Impacto de Vizinhança](https://pmiappnovo-copia.streamlit.app/estudo-de-impacto-de-vizinhanca)
        """
    )

    st.divider()

    st.caption(
        "Verificação de preenchimento entre "
        "Cadastro Municipal e Aprova Digital."
    )


# ============================================================
# TÍTULO
# ============================================================

st.title("🏢 Verifica preenchimento - ALF - Aprova Digital")

st.write(
    "Cole abaixo o conteúdo completo dos dois documentos "
    "para realizar a comparação automática."
)


# ============================================================
# CAMPOS DE ENTRADA
# ============================================================

col1, col2 = st.columns(2)

with col1:

    st.subheader("📄 Cadastro Municipal")

    texto_cadastro = st.text_area(
        "Cole o Extrato do Cadastro de Contribuinte Pessoa Jurídica",
        height=500,
        key="texto_cadastro",
        placeholder=(
            "Cole aqui o texto completo do "
            "Extrato do Cadastro..."
        )
    )


with col2:

    st.subheader("📄 Aprova Digital")

    texto_aprova = st.text_area(
        "Cole o conteúdo completo da Análise do Alvará",
        height=500,
        key="texto_aprova",
        placeholder=(
            "Cole aqui o texto completo "
            "do Aprova Digital..."
        )
    )


# ============================================================
# BOTÕES
# ============================================================

col_botao1, col_botao2, _ = st.columns([1, 1, 4])

with col_botao1:

    analisar = st.button(
        "🔎 Analisar",
        type="primary",
        use_container_width=True
    )

with col_botao2:

    limpar = st.button(
        "🗑️ Limpar",
        use_container_width=True
    )


# ============================================================
# LIMPAR
# ============================================================

if limpar:

    st.session_state["texto_cadastro"] = ""
    st.session_state["texto_aprova"] = ""

    st.rerun()


# ============================================================
# ANÁLISE
# ============================================================

if analisar:

    if not texto_cadastro.strip():

        st.error(
            "❌ Cole o conteúdo do Cadastro Municipal."
        )
        st.stop()

    if not texto_aprova.strip():

        st.error(
            "❌ Cole o conteúdo do Aprova Digital."
        )
        st.stop()

    # --------------------------------------------------------
    # EXTRAÇÃO
    # --------------------------------------------------------

    try:

        cadastro = extrair_cadastro_municipal(
            texto_cadastro
        )

        aprova = extrair_aprova(
            texto_aprova
        )

    except Exception as e:

        st.error(
            "Ocorreu um erro durante a leitura dos documentos."
        )

        st.exception(e)

        st.stop()

    # --------------------------------------------------------
    # CABEÇALHO DO RESULTADO
    # --------------------------------------------------------

    st.divider()

    st.header("📋 Resultado da análise")

    # --------------------------------------------------------
    # PROTOCOLO
    # --------------------------------------------------------

    if aprova["protocolo"]:

        st.info(
            f"**Protocolo Aprova Digital:** "
            f"`{aprova['protocolo']}`"
        )

    # --------------------------------------------------------
    # DADOS CADASTRAIS
    # --------------------------------------------------------

    st.subheader("1. Dados cadastrais")

    mostrar_comparacao(
        "CNPJ",
        cadastro["cnpj"],
        aprova["cnpj"],
        normalizador=normalizar_cnpj
    )

    mostrar_comparacao(
        "Razão social / Nome empresarial",
        cadastro["razao_social"],
        aprova["razao_social"],
        normalizador=normalizar_texto
    )

    mostrar_comparacao(
        "Natureza jurídica",
        cadastro["natureza_juridica"],
        aprova["natureza_juridica"],
        normalizador=normalizar_texto
    )

    # --------------------------------------------------------
    # ENDEREÇO
    # --------------------------------------------------------

    st.subheader("2. Endereço")

    mostrar_comparacao(
        "Logradouro",
        cadastro["logradouro"],
        aprova["logradouro"],
        normalizador=normalizar_logradouro
    )

    mostrar_comparacao(
        "Número",
        cadastro["numero"],
        aprova["numero"],
        normalizador=normalizar_texto
    )

    mostrar_comparacao(
        "Bairro",
        cadastro["bairro"],
        aprova["bairro"],
        normalizador=normalizar_bairro
    )

    mostrar_comparacao(
        "Complemento",
        cadastro["complemento"],
        aprova["complemento"],
        normalizador=normalizar_complemento
    )

    mostrar_comparacao(
        "CEP",
        cadastro["cep"],
        aprova["cep"],
        normalizador=normalizar_cep
    )

    # --------------------------------------------------------
    # CNAEs
    # --------------------------------------------------------

    st.subheader("3. Atividades econômicas")

    resultado_cnae = comparar_cnaes(
        cadastro,
        aprova
    )

    # --------------------------------------------------------
    # RESUMO FINAL
    # --------------------------------------------------------

    st.divider()

    st.header("📌 Resumo")

    problemas = []

    # CNPJ
    if normalizar_cnpj(cadastro["cnpj"]) != normalizar_cnpj(
        aprova["cnpj"]
    ):
        problemas.append("CNPJ")

    # Razão social
    if normalizar_texto(cadastro["razao_social"]) != normalizar_texto(
        aprova["razao_social"]
    ):
        problemas.append("Razão social")

    # Natureza jurídica
    if normalizar_texto(cadastro["natureza_juridica"]) != normalizar_texto(
        aprova["natureza_juridica"]
    ):
        problemas.append("Natureza jurídica")

    # Endereço
    if normalizar_logradouro(cadastro["logradouro"]) != normalizar_logradouro(
        aprova["logradouro"]
    ):
        problemas.append("Logradouro")

    if normalizar_texto(cadastro["numero"]) != normalizar_texto(
        aprova["numero"]
    ):
        problemas.append("Número")

    if normalizar_bairro(cadastro["bairro"]) != normalizar_bairro(
        aprova["bairro"]
    ):
        problemas.append("Bairro")

    if normalizar_complemento(cadastro["complemento"]) != normalizar_complemento(
        aprova["complemento"]
    ):
        problemas.append("Complemento")

    if normalizar_cep(cadastro["cep"]) != normalizar_cep(
        aprova["cep"]
    ):
        problemas.append("CEP")

    # CNAEs
    if resultado_cnae["somente_cadastro"]:
        problemas.append(
            "CNAEs existentes no Cadastro e ausentes no Aprova"
        )

    if resultado_cnae["somente_aprova"]:
        problemas.append(
            "CNAEs existentes no Aprova e ausentes no Cadastro"
        )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    if problemas:

        st.error(
            "🔴 **FORAM ENCONTRADAS DIVERGÊNCIAS**"
        )

        st.write(
            "Verifique os seguintes itens:"
        )

        for problema in problemas:

            st.write(
                f"- {problema}"
            )

    else:

        st.success(
            "🟢 **NÃO FORAM ENCONTRADAS DIVERGÊNCIAS "
            "NOS CAMPOS ANALISADOS.**"
        )
