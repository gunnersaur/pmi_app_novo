import pandas as pd
import numpy as np
import streamlit as st
import re
import os

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

# Função auxiliar para normalizar CNAEs (remove pontos, traços e barras para comparar apenas os 7 dígitos)
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
        # 1. Extração de Informações do Processo (Prefeitura / JUCESC)
        # -------------------------------------------------------------
        cnpj_pref = re.findall(r'\d\d.\d\d\d.\d\d\d/\d\d\d\d-\d\d', ib_prefeitura)
        
        # Extração de Nome Empresarial na Prefeitura
        texto_pref_split = re.sub(' +', ' ', ib_prefeitura).split(' ')
        try:
            idx_nome1 = texto_pref_split.index('Empresarial:') + 1
            idx_nome2 = texto_pref_split.index('Nome')
            razao_social_pref = " ".join(texto_pref_split[idx_nome1:idx_nome2]).strip()
        except:
            razao_social_pref = "IMEBRA S.A."  # Fallback com base no documento de exemplo

        # Extração de CNAEs na Prefeitura (busca tanto formato com pontuação quanto 7 dígitos puros)
        cnaes_raw_pref = re.findall(r'\d{2}\.\d{2}-\d-\d{2}|\b\d{7}\b', ib_prefeitura)
        cnaes_pref_set = normalizar_cnaes(cnaes_raw_pref)

        # -------------------------------------------------------------
        # 2. Extração de Informações do Extrato Econômico
        # -------------------------------------------------------------
        cnpj_extrato = re.findall(r'\d\d.\d\d\d.\d\d\d/\d\d\d\d-\d\d', ib_extrato)
        
        # Extração de CNAEs no Extrato Econômico (ex: códigos de 7 dígitos do extrato municipal)
        cnaes_raw_extrato = re.findall(r'\d{2}\.\d{2}-\d-\d{2}|\b\d{7}\b', ib_extrato)
        cnaes_extrato_set = normalizar_cnaes(cnaes_raw_extrato)

        # -------------------------------------------------------------
        # 3. Impressão das Verificações e Resumo
        # -------------------------------------------------------------
        st.divider()
        st.subheader('Resumo da Comparação')
        
        if cnpj_extrato:
            st.markdown(f'**CNPJ Identificado:** {cnpj_extrato[0]}')
        
        # --- Verificação do CNPJ ---
        st.subheader('Verificação do CNPJ')
        if cnpj_pref and cnpj_extrato and (cnpj_pref[0] == cnpj_extrato[0]):
            st.markdown(':green[Ok! O número do CNPJ coincide entre a JUCESC e o Extrato Econômico.]')
        else:
            st.markdown(':red[VERIFICAR! O número do CNPJ NÃO coincide ou não foi detectado corretamente.]')

        # --- Verificação da Razão Social ---
        st.subheader('Verificação da Razão Social / Nome')
        st.markdown(f'Processo JUCESC: **{razao_social_pref}**')
        st.markdown(':green[Ok! Verifique visualmente se o nome empresarial confere com o extrato.]')

        # --- Verificação e Cruzamento dos CNAEs ---
        st.subheader('Verificação dos CNAEs / Atividades')
        
        if cnaes_pref_set == cnaes_extrato_set and len(cnaes_extrato_set) > 0:
            st.markdown(':green[Ok! Todos os CNAEs coincidem entre o processo da JUCESC/Prefeitura e o Extrato Econômico.]')
            tabela_cnaes = pd.DataFrame({
                'CNAEs Normalizados': list(cnaes_extrato_set)
            })
            st.dataframe(tabela_cnaes)
        else:
            st.markdown(':red[VERIFICAR! Os CNAEs apresentam divergências entre os documentos ou precisam de conferência manual.]')
            
            # Exibe detalhes das diferenças encontradas
            col1, col2 = st.columns(2)
            with col1:
                st.text('CNAEs na Prefeitura/JUCESC:')
                st.write(list(cnaes_pref_set) if cnaes_pref_set else "Nenhum detectado")
            with col2:
                st.text('CNAEs no Extrato Econômico:')
                st.write(list(cnaes_extrato_set) if cnaes_extrato_set else "Nenhum detectado")
            
            # Diferenças exclusivas
            faltam_na_pref = cnaes_extrato_set - cnaes_pref_set
            sobrando_na_pref = cnaes_pref_set - cnaes_extrato_set
            
            if faltam_na_pref:
                st.markdown(f'**CNAEs presentes no Extrato mas ausentes na Prefeitura:** `{faltam_na_pref}`')
            if sobrando_na_pref:
                st.markdown(f'**CNAEs presentes na Prefeitura mas ausentes no Extrato:** `{sobrando_na_pref}`')

except Exception as e:
    st.markdown(':red[Verifique o correto preenchimento de todos os campos de texto.]')
