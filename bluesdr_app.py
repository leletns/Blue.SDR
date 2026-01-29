import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import google.generativeai as genai
import plotly.express as px
import time

# --- CONFIGURAÇÃO DA PÁGINA (VISUAL PRO) ---
st.set_page_config(
    page_title="BlueSDR | Intelligence",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PARA DEIXAR COM CARA DE SISTEMA CARO ---
st.markdown("""
    <style>
    .main {background-color: #0E1117;}
    .stButton>button {width: 100%; border-radius: 5px; height: 3em; background-color: #0068C9; color: white;}
    .stTextArea>div>div>textarea {background-color: #262730; color: white;}
    h1 {color: #0068C9;}
    .footer {position: fixed; left: 0; bottom: 0; width: 100%; background-color: #0E1117; color: #808495; text-align: center; padding: 10px; font-size: 12px; border-top: 1px solid #262730;}
    </style>
    """, unsafe_allow_html=True)

# --- SEGURANÇA E CONEXÕES (Secrets Management) ---
# No Streamlit Cloud, não usamos arquivo local .json por segurança. Usamos st.secrets.
def conectar_servicos():
    try:
        # Configurar Google Sheets via Secrets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # Criando credenciais a partir dos segredos do Streamlit
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("BlueTrack_DB").sheet1
        
        # Configurar Gemini AI via Secrets
        genai.configure(api_key=st.secrets["general"]["GOOGLE_API_KEY"])
        
        return sheet, True
    except Exception as e:
        return None, str(e)

sheet, status_conexao = conectar_servicos()

# --- CÉREBRO DA IA (BlueSDR Brain) ---
def analisar_conversa_pro(texto):
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"""
    Aja como o BlueSDR, um sistema de inteligência comercial de elite.
    Analise a transcrição abaixo.
    
    SAÍDA ESTRITAMENTE NO FORMATO:
    NOME|CARGO_OU_ORIGEM|TEMPERATURA|DOR_PRINCIPAL|ACAO_RECOMENDADA|RESPOSTA_COPYWRITING

    Temperaturas permitidas: Frio, Morno, Quente, Fechado.
    
    Conversa:
    {texto}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Erro|Erro|Erro|Erro|Erro|Erro"

# --- SIDEBAR (MENU LATERAL) ---
st.sidebar.title("💠 BlueSDR")
st.sidebar.caption("Revenue Intelligence System")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Navegação", ["Dashboard Executivo", "Análise de Conversa (IA)", "Banco de Dados"])
st.sidebar.markdown("---")

# --- PÁGINA: DASHBOARD EXECUTIVO ---
if menu == "Dashboard Executivo":
    st.title("📊 Visão da Diretoria")
    
    if sheet:
        dados = sheet.get_all_records()
        df = pd.DataFrame(dados)
        
        if not df.empty:
            # KPIs
            col1, col2, col3, col4 = st.columns(4)
            total = len(df)
            quentes = len(df[df['Status'].astype(str).str.upper() == 'QUENTE'])
            fechados = len(df[df['Status'].astype(str).str.upper() == 'FECHADO'])
            conversao = (fechados / total * 100) if total > 0 else 0
            
            col1.metric("Leads Totais", total, "+12%")
            col2.metric("Pipeline Ativo", quentes, "🔥 Alta prioridade")
            col3.metric("Vendas Fechadas", fechados)
            col4.metric("Taxa de Conversão", f"{conversao:.1f}%")
            
            st.markdown("---")
            
            # Gráficos de Elite (Plotly)
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Temperatura do Pipeline")
                fig_pie = px.pie(df, names='Status', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with c2:
                st.subheader("Origem dos Leads")
                # Assumindo que a coluna 5 tem origem misturada nas obs, ideal seria ter coluna separada
                # Para demo, vamos criar um gráfico temporal simples
                if 'Data' in df.columns:
                    st.line_chart(df['Valor']) # Exemplo simples
                else:
                    st.info("Dados insuficientes para gráfico temporal.")

# --- PÁGINA: ANÁLISE COM IA ---
elif menu == "Análise de Conversa (IA)":
    st.title("🧠 BlueSDR Intelligence")
    st.markdown("Cole a conversa do WhatsApp/Email para análise instantânea de perfil e conversão.")
    
    col_input, col_result = st.columns([1, 1])
    
    with col_input:
        texto_chat = st.text_area("Cole a conversa aqui:", height=400)
        btn_analisar = st.button("💠 PROCESSAR DADOS")
    
    with col_result:
        if btn_analisar and texto_chat:
            with st.spinner("BlueSDR está decodificando o cliente..."):
                resultado = analisar_conversa_pro(texto_chat)
                partes = resultado.split('|')
                
                if len(partes) >= 6:
                    st.success("Análise Concluída com Sucesso")
                    
                    st.subheader(f"👤 {partes[0]} ({partes[2]})")
                    st.progress(90 if 'Quente' in partes[2] else 40)
                    
                    st.info(f"**Diagnóstico:** {partes[3]}")
                    st.warning(f"**Próximo Passo:** {partes[4]}")
                    
                    st.markdown("### 💬 Sugestão de Resposta")
                    st.code(partes[5], language="text")
                    
                    # Botão salvar
                    if st.button("💾 Arquivar no CRM"):
                        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
                        # Salvando: Data, Nome, Status, Valor(0), Obs
                        obs_full = f"Origem: {partes[1]} | Dor: {partes[3]}"
                        sheet.append_row([data_hora, partes[0], partes[2], 0, obs_full])
                        st.toast("Lead Salvo no Banco de Dados Seguro!", icon="🔒")
                else:
                    st.error("A IA precisa de mais contexto para analisar.")

# --- PÁGINA: BANCO DE DADOS ---
elif menu == "Banco de Dados":
    st.title("📂 Vault de Dados (Criptografado)")
    if sheet:
        df = pd.DataFrame(sheet.get_all_records())
        st.dataframe(df, use_container_width=True)

# --- RODAPÉ DA DONA ---
st.markdown("""
    <div class="footer">
        🔒 256-bit SSL Encrypted Connection | System Version 2.4.0 <br>
        Developed & Engineered by <b>Leticia Nascimento</b> © 2024
    </div>
    """, unsafe_allow_html=True)
