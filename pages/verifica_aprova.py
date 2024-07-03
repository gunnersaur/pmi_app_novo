import pandas as pd
import numpy as np
import streamlit as st
import pydeck as pdk
import re
import os
from itertools import chain

#Configurações do Streamlit

st.set_page_config(page_title='Verifica preenchimento - ALF - Aprova Digital', 
                   layout="centered", 
                   initial_sidebar_state='expanded',
                   page_icon=('images/favicon.png'), 
                   menu_items=None
                   )

logo_image = ('images/logo.png')

#Sidebar
st.sidebar.image(logo_image, width=150)
st.sidebar.divider()
st.sidebar.page_link("app.py", label="01_Consulta de Viabilidade (inscr.)")
st.sidebar.page_link("pages/cv_zona.py", label="__Consulta de Viabilidade (zona)")
st.sidebar.page_link("pages/verifica_aprova.py", label="02_Verifica processo ALF")
st.sidebar.page_link("pages/links.py", label="03_Links úteis")
st.sidebar.page_link("pages/documentacao-complementar-ALF.py", label="04_Doc. complementar ALF")
st.sidebar.page_link("pages/estudo-de-impacto-de-vizinhanca.py", label="05_EIV")


#Página principal do Streamlit - fixa
st.subheader('Verifica preenchimento - ALF - Aprova Digital')

ib_aprova= st.text_input(
    "Cole todo o texto da página do processo do Aprova Digital",
    key="ib_aprova"
    )

ib_cnpj = st.text_input(
    "Cole todo o texto do CNPJ",
    key="ib_cnpj"
    )

#Botão limpar

def clear_text():
    st.session_state["ib_aprova"] = ""
    st.session_state["ib_cnpj"] = ""
st.button("Limpar", on_click=clear_text)


#Análise do processo
try:
    if ib_aprova and ib_cnpj != "":

        #Extrai informações do Aprova Digital
        texto_aprova_split = re.sub(' +', ' ',ib_aprova).split(' ')
        index_aprova1=texto_aprova_split.index('Selecione')
        index_aprova2=texto_aprova_split.index('Horário')
        inscricao_aprova = re.findall(r'\d\d\d.\d\d\d.\d\d.\d\d\d\d.\d\d\d\d.\d\d\d', ib_aprova)
        inscricao_aprova = inscricao_aprova[0]
        trecho_aprova = " ".join(texto_aprova_split[index_aprova1:index_aprova2])
        itens_analise=['Razao','Horário']
        index_aprova3=texto_aprova_split.index('Razao')
        index_aprova4=texto_aprova_split.index('Horário')
        trecho_aprova_split2 = texto_aprova_split[index_aprova3:index_aprova4]
        itens_analise=['Social','Nome']
        index_aprova5=trecho_aprova_split2.index('Social')+1
        index_aprova6=trecho_aprova_split2.index('Nome')
        razao_social_aprova = " ".join(trecho_aprova_split2[index_aprova5:index_aprova6])
        itens_analise=['REGIN','Razao']
        index_aprova7=texto_aprova_split.index('REGIN')
        index_aprova8=texto_aprova_split.index('Razao')
        trecho_aprova_split3 = texto_aprova_split[index_aprova7:index_aprova8]
        itens_analise=['Bairro','Logradouro']
        index_aprova9=trecho_aprova_split3.index('Bairro')+1
        index_aprova10=trecho_aprova_split3.index('Logradouro')
        index_aprova11=trecho_aprova_split3.index('Logradouro')+1
        index_aprova12=trecho_aprova_split3.index('Número')
        index_aprova13=trecho_aprova_split3.index('Predial')+1
        index_aprova14=trecho_aprova_split3.index('CEP')
        bairro_aprova = " ".join(trecho_aprova_split3[index_aprova9:index_aprova10])
        logradouro_aprova = " ".join(trecho_aprova_split3[index_aprova11:index_aprova12])
        numero_aprova = " ".join(trecho_aprova_split3[index_aprova13:index_aprova14])
        index_aprova17=trecho_aprova_split3.index('Sala)')
        index_aprova18=trecho_aprova_split3.index('(Sala)')
        index_aprova19=trecho_aprova_split3.index('(Box)')
        index_aprova20=trecho_aprova_split3.index('Telefone')
        complemento1_aprova = " ".join(trecho_aprova_split3[index_aprova17+1:index_aprova18-2])
        complemento2_aprova = " ".join(trecho_aprova_split3[index_aprova18+1:index_aprova19-2])
        complemento3_aprova = " ".join(trecho_aprova_split3[index_aprova19+1:index_aprova20])
        cnaes_aprova = re.findall(r'\d\d.\d\d-\d-\d\d', ib_aprova)
        cnaes_aprova=list(set(cnaes_aprova))
        itens_analise=['Razao','Horário']
        index_aprova15=texto_aprova_split.index('Razao')
        index_aprova16=texto_aprova_split.index('Horário')
        trecho_aprova_split4 = texto_aprova_split[index_aprova15:index_aprova16]
        trecho_aprova_cnpj = " ".join(trecho_aprova_split4)
        cnpj_aprova = re.findall(r'\d\d.\d\d\d.\d\d\d/\d\d\d\d-\d\d', trecho_aprova_cnpj)

        #Extrai informações do CNPJ
        cnaes_cnpj = re.findall(r'\d\d.\d\d-\d-\d\d', ib_cnpj)
        cnae_principal_cnpj=cnaes_cnpj[0]
        numero_cnpj = re.findall(r'\d\d.\d\d\d.\d\d\d/\d\d\d\d-\d\d', ib_cnpj)
        texto_cnpj_split = re.sub(' +', ' ',ib_cnpj).split(' ')
        itens_analise=['EMPRESARIAL','TÍTULO', 'LOGRADOURO','NÚMERO']
        index_cnpj1=texto_cnpj_split.index('EMPRESARIAL')+1
        index_cnpj2=texto_cnpj_split.index('TÍTULO')
        razao_social_cnpj = " ".join(texto_cnpj_split[index_cnpj1:index_cnpj2])
        index_cnpj3=texto_cnpj_split.index('NATUREZA')+1
        index_cnpj4=texto_cnpj_split.index('ESPECIAL')
        texto_cnpj_split2 = texto_cnpj_split[index_cnpj3:index_cnpj4] #função que separa o primeiro split
        index_cnpj5=texto_cnpj_split2.index('LOGRADOURO')+1
        index_cnpj6=texto_cnpj_split2.index('NÚMERO')
        logradouro_cnpj = " ".join(texto_cnpj_split2[index_cnpj5:index_cnpj6])
        index_cnpj7=texto_cnpj_split2.index('NÚMERO')+1
        index_cnpj8=texto_cnpj_split2.index('COMPLEMENTO')
        numeropredial_cnpj = " ".join(texto_cnpj_split2[index_cnpj7:index_cnpj8])
        index_cnpj9=texto_cnpj_split2.index('COMPLEMENTO')+1
        index_cnpj10=texto_cnpj_split2.index('CEP')
        complemento_cnpj = " ".join(texto_cnpj_split2[index_cnpj9:index_cnpj10])
        index_cnpj11=texto_cnpj_split2.index('BAIRRO/DISTRITO')+1
        index_cnpj12=texto_cnpj_split2.index('MUNICÍPIO')
        bairro_cnpj = " ".join(texto_cnpj_split2[index_cnpj11:index_cnpj12])

        #Printa as verificações
        #Resumo do processo
        st.divider()
        st.subheader('Resumo do processo')
        st.markdown('RAZÃO SOCIAL: '+razao_social_aprova+', CNPJ: '+cnpj_aprova[0])
        st.markdown(logradouro_cnpj+', '+bairro_cnpj+', '+numeropredial_cnpj+', '+complemento_cnpj)
        st.markdown('INSCRIÇÃO IMOBILIÁRIA: '+str(inscricao_aprova[0:15]))
        endereço_split = re.sub(' +', ' ',logradouro_aprova).split(' ')
        logradouro_google = "+".join(endereço_split)
        st.markdown(str('https://www.google.com/maps/place/')+logradouro_google+str(',+')+str(numero_aprova)+str('+,+Itaja%C3%AD+-+SC'))
        
        #Verifica o cnpj
        st.subheader('Verificação do CNPJ')
        if (numero_cnpj[0] == cnpj_aprova[0]):
            st.markdown(''':green[Ok! Número CNPJ inserido corretamente no Aprova.]''')
        else:
            st.markdown(''':red[VERIFICAR! Número CNPJ NÃO coincide]''')

        #Verifica razão social
        st.subheader('Verificação da Razão Social')
        if (razao_social_cnpj == razao_social_aprova.upper()):
            st.markdown(''':green[Ok! A razão social inserida corretamento no Aprova.]''')
        else:
            st.markdown(''':red[VERIFICAR! A razão social NÃO coincide com o Aprova.]''')
        
        #Verifica o endereço
        st.subheader('Verificação do endereço')
        st.markdown('** Verifique manualmente os endereços abaixo:')
        st.markdown('Endereço no APROVA: '+logradouro_aprova+', '+bairro_aprova+', '+numero_aprova+', '+complemento1_aprova+', '+complemento2_aprova+', '+complemento3_aprova)
        st.markdown('Endereço no CNPJ: '+logradouro_cnpj+', '+bairro_cnpj+', '+numeropredial_cnpj+', '+complemento_cnpj)
            
        #Verifica os cnaes
        st.subheader('Verificação dos CNAES')
        if (set(cnaes_cnpj) == set(cnaes_aprova)):
             st.markdown(''':green[Ok! CNAES coincidem entre o Aprova Digital e CNPJ.]''')
        else:
            st.markdown(''':red[VERIFICAR! CNAES não coincidem entre Aprova Digital e CNPJ.]''')
        
        if (set(cnaes_cnpj) == set(cnaes_aprova)):
            st.text('TABELA DE CNAES')
            tabela_cnaes = pd.DataFrame({ 'CNAES APROVA': cnaes_aprova, 'CNAES CNPJ': cnaes_cnpj })
            st.dataframe(tabela_cnaes)
        else:
            st.text('   ** CNAE principal: '+cnaes_cnpj[0])
            st.text('   ** CNAES não inseridos no APROVA: '+str(set(cnaes_cnpj)-set(cnaes_aprova)))
            verif_cnaes = set(cnaes_aprova)-set(cnaes_cnpj)
            if verif_cnaes == set():
                verif_cnaes = ""
                st.text('   ** CNAES inseridos no APROVA que não estão no CNPJ: '+str(verif_cnaes))
                st.text('CNAES do APROVA')
                st.dataframe(cnaes_aprova)
                st.text('CNAES do CNPJ')
                st.dataframe(cnaes_cnpj)

except:
    st.markdown(''':red[Verifique o correto preenchimento de todos os campos.]''')

