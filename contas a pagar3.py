import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF2
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

# --- CLASSE PDF COM GRÁFICOS VETORIAIS NATIVOS (SEM MATPLOTLIB) ---
class PDFReport(FPDF):
    def header(self):
        # Header Sólido Azul Marinho [cite: 1, 15]
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 35, 'F')
        self.set_xy(10, 12)
        self.set_font('Helvetica', 'B', 15)
        self.set_text_color(255, 255, 255)
        self.cell(0, 0, 'RELATÓRIO EXECUTIVO DE FLUXO DE CAIXA', 0, 0, 'L') [cite: 1, 39]
        self.set_font('Helvetica', '', 9)
        self.set_xy(10, 19)
        self.cell(0, 0, f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")} | Confidencial', 0, 0, 'L') [cite: 2, 40]
        self.ln(25)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Página {self.page_no()} | Análise Estratégica de Caixa', align='C') [cite: 36, 45]

    def draw_bar_chart(self, data_dict, title):
        self.ln(10)
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(31, 41, 55)
        self.cell(0, 10, title.upper(), 0, 1, 'L')
        
        # Configurações do gráfico
        x_start = 70
        y_current = self.get_y()
        max_val = max(data_dict.values()) if data_dict else 1
        chart_width = 120
        
        self.set_font('Helvetica', '', 8)
        for label, value in data_dict.items():
            # Nome da Categoria [cite: 28]
            self.set_xy(10, y_current)
            self.set_text_color(50, 50, 50)
            self.cell(60, 8, str(label)[:35], 0, 0, 'R')
            
            # Barra Azul [cite: 22]
            bar_len = (value / max_val) * chart_width
            self.set_fill_color(56, 189, 248)
            self.rect(x_start, y_current + 1, bar_len, 6, 'F')
            
            # Valor [cite: 4, 18, 19]
            self.set_xy(x_start + bar_len + 2, y_current)
            self.cell(0, 8, f"R$ {value:,.2f}", 0, 1, 'L')
            y_current += 9
        self.ln(5)

# --- FUNÇÕES DE APOIO ---
def format_brl(val):
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") [cite: 4, 18, 19, 41]

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
    ) [cite: 41, 44, 46]
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

    # Métricas Dashboard [cite: 3, 16, 17, 20]
    saidas_totais = df[df[col_v] < 0][col_v].sum() [cite: 4]
    impostos_totais = df[df['Tipo'] == 'Imposto/Retenção'][col_v].sum() [cite: 18, 41]
    operacional_puro = df[df['Tipo'] == 'Operacional'][col_v].sum() [cite: 19, 41]
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Cash Out Total", format_brl(abs(saidas_totais))) [cite: 3, 4]
    m2.metric("Impostos/Taxas", format_brl(abs(impostos_totais))) [cite: 16, 18]
    m3.metric("Operacional", format_brl(abs(operacional_puro))) [cite: 17, 19]
    m4.metric("Lançamentos", len(df)) [cite: 20]

    # --- LÓGICA DO PDF VETORIAL (SEM DEPENDÊNCIAS DE GRÁFICO) ---
    with c3:
        def make_pure_pdf():
            pdf = PDFReport()
            pdf.add_page()
            
            # Tabela de KPIs [cite: 3, 16, 17, 20]
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_fill_color(248, 250, 252)
            pdf.cell(47, 12, " CASH OUT", 1, 0, 'L', True) [cite: 3]
            pdf.cell(47, 12, " IMPOSTOS", 1, 0, 'L', True) [cite: 16]
            pdf.cell(47, 12, " OPERACIONAL", 1, 0, 'L', True) [cite: 17]
            pdf.cell(49, 12, " NOTAS", 1, 1, 'L', True) [cite: 20]
            
            pdf.set_font('Helvetica', '', 10)
            pdf.cell(47, 10, format_brl(abs(saidas_totais)), 1, 0, 'L') [cite: 4]
            pdf.cell(47, 10, format_brl(abs(impostos_totais)), 1, 0, 'L') [cite: 18]
            pdf.cell(47, 10, format_brl(abs(operacional_puro)), 1, 0, 'L') [cite: 19]
            pdf.cell(49, 10, str(len(df)), 1, 1, 'L')
            
            # Gráfico de Pareto Nativo (Top 10 Categorias) [cite: 22, 23, 24, 25, 26, 27, 29, 30, 31, 32, 33]
            pareto_data = df[df[col_v] < 0].groupby('Categoria')[col_v].sum().abs().sort_values(ascending=False).head(10).to_dict()
            pdf.draw_bar_chart(pareto_data, "Pareto: Top 10 Categorias de Saída") [cite: 22]
            
            # Tabela Resumo por Tipo [cite: 41, 44, 46]
            pdf.ln(10)
            pdf.set_font('Helvetica', 'B', 11)
            pdf.cell(0, 10, "DISTRIBUIÇÃO POR NATUREZA", 0, 1, 'L')
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_fill_color(241, 245, 249)
            pdf.cell(100, 10, " Natureza do Gasto", 1, 0, 'L', True)
            pdf.cell(90, 10, " Valor Total (R$)", 1, 1, 'C', True)
            
            pdf.set_font('Helvetica', '', 10)
            resumo_tipo = df.groupby('Tipo')[col_v].sum().abs().to_dict() [cite: 41]
            for tipo, valor in resumo_tipo.items():
                pdf.cell(100, 10, f" {tipo}", 1, 0, 'L') [cite: 44, 46]
                pdf.cell(90, 10, format_brl(valor), 1, 1, 'R') [cite: 41]

            return bytes(pdf.output())

        st.download_button(
            label="📥 Baixar PDF Premium",
            data=make_pure_pdf(),
            file_name=f"Relatorio_{mes_selecionado}.pdf",
            mime="application/pdf"
        )

    st.write("---")

    # Gráficos nativos do Streamlit (para a web, que já funcionam sem matplotlib)
    t1, t2, t3 = st.tabs(["🎯 Pareto", "🏛️ Fiscal vs Op", "📋 Dados Brutos"])
    with t1:
        st.bar_chart(df[df[col_v] < 0].groupby('Categoria')[col_v].sum().abs().sort_values(ascending=False), color="#38bdf8") [cite: 22]
    with t2:
        st.bar_chart(df.groupby('Tipo')[col_v].sum().abs(), color="#a21caf") [cite: 41]
    with t3:
        st.dataframe(df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro: {e}")

