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
# NORMALIZAÇÃO
# ============================================================

def normalizar_texto(valor):
    if valor is None:
        return ""

    valor = str(valor)
    valor = unicodedata.normalize("NFKC", valor)
    valor = re.sub(r"\s+", " ", valor)

    return valor.strip().upper()


def normalizar_sem_acentos(valor):
    valor = normalizar_texto(valor)

    valor = unicodedata.normalize("NFD", valor)

    return "".join(
        c for c in valor
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


def normalizar_logradouro(valor):

    valor = normalizar_sem_acentos(valor)

    valor = re.sub(
        r"\bN[º°]?\s*\d+\b",
        "",
        valor
    )

    valor = re.sub(
        r"[^A-Z0-9 ]",
        " ",
        valor
    )

    valor = re.sub(
        r"\s+",
        " ",
        valor
    ).strip()

    valor = re.sub(
        r"^(RUA|R\.|AVENIDA|AV\.|ALAMEDA|AL\.|TRAVESSA|TV\.|RODOVIA|ROD\.)\s+",
        "",
        valor
    )

    return valor


def normalizar_numero(valor):

    if not valor:
        return ""

    match = re.search(
        r"\d+",
        str(valor)
    )

    return match.group(0) if match else ""


def normalizar_cep(valor):

    if not valor:
        return ""

    return re.sub(
        r"\D",
        "",
        str(valor)
    )


def normalizar_complemento(valor):

    valor = normalizar_sem_acentos(valor)

    valor = re.sub(
        r"[^A-Z0-9 ]",
        " ",
        valor
    )

    valor = re.sub(
        r"\s+",
        " ",
        valor
    )

    return valor.strip()


def normalizar_cnae(valor):

    if not valor:
        return ""

    return re.sub(
        r"\D",
        "",
        str(valor)
    )


def formatar_cnae(codigo):

    codigo = normalizar_cnae(codigo)

    if len(codigo) != 7:
        return codigo

    return (
        codigo[:2]
        + "."
        + codigo[2:4]
        + "-"
        + codigo[4]
        + "/"
        + codigo[5:]
    )


# ============================================================
# EXTRAÇÃO DE BLOCOS
# ============================================================

def extrair_bloco(texto, inicio, fim=None):

    if not texto:
        return ""

    pos_inicio = texto.lower().find(
        inicio.lower()
    )

    if pos_inicio == -1:
        return ""

    pos_inicio += len(inicio)

    if fim:

        pos_fim = texto.lower().find(
            fim.lower(),
            pos_inicio
        )

        if pos_fim != -1:
            return texto[
                pos_inicio:pos_fim
            ]

    return texto[pos_inicio:]


# ============================================================
# EXTRAÇÃO DO CNPJ
# ============================================================

def extrair_cnpj(texto):

    if not texto:
        return ""

    padroes = [

        r"CPF/CNPJ\s*:\s*(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})",

        r"CNPJ\s*:\s*(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})",

        r"\b(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})\b"
    ]

    for padrao in padroes:

        match = re.search(
            padrao,
            texto,
            flags=re.IGNORECASE
        )

        if match:

            return re.sub(
                r"\D",
                "",
                match.group(1)
            )

    return ""


# ============================================================
# EXTRAÇÃO DOS CNAEs DO CADASTRO
# ============================================================

def extrair_cnaes_cadastro(texto):

    cnaes = []

    if not texto:
        return cnaes

    for linha in texto.splitlines():

        linha = linha.strip()

        # O CNAE do Cadastro aparece no início da linha
        # com exatamente 7 dígitos, seguido de espaço.
        #
        # Exemplo válido:
        # 4693100 COMÉRCIO ATACADISTA...
        #
        # Não aceitar:
        # 1570 GALPAO:3;SALA:93
        #
        # Isso impede que o endereço seja interpretado
        # como um CNAE.

        match = re.match(
            r"^(\d{7})\s+\S",
            linha
        )

        if not match:
            continue

        codigo = match.group(1)

        if len(codigo) != 7:
            continue

        codigo = normalizar_cnae(codigo)

        if codigo not in cnaes:
            cnaes.append(codigo)

    return cnaes


# ============================================================
# EXTRAÇÃO DO CADASTRO MUNICIPAL
# ============================================================

def extrair_cadastro_municipal(texto):

    dados = {
        "cnpj": "",
        "razao_social": "",
        "natureza_juridica": "",
        "logradouro": "",
        "numero": "",
        "bairro": "",
        "complemento": "",
        "cep": "",
        "cnaes": []
    }

    if not texto:
        return dados

    # --------------------------------------------------------
    # CNPJ
    # --------------------------------------------------------

    dados["cnpj"] = extrair_cnpj(texto)

    # --------------------------------------------------------
    # IDENTIFICAÇÃO DO CONTRIBUINTE
    # --------------------------------------------------------

    bloco_identificacao = extrair_bloco(
        texto,
        "Identificação do Contribuinte",
        "Endereço Correspondência"
    )

    if not bloco_identificacao:

        bloco_identificacao = extrair_bloco(
            texto,
            "Identificação do Contribuinte",
            "Endereço"
        )

    linhas_identificacao = [
        linha.strip()
        for linha in bloco_identificacao.splitlines()
        if linha.strip()
    ]

    # --------------------------------------------------------
    # RAZÃO SOCIAL
    # --------------------------------------------------------

    indice_email = None

    for i, linha in enumerate(linhas_identificacao):

        if normalizar_texto(linha) == "CORREIO ELETRÔNICO:":

            indice_email = i
            break

    if indice_email is not None:

        candidatos = []

        for linha in linhas_identificacao[
            indice_email + 1:
        ]:

            if normalizar_texto(linha) == "ENDEREÇO":
                break

            if "@" in linha:
                continue

            if re.fullmatch(
                r"\d+",
                linha
            ):
                continue

            if re.search(
                r"\d{5}-\d{3}",
                linha
            ):
                continue

            if re.search(
                r"\d{2}/\d{2}/\d{4}",
                linha
            ):
                continue

            if len(
                re.sub(
                    r"[^A-Za-zÀ-ÿ]",
                    "",
                    linha
                )
            ) < 3:
                continue

            candidatos.append(linha)

        if candidatos:

            dados["razao_social"] = candidatos[0]

    # --------------------------------------------------------
    # FALLBACK DA RAZÃO SOCIAL
    # --------------------------------------------------------

    if not dados["razao_social"]:

        match = re.search(
            r"\b([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ0-9&.\- ]{3,}\s+S\.?\s*A\.?)\b",
            texto,
            flags=re.IGNORECASE
        )

        if match:

            dados["razao_social"] = (
                match.group(1).strip()
            )

    # --------------------------------------------------------
    # NATUREZA JURÍDICA
    # --------------------------------------------------------

    padroes_natureza = [

        r"\b(\d{3}-\d)\s+Sociedade\s+Anônima\s+Fechada\b",

        r"\b(\d{3}-\d)\s+([A-Za-zÀ-ÿ][^\n\r]+)"
    ]

    for padrao in padroes_natureza:

        match = re.search(
            padrao,
            texto,
            flags=re.IGNORECASE
        )

        if match:

            if len(match.groups()) == 1:

                dados["natureza_juridica"] = (
                    match.group(1)
                )

            else:

                dados["natureza_juridica"] = (
                    match.group(1)
                    + " "
                    + match.group(2).strip()
                )

            break

    # --------------------------------------------------------
    # ENDEREÇO
    # --------------------------------------------------------

    bloco_endereco = extrair_bloco(
        texto,
        "Endereço",
        "Endereço Correspondência"
    )

    if bloco_endereco:

        linhas_endereco = [
            linha.strip()
            for linha in bloco_endereco.splitlines()
            if linha.strip()
        ]

        # ----------------------------------------------------
        # CEP
        # ----------------------------------------------------

        ceps = re.findall(
            r"\b\d{5}-\d{3}\b",
            bloco_endereco
        )

        if ceps:

            dados["cep"] = ceps[0]

        # ----------------------------------------------------
        # NÚMERO E COMPLEMENTO
        # ----------------------------------------------------

        indice_numero = None

        for i, linha in enumerate(linhas_endereco):

            match_numero = re.match(
                r"^(\d+)(?:\s+(.*))?$",
                linha
            )

            if match_numero:

                dados["numero"] = (
                    match_numero.group(1)
                )

                dados["complemento"] = (
                    match_numero.group(2) or ""
                ).strip()

                indice_numero = i

                break

        # ----------------------------------------------------
        # BAIRRO E LOGRADOURO
        # ----------------------------------------------------

        if indice_numero is not None:

            candidatos = []

            for linha in linhas_endereco[
                indice_numero + 1:
            ]:

                if not linha:
                    continue

                if linha.endswith(":"):
                    continue

                if "@" in linha:
                    continue

                if re.fullmatch(
                    r"\d{5}-\d{3}",
                    linha
                ):
                    continue

                quantidade_letras = len(
                    re.sub(
                        r"[^A-Za-zÀ-ÿ]",
                        "",
                        linha
                    )
                )

                if quantidade_letras < 3:
                    continue

                candidatos.append(linha)

            if candidatos:

                dados["bairro"] = candidatos[0]

            if len(candidatos) >= 2:

                dados["logradouro"] = candidatos[1]

    # --------------------------------------------------------
    # CNAEs
    # --------------------------------------------------------

    dados["cnaes"] = (
        extrair_cnaes_cadastro(texto)
    )

    return dados


# ============================================================
# EXTRAÇÃO DA LEGALIZAÇÃO
# ============================================================

def extrair_legalizacao(texto):

    dados = {
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
        "cnaes": []
    }

    if not texto:
        return dados

    # --------------------------------------------------------
    # CNPJ
    # --------------------------------------------------------

    dados["cnpj"] = extrair_cnpj(texto)

    # --------------------------------------------------------
    # RAZÃO SOCIAL
    # --------------------------------------------------------

    match = re.search(
        r"Nome Empresarial\s*:\s*(.+)",
        texto,
        flags=re.IGNORECASE
    )

    if match:

        dados["razao_social"] = (
            match.group(1).strip()
        )

    # --------------------------------------------------------
    # NATUREZA JURÍDICA
    # --------------------------------------------------------

    match = re.search(
        r"Natureza Jurídica\s*:\s*(.+)",
        texto,
        flags=re.IGNORECASE
    )

    if match:

        dados["natureza_juridica"] = (
            match.group(1).strip()
        )

    # --------------------------------------------------------
    # LOGRADOURO + NÚMERO
    # --------------------------------------------------------

    match = re.search(
        r"Logradouro\s*:\s*(.+)",
        texto,
        flags=re.IGNORECASE
    )

    if match:

        endereco = match.group(1).strip()

        numero_match = re.search(
            r"N[º°]\s*(\d+)",
            endereco,
            flags=re.IGNORECASE
        )

        if numero_match:

            dados["numero"] = (
                numero_match.group(1)
            )

            dados["logradouro"] = (
                endereco[:numero_match.start()]
                .rstrip(" ,")
            )

        else:

            dados["logradouro"] = endereco

    # --------------------------------------------------------
    # COMPLEMENTO
    # --------------------------------------------------------

    match = re.search(
        r"Complemento\s*:\s*(.*)",
        texto,
        flags=re.IGNORECASE
    )

    if match:

        dados["complemento"] = (
            match.group(1).strip()
        )

    # --------------------------------------------------------
    # BAIRRO
    # --------------------------------------------------------

    match = re.search(
        r"Bairro\s*:\s*(.*)",
        texto,
        flags=re.IGNORECASE
    )

    if match:

        dados["bairro"] = (
            match.group(1).strip()
        )

    # --------------------------------------------------------
    # CEP
    # --------------------------------------------------------

    match = re.search(
        r"CEP\s*:\s*(\d{5}-\d{3})",
        texto,
        flags=re.IGNORECASE
    )

    if match:

        dados["cep"] = (
            match.group(1)
        )

    # ========================================================
    # CNAEs
    # ========================================================

    padrao_cnae = re.compile(
        r"^\s*(\d{2}\.\d{2}-\d/\d{2})\s*-\s*(.+)$"
    )

    # --------------------------------------------------------
    # CNAE PRINCIPAL
    # --------------------------------------------------------

    secao_principal = extrair_bloco(
        texto,
        "Atividade Econômica Principal",
        "Atividades Econômicas Secundárias"
    )

    for linha in secao_principal.splitlines():

        linha = linha.strip()

        match = padrao_cnae.match(
            linha
        )

        if match:

            dados["cnae_principal"] = (
                normalizar_cnae(
                    match.group(1)
                )
            )

            break

    # --------------------------------------------------------
    # CNAEs SECUNDÁRIOS
    # --------------------------------------------------------

    secao_secundaria = extrair_bloco(
        texto,
        "Atividades Econômicas Secundárias",
        "Objeto Social"
    )

    for linha in secao_secundaria.splitlines():

        linha = linha.strip()

        match = padrao_cnae.match(
            linha
        )

        if match:

            codigo = normalizar_cnae(
                match.group(1)
            )

            if codigo not in (
                dados["cnaes_secundarios"]
            ):

                dados[
                    "cnaes_secundarios"
                ].append(codigo)

    # --------------------------------------------------------
    # LISTA COMPLETA DE CNAEs
    # --------------------------------------------------------

    if dados["cnae_principal"]:

        dados["cnaes"].append(
            dados["cnae_principal"]
        )

    for cnae in dados["cnaes_secundarios"]:

        if cnae not in dados["cnaes"]:

            dados["cnaes"].append(
                cnae
            )

    return dados


# ============================================================
# COMPARAÇÃO DE CAMPOS
# ============================================================

def comparar_campo(
    valor_cadastro,
    valor_legalizacao,
    normalizador
):

    cadastro = normalizador(
        valor_cadastro
    )

    legalizacao = normalizador(
        valor_legalizacao
    )

    if not cadastro and not legalizacao:

        return "ambos_nao_informados"

    if not cadastro:

        return "ausente_cadastro"

    if not legalizacao:

        return "ausente_legalizacao"

    if cadastro == legalizacao:

        return "igual"

    return "diferente"


# ============================================================
# EXIBIÇÃO DA COMPARAÇÃO
# ============================================================

def mostrar_comparacao(
    titulo,
    cadastro,
    legalizacao,
    normalizador
):

    status = comparar_campo(
        cadastro,
        legalizacao,
        normalizador
    )

    st.markdown(
        f"### {titulo}"
    )

    col1, col2, col3 = st.columns(
        [2, 2, 1]
    )

    with col1:

        st.caption(
            "Cadastro Municipal"
        )

        st.write(
            cadastro
            if cadastro
            else "— Não informado —"
        )

    with col2:

        st.caption(
            "Legalização"
        )

        st.write(
            legalizacao
            if legalizacao
            else "— Não informado —"
        )

    with col3:

        if status == "igual":

            st.success(
                "🟢 IGUAL"
            )

        elif status == "diferente":

            st.error(
                "🔴 DIVERGENTE"
            )

        elif status == "ausente_cadastro":

            st.warning(
                "🟠 AUSENTE NO CADASTRO"
            )

        elif status == "ausente_legalizacao":

            st.warning(
                "🟠 AUSENTE NA LEGALIZAÇÃO"
            )

        else:

            st.info(
                "⚪ NÃO INFORMADO"
            )

    return status


# ============================================================
# COMPARAÇÃO DOS CNAEs
# ============================================================

def comparar_cnaes(
    cadastro,
    legalizacao
):

    cadastro_set = set(cadastro)

    legalizacao_set = set(
        legalizacao
    )

    somente_cadastro = [
        cnae
        for cnae in cadastro
        if cnae not in legalizacao_set
    ]

    somente_legalizacao = [
        cnae
        for cnae in legalizacao
        if cnae not in cadastro_set
    ]

    comuns = [
        cnae
        for cnae in cadastro
        if cnae in legalizacao_set
    ]

    return (
        comuns,
        somente_cadastro,
        somente_legalizacao
    )


# ============================================================
# EXIBIÇÃO DOS CNAEs
# ============================================================

def mostrar_cnaes(
    cadastro,
    legalizacao
):

    st.markdown(
        "## 🏭 Comparação dos CNAEs"
    )

    (
        comuns,
        somente_cadastro,
        somente_legalizacao
    ) = comparar_cnaes(
        cadastro,
        legalizacao
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "CNAEs no Cadastro",
            len(cadastro)
        )

    with col2:

        st.metric(
            "CNAEs na Legalização",
            len(legalizacao)
        )

    with col3:

        st.metric(
            "CNAEs em comum",
            len(comuns)
        )

    # --------------------------------------------------------
    # CNAE PRINCIPAL
    # --------------------------------------------------------

    if legalizacao:

        principal = legalizacao[0]

        st.markdown(
            "### CNAE principal da Legalização"
        )

        if principal in set(cadastro):

            st.success(
                f"🟢 {formatar_cnae(principal)} "
                "— presente no Cadastro Municipal."
            )

        else:

            st.error(
                f"🔴 {formatar_cnae(principal)} "
                "— NÃO encontrado no Cadastro Municipal."
            )

    # --------------------------------------------------------
    # SOMENTE NO CADASTRO
    # --------------------------------------------------------

    if somente_cadastro:

        st.error(
            "🔴 CNAE(s) existente(s) no Cadastro "
            "Municipal e ausente(s) na Legalização:"
        )

        for cnae in somente_cadastro:

            st.write(
                f"- **{formatar_cnae(cnae)}**"
            )

    # --------------------------------------------------------
    # SOMENTE NA LEGALIZAÇÃO
    # --------------------------------------------------------

    if somente_legalizacao:

        st.error(
            "🔴 CNAE(s) existente(s) na Legalização "
            "e ausente(s) no Cadastro Municipal:"
        )

        for cnae in somente_legalizacao:

            st.write(
                f"- **{formatar_cnae(cnae)}**"
            )

    # --------------------------------------------------------
    # TODOS IGUAIS
    # --------------------------------------------------------

    if (
        not somente_cadastro
        and not somente_legalizacao
    ):

        st.success(
            f"🟢 Todos os {len(cadastro)} CNAEs "
            "do Cadastro Municipal estão presentes "
            "na Legalização e vice-versa."
        )

    # --------------------------------------------------------
    # TABELA COMPLETA
    # --------------------------------------------------------

    with st.expander(
        "📋 Ver comparação completa dos CNAEs"
    ):

        cadastro_set = set(
            cadastro
        )

        legalizacao_set = set(
            legalizacao
        )

        todos = []

        for cnae in cadastro:

            if cnae not in todos:

                todos.append(cnae)

        for cnae in legalizacao:

            if cnae not in todos:

                todos.append(cnae)

        tabela = []

        for cnae in todos:

            no_cadastro = (
                cnae in cadastro_set
            )

            na_legalizacao = (
                cnae in legalizacao_set
            )

            if (
                no_cadastro
                and na_legalizacao
            ):

                situacao = (
                    "🟢 Presente nos dois"
                )

            elif no_cadastro:

                situacao = (
                    "🔴 Somente no Cadastro"
                )

            else:

                situacao = (
                    "🔴 Somente na Legalização"
                )

            tabela.append(
                {
                    "CNAE": formatar_cnae(cnae),
                    "Cadastro": (
                        "✅"
                        if no_cadastro
                        else "❌"
                    ),
                    "Legalização": (
                        "✅"
                        if na_legalizacao
                        else "❌"
                    ),
                    "Situação": situacao
                }
            )

        st.dataframe(
            tabela,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# BOTÃO LIMPAR
# ============================================================

def limpar_campos():

    st.session_state[
        "texto_cadastro"
    ] = ""

    st.session_state[
        "texto_legalizacao"
    ] = ""


# ============================================================
# INTERFACE
# ============================================================

st.title(
    "🔎 Verifica preenchimento - Cadastro - Legalização"
)

st.write(
    "Compare os dados do Cadastro Municipal "
    "com os dados da Legalização."
)


# ============================================================
# CAMPOS DE INPUT
# ============================================================

col1, col2 = st.columns(2)


with col1:

    st.subheader(
        "📄 Arquivo 1 — Cadastro Municipal"
    )

    st.text_area(
        "Cole aqui o conteúdo completo do Cadastro Municipal",
        height=400,
        key="texto_cadastro"
    )


with col2:

    st.subheader(
        "📄 Arquivo 2 — Legalização"
    )

    st.text_area(
        "Cole aqui o conteúdo completo da Legalização",
        height=400,
        key="texto_legalizacao"
    )


# ============================================================
# BOTÕES
# ============================================================

col1, col2 = st.columns(2)


with col1:

    analisar = st.button(
        "🔎 Analisar documentos",
        type="primary",
        use_container_width=True
    )


with col2:

    st.button(
        "🧹 Limpar",
        on_click=limpar_campos,
        use_container_width=True
    )


# ============================================================
# PROCESSAMENTO
# ============================================================

if analisar:

    texto_cadastro = st.session_state[
        "texto_cadastro"
    ]

    texto_legalizacao = st.session_state[
        "texto_legalizacao"
    ]

    if (
        not texto_cadastro
        or not texto_legalizacao
    ):

        st.warning(
            "⚠️ Informe os dois documentos "
            "antes de realizar a análise."
        )

    else:

        cadastro = extrair_cadastro_municipal(
            texto_cadastro
        )

        legalizacao = extrair_legalizacao(
            texto_legalizacao
        )

        # ====================================================
        # DADOS IDENTIFICADOS
        # ====================================================

        st.divider()

        st.header(
            "📋 Dados identificados"
        )

        col1, col2 = st.columns(2)

        # ----------------------------------------------------
        # CADASTRO
        # ----------------------------------------------------

        with col1:

            st.subheader(
                "Cadastro Municipal"
            )

            st.write(
                f"**CNPJ:** "
                f"{cadastro['cnpj'] or 'Não informado'}"
            )

            st.write(
                f"**Razão Social:** "
                f"{cadastro['razao_social'] or 'Não informado'}"
            )

            st.write(
                f"**Natureza Jurídica:** "
                f"{cadastro['natureza_juridica'] or 'Não informado'}"
            )

            st.write(
                f"**Logradouro:** "
                f"{cadastro['logradouro'] or 'Não informado'}"
            )

            st.write(
                f"**Número:** "
                f"{cadastro['numero'] or 'Não informado'}"
            )

            st.write(
                f"**Bairro:** "
                f"{cadastro['bairro'] or 'Não informado'}"
            )

            st.write(
                f"**Complemento:** "
                f"{cadastro['complemento'] or 'Não informado'}"
            )

            st.write(
                f"**CEP:** "
                f"{cadastro['cep'] or 'Não informado'}"
            )

        # ----------------------------------------------------
        # LEGALIZAÇÃO
        # ----------------------------------------------------

        with col2:

            st.subheader(
                "Legalização"
            )

            st.write(
                f"**CNPJ:** "
                f"{legalizacao['cnpj'] or 'Não informado'}"
            )

            st.write(
                f"**Razão Social:** "
                f"{legalizacao['razao_social'] or 'Não informado'}"
            )

            st.write(
                f"**Natureza Jurídica:** "
                f"{legalizacao['natureza_juridica'] or 'Não informado'}"
            )

            st.write(
                f"**Logradouro:** "
                f"{legalizacao['logradouro'] or 'Não informado'}"
            )

            st.write(
                f"**Número:** "
                f"{legalizacao['numero'] or 'Não informado'}"
            )

            st.write(
                f"**Bairro:** "
                f"{legalizacao['bairro'] or 'Não informado'}"
            )

            st.write(
                f"**Complemento:** "
                f"{legalizacao['complemento'] or 'Não informado'}"
            )

            st.write(
                f"**CEP:** "
                f"{legalizacao['cep'] or 'Não informado'}"
            )

        # ====================================================
        # COMPARAÇÃO
        # ====================================================

        st.divider()

        st.header(
            "🔍 Comparação dos dados"
        )

        resultados = {}

        resultados["CNPJ"] = mostrar_comparacao(
            "CNPJ",
            cadastro["cnpj"],
            legalizacao["cnpj"],
            normalizar_cep
        )

        resultados["Razão Social"] = mostrar_comparacao(
            "Razão Social",
            cadastro["razao_social"],
            legalizacao["razao_social"],
            normalizar_razao_social
        )

        resultados["Natureza Jurídica"] = mostrar_comparacao(
            "Natureza Jurídica",
            cadastro["natureza_juridica"],
            legalizacao["natureza_juridica"],
            normalizar_natureza_juridica
        )

        resultados["Logradouro"] = mostrar_comparacao(
            "Logradouro",
            cadastro["logradouro"],
            legalizacao["logradouro"],
            normalizar_logradouro
        )

        resultados["Número"] = mostrar_comparacao(
            "Número",
            cadastro["numero"],
            legalizacao["numero"],
            normalizar_numero
        )

        resultados["Bairro"] = mostrar_comparacao(
            "Bairro",
            cadastro["bairro"],
            legalizacao["bairro"],
            normalizar_sem_acentos
        )

        resultados["Complemento"] = mostrar_comparacao(
            "Complemento",
            cadastro["complemento"],
            legalizacao["complemento"],
            normalizar_complemento
        )

        resultados["CEP"] = mostrar_comparacao(
            "CEP",
            cadastro["cep"],
            legalizacao["cep"],
            normalizar_cep
        )

        # ====================================================
        # CNAEs
        # ====================================================

        st.divider()

        mostrar_cnaes(
            cadastro["cnaes"],
            legalizacao["cnaes"]
        )

        # ====================================================
        # RESULTADO FINAL
        # ====================================================

        st.divider()

        st.header(
            "📊 Resultado da análise"
        )

        divergencias = []
        pendencias = []

        for campo, status in resultados.items():

            if status in (
                "diferente",
                "ausente_cadastro",
                "ausente_legalizacao"
            ):

                divergencias.append(
                    campo
                )

            elif status == (
                "ambos_nao_informados"
            ):

                pendencias.append(
                    campo
                )

        (
            _,
            somente_cadastro,
            somente_legalizacao
        ) = comparar_cnaes(
            cadastro["cnaes"],
            legalizacao["cnaes"]
        )

        if (
            somente_cadastro
            or somente_legalizacao
        ):

            divergencias.append(
                "CNAEs"
            )

        # ----------------------------------------------------
        # RESULTADO FINAL
        # ----------------------------------------------------

        if divergencias:

            st.error(
                "🔴 Foram encontradas divergências."
            )

            st.write(
                "**Campos com divergência:** "
                + ", ".join(divergencias)
            )

        elif pendencias:

            st.warning(
                "🟠 Não foram encontradas divergências "
                "nos dados informados, mas existem campos "
                "não informados nos dois documentos."
            )

            st.write(
                "**Campos não informados:** "
                + ", ".join(pendencias)
            )

        else:

            st.success(
                "🟢 Os dados analisados estão consistentes "
                "entre o Cadastro Municipal e a Legalização."
            )

        # ====================================================
        # CONFERÊNCIA TÉCNICA
        # ====================================================

        with st.expander(
            "🛠️ Conferência técnica da extração"
        ):

            st.write(
                "**Quantidade de CNAEs no Cadastro:**",
                len(cadastro["cnaes"])
            )

            st.write(
                [
                    formatar_cnae(cnae)
                    for cnae in cadastro["cnaes"]
                ]
            )

            st.write(
                "**Quantidade de CNAEs na Legalização:**",
                len(legalizacao["cnaes"])
            )

            st.write(
                [
                    formatar_cnae(cnae)
                    for cnae in legalizacao["cnaes"]
                ]
            )
