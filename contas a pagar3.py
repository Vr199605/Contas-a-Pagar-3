import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF
from datetime import datetime
import io

# 1. Configuração de Página e Estilo Dark Premium (Interface Original)
st.set_page_config(page_title="CASH FLOW PROJECT", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0E1117; }
    
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155; padding: 20px; border-radius: 20px;
    }
    div[data-testid="stMetricValue"] { color: #38bdf8; font-weight: 700; }
    
    .stButton>button {
        background: linear-gradient(90deg, #d946ef, #a21caf); border: none; color: white;
        border-radius: 12px; font-weight: bold; width: 100%; height: 3em;
    }
    .stDownloadButton>button {
        background: linear-gradient(90deg, #06b6d4, #0891b2); border: none; color: white;
        border-radius: 12px; font-weight: bold; width: 100%; height: 3em;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CLASSE PDF REFORMULADA PARA LAYOUT IMPECÁVEL ---
class PDFReport(FPDF):
    def header(self):
        # Header Sólido Azul Marinho
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

# --- FUNÇÕES DE APOIO ---
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
    
    keywords_imposto = ['ISS', 'IRPJ', 'CSLL', 'PIS', 'COFINS', 'RETIDO', 'IMPOSTO', 'TAXA', 'DARF']
    df['Tipo'] = df['Categoria'].apply(
        lambda x: 'Imposto/Retenção' if any(k in str(x).upper() for k in keywords_imposto) else 'Operacional'
    )
    return df

# --- DASHBOARD ---
try:
    df_raw = load_and_process()
    col_v = 'Valor categoria/centro de custo'

    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        st.title("💎 CASH FLOW PROJECT")
    with c2:
        if st.button("🔄 Sincronizar"):
            st.cache_data.clear()
            st.rerun()

    lista_meses = sorted(df_raw['Mes_Ano'].unique(), key=lambda x: pd.to_datetime(x, format='%m/%Y'))
    lista_meses.insert(0, "Todos os Meses")
    mes_selecionado = st.selectbox("📅 Período:", lista_meses)

    df = df_raw if mes_selecionado == "Todos os Meses" else df_raw[df_raw['Mes_Ano'] == mes_selecionado].copy()

    # Métricas Dashboard
    saidas_totais = df[df[col_v] < 0][col_v].sum()
    impostos_totais = df[df['Tipo'] == 'Imposto/Retenção'][col_v].sum()
    operacional_puro = df[df['Tipo'] == 'Operacional'][col_v].sum()
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Cash Out Total", format_brl(abs(saidas_totais)))
    m2.metric("Impostos/Taxas", format_brl(abs(impostos_totais)))
    m3.metric("Operacional", format_brl(abs(operacional_puro)))
    m4.metric("Lançamentos", len(df))

    # --- LÓGICA DO PDF ---
    with c3:
        def make_pdf():
            plt.style.use('seaborn-v0_8-whitegrid')
            
            # 1. Plot Burn
            fig1, ax1 = plt.subplots(figsize=(10, 4))
            burn = df.groupby('Data de pagamento')[col_v].sum().cumsum().abs()
            ax1.fill_between(burn.index, burn, color='#0ea5e9', alpha=0.15)
            ax1.plot(burn.index, burn, color='#0284c7', linewidth=2)
            ax1.set_title("CASH BURN ACUMULADO", fontweight='bold')
            buf1 = io.BytesIO()
            plt.savefig(buf1, format='png', dpi=180)
            buf1.seek(0)
            plt.close()

            # 2. Plot Pareto
            fig2, ax2 = plt.subplots(figsize=(10, 5))
            pareto = df[df[col_v] < 0].groupby('Categoria')[col_v].sum().abs().sort_values(ascending=False).head(8)
            pareto.plot(kind='bar', color='#38bdf8', ax=ax2)
            ax2.set_title("PARETO: MAIORES DESPESAS", fontweight='bold')
            plt.xticks(rotation=30, ha='right')
            buf2 = io.BytesIO()
            plt.savefig(buf2, format='png', dpi=180)
            buf2.seek(0)
            plt.close()

            # 3. Plot Pizza
            fig3, ax3 = plt.subplots(figsize=(6, 5))
            dist = df.groupby('Tipo')[col_v].sum().abs()
            ax3.pie(dist, labels=dist.index, autopct='%1.1f%%', colors=['#0ea5e9', '#d946ef'], startangle=140)
            ax3.set_title("DISTRIBUIÇÃO FISCAL VS OP", fontweight='bold')
            buf3 = io.BytesIO()
            plt.savefig(buf3, format='png', dpi=180)
            buf3.seek(0)
            plt.close()

            pdf = PDFReport()
            pdf.add_page()
            
            # Resumo KPIs
            pdf.section_divider(f"Resumo do Período: {mes_selecionado}")
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_fill_color(248, 250, 252)
            pdf.cell(47, 10, " Cash Out", 1, 0, 'L', True)
            pdf.cell(47, 10, " Impostos", 1, 0, 'L', True)
            pdf.cell(47, 10, " Operacional", 1, 0, 'L', True)
            pdf.cell(49, 10, " Notas", 1, 1, 'L', True)
            pdf.set_font('Helvetica', '', 10)
            pdf.cell(47, 10, format_brl(abs(saidas_totais)), 1, 0, 'L')
            pdf.cell(47, 10, format_brl(abs(impostos_totais)), 1, 0, 'L')
            pdf.cell(47, 10, format_brl(abs(operacional_puro)), 1, 0, 'L')
            pdf.cell(49, 10, str(len(df)), 1, 1, 'L')

            # Gráficos
            pdf.section_divider("Dinâmica de Caixa")
            pdf.image(buf1, x=10, w=190)
            
            pdf.add_page()
            pdf.section_divider("Análise de Categorias e Natureza")
            pdf.image(buf2, x=10, w=190)
            pdf.ln(5)
            pdf.image(buf3, x=55, w=100)

            # Tabela Final
            pdf.ln(5)
            pdf.section_divider("Consolidado por Natureza")
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_fill_color(241, 245, 249)
            pdf.cell(100, 10, " Natureza", 1, 0, 'L', True)
            pdf.cell(90, 10, " Valor Total", 1, 1, 'C', True)
            for tipo, valor in df.groupby('Tipo')[col_v].sum().abs().items():
                pdf.cell(100, 10, f" {tipo}", 1, 0, 'L')
                pdf.cell(90, 10, format_brl(valor), 1, 1, 'R')

            out = pdf.output()
            return bytes(out) if isinstance(out, bytearray) else out

        st.download_button(
            label="📥 Baixar PDF Impecável",
            data=make_pdf(),
            file_name=f"Relatorio_{mes_selecionado}.pdf",
            mime="application/pdf"
        )

    st.write("---")

    # Abas Visuais
    t1, t2, t3, t4 = st.tabs(["🔥 Burn Diário", "🎯 Pareto", "🏛️ Fiscal vs Op", "📋 Dados Brutos"])
    with t1:
        st.area_chart(df.groupby('Data de pagamento')[col_v].sum().cumsum().abs(), color="#f43f5e")
    with t2:
        st.bar_chart(df[df[col_v] < 0].groupby('Categoria')[col_v].sum().abs().sort_values(ascending=False), color="#38bdf8")
    with t3:
        st.bar_chart(df.groupby('Tipo')[col_v].sum().abs(), color="#a21caf")
    with t4:
        st.dataframe(df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro Crítico: {e}")
