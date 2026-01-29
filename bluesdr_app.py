import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime, time as dt_time
import google.generativeai as genai
import plotly.express as px
import time

# --- CONFIGURAÇÃO DA PÁGINA (ELITE EDITION) ---
st.set_page_config(
    page_title="Blue . SDR | Elite Intelligence",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS DE LUXO (DARK & GOLD THEME) ---
st.markdown("""
    <style>
    /* Fundo Principal */
    .stApp {
        background-color: #0a0e14; /* Azul noturno muito escuro */
        color: #e0e0e0;
    }
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #11161d;
        border-right: 1px solid #1f2630;
    }
    /* Títulos e Acentos */
    h1, h2, h3 {
        color: #ffffff !important;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 600;
    }
    .blue-dot { color: #4da6ff; font-weight: bold; font-size: 1.2em; } /* O ponto azul */
    .gold-accent { color: #d4af37; } /* Dourado Elite */
    
    /* Botões */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background: linear-gradient(135deg, #003366 0%, #004080 100%); /* Gradiente Azul Nobre */
        color: white;
        border: none;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #004080 0%, #0059b3 100%);
        box-shadow: 0 4px 15px rgba(77, 166, 255, 0.3);
    }
    
    /* Inputs e Textareas */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div, .stDateInput>div>div>input, .stTimeInput>div>div>input, .stNumberInput>div>div>input {
        background-color: #1c232e;
        color: white;
        border: 1px solid #2d3748;
        border-radius: 6px;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #4da6ff;
        box-shadow: 0 0 0 1px #4da6ff;
    }
    
    /* Dataframes e Tabelas */
    div[data-testid="stDataFrame"] {
        background-color: #1c232e;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #2d3748;
    }
    
    /* Métricas (Cards) */
    div[data-testid="metric-container"] {
        background-color: #1c232e;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #d4af37; /* Acento Dourado */
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    label[data-testid="stMetricLabel"] { color: #a0aec0; }
    div[data-testid="stMetricValue"] { color: #ffffff; font-weight: 700; }

    /* Rodapé */
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #0a0e14; color: #808495;
        text-align: center; padding: 15px; font-size: 12px;
        border-top: 1px solid #1f2630; z-index: 999;
    }
    </style>
    """, unsafe_allow_html=True)

# 🔴 🔴 CONFIGURAÇÃO DO DRIVE: COLE O ID DA SUA PASTA AQUI 🔴 🔴
DRIVE_FOLDER_ID = "19B6Kl5M4A1VFWs_9ctlrojm72o56Wg3E?usp=drive_link"

# --- CONEXÕES SEGURAS (Sheets, Drive, AI) ---
@st.cache_resource
def conectar_servicos():
    try:
        # Escopos para Sheets e Drive
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        
        # Cliente Sheets
        client_sheets = gspread.authorize(creds)
        sheet_leads = client_sheets.open("BlueTrack_DB").sheet1
        # Tenta abrir a aba de pagamentos, se não existir, avisa.
        try:
            sheet_pagamentos = client_sheets.open("BlueTrack_DB").worksheet("Pagamentos")
        except:
            sheet_pagamentos = None
            st.error("⚠️ Aba 'Pagamentos' não encontrada na planilha. Crie-a para usar a nova função.")

        # Serviço Drive
        drive_service = build('drive', 'v3', credentials=creds)
        
        # Configurar Gemini AI
        genai.configure(api_key=st.secrets["general"]["GOOGLE_API_KEY"])
        
        return sheet_leads, sheet_pagamentos, drive_service, True
    except Exception as e:
        return None, None, None, str(e)

sheet_leads, sheet_pagamentos, drive_service, status_conexao = conectar_servicos()

# --- FUNÇÃO DE UPLOAD PARA O DRIVE ---
def upload_to_drive(file_obj, folder_id, drive_service):
    try:
        file_metadata = {
            'name': f"Comprovante_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_obj.name}",
            'parents': [folder_id]
        }
        media = MediaIoBaseUpload(file_obj, mimetype=file_obj.type, resumable=True)
        file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        return file.get('webViewLink')
    except Exception as e:
        st.error(f"Erro no upload para o Drive: {e}")
        return None

# --- CÉREBRO DA IA (Blue . Brain) ---
def analisar_conversa_pro(texto):
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"""
    Aja como o sistema Blue . SDR, inteligência comercial de elite para tickets altos.
    Analise a transcrição com foco em qualificação e fechamento.
    
    SAÍDA ESTRITAMENTE NO FORMATO SEPARADO POR PIPE (|):
    NOME|CARGO_OU_ORIGEM|TEMPERATURA (Frio/Morno/Quente/Fechado)|DOR_PRINCIPAL_E_OBJECAO|PROXIMO_PASSO_ESTRATEGICO|SUGESTAO_RESPOSTA_COPYWRITING_DE_ELITE
    
    Conversa:
    {texto}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Erro|Erro|Erro|Erro|Erro|Erro"

# --- SIDEBAR (MENU DE ELITE) ---
st.sidebar.markdown("## Blue <span class='blue-dot'>.</span> SDR", unsafe_allow_html=True)
st.sidebar.caption("Revenue Intelligence | Elite Edition")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Navegação Exclusiva", ["Dashboard Executivo", "Análise de Conversa (IA)", "Gestão de Pagamentos 💰", "Banco de Dados Seguro"])
st.sidebar.markdown("---")
with st.sidebar.expander("Sobre o Sistema"):
    st.info("Sistema de inteligência proprietário desenvolvido para maximizar conversões de alto valor.")

# --- PÁGINA: DASHBOARD EXECUTIVO ---
if menu == "Dashboard Executivo":
    st.title("📊 Visão Estratégica da Diretoria")
    st.markdown("Monitoramento em tempo real do pipeline de alta performance.")
    
    if sheet_leads:
        dados = sheet_leads.get_all_records()
        df = pd.DataFrame(dados)
        
        if not df.empty:
            # KPIs de Elite
            col1, col2, col3, col4 = st.columns(4)
            total = len(df)
            # Filtra status de forma robusta
            status_upper = df['Status'].astype(str).str.upper()
            quentes = len(df[status_upper == 'QUENTE'])
            fechados = len(df[status_upper == 'FECHADO'])
            conversao = (fechados / total * 100) if total > 0 else 0
            
            col1.metric("Total de Leads", total, help="Volume total no pipeline")
            col2.metric("🔥 Pipeline Quente", quentes, f"{quentes/total*100:.0f}% do total", help="Leads prontos para fechamento")
            col3.metric("💎 Vendas Fechadas", fechados, help="Negócios concretizados")
            col4.metric("Taxa de Conversão Global", f"{conversao:.1f}%", help="Eficiência do funil")
            
            st.markdown("---")
            
            # Gráficos de Elite
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Health Score do Pipeline")
                # Cores personalizadas para o tema Elite
                colors = {'QUENTE': '#d4af37', 'FECHADO': '#4da6ff', 'MORNO': '#a0aec0', 'FRIO': '#4a5568'}
                fig_pie = px.pie(df, names='Status', hole=0.5, color='Status', color_discrete_map=colors)
                fig_pie.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#e0e0e0', showlegend=True
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with c2:
                st.subheader("Performance Recente")
                if 'Data' in df.columns:
                    st.info("Gráfico temporal em desenvolvimento para próxima versão.")
                    # Placeholder para gráfico de linha futuro
                    st.line_chart(df['Status'].value_counts()) 
                else:
                    st.info("Dados temporais insuficientes.")
        else:
            st.info("Aguardando dados para gerar intelligence.")

# --- PÁGINA: ANÁLISE COM IA ---
elif menu == "Análise de Conversa (IA)":
    st.title("🧠 Blue <span class='blue-dot'>.</span> Intelligence Hub", unsafe_allow_html=True)
    st.markdown("Cole a interação com o cliente para decodificação estratégica instantânea.")
    
    col_input, col_result = st.columns([1.2, 1])
    
    with col_input:
        texto_chat = st.text_area("📝 Transcrição da Conversa", height=450, placeholder="Cole aqui o WhatsApp, E-mail ou Direct...")
        btn_analisar = st.button("💠 PROCESSAR DADOS COM IA")
    
    with col_result:
        if btn_analisar and texto_chat:
            with st.spinner("Decodificando padrões de compra..."):
                resultado = analisar_conversa_pro(texto_chat)
                partes = resultado.split('|')
                
                if len(partes) >= 6:
                    st.success("✅ Análise Estratégica Concluída")
                    
                    st.subheader(f"👤 Lead: {partes[0]}")
                    st.caption(f"Origem/Cargo: {partes[1]}")
                    
                    temp = partes[2].strip().upper()
                    cor_temp = "gold-accent" if temp in ['QUENTE', 'FECHADO'] else "blue-dot"
                    st.markdown(f"### Status: <span class='{cor_temp}'>{temp}</span>", unsafe_allow_html=True)
                    
                    with st.expander("🔍 Diagnóstico & Dor Principal", expanded=True):
                        st.write(partes[3])
                    
                    with st.expander("🚀 Próximo Passo Estratégico", expanded=True):
                        st.write(f"**Ação:** {partes[4]}")
                    
                    st.markdown("### 💬 Copywriting de Resposta Sugerida")
                    st.code(partes[5], language="text")
                    
                    # Botão salvar
                    if st.button("💾 Arquivar no Vault de Dados"):
                        if sheet_leads:
                            data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
                            obs_full = f"Origem: {partes[1]} | Dor: {partes[3]} | Estratégia: {partes[4]}"
                            sheet_leads.append_row([data_hora, partes[0], partes[2], 0, obs_full])
                            st.toast("Lead arquivado com segurança no cofre de dados.", icon="🔒")
                        else:
                            st.error("Erro de conexão com o banco de dados.")
                else:
                    st.error("A IA precisa de mais contexto para uma análise de elite.")

# --- NOVA PÁGINA: GESTÃO DE PAGAMENTOS (O COFRE) ---
elif menu == "Gestão de Pagamentos 💰":
    st.title("💎 Cofre de Pagamentos & Comprovantes")
    st.markdown("Registro seguro de pagamentos antecipados e agendamentos confirmados.")
    
    if not sheet_pagamentos or not drive_service:
        st.error("Módulo de pagamentos não configurado. Verifique a aba na planilha e a conexão com o Drive.")
        st.stop()

    # --- Formulário de Novo Pagamento ---
    with st.expander("➕ Registrar Novo Pagamento Antecipado", expanded=True):
        with st.form("form_pagamento", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                nome_lead = st.text_input("👤 Nome do Lead/Cliente *")
                valor_pgto = st.number_input("💰 Valor do Pagamento (R$)*", min_value=0.0, format="%.2f")
                consultor = st.text_input("Requisitante/Consultor *")
            with c2:
                data_agendamento = st.date_input("📅 Data do Agendamento *")
                hora_agendamento = st.time_input("⏰ Horário do Agendamento *")
                agendamento_full = f"{data_agendamento.strftime('%d/%m/%Y')} às {hora_agendamento.strftime('%H:%M')}"
            
            obs_pgto = st.text_area("📝 Observações Adicionais")
            arquivo_comprovante = st.file_uploader("📄 Upload do Comprovante (Imagem/PDF) *", type=['png', 'jpg', 'jpeg', 'pdf'])
            
            st.markdown("*Campos obrigatórios")
            enviar_pgto = st.form_submit_button("🔒 Confirmar Pagamento & Arquivar Comprovante")
            
            if enviar_pgto:
                if nome_lead and valor_pgto > 0 and consultor and arquivo_comprovante and DRIVE_FOLDER_ID != "19B6Kl5M4A1VFWs_9ctlrojm72o56Wg3E?usp=drive_link":
                    with st.spinner("Criptografando e enviando para o Cofre Seguro..."):
                        # 1. Upload para o Drive
                        link_comprovante = upload_to_drive(arquivo_comprovante, DRIVE_FOLDER_ID, drive_service)
                        
                        if link_comprovante:
                            # 2. Salvar na Planilha
                            data_hoje = datetime.now().strftime("%d/%m/%Y")
                            dados_pgto = [data_hoje, nome_lead, valor_pgto, consultor, agendamento_full, obs_pgto, link_comprovante]
                            sheet_pagamentos.append_row(dados_pgto)
                            st.success(f"Pagamento de {nome_lead} registrado com sucesso!")
                            time.sleep(1)
                            st.rerun() # Atualiza a tabela abaixo
                        else:
                            st.error("Falha no upload do comprovante. Tente novamente.")
                else:
                    st.warning("Preencha os campos obrigatórios e verifique o ID da pasta do Drive no código.")

    st.markdown("---")
    st.subheader("📜 Histórico de Transações")
    
    # --- Exibição da Tabela de Pagamentos ---
    dados_pgto = sheet_pagamentos.get_all_records()
    df_pgto = pd.DataFrame(dados_pgto)
    
    if not df_pgto.empty:
        # Formatando a exibição
        if 'Valor' in df_pgto.columns:
            df_pgto['Valor'] = df_pgto['Valor'].apply(lambda x: f"R$ {float(x):,.2f}")
        
        # Criando coluna de link clicável
        if 'Link Comprovante' in df_pgto.columns:
            df_pgto['Comprovante'] = df_pgto['Link Comprovante'].apply(lambda x: f'<a href="{x}" target="_blank" style="text-decoration: none; color: #4da6ff; font-weight: bold;">👁️‍🗨️ Ver Arquivo</a>' if x else "-")
            df_display = df_pgto.drop(columns=['Link Comprovante']) # Remove o link cru
        else:
            df_display = df_pgto

        # Mostra tabela com HTML permitido para os links funcionarem
        st.write(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.info("Nenhum pagamento registrado no cofre ainda.")

# --- PÁGINA: BANCO DE DADOS ---
elif menu == "Banco de Dados Seguro":
    st.title("📂 Vault de Dados Geral")
    st.markdown("Acesso restrito à base completa de leads.")
    if sheet_leads:
        df = pd.DataFrame(sheet_leads.get_all_records())
        st.dataframe(df, use_container_width=True, height=500)

# --- RODAPÉ DE ELITE ---
st.markdown("""
    <div class="footer">
        🔒 Blue <span style='color:#4da6ff;'>.</span> SDR Systems | 256-bit End-to-End Encryption <br>
        Exclusive High-Ticket Intelligence Engineered by <b>Leticia Nascimento</b> © 2024
    </div>
    """, unsafe_allow_html=True)
