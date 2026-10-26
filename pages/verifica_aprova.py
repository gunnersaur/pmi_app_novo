    c2.write(valor_legalizacao or "Não identificado")
    if not valor_cadastro or not valor_legalizacao:
        c3.warning("Conferir")
    elif not comparar or normalizar_comparacao(valor_cadastro) == normalizar_comparacao(valor_legalizacao):
        c3.success("Coincide" if comparar else "Manual")
    else:
        c3.error("Diverge")

# ============================================================
# INTERFACE STREAMLIT
# ============================================================
st.title("Verifica preenchimento - Cadastro - Legalização")
st.caption("Comparação do Extrato do Cadastro de Contribuinte Pessoa Jurídica com a Análise do Alvará do Aprova Digital.")
st.info("Cole o texto completo de cada documento. A extração automática depende da estrutura do texto copiado; confira os campos marcados para revisão.")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Cadastro Municipal")
    texto_cadastro = st.text_area(
        "Texto do Cadastro Municipal", height=380, key="texto_cadastro",
        placeholder="Cole aqui o Extrato do Cadastro de Contribuinte Pessoa Jurídica...",
        label_visibility="collapsed",
    )
with col2:
    st.subheader("Legalização")
    texto_legalizacao = st.text_area(
        "Texto da Legalização", height=380, key="texto_legalizacao",
        placeholder="Cole aqui o texto da Análise do Alvará do Aprova Digital...",
        label_visibility="collapsed",
    )

b1, b2, _ = st.columns([1, 1, 4])
with b1:
    verificar = st.button("🔎 VERIFICAR", type="primary", use_container_width=True)
with b2:
    limpar = st.button("🧹 LIMPAR", use_container_width=True)
if limpar:
    st.session_state["texto_cadastro"] = ""
    st.session_state["texto_legalizacao"] = ""
    st.rerun()

if verificar:
    if not texto_cadastro.strip() or not texto_legalizacao.strip():
        st.warning("Preencha os dois campos antes de verificar.")
        st.stop()

    cadastro = extrair_dados_cadastro(texto_cadastro)
    legalizacao = extrair_dados_legalizacao(texto_legalizacao)
    st.divider()
    st.header("Resultado da comparação")

    st.subheader("1. Identificação da empresa")
    exibir_comparacao_campo("CNPJ", cadastro["cnpj"], legalizacao["cnpj"])
    exibir_comparacao_campo("Razão social", cadastro["razao_social"], legalizacao["razao_social"])
    exibir_comparacao_campo("Natureza jurídica", cadastro["natureza_juridica"], legalizacao["natureza_juridica"])

    st.subheader("2. Endereço")
    ec, el = cadastro["endereco"], legalizacao["endereco"]
    for rotulo, chave in [("Logradouro", "logradouro"), ("Número", "numero"), ("Complemento", "complemento"), ("Bairro", "bairro"), ("CEP", "cep")]:
        exibir_comparacao_campo(rotulo, ec.get(chave), el.get(chave), comparar=(chave != "complemento"))
    if ec.get("logradouro") and ec.get("numero"):
        endereco_maps = f'{ec["logradouro"]}, {ec["numero"]}, Itajaí - SC'
        st.link_button("📍 Abrir endereço do Cadastro no Google Maps", "https://www.google.com/maps/search/?api=1&query=" + quote_plus(endereco_maps))

    st.subheader("3. Comparação dos CNAEs")
    cnaes_cad, cnaes_leg = set(cadastro["cnaes"]), set(legalizacao["cnaes"])
    if cnaes_cad and cnaes_leg and cnaes_cad == cnaes_leg:
        st.success("Os CNAEs identificados coincidem.")
    elif not cnaes_cad or not cnaes_leg:
        st.warning("Não foi possível identificar CNAEs em um dos documentos. Confira o texto extraído.")
    else:
        st.error("Há diferenças entre os CNAEs identificados.")
    todos = sorted(cnaes_cad | cnaes_leg)
    if todos:
        st.dataframe(pd.DataFrame({
            "CNAE": [formatar_cnae(x) for x in todos],
            "Cadastro Municipal": ["✓" if x in cnaes_cad else "—" for x in todos],
            "Legalização": ["✓" if x in cnaes_leg else "—" for x in todos],
            "Resultado": ["Coincide" if x in cnaes_cad and x in cnaes_leg else "Somente em um documento" for x in todos],
        }), use_container_width=True, hide_index=True)

    st.subheader("4. Comparação de sócios e responsáveis")
    socios = comparar_socios(texto_cadastro, texto_legalizacao)
    n_correspondentes = len(socios["correspondentes"])
    n_divergencias = len(socios["divergencias_nome"])
    n_somente = len(socios["somente_cadastro"]) + len(socios["somente_legalizacao"])
    m1, m2, m3 = st.columns(3)
    m1.metric("Correspondentes", n_correspondentes)
    m2.metric("Divergências de nome", n_divergencias)
    m3.metric("Não localizados no outro documento", n_somente)

    if not socios["cadastro"]:
        st.warning("Não foi possível identificar sócios na seção 'Sócios' do Cadastro Municipal.")
    if not socios["legalizacao"]:
        st.warning("Não foi possível identificar sócios na seção 'Quadro Societário' da Legalização.")

    if socios["correspondentes"]:
        st.markdown("**🟢 Sócios correspondentes**")
        st.dataframe(pd.DataFrame(socios["correspondentes"]), use_container_width=True, hide_index=True)
    if socios["divergencias_nome"]:
        st.markdown("**🔴 Mesmo CPF, mas nome divergente**")
        st.dataframe(pd.DataFrame(socios["divergencias_nome"]), use_container_width=True, hide_index=True)
    if socios["somente_cadastro"]:
        st.markdown("**🟡 Encontrados somente no Cadastro Municipal**")
        st.dataframe(pd.DataFrame([{"CPF": x["cpf"] or "Não identificado", "Nome": x["nome"], "Qualificação": x["qualificacao"] or "Não identificada"} for x in socios["somente_cadastro"]]), use_container_width=True, hide_index=True)
    if socios["somente_legalizacao"]:
        st.markdown("**🟡 Encontrados somente na Legalização**")
        st.dataframe(pd.DataFrame([{"CPF": x["cpf"] or "Não identificado", "Nome": x["nome"], "Qualificação": x["qualificacao"] or "Não identificada"} for x in socios["somente_legalizacao"]]), use_container_width=True, hide_index=True)
    if not socios["correspondentes"] and not socios["divergencias_nome"] and not n_somente:
        st.info("Não há registros suficientes para concluir a comparação societária automaticamente.")
    st.caption("A comparação utiliza o CPF como chave preferencial e o nome normalizado como conferência. A repetição do mesmo CPF em 'Sócios' e 'Responsáveis' no Cadastro Municipal é deduplicada.")

    with st.expander("🔧 Diagnóstico dos dados extraídos"):
        st.json({
            "cadastro": cadastro,
            "legalizacao": legalizacao,
            "socios_cadastro_extraidos": socios["cadastro"],
            "socios_legalizacao_extraidos": socios["legalizacao"],
        })
