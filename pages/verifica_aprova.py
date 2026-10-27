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

        socios_comuns, socios_somente_cadastro, socios_somente_legalizacao = comparar_socios(
            cadastro["socios"], legalizacao["socios"]
        )
        if socios_somente_cadastro or socios_somente_legalizacao:
            divergencias.append("Sócios")
        elif not cadastro["socios"] or not legalizacao["socios"]:
            pendencias.append("Sócios (extração não confirmada)")

        if divergencias:

            st.error(
                "🔴 Foram encontradas divergências."
            )

            st.write(
                "**Campos com divergência:** "
                + ", ".join(
                    divergencias
                )
            )

        elif pendencias:

            st.warning(
                "🟠 Não foram encontradas divergências "
                "nos dados informados, mas existem campos "
                "não informados nos dois documentos."
            )

            st.write(
                "**Campos não informados:** "
                + ", ".join(
                    pendencias
                )
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

            st.write(
                "**Número extraído do Cadastro:**",
                cadastro["numero"]
            )

            st.write(
                "**Logradouro extraído do Cadastro:**",
                cadastro["logradouro"]
            )

            st.write(
                "**Bairro extraído do Cadastro:**",
                cadastro["bairro"]
            )

            st.write(
                "**Complemento extraído do Cadastro:**",
                cadastro["complemento"]
            )

            st.write(
                "**CEP extraído do Cadastro:**",
                cadastro["cep"]
            )
