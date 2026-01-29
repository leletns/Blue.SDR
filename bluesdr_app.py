import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime
import google.generativeai as genai
import plotly.express as px
import time

# --- 1. CONFIGURAÇÃO INICIAL ---
st.set_page_config(
    page_title="blue . system",
    page_icon=None, # Sem ícone
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. SISTEMA DE LOGIN (CLEAN) ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["auth"]["SENHA_SISTEMA"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    # TELA DE LOGIN (Minimalista)
    st.markdown("""
    <style>
    .stApp {background-color: #050505;}
    .login-title {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 300;
        font-size: 3rem;
        color: white;
        text-align: center;
        margin-bottom: 0px;
        letter-spacing: -1px;
    }
    .blue-dot { color: #4da6ff; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<div class='login-title'>blue <span class='blue-dot'>.</span></div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666; font-size: 0.8rem; letter-spacing: 2px; text-transform: uppercase;'>Restricted Environment</p>", unsafe_allow_html=True)
        
        st.text_input(
            "AUTHENTICATION KEY", 
            type="password", 
            on_change=password_entered, 
            key="password",
            label_visibility="collapsed",
            placeholder="Enter access key..."
        )
        
        if "password_correct" in st.session_state:
            st.markdown("<p style='text-align: center; color: #ff4b4b; font-size: 0.8rem;'>ACCESS DENIED</p>", unsafe_allow_html=True)

    return False

if not check_password():
    st.stop()

# ==============================================================================
# 🚀 ÁREA SEGURA
# ==============================================================================

# --- 3. CSS DE ELITE (CLEAN & THIN) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', 'Helvetica Neue', sans-serif;
    }
    
    /* Fundo */
    .stApp {
        background-color: #0a0a0a;
        color: #e0e0e0;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0f0f0f;
        border-right: 1px solid #1a1a1a;
    }
    
    /* Logo na Sidebar */
    .sidebar-logo {
        font-weight: 200; /* Thin */
        font-size: 2rem;
        color: white;
        letter-spacing: -1px;
    }
    
    /* Títulos */
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 300 !important; /* Thin */
        letter-spacing: -0.5px;
    }
    
    /* Inputs */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div, .stNumberInput>div>div>input {
        background-color: #141414;
        color: white;
        border: 1px solid #333;
        border-radius: 4px;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #4da6ff;
        box-shadow: none;
    }
    
    /* Botões */
    .stButton>button {
        width: 100%;
        border-radius: 4px;
        height: 3em;
        background-color: #4da6ff;
        color: black;
        border: none;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 0.8rem;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #ffffff;
    }
    
    /* Métricas */
    div[data-testid="metric-container"] {
        background-color: #141414;
        padding: 20px;
        border-radius: 0px;
        border-left: 1px solid #333;
    }
    label[data-testid="stMetricLabel"] { 
        color: #666; 
        font-size: 0.7rem; 
        text-transform: uppercase; 
        letter-spacing: 1px;
    }
    div[data-testid="stMetricValue"] { color: #fff; font-weight: 300; }

    /* Rodapé */
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #0a0a0a; color: #444;
        text-align: center; padding: 20px; font-size: 10px;
        text-transform: uppercase; letter-spacing: 2px;
        border-top: 1px solid #1a1a1a; z-index: 999;
    }
    </style>
    """, unsafe_allow_html=True)

# 🔴 CONFIGURAÇÃO DO DRIVE 🔴
DRIVE_FOLDER_ID = "19B6Kl5M4A1VFWs_9ctlrojm72o56Wg3E?usp=drive_link" 

# --- 4. CONEXÕES ---
@st.cache_resource
def conectar_servicos():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client_sheets = gspread.authorize(creds)
        sheet_leads = client_sheets.open("BlueTrack_DB").sheet1
        try:
            sheet_pagamentos = client_sheets.open("BlueTrack_DB").worksheet("Pagamentos")
        except:
            sheet_pagamentos = None
        drive_service = build('drive', 'v3', credentials=creds)
        genai.configure(api_key=st.secrets["general"]["GOOGLE_API_KEY"])
        return sheet_leads, sheet_pagamentos, drive_service
    except:
        return None, None, None

sheet_leads, sheet_pagamentos, drive_service = conectar_servicos()

# --- 5. FUNÇÕES ---
def upload_to_drive(file_obj, folder_id, drive_service):
    try:
        file_metadata = {'name': f"DOC_{datetime.now().strftime('%Y%m%d')}_{file_obj.name}", 'parents': [folder_id]}
        media = MediaIoBaseUpload(file_obj, mimetype=file_obj.type, resumable=True)
        file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        return file.get('webViewLink')
    except:
        return None

def analisar_conversa_pro(texto):
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"""
    SYSTEM: blue . intelligent analysis.
    Analyze the following high-ticket sales conversation.
    OUTPUT FORMAT (Pipe separated):
    NAME|ORIGIN|TEMPERATURE (Cold/Warm/Hot/Closed)|MAIN PAIN|NEXT STEP|SUGGESTED REPLY (No emojis, professional tone)
    Conversation: {texto}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Error|Error|Error|Error|Error|Error"

# --- 6. SIDEBAR ---
st.sidebar.markdown("<div class='sidebar-logo'>blue <span style='color:#4da6ff; font-weight:bold'>.</span></div>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='color:#666; font-size: 10px; letter-spacing: 2px; margin-top: -10px;'>INTELLIGENCE SYSTEM</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")
menu = st.sidebar.radio("MENU", ["DASHBOARD", "INTELLIGENCE AI", "PAYMENTS VAULT", "DATABASE"], label_visibility="collapsed")

# --- 7. PÁGINAS ---

if menu == "DASHBOARD":
    st.title("EXECUTIVE OVERVIEW")
    if sheet_leads:
        df = pd.DataFrame(sheet_leads.get_all_records())
        if not df.empty:
            c1, c2, c3, c4 = st.columns(4)
            total = len(df)
            quentes = len(df[df['Status'].astype(str).str.upper() == 'QUENTE'])
            fechados = len(df[df['Status'].astype(str).str.upper() == 'FECHADO'])
            conversao = (fechados/total*100) if total > 0 else 0
            
            c1.metric("TOTAL LEADS", total)
            c2.metric("ACTIVE PIPELINE", quentes)
            c3.metric("CLOSED DEALS", fechados)
            c4.metric("CONVERSION RATE", f"{conversao:.1f}%")
            
            st.markdown("<br>", unsafe_allow_html=True)
            col_graph1, col_graph2 = st.columns(2)
            with col_graph1:
                st.markdown("##### PIPELINE HEALTH")
                fig = px.pie(df, names='Status', hole=0.6, color_discrete_sequence=['#4da6ff', '#ffffff', '#333333', '#111111'])
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#666', showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("NO DATA AVAILABLE")

elif menu == "INTELLIGENCE AI":
    st.title("CONVERSATION DECODER")
    col_in, col_out = st.columns([1, 1])
    with col_in:
        txt = st.text_area("TRANSCRIPT INPUT", height=400, label_visibility="collapsed", placeholder="Paste conversation transcript here...")
        if st.button("PROCESS DATA"):
            with st.spinner("PROCESSING..."):
                res = analisar_conversa_pro(txt)
                st.session_state['analise_last'] = res.split('|')

    with col_out:
        if 'analise_last' in st.session_state and len(st.session_state['analise_last']) >= 6:
            dados = st.session_state['analise_last']
            st.markdown("##### ANALYSIS REPORT")
            st.markdown(f"**LEAD:** {dados[0]} <br> **STATUS:** {dados[2]}", unsafe_allow_html=True)
            st.markdown(f"<div style='background-color:#141414; padding:15px; border-left:2px solid #4da6ff; margin: 10px 0;'>{dados[3]}</div>", unsafe_allow_html=True)
            st.markdown(f"**STRATEGY:** {dados[4]}")
            st.text_area("SUGGESTED REPLY", value=dados[5], height=150)
            
            if st.button("ARCHIVE LEAD"):
                ts = datetime.now().strftime("%d/%m/%Y %H:%M")
                sheet_leads.append_row([ts, dados[0], dados[2], 0, f"Source: {dados[1]} | {dados[3]}"])
                st.toast("DATA ARCHIVED")

elif menu == "PAYMENTS VAULT":
    st.title("PAYMENTS & ASSETS")
    
    if not sheet_pagamentos:
        st.error("CONFIGURATION ERROR: MISSING 'Pagamentos' SHEET")
    else:
        with st.expander("REGISTER NEW TRANSACTION", expanded=True):
            with st.form("pgto"):
                c1, c2 = st.columns(2)
                nome = c1.text_input("CLIENT NAME")
                val = c1.number_input("VALUE", min_value=0.0)
                data = c2.date_input("DATE")
                hora = c2.time_input("TIME")
                file = st.file_uploader("PROOF OF PAYMENT", type=['png','jpg','pdf'])
                
                if st.form_submit_button("CONFIRM UPLOAD"):
                    if file and DRIVE_FOLDER_ID != "19B6Kl5M4A1VFWs_9ctlrojm72o56Wg3E?usp=drive_link":
                        link = upload_to_drive(file, DRIVE_FOLDER_ID, drive_service)
                        if link:
                            sheet_pagamentos.append_row([datetime.now().strftime("%d/%m/%Y"), nome, val, "SDR", f"{data} {hora}", "Obs", link])
                            st.success("TRANSACTION RECORDED")
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.warning("CHECK DRIVE ID")
        
        st.markdown("<br>", unsafe_allow_html=True)
        df_pg = pd.DataFrame(sheet_pagamentos.get_all_records())
        if not df_pg.empty:
            if 'Link Comprovante' in df_pg.columns:
                df_pg['ASSET'] = df_pg['Link Comprovante'].apply(lambda x: f'<a href="{x}" target="_blank" style="color:#4da6ff; text-decoration:none;">VIEW DOC</a>')
                st.write(df_pg.drop(columns=['Link Comprovante']).to_html(escape=False, index=False), unsafe_allow_html=True)

elif menu == "DATABASE":
    st.title("DATA VAULT")
    if sheet_leads:
        st.dataframe(pd.DataFrame(sheet_leads.get_all_records()), use_container_width=True)

# --- 8. RODAPÉ DE GRIFE ---
st.markdown("""
    <div class="footer">
        blue <span style='color:#4da6ff; font-weight:bold'>.</span> system &nbsp;|&nbsp; restricted access &nbsp;|&nbsp; engineered by leticia nascimento &copy; 2024
    </div>
    """, unsafe_allow_html=True)
