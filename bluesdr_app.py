import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import google.generativeai as genai
import plotly.express as px
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="BlueSDR | Intelligence",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PRO ---
st.markdown("""
    <style>
    .main {background-color: #0E1117;}
    .stButton>button {width: 100%; border-radius: 5px; height: 3em; background-color: #0068C9; color: white; font-weight: bold;}
    h1, h2, h3 {color: #0068C9;}
    .footer {position: fixed; left: 0; bottom: 0; width: 100%; background-color: #0E1117; color: #808495; text-align: center; padding: 10px; font-size: 12px; border-top: 1px solid #262730;}
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO DE AUTO-CURA (RESOLVE O ERRO DE ABAS FALTANDO) ---
def get_or_create_worksheet(sh, name):
    try:
        return sh.worksheet(name)
    except:
        # Se não achar a aba, CRIA ela automaticamente com cabeçalho
        ws = sh.add_worksheet(title=name, rows=1000, cols=20)
        if name == "Leads":
            ws.append_row(["Data", "Nome", "Origem", "Status", "Dor", "Sugestão IA"])
        elif name == "Pagamentos":
            ws.append_row(["Data", "Cliente", "Valor", "Status", "Obs"])
        return ws

# --- CONEXÃO BLINDADA ---
def conectar_sistema():
    try:
        # 1. Verifica se os segredos existem
        if "gcp_service_account" not in st.secrets:
            st.error("❌ ERRO CRÍTICO: Secrets não configurados no Streamlit Cloud.")
            st.stop()

        # 2. Prepara as credenciais (Corrige o erro de \n automaticamente)
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        # 3. Abre a planilha (TEM QUE SER O NOME EXATO)
        sh = client.open("BlueTrack_DB")

        # 4. Garante que as abas existem (Auto-Cura)
        sheet_leads = get_or_create_worksheet(sh, "Leads")
        sheet_pagamentos = get_or_create_worksheet(sh, "Pagamentos")

        # 5. Conecta IA
        if "general" in st.secrets:
            genai.configure(api_key=st.secrets["general"]["GOOGLE_API_KEY"])

        return sheet_leads, sheet_pagamentos

    except Exception as e:
        st.error(f"🚨 ERRO DE CONEXÃO: {e}")
        st.warning("👉 DICA: Verifique se você compartilhou a planilha 'BlueTrack_DB' com o email do robô (client_email) como EDITOR.")
        st.stop() # Para tudo se der erro

# Carrega conexões
sheet_leads, sheet_pagamentos = conectar_sistema()

# --- CÉREBRO DA IA ---
def analisar_conversa(texto):
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"""
    Aja como o BlueSDR, um sistema de inteligência comercial de elite.
    Analise a transcrição abaixo.
    
    SAÍDA ESTRITAMENTE NO FORMATO (separado por | ):
    NOME|ORIGEM|TEMPERATURA|DOR_PRINCIPAL|ACAO_RECOMENDADA|RESPOSTA_COPYWRITING

    Temperaturas: Frio, Morno, Quente, Fechado.
    
    Conversa:
    {texto}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Erro|Erro|Erro|Erro|Erro|Erro na IA"

# --- INTERFACE ---
st.sidebar.title("💠 BlueSDR")
st.sidebar.caption("System v3.0 | Auto-Healing")
menu = st.sidebar.radio("Menu", ["Dashboard", "Análise IA", "Banco de Dados"])

# --- DASHBOARD ---
if menu == "Dashboard":
    st.title("📊 Visão Executiva")
    
    # Puxa dados reais
    dados = sheet_leads.get_all_records()
    df = pd.DataFrame(dados)

    col1, col2, col3 = st.columns(3)
    
    if not df.empty:
        total = len(df)
        quentes = len(df[df['Status'].astype(str).str.contains('Quente', case=False, na=False)])
        
        col1.metric("Total de Leads", total)
        col2.metric("🔥 Leads Quentes", quentes)
        col3.metric("Meta Mensal", "R$ 50.000", "Em progresso")
        
        st.markdown("---")
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Temperatura")
            fig = px.pie(df, names='Status', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.subheader("Últimos Registros")
            st.dataframe(df.tail(5)[['Data', 'Nome', 'Status']], use_container_width=True, hide_index=True)
    else:
        st.info("Aguardando primeiros dados para gerar gráficos.")

# --- ANÁLISE IA ---
elif menu == "Análise IA":
    st.title("🧠 Inteligência Comercial")
    texto = st.text_area("Cole a conversa aqui:", height=200)
    
    if st.button("💠 ANALISAR AGORA"):
        if texto:
            with st.spinner("Processando neuro-linguística..."):
                res = analisar_conversa(texto)
                partes = res.split('|')
                
                if len(partes) >= 6:
                    st.success("Análise Completa!")
                    st.session_state['dados_temp'] = partes # Salva na memória temporária
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.subheader(f"👤 {partes[0]}")
                        st.info(f"**Origem:** {partes[1]}")
                        st.warning(f"**Status:** {partes[2]}")
                        st.error(f"**Dor:** {partes[3]}")
                    with c2:
                        st.subheader("💬 Sugestão de Resposta")
                        st.code(partes[5], language="text")
                else:
                    st.error("A IA não conseguiu entender. Tente colar mais contexto.")

    # Botão de Salvar aparece se tiver análise feita
    if 'dados_temp' in st.session_state:
        st.markdown("---")
        if st.button("💾 SALVAR NO BANCO DE DADOS"):
            p = st.session_state['dados_temp']
            data = datetime.now().strftime("%d/%m/%Y %H:%M")
            # Salva na ordem do cabeçalho: Data, Nome, Origem, Status, Dor, Sugestão
            sheet_leads.append_row([data, p[0], p[1], p[2], p[3], p[5]])
            st.toast("Salvo com sucesso!", icon="✅")
            del st.session_state['dados_temp'] # Limpa memória
            time.sleep(1)
            st.rerun()

# --- BANCO DE DADOS ---
elif menu == "Banco de Dados":
    st.title("📂 Vault de Dados")
    tab1, tab2 = st.tabs(["Leads", "Pagamentos"])
    
    with tab1:
        st.dataframe(pd.DataFrame(sheet_leads.get_all_records()), use_container_width=True)
    with tab2:
        st.dataframe(pd.DataFrame(sheet_pagamentos.get_all_records()), use_container_width=True)

# --- RODAPÉ ---
st.markdown("""
    <div class="footer">
        🔒 BlueSDR Enterprise System <br>
        Developed by <b>Leticia Nascimento</b> © 2024
    </div>
    """, unsafe_allow_html=True)
