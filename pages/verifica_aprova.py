import pandas as pd
import numpy as np
import streamlit as st
import re

# Configurações do Streamlit
st.set_page_config(
    page_title='Verifica preenchimento - JUCESC vs Extrato - Itajaí', 
    layout="centered", 
    initial_sidebar_state='expanded',
    menu_items=None
)

st.subheader('Verificação de Processo JUCESC x Extrato Econômico')

# Entradas de texto para colar o conteúdo dos arquivos
ib_prefeitura = st.text_input(
    "Cole todo o texto da página de detalhes do Processo (Prefeitura / JUCESC)",
    key="ib_prefeitura"
)

ib_extrato = st.text_input(
    "Cole todo o texto do Extrato do Cadastro Econômico",
    key="ib_extrato"
)

# Botão limpar
def clear_text():
    st.session_state["ib_prefeitura"] = ""
    st.session_state["ib_extrato"] = ""

st.button("Limpar", on_click=clear_text)

# Função auxiliar para normalizar CNAEs (remove pontuações e mantém os 7 dígitos)
def normalizar_cnaes(lista_cnaes):
    normalizados = set()
    for cnae in lista_cnaes:
        apenas_digitos = re.sub(r'\D', '', cnae)
        if len(apenas_digitos) >= 7:
            normalizados.add(apenas_digitos[:7])
    return normalizados

# Análise e cruzamento dos dados
try:
    if ib_prefeitura and ib_extrato != "":

        # -------------------------------------------------------------
        # 1. Extração segura de Informações do Processo (Prefeitura / JUCESC)
        # -------------------------------------------------------------
        cnpj_pref_match = re.search(r'\d\d.\d\d\d.\d\d\d/\d\d\d\d-\d\d', ib_prefeitura)
        cnpj_pref = cnpj_pref_match.group(0) if cnpj_pref_match else ""

        # Extração tolerante da Razão Social ignorando quebras de linha e pipes (|)
        nome_match = re.search(r'Nome Empresarial:\s*(?:\|\s*)*([^\n]+)', ib_prefeitura, re.IGNORECASE)
        razao_social_pref = nome_match.group(1).strip() if nome_match else "Não encontrada"

        # CNAEs eventualmente presentes na JUCESC
        cnaes_raw_pref = re.findall(r'\d{2}\.\d{2}-\d-\d{2}|\b\d{7}\b', ib_prefeitura)
        cnaes_pref_set = normalizar_cnaes(cnaes_raw_pref)

        # -------------------------------------------------------------
        # 2. Extração de Informações do Extrato Econômico
        # -------------------------------------------------------------
        cnpj_ext_match = re.search(r'\d\d.\d\d\d.\d\d\d/\d\d\d\d-\d\d', ib_extrato)
        cnpj_extrato = cnpj_ext_match.group(0) if cnpj_ext_match else ""

        # CNAEs no Extrato Econômico[cite: 3]
        cnaes_raw_extrato = re.findall(r'\d{2}\.\d{2}-\d-\d{2}|\b\d{7}\b', ib_extrato)
        cnaes_extrato_set = normalizar_cnaes(cnaes_raw_extrato)

        # -------------------------------------------------------------
        # 3. Impressão das Verificações e Resumo
        # -------------------------------------------------------------
        st.divider()
        st.subheader('Resumo da Comparação')
        
        if cnpj_extrato:
            st.markdown(f'**CNPJ Identificado:** {cnpj_extrato}')
        
        # --- Verificação do CNPJ ---
        st.subheader('Verificação do CNPJ')
        if cnpj_pref and cnpj_extrato and (cnpj_pref == cnpj_extrato):
            st.markdown(':green[Ok! O número do CNPJ coincide entre a JUCESC e o Extrato Econômico.]')
        else:
            st.markdown(':red[VERIFICAR! O número do CNPJ NÃO coincide ou não foi localizado.]')

        # --- Verificação da Razão Social ---
        st.subheader('Verificação da Razão Social / Nome')
        st.markdown(f'Processo JUCESC: **{razao_social_pref}**')
        st.markdown(':green[Ok! Extraído com sucesso da JUCESC. Confira visualmente se confere com o extrato.]')

        # --- Verificação dos CNAEs ---
        st.subheader('Verificação dos CNAEs / Atividades')
        
        if len(cnaes_pref_set) == 0:
            st.markdown(':orange[Nota: O texto colado da JUCESC não contém a listagem de códigos CNAE (comportamento padrão dessa tela do sistema). Abaixo estão os CNAEs detectados no Extrato Econômico:]')
            tabela_cnaes = pd.DataFrame({'CNAEs do Extrato Econômico': list(cnaes_extrato_set)})
            st.dataframe(tabela_cnaes)
        elif cnaes_pref_set == cnaes_extrato_set:
            st.markdown(':green[Ok! Todos os CNAEs coincidem perfeitamente entre os documentos.]')
            tabela_cnaes = pd.DataFrame({'CNAEs Validados': list(cnaes_extrato_set)})
            st.dataframe(tabela_cnaes)
        else:
            st.markdown(':red[VERIFICAR! Foram encontradas divergências entre as listas de CNAEs.]')
            col1, col2 = st.columns(2)
            with col1:
                st.text('CNAEs na JUCESC:')
                st.write(list(cnaes_pref_set))
            with col2:
                st.text('CNAEs no Extrato:')
                st.write(list(cnaes_extrato_set))

except Exception as e:
    st.markdown(':red[Verifique o correto preenchimento de todos os campos de texto.]')
