import streamlit as st
import pandas as pd
import re
import unicodedata

# ============================================================
# CONFIGURAÇÕES
# ============================================================

st.set_page_config(
    page_title="Verifica Cadastro Econômico x Prefeitura",
    layout="centered",
    initial_sidebar_state="expanded",
    page_icon="images/favicon.png",
    menu_items=None,
)

# Sidebar
try:
    st.sidebar.image("images/logo.png", width=150)
except Exception:
    pass

st.sidebar.divider()

# Mantém a navegação do projeto, quando os arquivos existirem
st.sidebar.page_link("app.py", label="01_Consulta de Viabilidade (inscr.)")
st.sidebar.page_link("pages/cv_zona.py", label="__Consulta de Viabilidade (zona)")
st.sidebar.page_link("pages/verifica_aprova.py", label="02_Verifica processo ALF")
st.sidebar.page_link("pages/links.py", label="03_Links úteis")
st.sidebar.page_link(
    "pages/documentacao-complementar-ALF.py",
    label="04_Doc. complementar ALF",
)
st.sidebar.page_link(
    "pages/estudo-de-impacto-de-vizinhanca.py",
    label="05_EIV",
)
st.sidebar.page_link("pages/regin.py", label="06_REGIN - Alvará")
st.sidebar.page_link("pages/regin-viabilidade.py", label="07_REGIN - Viabilidade")
st.sidebar.page_link("pages/risco_regin.py", label="08_REGIN - Classificação de risco")


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def limpar_espacos(valor):
    """Converte múltiplos espaços/quebras de linha em um único espaço."""
    if valor is None:
        return ""
    return re.sub(r"\s+", " ", str(valor)).strip()


def somente_digitos(valor):
    return re.sub(r"\D", "", str(valor or ""))


def normalizar_texto(valor):
    """
    Normalização usada apenas para COMPARAÇÃO.
    Não altera o texto apresentado ao usuário.
    """
    valor = limpar_espacos(valor).upper()
    valor = unicodedata.normalize("NFKD", valor)
    valor = "".join(c for c in valor if not unicodedata.combining(c))
    return valor


def normalizar_logradouro(valor):
    """
    Remove apenas o tipo de logradouro do início para permitir
    comparar, por exemplo:

        JOAO THOMAZ PINTO
        RUA JOAO THOMAZ PINTO

    O valor original continua sendo exibido na tabela.
    """
    valor = normalizar_texto(valor)

    tipos = (
        r"RUA|R\.|AVENIDA|AV\.|ALAMEDA|AL\.|"
        r"TRAVESSA|TV\.|RODOVIA|ROD\.|ESTRADA|EST\.|"
        r"PRACA|PRACA\.|PRAÇA|LARGO"
    )

    valor = re.sub(rf"^(?:{tipos})\s+", "", valor)
    valor = re.sub(r"[,.]", "", valor)
    return limpar_espacos(valor)


def extrair_primeiro(regex, texto, flags=re.IGNORECASE | re.MULTILINE):
    resultado = re.search(regex, texto, flags)
    if not resultado:
        return ""
    return limpar_espacos(resultado.group(1))


# ============================================================
# PARSER — EXTRATO DO CADASTRO ECONÔMICO
# ============================================================

def extrair_cadastro_economico(texto):
    """
    Parser específico para o texto do:

    EXTRATO DO CADASTRO DE CONTRIBUINTE
    PESSOA JURÍDICA

    A lógica considera a organização observada no PDF:
    os rótulos de endereço aparecem antes do bloco de valores,
    sendo que o CEP aparece junto ao rótulo.
    """

    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    linhas = [limpar_espacos(x) for x in texto.split("\n")]
    linhas = [x for x in linhas if x != ""]

    resultado = {
        "cnpj": "",
        "razao_social": "",
        "nome_fantasia": "",
        "natureza": "",
        "logradouro": "",
        "numero": "",
        "complemento": "",
        "bairro": "",
        "cep": "",
        "cnaes": [],
        "situacao": "",
        "data_abertura": "",
        "horario": "",
        "inscricao_municipal": "",
    }

    # --------------------------------------------------------
    # CNPJ
    # --------------------------------------------------------
    cnpjs = re.findall(
        r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b",
        texto,
    )
    if cnpjs:
        resultado["cnpj"] = cnpjs[0]

    # --------------------------------------------------------
    # IDENTIFICAÇÃO DO CONTRIBUINTE
    # --------------------------------------------------------
    resultado["razao_social"] = extrair_primeiro(
        r"Nome:\s*(.*?)\s*(?:Nome Fantasia:|Desc\.?\s*Natureza Jurídica:|Natureza Jurídica:)",
        texto,
    )

    resultado["nome_fantasia"] = extrair_primeiro(
        r"Nome Fantasia:\s*(.*?)\s*(?:Desc\.?\s*Natureza Jurídica:|Natureza Jurídica:)",
        texto,
    )

    resultado["natureza"] = extrair_primeiro(
        r"(?:Desc\.?\s*Natureza Jurídica:|Natureza Jurídica:)\s*(.*?)(?:E-mail:|Endereço|Logradouro:)",
        texto,
    )

    # --------------------------------------------------------
    # ENDEREÇO
    #
    # No extrato analisado, o texto extraído do PDF apresenta:
    #
    # CEP: 88313-045
    # 1570 GALPAO:3;SALA:93
    # CANHANDUBA
    # JOAO THOMAZ PINTO
    #
    # após os rótulos de endereço.
    # --------------------------------------------------------
    indice_cep = -1

    for i, linha in enumerate(linhas):
        if re.search(r"\bCEP\s*:", linha, re.IGNORECASE):
            indice_cep = i
            cep = extrair_primeiro(r"CEP\s*:\s*(\d{5}-?\d{3})", linha)
            if cep:
                resultado["cep"] = cep
            break

    if indice_cep >= 0:
        bloco_endereco = linhas[indice_cep + 1: indice_cep + 4]

        if len(bloco_endereco) >= 1:
            linha_numero_complemento = bloco_endereco[0]

            # Ex.: "1570 GALPAO:3;SALA:93"
            numero = re.match(r"^(\d+[A-Z0-9\-]*)\b", linha_numero_complemento, re.IGNORECASE)

            if numero:
                resultado["numero"] = numero.group(1)
                resultado["complemento"] = limpar_espacos(
                    linha_numero_complemento[numero.end():]
                )

        if len(bloco_endereco) >= 2:
            resultado["bairro"] = bloco_endereco[1]

        if len(bloco_endereco) >= 3:
            resultado["logradouro"] = bloco_endereco[2]

    # --------------------------------------------------------
    # CNAEs
    #
    # O extrato possui vários códigos de 7 dígitos na seção
    # "Atividade Econômica CNAE".
    # Pegamos somente códigos de 7 dígitos em linhas próprias,
    # evitando confundir CNPJ, CEP etc.
    # --------------------------------------------------------
    inicio_cnae = -1
    fim_cnae = len(linhas)

    for i, linha in enumerate(linhas):
        if re.search(r"Atividade Econômica CNAE", linha, re.IGNORECASE):
            inicio_cnae = i
            break

    if inicio_cnae >= 0:
        for i in range(inicio_cnae + 1, len(linhas)):
            if re.search(
                r"Atividade Econômica Atual|Identificação do Contribuinte",
                linhas[i],
                re.IGNORECASE,
            ):
                fim_cnae = i
                break

        bloco_cnae = "\n".join(linhas[inicio_cnae + 1: fim_cnae])

        resultado["cnaes"] = sorted(
            set(re.findall(r"(?m)^\s*(\d{7})\b", bloco_cnae))
        )

    # --------------------------------------------------------
    # SITUAÇÃO / HORÁRIO / DATA
    # --------------------------------------------------------
    resultado["situacao"] = extrair_primeiro(
        r"Situação\s*:\s*(.*?)(?:Horário|Data|$)",
        texto,
    )

    resultado["horario"] = extrair_primeiro(
        r"Horário\s*:\s*(.*?)(?:Data|$)",
        texto,
    )

    resultado["data_abertura"] = extrair_primeiro(
        r"Data Abertura\s*:\s*(\d{2}/\d{2}/\d{4})",
        texto,
    )

    resultado["inscricao_municipal"] = extrair_primeiro(
        r"Inscrição Municipal\s*:\s*([0-9./-]+)",
        texto,
    )

    return resultado


# ============================================================
# PARSER — PREFEITURA / ANÁLISE DO ALVARÁ
# ============================================================

def extrair_prefeitura(texto):
    """
    Parser específico para o texto da Prefeitura/Aprova
    "Análise do Alvará".
    """

    texto = texto.replace("\r\n", "\n").replace("\r", "\n")

    resultado = {
        "protocolo": "",
        "data": "",
        "acao": "",
        "status": "",
        "cnpj": "",
        "razao_social": "",
        "nome_fantasia": "",
        "natureza": "",
        "capital_social": "",
        "tipo": "",
        "data_atividade": "",
        "regime": "",
        "logradouro": "",
        "numero": "",
        "complemento": "",
        "bairro": "",
        "municipio": "",
        "estado": "",
        "cep": "",
        "area_construida": "",
        "evento": "",
        "cnaes": [],
    }

    # --------------------------------------------------------
    # DADOS GERAIS
    # --------------------------------------------------------
    resultado["protocolo"] = extrair_primeiro(
        r"Protocolo\s*:?\s*(\d+)",
        texto,
    )

    resultado["data"] = extrair_primeiro(
        r"Data\s*:?\s*(\d{2}/\d{2}/\d{4})",
        texto,
    )

    resultado["acao"] = extrair_primeiro(
        r"Ação\s*:?\s*([^\n]+)",
        texto,
    )

    resultado["status"] = extrair_primeiro(
        r"Status\s*:?\s*([^\n]+)",
        texto,
    )

    # --------------------------------------------------------
    # IDENTIFICAÇÃO
    # --------------------------------------------------------
    resultado["natureza"] = extrair_primeiro(
        r"Natureza\s*:?\s*([^\n]+)",
        texto,
    )

    resultado["razao_social"] = extrair_primeiro(
        r"Nome Empresarial\s*:?\s*([^\n]+)",
        texto,
    )

    resultado["nome_fantasia"] = extrair_primeiro(
        r"Nome Fantasia\s*:?\s*([^\n]*)",
        texto,
    )

    resultado["capital_social"] = extrair_primeiro(
        r"Capital Social\s*:?\s*([^\n]+)",
        texto,
    )

    resultado["tipo"] = extrair_primeiro(
        r"Tipo\s*:?\s*([^\n]+)",
        texto,
    )

    resultado["data_atividade"] = extrair_primeiro(
        r"Data(?: de)? atividade\s*:?\s*(\d{2}/\d{2}/\d{4})",
        texto,
    )

    resultado["regime"] = extrair_primeiro(
        r"Regime(?: tributário)?\s*:?\s*([^\n]+)",
        texto,
    )

    # --------------------------------------------------------
    # CNPJ
    # --------------------------------------------------------
    cnpjs = re.findall(
        r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b",
        texto,
    )
    if cnpjs:
        # O primeiro CNPJ identificado no documento é usado.
        resultado["cnpj"] = cnpjs[0]

    # --------------------------------------------------------
    # EVENTO
    # --------------------------------------------------------
    resultado["evento"] = extrair_primeiro(
        r"Evento\s*:?\s*(.*?)(?:CNPJ|NIRE|Logradouro)",
        texto,
    )

    # --------------------------------------------------------
    # ENDEREÇO
    # --------------------------------------------------------
    resultado["logradouro"] = extrair_primeiro(
        r"Logradouro\s*:?\s*([^\n]+)",
        texto,
    ).rstrip(",")

    resultado["numero"] = extrair_primeiro(
        r"(?:Nº|N°|Numero|Número)\s*:?\s*([^\n]+)",
        texto,
    )

    resultado["complemento"] = extrair_primeiro(
        r"Complemento\s*:?\s*([^\n]+)",
        texto,
    )

    resultado["bairro"] = extrair_primeiro(
        r"Bairro\s*:?\s*([^\n]+)",
        texto,
    )

    resultado["municipio"] = extrair_primeiro(
        r"Município\s*:?\s*([^\n]+)",
        texto,
    )

    resultado["estado"] = extrair_primeiro(
        r"Estado\s*:?\s*([A-Z]{2})",
        texto,
    )

    resultado["cep"] = extrair_primeiro(
        r"CEP\s*:?\s*(\d{5}-?\d{3})",
        texto,
    )

    resultado["area_construida"] = extrair_primeiro(
        r"Área Construída\s*:?\s*([^\n]+)",
        texto,
    )

    # O documento da Prefeitura analisado não apresenta uma
    # relação explícita de CNAEs. Portanto, não inferimos CNAEs.
    resultado["cnaes"] = []

    return resultado


# ============================================================
# COMPARAÇÕES
# ============================================================

def comparar_exato(valor1, valor2):
    a = normalizar_texto(valor1)
    b = normalizar_texto(valor2)

    if a == b:
        return "OK", "🟢"

    return "DIFERENTE", "🔴"


def comparar_cnpj(valor1, valor2):
    a = somente_digitos(valor1)
    b = somente_digitos(valor2)

    if a and b and a == b:
        return "OK", "🟢"

    if not a or not b:
        return "NÃO LOCALIZADO", "🟡"

    return "DIFERENTE", "🔴"


def comparar_logradouro(valor1, valor2):
    a_original = normalizar_texto(valor1)
    b_original = normalizar_texto(valor2)

    if a_original == b_original:
        return "OK", "🟢"

    a = normalizar_logradouro(valor1)
    b = normalizar_logradouro(valor2)

    if a and b and a == b:
        return "EQUIVALENTE APÓS NORMALIZAÇÃO", "🟡"

    return "DIFERENTE", "🔴"


def comparar_campo(campo, cadastro, prefeitura):
    valor_cadastro = cadastro.get(campo, "")
    valor_prefeitura = prefeitura.get(campo, "")

    if campo == "cnpj":
        status, simbolo = comparar_cnpj(valor_cadastro, valor_prefeitura)
    elif campo == "logradouro":
        status, simbolo = comparar_logradouro(
            valor_cadastro,
            valor_prefeitura,
        )
    else:
        status, simbolo = comparar_exato(
            valor_cadastro,
            valor_prefeitura,
        )

    return {
        "Campo": campo.replace("_", " ").upper(),
        "Cadastro Econômico": valor_cadastro or "—",
        "Prefeitura / Aprova": valor_prefeitura or "—",
        "Resultado": f"{simbolo} {status}",
    }


# ============================================================
# ESTILO DA TABELA
# ============================================================

def destacar_resultado(row):
    resultado = str(row["Resultado"])

    if "🟢" in resultado:
        return [""] * len(row)

    if "🟡" in resultado:
        return ["background-color: #fff3cd"] * len(row)

    if "🔴" in resultado:
        return ["background-color: #f8d7da"] * len(row)

    return [""] * len(row)


# ============================================================
# INTERFACE
# ============================================================

st.subheader("Verifica Cadastro Econômico x Prefeitura / Aprova")

st.write(
    "Cole o texto extraído dos dois documentos abaixo. "
    "O parser mantém a lógica específica dos documentos e as "
    "comparações são feitas somente depois da extração."
)

st.text_area(
    "1. Cole todo o texto do Extrato do Cadastro de Contribuinte Pessoa Jurídica",
    key="ib_cadastro",
    height=350,
)

st.text_area(
    "2. Cole todo o texto da Análise do Alvará / Prefeitura",
    key="ib_prefeitura",
    height=350,
)


# ------------------------------------------------------------
# LIMPAR
# ------------------------------------------------------------

def clear_text():
    st.session_state["ib_cadastro"] = ""
    st.session_state["ib_prefeitura"] = ""


st.button("Limpar", on_click=clear_text)


# ============================================================
# ANÁLISE
# ============================================================

texto_cadastro = st.session_state.get("ib_cadastro", "")
texto_prefeitura = st.session_state.get("ib_prefeitura", "")

if texto_cadastro and texto_prefeitura:

    try:
        cadastro = extrair_cadastro_economico(texto_cadastro)
        prefeitura = extrair_prefeitura(texto_prefeitura)

        # ----------------------------------------------------
        # RESUMO
        # ----------------------------------------------------
        st.divider()
        st.subheader("Resumo do processo")

        st.markdown(
            f"**RAZÃO SOCIAL:** "
            f"{cadastro['razao_social'] or 'Não localizada'}"
        )

        st.markdown(
            f"**CNPJ:** "
            f"{cadastro['cnpj'] or 'Não localizado'}"
        )

        endereco_cadastro = ", ".join(
            x for x in [
                cadastro["logradouro"],
                cadastro["numero"],
                cadastro["complemento"],
                cadastro["bairro"],
                cadastro["cep"],
            ]
            if x
        )

        endereco_prefeitura = ", ".join(
            x for x in [
                prefeitura["logradouro"],
                prefeitura["numero"],
                prefeitura["complemento"],
                prefeitura["bairro"],
                prefeitura["cep"],
            ]
            if x
        )

        st.markdown(f"**ENDEREÇO – CADASTRO:** {endereco_cadastro}")
        st.markdown(f"**ENDEREÇO – PREFEITURA:** {endereco_prefeitura}")

        # ----------------------------------------------------
        # TABELA DE COMPARAÇÃO
        # ----------------------------------------------------
        st.subheader("Tabela de conferência")

        campos = [
            "cnpj",
            "razao_social",
            "nome_fantasia",
            "natureza",
            "logradouro",
            "numero",
            "complemento",
            "bairro",
            "cep",
        ]

        dados_comparacao = [
            comparar_campo(campo, cadastro, prefeitura)
            for campo in campos
        ]

        tabela = pd.DataFrame(dados_comparacao)

        st.dataframe(
            tabela.style.apply(destacar_resultado, axis=1),
            use_container_width=True,
            hide_index=True,
        )

        # ----------------------------------------------------
        # CNAEs
        # ----------------------------------------------------
        st.subheader("Verificação dos CNAEs")

        cnaes_cadastro = set(cadastro["cnaes"])
        cnaes_prefeitura = set(prefeitura["cnaes"])

        if not cnaes_prefeitura:
            st.warning(
                "🟡 O documento da Prefeitura / Análise do Alvará "
                "não apresenta uma relação explícita de CNAEs. "
                "Não foi feita inferência de CNAEs."
            )

            if cnaes_cadastro:
                st.write(
                    "CNAEs identificados no Cadastro Econômico:"
                )
                tabela_cnaes = pd.DataFrame(
                    {"CNAEs do Cadastro Econômico": sorted(cnaes_cadastro)}
                )
                st.dataframe(
                    tabela_cnaes,
                    use_container_width=True,
                    hide_index=True,
                )
        else:
            if cnaes_cadastro == cnaes_prefeitura:
                st.success(
                    "🟢 CNAEs coincidem entre os dois documentos."
                )
            else:
                st.error(
                    "🔴 Há diferenças entre os CNAEs dos documentos."
                )

                somente_cadastro = sorted(
                    cnaes_cadastro - cnaes_prefeitura
                )
                somente_prefeitura = sorted(
                    cnaes_prefeitura - cnaes_cadastro
                )

                if somente_cadastro:
                    st.write(
                        "**CNAEs somente no Cadastro Econômico:**"
                    )
                    st.dataframe(
                        pd.DataFrame(
                            {"CNAE": somente_cadastro}
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )

                if somente_prefeitura:
                    st.write(
                        "**CNAEs somente na Prefeitura / Aprova:**"
                    )
                    st.dataframe(
                        pd.DataFrame(
                            {"CNAE": somente_prefeitura}
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )

        # ----------------------------------------------------
        # CHECKLIST FINAL
        # ----------------------------------------------------
        st.subheader("Checklist final")

        verificacoes = []

        for campo in campos:
            item = comparar_campo(campo, cadastro, prefeitura)

            if "🟢" in item["Resultado"]:
                verificacoes.append(
                    ("🟢", item["Campo"], "Conferido")
                )
            elif "🟡" in item["Resultado"]:
                verificacoes.append(
                    ("🟡", item["Campo"], item["Resultado"])
                )
            else:
                verificacoes.append(
                    ("🔴", item["Campo"], item["Resultado"])
                )

        # CNAEs são separados porque o documento da Prefeitura
        # analisado não os apresenta.
        if not prefeitura["cnaes"]:
            verificacoes.append(
                (
                    "🟡",
                    "CNAES",
                    "Não apresentados na Análise do Alvará — conferir manualmente",
                )
            )

        checklist = pd.DataFrame(
            verificacoes,
            columns=["", "VERIFICAÇÃO", "SITUAÇÃO"],
        )

        st.dataframe(
            checklist,
            use_container_width=True,
            hide_index=True,
        )

        # ----------------------------------------------------
        # OBSERVAÇÕES IMPORTANTES
        # ----------------------------------------------------
        st.subheader("Observações")

        if (
            normalizar_texto(cadastro["logradouro"])
            != normalizar_texto(prefeitura["logradouro"])
            and normalizar_logradouro(cadastro["logradouro"])
            == normalizar_logradouro(prefeitura["logradouro"])
        ):
            st.info(
                "🟡 O logradouro aparece como "
                f"'{cadastro['logradouro']}' no Cadastro Econômico e "
                f"'{prefeitura['logradouro']}' na Prefeitura. "
                "Após retirar apenas o prefixo do tipo de logradouro, "
                "os nomes são equivalentes. A diferença original é "
                "mantida na tabela."
            )

        if (
            cadastro["nome_fantasia"]
            and not prefeitura["nome_fantasia"]
        ):
            st.info(
                "🟡 O Cadastro Econômico informa Nome Fantasia, "
                "mas o campo correspondente da Prefeitura / Aprova "
                "está vazio no texto analisado."
            )

        st.info(
            "A ausência de CNAEs no documento da Prefeitura não foi "
            "tratada como divergência. O código não foi inventado "
            "nem inferido a partir do evento de alteração de atividades."
        )

    except Exception as erro:
        st.error(
            "Erro durante a análise. Verifique se os textos "
            "correspondem aos documentos esperados."
        )
        st.exception(erro)

else:
    st.info(
        "Cole os dois documentos acima para iniciar a análise."
    )
