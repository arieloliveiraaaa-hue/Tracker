import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time

# Configuração da página
st.set_page_config(page_title="Equity Monitor Pro", layout="wide", page_icon="📈")

# =========================================================
# DESIGN PREMIUM (MANTIDO CONFORME ORIGINAL)
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
            text-align: center !important;
            border-bottom: 2px solid #222 !important;
        }

        .desktop-view-container td {
            padding: 18px 10px !important;
            border-bottom: 1px solid #111 !important;
            font-size: 15px !important;
            color: #D1D1D1 !important;
            text-align: center !important;
            font-family: 'Inter', sans-serif !important;
        }

        .ticker-style { font-weight: 900 !important; color: #FFFFFF !important; }

        /* DESTAQUE DO IBOVESPA */
        .ibov-row td {
            background-color: #080808 !important;
            border-top: 1px solid #333 !important;
            border-bottom: 1px solid #333 !important;
        }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# DADOS E LÓGICA (REVERTIDO PARA O SEU PADRÃO)
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
    if val == "-" or pd.isna(val): return "-"
    formatted = "{:,.2f}".format(val).replace(",", "X").replace(".", ",").replace("X", ".")
    if is_pct: return f"{formatted}%"
    if moeda_sym: return f"{moeda_sym} {formatted}"
    return formatted

def color_pct(val):
    if val == "-": return "-"
    color = "#00FF95" if val > 0 else "#FF4B4B" if val < 0 else "#555"
    return f'<span style="color: {color}; font-family: \'JetBrains Mono\';">{format_br(val, is_pct=True)}</span>'

@st.cache_data(ttl=60)
def get_data():
    # Inclui o Ibovespa na lista de busca
    tickers = ["^BVSP"] + list(MINHA_COBERTURA.keys())
    df = yf.download(tickers, period="1y", group_by='ticker', auto_adjust=True)
    return df

# =========================================================
# INTERFACE
# =========================================================
st.markdown('<span class="main-title">EQUITY MONITOR</span>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">TERMINAL • {datetime.now().strftime("%d %b %Y")}</div>', unsafe_allow_html=True)

raw_data = get_data()

# Construção da Tabela HTML
table_body = ""
tickers_to_show = ["^BVSP"] + list(MINHA_COBERTURA.keys())

for t in tickers_to_show:
    try:
        hist = raw_data[t]['Close'].dropna()
        if hist.empty: continue
        
        p_atual = hist.iloc[-1]
        p_ontem = hist.iloc[-2]
        
        # Variáveis padrão
        hoje = ((p_atual / p_ontem) - 1) * 100
        m1 = ((p_atual / hist.iloc[-22]) - 1) * 100 if len(hist) > 22 else 0
        m6 = ((p_atual / hist.iloc[-126]) - 1) * 100 if len(hist) > 126 else 0
        y1 = ((p_atual / hist.iloc[0]) - 1) * 100
        vol = (raw_data[t]['Volume'].iloc[-1] / 1_000_000)
        
        # Lógica específica para o Ibovespa (Destaque)
        if t == "^BVSP":
            row_style = 'class="ibov-row"'
            ticker_name = "IBOVESPA"
            rec, alvo, upside, moeda, v_mm = "-", "-", "-", "", "-"
        else:
            row_style = ""
            ticker_name = t.replace(".SA", "")
            rec = MINHA_COBERTURA[t]["Rec"]
            alvo_val = MINHA_COBERTURA[t]["Alvo"]
            alvo = format_br(alvo_val, moeda_sym="R$")
            upside = ((alvo_val / p_atual) - 1) * 100
            moeda = "R$ "
            v_mm = format_br(vol)

        table_body += f"""
            <tr {row_style}>
                <td><span class="ticker-style">{ticker_name}</span></td>
                <td>{rec}</td>
                <td>{alvo}</td>
                <td>{format_br(p_atual, moeda_sym=moeda)}</td>
                <td>{color_pct(upside)}</td>
                <td>{color_pct(hoje)}</td>
                <td>{color_pct(m1)}</td>
                <td>{color_pct(m6)}</td>
                <td>{color_pct(y1)}</td>
                <td>{v_mm}</td>
            </tr>
        """
    except: continue

st.markdown(f"""
    <div class="desktop-view-container">
        <table>
            <thead>
                <tr>
                    <th>Ticker</th><th>Rec.</th><th>Alvo</th><th>Preço</th>
                    <th>Upside</th><th>Hoje</th><th>30D</th><th>6M</th><th>12M</th><th>Vol (MM)</th>
                </tr>
            </thead>
            <tbody>{table_body}</tbody>
        </table>
    </div>
""", unsafe_allow_html=True)

time.sleep(60)
st.rerun()
