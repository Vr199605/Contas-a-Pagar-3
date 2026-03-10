import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF
from datetime import datetime
import io

# 1. Configuração de Página e Estilo Dark Premium (Interface Original Mantida)
st.set_page_config(page_title="CASH FLOW PROJECT - ACCOUNTS PAYABLE", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0E1117; }
    
    /* Cards de Métricas */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        padding: 20px;
        border-radius: 20px;
    }
    div[data-testid="stMetricValue"] { color: #38bdf8; font-weight: 700; }
    
    /* Abas Customizadas */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e293b;
        border-radius: 10px 10px 0px 0px;
        color: white;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #38bdf8 !important; color: #000 !important; }
    
    /* Botões */
    .stButton>button {
        background: linear-gradient(90deg, #d946ef, #a21caf); border: none; color: white;
        border-radius: 12px; font-weight: bold; width: 100%;
    }
    .stDownloadButton>button {
        background: linear-gradient(90deg, #0ea5e9, #2563eb); border: none; color: white;
        border-radius: 12px; font-weight: bold; width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CLASSE PDF REFORMULADA (LAYOUT IMPECÁVEL) ---
class PDFReport(FPDF):
    def header(self):
        # Header Sólido - Estilo Relatório Bancário
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 35, 'F')
        self.set_xy(10, 12)
        self.set_font('Helvetica', 'B', 15)
        self.set_text_color(255, 255, 255)
        self.cell(0, 0, 'RELATÓRIO EXECUTIVO DE FLUXO DE CAIXA', 0, 0, 'L')
        self.set_font('Helvetica', '', 9)
        self.set_xy(10, 19)
        self.cell(0, 0, f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")} | Confidencial', 0, 0, 'L')
        self.ln(25)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Página {self.page_no()} | Análise Estratégica de Contas a Pagar', align='C')

    def section_divider(self, label):
        self.ln(8)
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(31, 41, 55)
        self.cell(0, 10, label.upper(), 0, 1, 'L')
        self.set_draw_color(56, 189, 248)
        self.line(self.get_x(), self.get_y(), self.get_x() + 190, self.get_y())
        self.ln(5)

# --- FUNÇÕES AUXILIARES ---
def format_brl(val):
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

@st.cache_data(ttl=600)
def load_and_process():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT7KV7hi8lJHEleaPoPyAKWo7ChUTlLuorbLX9v4aZGXPKI6aeudpF06eUc60hmIPX8Pkz5BrZOhc1G/pub?output=csv"
    df = pd.read_csv(url)
    
    def clean_val(v):
        if isinstance(v, str):
            v = v.replace('R$', '').replace('.', '').replace(' ', '').replace(',', '.')
            try: return float(v)
            except: return 0.0
        return v

    col_v = 'Valor categoria/centro de custo'
    df[col_v] = df[col_v].apply(clean_val)
    df['Data de pagamento'] = pd.to_datetime(df['Data de pagamento'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Data de pagamento']).sort_values('Data de pagamento')
    df['Mes_Ano'] = df['Data de pagamento'].dt.strftime('%m/%Y')
    df['Periodo_Sort'] = df['Data de pagamento'].dt.to_period('M')

    keywords_imposto = ['ISS', 'IRPJ', 'CSLL', 'PIS', 'COFINS', 'RETIDO', 'IMPOSTO', 'TAXA', 'DARF']
    df['Tipo'] = df['Categoria'].apply(
        lambda x: 'Imposto/Retenção' if any(k in str(x).upper() for k in keywords_imposto) else 'Operacional'
    )
    return df

# --- MOTOR DO DASHBOARD ---
try:
    df_raw = load_and_process()
    col_v = 'Valor categoria/centro de custo'

    # Header Superior
    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        st.title("💎 CASH FLOW PROJECT")
    with c2:
        if st.button("🔄 Sincronizar Dados"):
            st.cache_data.clear()
            st.rerun()

    lista_meses = sorted(df_raw['Mes_Ano'].unique(), key=lambda x: pd.to_datetime(x, format='%m/%Y'))
    lista_meses.insert(0, "Todos os Meses")
    mes_selecionado = st.selectbox("📅 Período de Análise:", lista_meses)

    df = df_raw if mes_selecionado == "Todos os Meses" else df_raw[df_raw['Mes_Ano'] == mes_selecionado].copy()

    st.write("---")

    # Métricas de Alto Impacto
    saidas_totais = df[df[col_v] < 0][col_v].sum()
    impostos_totais = df[df['Tipo'] == 'Imposto/Retenção'][col_v].sum()
    operacional_puro = df[df['Tipo'] == 'Operacional'][col_v].sum()
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Cash Out Total", format_brl(abs(saidas_totais)))
    tax_perc = abs(impostos_totais/saidas_totais)*100 if saidas_totais != 0 else 0
    m2.metric("Impostos", format_brl(abs(impostos_totais)), f"{tax_perc:.1f}%")
    m3.metric("Operacional", format_brl(abs(operacional_puro)))
    m4.metric("Qtd. Notas", len(df))

    # --- GERADOR DE PDF EXECUTIVO (MUDANÇAS AQUI) ---
    with c3:
        def generate_exec_pdf():
            # Configuração visual dos gráficos (Fundo Branco para PDF)
            plt.rcParams.update({'figure.facecolor': 'white', 'font.size': 10})
            
            # Plot 1: Cash Burn (Área)
            fig1, ax1 = plt.subplots(figsize=(10, 4))
            burn = df.groupby('Data de pagamento')[col_v].sum().cumsum().abs()
            ax1.fill_between(burn.index, burn, color='#0ea5e9', alpha=0.15)
            ax1.plot(burn.index, burn, color='#0284c7', linewidth=2)
            ax1.set_title("CONSUMO DE CAIXA ACUMULADO", fontweight='bold')
            plt.tight_layout()
            buf1 = io.BytesIO()
            plt.savefig(buf1, format='png', dpi=200)
            buf1.seek(0)

            # Plot 2: Pareto (Barras)
            fig2, ax2 = plt.subplots(figsize=(10, 5))
            pareto = df[df[col_v] < 0].groupby('Categoria')[col_v].sum().abs().sort_values(ascending=False).head(8)
            pareto.plot(kind='bar', color='#38bdf8', ax=ax2)
            ax2.set_title("TOP 8 CATEGORIAS DE DESPESA", fontweight='bold')
            plt.xticks(rotation=30, ha='right')
            plt.tight_layout()
            buf2 = io.BytesIO()
            plt.savefig(buf2, format='png', dpi=200)
            buf2.seek(0)

            # Plot 3: Pizza (Fiscal vs Op)
            fig3, ax3 = plt.subplots(figsize=(6, 5))
            dist = df.groupby('Tipo')[col_v].sum().abs()
            ax3.pie(dist, labels=dist.index, autopct='%1.1f%%', colors=['#0ea5e9', '#d946ef'], startangle=140)
            ax3.set_title("FISCAL VS OPERACIONAL", fontweight='bold')
            plt.tight_layout()
            buf3 = io.BytesIO()
            plt.savefig(buf3, format='png', dpi=200)
            buf3.seek(0)

            # Montagem do PDF
            pdf = PDFReport()
            pdf.add_page()
            
            # Seção 1: Resumo Numérico
            pdf.section_divider(f"Visão Geral: {mes_selecionado}")
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_fill_color(248, 250, 252)
            pdf.cell(47, 10, " Cash Out Total", 1, 0, 'L', True)
            pdf.cell(47, 10, " Total Impostos", 1, 0, 'L', True)
            pdf.cell(47, 10, " Custo Operacional", 1, 0, 'L', True)
            pdf.cell(49, 10, " Notas Processadas", 1, 1, 'L', True)
            
            pdf.set_font('Helvetica', '', 10)
            pdf.cell(47, 10, format_brl(abs(saidas_totais)), 1, 0, 'L')
            pdf.cell(47, 10, format_brl(abs(impostos_totais)), 1, 0, 'L')
            pdf.cell(47, 10, format_brl(abs(operacional_puro)), 1, 0, 'L')
            pdf.cell(49, 10, str(len(df)), 1, 1, 'L')

            # Seção 2: Cash Burn
            pdf.section_divider("Dinâmica de Saída de Caixa")
            pdf.image(buf1, x=10, w=190)

            # Seção 3: Pareto e Pizza (Página 2 para evitar desformatação)
            pdf.add_page()
            pdf.section_divider("Distribuição de Custos e Natureza")
            pdf.image(buf2, x=10, w=190)
            pdf.ln(5)
            pdf.image(buf3, x=55, w=100)

            # Tabela Final de Auditoria
            pdf.ln(5)
            pdf.section_divider("Resumo Consolidado por Tipo")
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_fill_color(241, 245, 249)
            pdf.cell(100, 10, " Natureza do Lançamento", 1, 0, 'L', True)
            pdf.cell(90, 10, " Valor Consolidado (R$)", 1, 1, 'C', True)
            
            pdf.set_font('Helvetica', '', 10)
            for tipo, valor in df.groupby('Tipo')[col_v].sum().abs().items():
                pdf.cell(100, 10, f" {tipo}", 1, 0, 'L')
                pdf.cell(90, 10, format_brl(valor), 1, 1, 'R')

            out = pdf.output()
            return bytes(out) if isinstance(out, bytearray) else out

        st.download_button(
            label="📥 Baixar Relatório Executivo PDF",
            data=generate_exec_pdf(),
            file_name=f"Relatorio_Financeiro_{mes_selecionado}.pdf",
            mime="application/pdf"
        )

    # --- ABAS ORIGINAIS (MANTIDAS) ---
    tab_proj, tab_burn, tab_pareto, tab_tax, tab_raw = st.tabs([
        "📊 Projeção Mensal", "🔥 Cash Burn Diário", "🎯 Pareto (80/20)", "🏛️ Fiscal vs Op", "📋 Dados Brutos"
    ])

    with tab_proj:
        st.subheader("Análise Evolutiva: Histórico Mês a Mês")
        proj_mensal = df_raw[df_raw[col_v] < 0].groupby('Periodo_Sort')[col_v].sum().abs().reset_index()
        proj_mensal['Mês/Ano'] = proj_mensal['Periodo_Sort'].astype(str)
        st.bar_chart(proj_mensal.set_index('Mês/Ano')[col_v], color="#38bdf8")

    with tab_burn:
        st.subheader("Evolução do Consumo de Caixa (Acumulado)")
        burn_df = df.groupby('Data de pagamento')[col_v].sum().cumsum().abs().reset_index()
        st.area_chart(burn_df.set_index('Data de pagamento'), color="#f43f5e")

    with tab_pareto:
        st.subheader("Análise de Pareto: Maiores Saídas")
        resumo_cat = df[df[col_v] < 0].groupby('Categoria')[col_v].sum().abs().sort_values(ascending=False).head(10)
        st.bar_chart(resumo_cat, color="#38bdf8")

    with tab_tax:
        st.subheader("Distribuição Fiscal vs Operacional")
        dist_tipo = df.groupby('Tipo')[col_v].sum().abs()
        st.bar_chart(dist_tipo, color="#a21caf")

    with tab_raw:
        st.subheader("Explorador Geral de Dados")
        st.dataframe(df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro ao carregar dashboard: {e}")