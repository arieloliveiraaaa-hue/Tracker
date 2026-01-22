import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time

# Configuração da página
st.set_page_config(page_title="Equity Monitor Pro", layout="wide", page_icon="📈")

# =========================================================
# DESIGN PREMIUM (SEM ALTERAÇÕES)
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

        .top-nav {
            display: flex; gap: 18px; align-items: center; justify-content: flex-start; margin-bottom: 18px;
            font-family: 'JetBrains Mono', monospace !important; text-transform: uppercase !important;
            letter-spacing: 4px !important; font-size: 12px !important;
        }

        .main-title {
            font-family: 'Inter', sans-serif !important; font-size: 60px !important; font-weight: 900 !important;
            color: #FFFFFF !important; letter-spacing: -4px !important; line-height: 1 !important; display: block !important;
        }
        
        .sub-header {
            font-family: 'JetBrains Mono', monospace !important; font-size: 15px !important; color: #444 !important;
            margin-top: 10px !important; margin-bottom: 30px !important; text-transform: uppercase !important;
            letter-spacing: 5px !important; display: block !important;
        }

        .desktop-view-container table {
            width: 100% !important; border-collapse: collapse !important; background-color: #000000 !important; border: none !important;
        }

        .desktop-view-container th {
            background-color: #000000 !important; color: #FFFFFF !important; font-size: 13px !important;
            font-weight: 700 !important; text-transform: uppercase !important; padding: 20px 10px !important;
            text-align: center !important; border-bottom: 2px solid #222 !important; font-family: 'Inter', sans-serif !important;
        }

        .desktop-view-container td {
            padding: 18px 10px !important; border-bottom: 1px solid #111 !important; font-size: 15px !important;
            background-color: #000000 !important; color: #D1D1D1 !important; font-family: 'Inter', sans-serif !important; text-align: center !important;
        }

        .desktop-view-container tr:nth-child(even) td { background-color: #050505 !important; }
        .ticker-style { font-weight: 900 !important; color: #FFFFFF !important; }

        /* DESTAQUE LEVE PARA O IBOVESPA */
        .ibov-highlight td { border-top: 1px solid #333 !important; border-bottom: 1px solid #333 !important; background-color: #080808 !important; }

        /* MOBILE CARDS */
        details.mobile-card { background-color: #0a0a0a; border: 1px solid #222; border-radius: 8px; margin-bottom: 10px; overflow: hidden; font-family: 'Inter', sans-serif; }
        summary.m-summary { padding: 15px; cursor: pointer; list-style: none; display: flex; flex-direction: column; gap: 5px; background-color: #0e0e0e; }
        .m-header-top { display: flex; justify-content: space-between; align-items: center; width: 100%; }
        .m-ticker { font-size: 18px; font-weight: 900; color: #fff; }
        .m-price { font-size: 18px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
        .m-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; padding: 15px; background-color: #000; border-top: 1px solid #222;}
        .m-label { color: #555; font-size: 10px; text-transform: uppercase; margin-bottom: 4px; display:block;}
        .m-value { color: #ddd; font-size: 14px; font-weight: 600; font-family: 'JetBrains Mono', monospace; }

        @media (min-width: 769px) { .mobile-wrapper { display: none !important; } .desktop-view-container { display: block !important; } }
        @media (max-width: 768px) { .desktop-view-container { display: none !important; } .mobile-wrapper { display: block !important; } }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# LÓGICA DE DADOS (INCLUINDO IBOVESPA NO TOPO)
# =========================================================
MINHA_COBERTURA = {
    "^BVSP": {"Rec": "-", "Alvo": 0.0}, # Adicionado aqui
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
    if pd.isna(val) or (val == 0 and not is_pct): return "-"
    formatted = "{:,.2f}".format(val).replace(",", "X").replace(".", ",").replace("X", ".")
    if is_pct: return f"{formatted}%"
    if moeda_sym: return f"{moeda_sym} {formatted}"
    return formatted

@st.cache_data(ttl=60, show_spinner=False)
def get_stock_data(tickers):
    data_list = []
    raw = yf.download(tickers, period="6y", auto_adjust=True, group_by="ticker", progress=False)
    
    for ticker in tickers:
        try:
            hist = raw[ticker]['Close'].dropna()
            price_current = float(hist.iloc[-1])
            price_prev = float(hist.iloc[-2])
            
            dados = MINHA_COBERTURA.get(ticker)
            upside = (dados["Alvo"] / price_current - 1) * 100 if dados["Alvo"] > 0 else 0.0
            
            data_list.append({
                "Ticker": "IBOVESPA" if ticker == "^BVSP" else ticker.replace(".SA", ""),
                "Moeda": "R$" if ticker.endswith(".SA") or ticker == "^BVSP" else "$",
                "Preço": price_current,
                "Recomendação": dados["Rec"],
                "Preço-Alvo": dados["Alvo"],
                "Upside": upside,
                "Hoje %": ((price_current / price_prev) - 1) * 100,
                "30 Dias %": ((price_current / hist.iloc[-22]) - 1) * 100,
                "6 Meses %": ((price_current / hist.iloc[-126]) - 1) * 100,
                "12 Meses %": ((price_current / hist.iloc[-252]) - 1) * 100,
                "Vol (MM)": (raw[ticker]['Volume'].iloc[-1] / 1_000_000) if ticker != "^BVSP" else 0.0,
                "is_ibov": ticker == "^BVSP"
            })
        except: continue
    return pd.DataFrame(data_list)

def color_pct(val, is_upside_ibov=False):
    if is_upside_ibov: return "-"
    color = "#00FF95" if val > 0.001 else "#FF4B4B" if val < -0.001 else "#555"
    return f'<span style="color: {color}; font-family: \'JetBrains Mono\';">{format_br(val, is_pct=True)}</span>'

# =========================================================
# UI
# =========================================================
st.markdown('<span class="main-title">EQUITY MONITOR</span>', unsafe_allow_html=True)
st.markdown(f'<span class="sub-header">TERMINAL • {datetime.now().strftime("%d %b %Y")}</span>', unsafe_allow_html=True)

df = get_stock_data(list(MINHA_COBERTURA.keys()))

if not df.empty:
    # Gerando Tabela HTML Manualmente para aplicar a classe de destaque no IBOV
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
    for _, r in df.iterrows():
        row_class = 'class="ibov-highlight"' if r['is_ibov'] else ""
        table_html += f"""
            <tr {row_class}>
                <td><span class="ticker-style">{r['Ticker']}</span></td>
                <td>{r['Recomendação']}</td>
                <td>{format_br(r['Preço-Alvo'], moeda_sym=r['Moeda']) if r['Preço-Alvo'] > 0 else '-'}</td>
                <td>{format_br(r['Preço'], moeda_sym=r['Moeda'])}</td>
                <td>{color_pct(r['Upside'], is_upside_ibov=r['is_ibov'])}</td>
                <td>{color_pct(r['Hoje %'])}</td>
                <td>{color_pct(r['30 Dias %'])}</td>
                <td>{color_pct(r['6 Meses %'])}</td>
                <td>{color_pct(r['12 Meses %'])}</td>
                <td>{format_br(r['Vol (MM)']) if not r['is_ibov'] else '-'}</td>
            </tr>
        """
    table_html += "</tbody></table></div>"
    st.markdown(table_html, unsafe_allow_html=True)

    # Mobile View simplificado acompanhando a lógica
    mobile_cards = ""
    for _, r in df.iterrows():
        c_price = "#00FF95" if r['Hoje %'] > 0 else "#FF4B4B" if r['Hoje %'] < 0 else "#FFFFFF"
        mobile_cards += f"""
        <details class="mobile-card">
            <summary class="m-summary">
                <div class="m-header-top"><span class="m-ticker">{r['Ticker']}</span><span class="m-price" style="color: {c_price}">{r['Moeda']} {format_br(r['Preço'])}</span></div>
            </summary>
            <div class="m-grid">
                <div class="m-item"><span class="m-label">Hoje</span><span class="m-value" style="color:{c_price}">{format_br(r['Hoje %'], is_pct=True)}</span></div>
                <div class="m-item"><span class="m-label">12M</span><span class="m-value">{format_br(r['12 Meses %'], is_pct=True)}</span></div>
            </div>
        </details>"""
    st.markdown(f'<div class="mobile-wrapper">{mobile_cards}</div>', unsafe_allow_html=True)

    time.sleep(60)
    st.rerun()
