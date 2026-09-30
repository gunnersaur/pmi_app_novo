import pandas as pd
import streamlit as st
import re

# Configurações do Streamlit
st.set_page_config(
    page_title='Verifica preenchimento - ALF - Aprova Digital', 
    layout="centered", 
    initial_sidebar_state='expanded',
    page_icon=('images/favicon.png'), 
    menu_items=None
)

logo_image = ('images/logo.png')

# Sidebar
# st.sidebar.image(logo_image, width=150) # Descomente se tiver a imagem
st.sidebar.divider()
st.sidebar.page_link("app.py", label="01_Consulta de Viabilidade (inscr.)")
# ... Adicione os outros links da sidebar conforme o original ...

# Página principal do Streamlit
st.subheader('Verifica preenchimento - ALF - Aprova Digital')

ib_aprova = st.text_area("Cole todo o texto da página do processo do Aprova Digital", key="ib_aprova", height=200)
ib_cnpj = st.text_area("Cole todo o texto do CNPJ", key="ib_cnpj", height=200)

# Botão limpar
def clear_text():
    st.session_state["ib_aprova"] = ""
    st.session_state["ib_cnpj"] = ""
st.button("Limpar", on_click=clear_text)

# Funções auxiliares de extração segura
def extract_regex(pattern, text, default="Não encontrado"):
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else default

# Análise do processo
if ib_aprova and ib_cnpj:
    try:
        # ==========================================
        # 1. EXTRAÇÃO DE INFORMAÇÕES - APROVA DIGITAL
        # ==========================================
        inscricao_match = re.search(r'\d{3}\.\d{3}\.\d{2}\.\d{4}\.\d{4}\.\d{3}', ib_aprova)
        inscricao_aprova = inscricao_match.group(0) if inscricao_match else "Não encontrado"
        
        cnpj_aprova_match = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', ib_aprova)
        cnpj_aprova = cnpj_aprova_match.group(0) if cnpj_aprova_match else "Não encontrado"
        
        razao_social_aprova = extract_regex(r'Razao Social\s+(.*?)\s+Nome Fantasia', ib_aprova)
        
        bairro_aprova = extract_regex(r'Bairro\s+(.*?)\s+Logradouro', ib_aprova)
        logradouro_aprova = extract_regex(r'Logradouro\s+(.*?)\s+N[úu]mero Predial', ib_aprova)
        numero_aprova = extract_regex(r'N[úu]mero Predial\s+(.*?)\s+CEP', ib_aprova)
        complemento1_aprova = extract_regex(r'Complemento 1[^\n]*\s+(.*?)\s+Complemento 2', ib_aprova)
        complemento2_aprova = extract_regex(r'Complemento 2[^\n]*\s+(.*?)\s+Complemento 3', ib_aprova)
        complemento3_aprova = extract_regex(r'Complemento 3[^\n]*\s+(.*?)\s+Telefone Empresa', ib_aprova)

        cnaes_aprova = list(set(re.findall(r'\d{2}\.\d{2}-\d-\d{2}', ib_aprova)))

        # ==========================================
        # 2. EXTRAÇÃO DE INFORMAÇÕES - CNPJ
        # ==========================================
        numero_cnpj_match = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', ib_cnpj)
        numero_cnpj = numero_cnpj_match.group(0) if numero_cnpj_match else "Não encontrado"
        
        razao_social_cnpj = extract_regex(r'NOME EMPRESARIAL\s+(.*?)\s+T[ÍI]TULO DO ESTABELECIMENTO', ib_cnpj)
        
        logradouro_cnpj = extract_regex(r'LOGRADOURO\s+(.*?)\s+CEP', ib_cnpj)
        bairro_cnpj = extract_regex(r'BAIRRO/DISTRITO\s+(.*?)\s+N[ÚU]MERO', ib_cnpj)
        
        # O CNPJ coloca o número e o complemento juntos após os títulos
        numeropredial_cnpj = extract_regex(r'N[ÚU]MERO\s+COMPLEMENTO\s+(\d+)', ib_cnpj)
        complemento_cnpj = extract_regex(r'N[ÚU]MERO\s+COMPLEMENTO\s+\d+\s+(.*?)\s+MUNIC[ÍI]PIO', ib_cnpj)

        cnaes_cnpj = list(set(re.findall(r'\d{2}\.\d{2}-\d-\d{2}', ib_cnpj)))

        # ==========================================
        # 3. EXIBIÇÃO E VERIFICAÇÕES
        # ==========================================
        st.divider()
        st.subheader('Resumo do processo')
        st.markdown(f'**RAZÃO SOCIAL:** {razao_social_aprova} | **CNPJ:** {cnpj_aprova}')
        st.markdown(f'**ENDEREÇO CNPJ:** {logradouro_cnpj}, {numeropredial_cnpj}, {bairro_cnpj}, {complemento_cnpj}')
        st.markdown(f'**INSCRIÇÃO IMOBILIÁRIA:** {inscricao_aprova}')
        
        logradouro_google = "+".join(logradouro_aprova.split())
        maps_link = f'https://www.google.com/maps/place/{logradouro_google},+{numero_aprova},+Itaja%C3%AD+-+SC'
        st.markdown(f"[Ver no Google Maps]({maps_link})")
        
        # Verifica CNPJ
        st.subheader('Verificação do CNPJ')
        if numero_cnpj == cnpj_aprova:
            st.success('Ok! Número CNPJ inserido corretamente no Aprova.')
        else:
            st.error('VERIFICAR! Número CNPJ NÃO coincide.')

        # Verifica Razão Social
        st.subheader('Verificação da Razão Social')
        # Tratamos .upper() e removemos espaços em branco extras para comparar com segurança
        if re.sub(r'\s+', ' ', razao_social_cnpj.upper()) == re.sub(r'\s+', ' ', razao_social_aprova.upper()):
            st.success('Ok! A razão social inserida corretamente no Aprova.')
        else:
            st.error(f'VERIFICAR! A razão social NÃO coincide com o Aprova.\n\nCNPJ: {razao_social_cnpj}\nAprova: {razao_social_aprova}')
        
        # Verifica Endereço
        st.subheader('Verificação do endereço')
        st.markdown('**Verifique manualmente os endereços abaixo:**')
        st.info(f'**Endereço no APROVA:** {logradouro_aprova}, {numero_aprova}, {bairro_aprova} - {complemento1_aprova}, {complemento2_aprova}, {complemento3_aprova}')
        st.info(f'**Endereço no CNPJ:** {logradouro_cnpj}, {numeropredial_cnpj}, {bairro_cnpj} - {complemento_cnpj}')
            
        # Verifica CNAEs
        st.subheader('Verificação dos CNAES')
        if set(cnaes_cnpj) == set(cnaes_aprova):
            st.success('Ok! CNAES coincidem entre o Aprova Digital e CNPJ.')
            tabela_cnaes = pd.DataFrame({'CNAES (APROVA = CNPJ)': cnaes_aprova})
            st.dataframe(tabela_cnaes, use_container_width=True)
        else:
            st.error('VERIFICAR! CNAES não coincidem entre Aprova Digital e CNPJ.')
            col1, col2 = st.columns(2)
            with col1:
                st.write("**CNAES no APROVA**")
                st.dataframe(pd.DataFrame({"CNAE": cnaes_aprova}), use_container_width=True)
            with col2:
                st.write("**CNAES no CNPJ**")
                st.dataframe(pd.DataFrame({"CNAE": cnaes_cnpj}), use_container_width=True)
                
            cnaes_faltando_aprova = set(cnaes_cnpj) - set(cnaes_aprova)
            cnaes_sobrando_aprova = set(cnaes_aprova) - set(cnaes_cnpj)
            
            if cnaes_faltando_aprova:
                st.warning(f'**CNAES no CNPJ que NÃO foram inseridos no APROVA:** {", ".join(cnaes_faltando_aprova)}')
            if cnaes_sobrando_aprova:
                st.warning(f'**CNAES no APROVA que NÃO constam no CNPJ:** {", ".join(cnaes_sobrando_aprova)}')

    except Exception as e:
        st.error(f'Verifique o correto preenchimento de todos os campos. Erro interno: {e}')
