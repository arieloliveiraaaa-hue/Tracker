import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time

# Configuração da página
st.set_page_config(page_title="Equity Monitor Pro", layout="wide", page_icon="📈")

# =========================================================
# DESIGN PREMIUM
# =========================================================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=JetBrains+Mono:wght@500;700&display=swap');

        .stApp { background-color: #000000 !important; }
        header, footer, #MainMenu {visibility: hidden;}
        .block-container { padding: 3rem 5rem !important; }
        
        @media (max-width: 768px) {
            .block-container { padding: 1rem 0.5rem !important; }
        }

        .main-title {
            font-family: 'Inter', sans-serif !important;
            font-size: 60px !important;
            font-weight: 900 !important;
            color: #FFFFFF !important;
            letter-spacing: -4px !important;
            line-height: 1 !important;
            display: block !important;
        }

        .sub-header {
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 15px !important;
            color: #444 !important;
            margin-top: 10px !important;
            margin-bottom: 30px !important;
            text-transform: uppercase !important;
            letter-spacing: 5px !important;
        }

        /* TABELA */
        .desktop-view-container table {
            width: 100% !important;
            border-collapse: collapse !important;
            background-color: #000000 !important;
        }

        .desktop-view-container th {
            background-color: #000000 !important;
            color: #FFFFFF !important;
            font-size: 13px !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            padding: 20px 10px !important;
            border-bottom: 2px solid #222 !important;
            font-family: 'Inter', sans-serif !important;
            text-align: center !important;
        }

        .desktop-view-container td {
            padding: 18px 10px !important;
            border-bottom: 1px solid #111 !important;
            font-size: 15px !important;
            color: #D1D1D1 !important;
            font-family: 'Inter', sans-serif !important;
            text-align: center !important;
        }

        .ticker-style { font-weight: 900 !important; color: #FFFFFF !important; }

        /* DESTAQUE LEVE PARA O IBOVESPA */
        .ibov-highlight-row td {
            background-color: #080808 !important;
            border-top: 1px solid #333 !important;
            border-bottom: 1px solid #333 !important;
        }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# LÓGICA DE DADOS
# =========================================================
MINHA_COBERTURA = {
    "TOTS3.SA": {"Rec": "Compra", "Alvo": 48.00},
    "VIVT3.SA": {"Rec": "Compra", "Alvo": 38.00},
    "CPLE3.SA": {"Rec": "Neutro", "Alvo": 11.00},
    "AXIA3.SA": {"Rec": "Compra", "Alvo": 59.00},
    "ENGI3.SA": {"Rec": "Compra", "Alvo": 46.00},
    "TAEE11.SA": {"Rec": "Compra", "Alvo": 34.00},
    "EQTL3.SA": {"Rec": "Compra", "Alvo": 35.00},
    "RDOR3.SA": {"Rec": "Compra", "Alvo": 34.00},
    "HAPV3.SA": {"Rec": "Compra", "Alvo": 64.80},
}

def format_br(val, is_pct=False, moeda_sym=""):
    if pd.isna(val) or val == 0 and not is_pct: return "-"
    formatted = "{:,.2f}".format(val).replace(",", "X").replace(".", ",").replace("X", ".")
    if is_pct: return f"{formatted}%"
    if moeda_sym: return f"{moeda_sym} {formatted}"
    return formatted

def color_pct(val):
    color = "#00FF95" if val > 0.001 else "#FF4B4B" if val < -0.001 else "#555"
    return f'<span style="color: {color}; font-family: \'JetBrains Mono\';">{format_br(val, is_pct=True)}</span>'

@st.cache_data(ttl=60)
def get_monitor_data():
    tickers = ["^BVSP"] + list(MINHA_COBERTURA.keys())
    data = yf.download(tickers, period="1y", interval="1d", auto_adjust=True)
    
    rows = []
    for t in tickers:
        try:
            hist = data['Close'][t].dropna()
            price = hist.iloc[-1]
            prev_price = hist.iloc[-2]
            
            # Cálculo de variações
            hoje_pct = ((price / prev_price) - 1) * 100
            val_30d = ((price / hist.iloc[-22]) - 1) * 100 if len(hist) > 22 else 0
            val_6m = ((price / hist.iloc[-126]) - 1) * 100 if len(hist) > 126 else 0
            val_12m = ((price / hist.iloc[0]) - 1) * 100 if len(hist) > 0 else 0
            
            vol = (data['Volume'][t].iloc[-1] / 1_000_000) if t != "^BVSP" else 0

            if t == "^BVSP":
                rows.append({
                    "Ticker": "IBOVESPA", "Rec": "-", "Alvo": "-", "Preço": format_br(price),
                    "Upside": "-", "Hoje": hoje_pct, "30D": val_30d, "6M": val_6m, "12M": val_12m, 
                    "Vol": "-", "is_ibov": True
                })
            else:
                info = MINHA_COBERTURA[t]
                upside = ((info['Alvo'] / price) - 1) * 100
                rows.append({
                    "Ticker": t.replace(".SA", ""), "Rec": info['Rec'], "Alvo": format_br(info['Alvo'], moeda_sym="R$"),
                    "Preço": format_br(price, moeda_sym="R$"), "Upside": upside, "Hoje": hoje_pct, 
                    "30D": val_30d, "6M": val_6m, "12M": val_12m, "Vol": format_br(vol), "is_ibov": False
                })
        except: continue
    return rows

# =========================================================
# RENDERIZAÇÃO
# =========================================================
st.markdown('<span class="main-title">EQUITY MONITOR</span>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">TERMINAL • {datetime.now().strftime("%d %b %Y")}</div>', unsafe_allow_html=True)

data_rows = get_monitor_data()

table_html = """
<div class="desktop-view-container">
    <table>
        <thead>
            <tr>
                <th>Ticker</th><th>Rec.</th><th>Alvo</th><th>Preço</th>
                <th>Upside</th><th>Hoje</th><th>30D</th><th>6M</th><th>12M</th><th>Vol (MM)</th>
            </tr>
        </thead>
        <tbody>
"""

for r in data_rows:
    row_class = 'class="ibov-highlight-row"' if r['is_ibov'] else ""
    table_html += f"""
        <tr {row_class}>
            <td><span class="ticker-style">{r['Ticker']}</span></td>
            <td>{r['Rec']}</td>
            <td>{r['Alvo']}</td>
            <td>{r['Preço']}</td>
            <td>{color_pct(r['Upside']) if isinstance(r['Upside'], float) else r['Upside']}</td>
            <td>{color_pct(r['Hoje'])}</td>
            <td>{color_pct(r['30D'])}</td>
            <td>{color_pct(r['6M'])}</td>
            <td>{color_pct(r['12M'])}</td>
            <td>{r['Vol']}</td>
        </tr>
    """

table_html += "</tbody></table></div>"
st.markdown(table_html, unsafe_allow_html=True)

# Próximo passo: Gostaria que eu adicionasse um gráfico de performance histórica ao clicar em uma linha?
