import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import google.generativeai as genai
import plotly.express as px
import plotly.graph_objects as go
import time

# --- 1. CONFIGURAÇÃO DE ALTO NÍVEL ---
st.set_page_config(
    page_title="BlueSDR | Enterprise Intelligence",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS CUSTOMIZADO (VISUAL DE R$ 100K) ---
st.markdown("""
    <style>
    /* Fundo e Fontes */
    .stApp {background-color: #0E1117;}
    h1, h2, h3 {color: #4da6ff; font-family: 'Helvetica Neue', sans-serif;}
    
    /* Métricas Estilizadas */
    div[data-testid="stMetric"] {
        background-color: #1f2937;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #4da6ff;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
    }
    
    /* Botões Premium */
    .stButton>button {
        background: linear-gradient(90deg, #0066cc 0%, #0099ff 100%);
        color: white;
        border: none;
        border-radius: 8px;
        height: 50px;
        font-weight: bold;
        letter-spacing: 1px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(0, 153, 255, 0.6);
    }
    
    /* Footer */
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #0E1117; color: #6b7280;
        text-align: center; padding: 10px; font-size: 11px;
        border-top: 1px solid #1f2937; z-index: 999;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONEXÃO BLINDADA (COM AUTO-CURA) ---
@st.cache_resource(show_spinner="Conectando ao Vault Seguro...")
def conectar_sistema_elite():
    try:
        # Verifica Segredos
        if "gcp_service_account" not in st.secrets:
            return None, None, "Erro: Secrets não configurados."

        # Prepara Credenciais
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        sh = client.open("BlueTrack_DB")

        # Função interna de Auto-Cura de Abas
        def garantir_aba(nome, colunas):
            try:
                return sh.worksheet(nome)
            except:
                ws = sh.add_worksheet(title=nome, rows=1000, cols=20)
                ws.append_row(colunas)
                return ws

        sheet_leads = garantir_aba("Leads", ["Data", "Nome", "Origem", "Status", "Dor", "Valor Potencial", "Obs"])
        sheet_pgt = garantir_aba("Pagamentos", ["Data", "Cliente", "Serviço", "Valor", "Status", "Forma Pagamento"])
        
        # Conecta IA
        if "general" in st.secrets:
            genai.configure(api_key=st.secrets["general"]["GOOGLE_API_KEY"])
            
        return sheet_leads, sheet_pgt, "OK"

    except Exception as e:
        return None, None, str(e)

# Inicializa Conexão
sheet_leads, sheet_pagamentos, status_msg = conectar_sistema_elite()

if status_msg != "OK":
    st.error(f"🚨 FALHA DE SISTEMA: {status_msg}")
    st.info("Verifique se o email do robô é EDITOR na planilha.")
    st.stop()

# --- 4. FUNÇÕES DE INTELIGÊNCIA ---
def analisar_conversa_pro(texto):
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"""
    Aja como o 'BlueSDR AI', um especialista em vendas consultivas de alto ticket.
    Analise esta conversa.
    
    SAÍDA ESTRITA (Separada por |):
    NOME DO LEAD|ORIGEM (Insta/Google/Indicação)|TEMPERATURA (Frio/Morno/Quente/Venda)|DOR PRINCIPAL (Resumo)|VALOR ESTIMADO (Numérico ou 0)|SUGESTÃO DE RESPOSTA (Persuasiva)

    Conversa:
    {texto}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Erro|Erro|Erro|Erro|0|Erro de IA"

# --- 5. INTERFACE DO SISTEMA ---

# Sidebar de Navegação
with st.sidebar:
    st.title("💠 BlueSDR")
    st.caption("Intelligence System v4.0")
    st.markdown("---")
    menu = st.radio("Navegação", ["📊 Dashboard Executivo", "🧠 Inteligência Artificial", "💰 Gestão Financeira", "📂 Database"])
    st.markdown("---")
    st.info(f"Status Conexão: 🟢 Segura (TLS)")

# >>> PÁGINA 1: DASHBOARD EXECUTIVO <<<
if menu == "📊 Dashboard Executivo":
    st.title("Visão Geral de Receita")
    st.markdown("Monitoramento em tempo real do pipeline de vendas.")
    
    # Processamento de Dados
    dados = sheet_leads.get_all_records()
    df = pd.DataFrame(dados)
    
    # Tratamento de erro se vazio
    if df.empty:
        st.warning("Aguardando dados para gerar inteligência.")
    else:
        # Limpeza de dados para numérico
        if 'Valor Potencial' in df.columns:
            df['Valor Potencial'] = pd.to_numeric(df['Valor Potencial'], errors='coerce').fillna(0)
        
        # KPIs Topo
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        total_leads = len(df)
        quentes = len(df[df['Status'].str.contains('Quente', case=False, na=False)])
        pipeline_val = df['Valor Potencial'].sum()
        vendas = len(df[df['Status'].str.contains('Venda|Fechado', case=False, na=False)])
        
        kpi1.metric("Leads Totais", total_leads, "Base Total")
        kpi2.metric("Oportunidades Quentes", quentes, "🔥 Alta Prioridade")
        kpi3.metric("Pipeline Estimado", f"R$ {pipeline_val:,.2f}", "Em negociação")
        kpi4.metric("Fechamentos", vendas, "Convertidos")
        
        st.markdown("---")
        
        # Gráficos Avançados
        g1, g2 = st.columns([2,1])
        
        with g1:
            st.subheader("Funil de Conversão")
            # Agrupa por status
            funnel_data = df['Status'].value_counts().reset_index()
            funnel_data.columns = ['Status', 'Count']
            
            fig_funnel = px.funnel(funnel_data, x='Count', y='Status', title="Saúde do Pipeline", color='Status', 
                                   color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_funnel.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig_funnel, use_container_width=True)
            
        with g2:
            st.subheader("Origem dos Leads")
            fig_pie = px.pie(df, names='Origem', hole=0.5, color_discrete_sequence=px.colors.sequential.Blues_r)
            fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white", showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)

# >>> PÁGINA 2: INTELIGÊNCIA ARTIFICIAL <<<
elif menu == "🧠 Inteligência Artificial":
    st.title("BlueSDR Copilot")
    st.markdown("Cole a conversa do WhatsApp/Email abaixo para análise instantânea.")
    
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.subheader("📥 Entrada de Dados")
        texto_chat = st.text_area("Transcrição da Conversa", height=350, placeholder="Cole a conversa aqui...")
        btn_analisar = st.button("⚡ ANALISAR AGORA")
    
    with c2:
        st.subheader("📤 Diagnóstico da IA")
        if btn_analisar and texto_chat:
            with st.spinner("Decodificando perfil comportamental e financeiro..."):
                res = analisar_conversa_pro(texto_chat)
                partes = res.split('|')
                
                if len(partes) >= 6:
                    st.session_state['analise_temp'] = partes
                    st.success("Análise Concluída com Sucesso!")
                else:
                    st.error("Erro na leitura. Tente novamente.")

        # Exibe resultado se existir
        if 'analise_temp' in st.session_state:
            p = st.session_state['analise_temp']
            
            # Card de Resultado
            with st.container():
                st.markdown(f"""
                <div style="background-color: #1f2937; padding: 20px; border-radius: 10px; border: 1px solid #374151;">
                    <h3 style="margin:0; color: #4da6ff;">👤 {p[0]}</h3>
                    <p style="color: #9ca3af;">Origem: {p[1]} | Potencial: <b>R$ {p[4]}</b></p>
                    <hr style="border-color: #374151;">
                    <p style="color: white; font-size: 16px;"><b>Diagnóstico:</b> {p[3]}</p>
                    <p style="color: #fbbf24;"><b>Status:</b> {p[2]}</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("#### 💬 Sugestão de Resposta")
                st.code(p[5], language="text")
                
                if st.button("💾 CONFIRMAR E SALVAR NO CRM"):
                    # Salva: Data, Nome, Origem, Status, Dor, Valor, Obs
                    data = datetime.now().strftime("%d/%m/%Y %H:%M")
                    try:
                        sheet_leads.append_row([data, p[0], p[1], p[2], p[3], p[4], f"Sugestão IA: {p[5]}"])
                        st.toast(f"Lead {p[0]} salvo com segurança!", icon="✅")
                        del st.session_state['analise_temp']
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

# >>> PÁGINA 3: GESTÃO FINANCEIRA <<<
elif menu == "💰 Gestão Financeira":
    st.title("Controle de Caixa")
    
    # Formulário Rápido
    with st.expander("➕ Novo Pagamento / Recebimento", expanded=True):
        with st.form("form_fin"):
            c1, c2, c3 = st.columns(3)
            cliente = c1.text_input("Cliente")
            valor = c2.number_input("Valor (R$)", min_value=0.0)
            servico = c3.text_input("Serviço/Produto")
            
            c4, c5 = st.columns(2)
            forma = c4.selectbox("Forma", ["Pix", "Cartão Crédito", "Cartão Débito", "Dinheiro"])
            status = c5.selectbox("Status", ["Pago", "Pendente", "Agendado"])
            
            if st.form_submit_button("Registrar Transação"):
                dt = datetime.now().strftime("%d/%m/%Y")
                sheet_pagamentos.append_row([dt, cliente, servico, valor, status, forma])
                st.success("Transação registrada!")
                time.sleep(1)
                st.rerun()
    
    # Tabela
    st.markdown("### Histórico Recente")
    df_pgt = pd.DataFrame(sheet_pagamentos.get_all_records())
    if not df_pgt.empty:
        st.dataframe(df_pgt, use_container_width=True)
        total_caixa = pd.to_numeric(df_pgt[df_pgt['Status']=='Pago']['Valor'], errors='coerce').sum()
        st.metric("Total em Caixa (Confirmado)", f"R$ {total_caixa:,.2f}")
    else:
        st.info("Nenhuma transação registrada.")

# >>> PÁGINA 4: DATABASE <<<
elif menu == "📂 Database":
    st.title("Vault de Dados (Master View)")
    tab1, tab2 = st.tabs(["Base de Leads", "Base Financeira"])
    
    with tab1:
        st.dataframe(pd.DataFrame(sheet_leads.get_all_records()), use_container_width=True, height=500)
    with tab2:
        st.dataframe(pd.DataFrame(sheet_pagamentos.get_all_records()), use_container_width=True, height=500)

# --- RODAPÉ ---
st.markdown("""
    <div class="footer">
        🔒 <b>BlueSDR Enterprise</b> | 256-bit SSL Encrypted <br>
        Developed by <b>Leticia Nascimento</b> © 2024
    </div>
    """, unsafe_allow_html=True)
