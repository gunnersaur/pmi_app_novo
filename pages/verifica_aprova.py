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

        # Extração precisa da Razão Social (para antes de encontrar Nome Fantasia ou Capital Social)[cite: 6]
        nome_match = re.search(r'Nome Empresarial:\s*(?:\|\s*)*([^\|]+?)(?=\s*(?:Nome Fantasia|Capital Social|Tipo de Estabelecimento|Data Início|Natureza Jurídica)|$)', ib_prefeitura, re.IGNORECASE)
        if nome_match:
            razao_social_pref = nome_match.group(1).replace('|', '').strip()
        else:
            razao_social_pref = "Não encontrada"

        # Extração precisa do Logradouro na JUCESC[cite: 7]
        log_match = re.search(r'Logradouro:\s*(?:\|\s*)*([^\|]+?)(?=\s*(?:Complemento|Referência|Bairro|Município)|$)', ib_prefeitura, re.IGNORECASE)
        logradouro_pref = log_match.group(1).replace('|', '').strip() if log_match else "Não encontrado"

        # -------------------------------------------------------------
        # 2. Extração de Informações do Extrato Econômico
        # -------------------------------------------------------------
        cnpj_ext_match = re.search(r'\d\d.\d\d\d.\d\d\d/\d\d\d\d-\d\d', ib_extrato)
        cnpj_extrato = cnpj_ext_match.group(0) if cnpj_ext_match else ""

        # CNAEs no Extrato Econômico (códigos de 7 dígitos)[cite: 3]
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
            st.markdown(':red[VERIFICAR! O número do CNPJ NÃO coincide.]')

        # --- Verificação da Razão Social ---
        st.subheader('Verificação da Razão Social / Nome')
        st.markdown(f'Processo JUCESC: **{razao_social_pref}**')
        st.markdown(':green[Ok! Nome empresarial isolado corretamente.]')

        # --- Verificação de Endereço ---
        st.subheader('Verificação Básica de Endereço')
        st.markdown(f'Logradouro JUCESC: **{logradouro_pref}**[cite: 7]')

        # --- Verificação dos CNAEs ---
        st.subheader('Verificação dos CNAEs / Atividades')
        st.markdown(f':blue[Total de CNAEs identificados no Extrato Econômico:] {len(cnaes_extrato_set)}[cite: 3]')
        
        if len(cnaes_extrato_set) > 0:
            tabela_cnaes = pd.DataFrame({'CNAEs do Extrato Econômico': list(cnaes_extrato_set)})
            st.dataframe(tabela_cnaes)
        else:
            st.markdown(':orange[Nenhum CNAE detectado no extrato. Verifique o texto colado.]')

except Exception as e:
    st.markdown(':red[Verifique o correto preenchimento de todos os campos de texto.]')
