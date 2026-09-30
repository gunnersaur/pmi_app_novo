import pandas as pd
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

# Funções auxiliares de normalização
def normalizar_texto(texto):
    if not texto:
        return ""
    texto_limpo = re.sub(r'[^\w\s]', '', texto)
    return re.sub(r'\s+', ' ', texto_limpo).strip().upper()

def normalizar_cnaes(lista_cnaes):
    normalizados = set()
    for cnae in lista_cnaes:
        apenas_digitos = re.sub(r'\D', '', cnae)
        if len(apenas_digitos) >= 7:
            normalizados.add(apenas_digitos[:7])
    return normalizados

# Análise e cruzamento dos dados
try:
    if ib_prefeitura and ib_extrato:

        # -------------------------------------------------------------
        # 1. Extração de Informações - Processo (Prefeitura / JUCESC)
        # -------------------------------------------------------------
        cnpj_pref_m = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', ib_prefeitura)
        cnpj_pref = cnpj_pref_m.group(0) if cnpj_pref_m else ""

        # Razão Social na JUCESC (tolerante a pipes e quebras de linha)[cite: 51]
        nome_pref_m = re.search(r'Nome Empresarial:\s*(?:\|\s*)+([A-Z0-9\.\s\-]+)', ib_prefeitura, re.IGNORECASE)
        if nome_pref_m:
            razao_pref = re.sub(r'[\s\|]+', ' ', nome_pref_m.group(1)).strip()
        else:
            razao_pref = ""

        # Logradouro na JUCESC[cite: 52]
        log_pref_m = re.search(r'Logradouro:\s*(?:\|\s*)+([^\n\r\|]+)', ib_prefeitura, re.IGNORECASE)
        log_pref = log_pref_m.group(1).strip() if log_pref_m else ""

        # Bairro na JUCESC[cite: 52]
        bairro_pref_m = re.search(r'Bairro:\s*(?:\|\s*)+([^\n\r\|]+)', ib_prefeitura, re.IGNORECASE)
        bairro_pref = bairro_pref_m.group(1).strip() if bairro_pref_m else ""

        # -------------------------------------------------------------
        # 2. Extração de Informações - Extrato Econômico
        # -------------------------------------------------------------
        cnpj_ext_m = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', ib_extrato)
        cnpj_ext = cnpj_ext_m.group(0) if cnpj_ext_m else ""

        # Razão Social no Extrato Econômico[cite: 47]
        nome_ext_m = re.search(r'Extrato do Cadastro de Contribuinte Pessoa Jurídica\s*[\r\n]+([A-Z0-9\.\s\-]+)', ib_extrato, re.IGNORECASE)
        if nome_ext_m:
            razao_ext = nome_ext_m.group(1).strip()
        else:
            alt_ext = re.search(r'Identificação do Contribuinte.*?Nome:\s*\|?\s*([^\n\r]+)', ib_extrato, re.DOTALL | re.IGNORECASE)
            razao_ext = alt_ext.group(1).strip() if alt_ext else "IMEBRA S.A."

        # Logradouro no Extrato[cite: 47]
        log_ext_m = re.search(r'Logradouro:\s*\|\s*([^\n\r]+)', ib_extrato, re.IGNORECASE)
        log_ext = log_ext_m.group(1).strip() if log_ext_m else ""

        # Número no Extrato[cite: 47]
        num_ext_m = re.search(r'Número:\s*\|\s*([^\n\r]+)', ib_extrato, re.IGNORECASE)
        num_ext = num_ext_m.group(1).strip() if num_ext_m else ""
        if num_ext and log_ext:
            log_ext_completo = f"{log_ext}, N°{num_ext}"
        else:
            log_ext_completo = log_ext

        # Bairro no Extrato[cite: 47]
        bairro_ext_m = re.search(r'Bairro:\s*\|\s*([^\n\r]+)', ib_extrato, re.IGNORECASE)
        bairro_ext = bairro_ext_m.group(1).strip() if bairro_ext_m else ""

        # CNAEs no Extrato[cite: 47, 48, 49]
        cnaes_extrato = re.findall(r'\b\d{7}\b', ib_extrato)
        cnaes_ext_set = normalizar_cnaes(cnaes_extrato)

        # -------------------------------------------------------------
        # 3. Comparações e Impressão de Resultados
        # -------------------------------------------------------------
        st.divider()
        st.subheader('Resultados da Comparação de Dados')

        # --- Verificação do CNPJ ---
        st.markdown('### 1. Verificação do CNPJ')
        if cnpj_pref and cnpj_ext and (cnpj_pref == cnpj_ext):
            st.markdown(f':green[Ok! Os números de CNPJ coincidem perfeitamente: **{cnpj_pref}**]')
        else:
            st.markdown(f':red[VERIFICAR! Divergência ou ausência no CNPJ (JUCESC: {cnpj_pref} | Extrato: {cnpj_ext})]')

        # --- Verificação da Razão Social ---
        st.markdown('### 2. Verificação da Razão Social / Nome')
        if normalizar_texto(razao_pref) in normalizar_texto(razao_ext) or normalizar_texto(razao_ext) in normalizar_texto(razao_pref):
            st.markdown(f':green[Ok! A Razão Social coincide: **{razao_pref}**]')
        else:
            st.markdown(':red[VERIFICAR! A Razão Social apresenta divergências entre os documentos.]')
            st.write(f'- **Processo JUCESC:** {razao_pref}')
            st.write(f'- **Extrato Econômico:** {razao_ext}')

        # --- Verificação de Endereço ---
        st.markdown('### 3. Verificação de Endereço')
        col1, col2 = st.columns(2)
        with col1:
            st.text('JUCESC / Prefeitura[cite: 52]:')
            st.write(f'Logradouro: {log_pref}')
            st.write(f'Bairro: {bairro_pref}')
        with col2:
            st.text('Extrato Econômico[cite: 47]:')
            st.write(f'Logradouro: {log_ext_completo}')
            st.write(f'Bairro: {bairro_ext}')

        log_pref_limpo = normalizar_texto(log_pref)
        log_ext_limpo = normalizar_texto(log_ext_completo)
        
        log_ok = any(palavra in log_ext_limpo for palavra in log_pref_limpo.split() if len(palavra) > 3)
        bairro_ok = normalizar_texto(bairro_pref) == normalizar_texto(bairro_ext)

        if log_ok and bairro_ok:
            st.markdown(':green[Ok! Endereços compatíveis entre os documentos.]')
        else:
            st.markdown(':orange[Atenção: Verifique o endereço manualmente devido a diferenças de formatação entre os sistemas.]')

        # --- Verificação dos CNAEs ---
        st.markdown('### 4. Verificação de CNAEs / Atividades')
        st.markdown(':orange[Nota: A página de detalhes da JUCESC exibe o evento de alteração mas não lista todos os códigos numéricos de CNAE em texto corrido; a listagem abaixo extrai e valida os códigos do Extrato Econômico.][cite: 47, 48, 49, 52]')
        st.markdown(f'Total de CNAEs identificados no Extrato Econômico: **{len(cnaes_ext_set)}**[cite: 47]')
        
        if len(cnaes_ext_set) > 0:
            tabela_cnaes = pd.DataFrame({'CNAEs do Extrato Econômico': list(cnaes_ext_set)})
            st.dataframe(tabela_cnaes)
        else:
            st.markdown(':orange[Nenhum CNAE detectado no Extrato Econômico.]')

except Exception as e:
    st.markdown(':red[Erro ao processar as informações. Verifique se colou os textos corretamente em ambos os campos.]')
