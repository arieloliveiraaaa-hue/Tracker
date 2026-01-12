import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time

# Configuração da página
st.set_page_config(page_title="Equity Monitor Pro", layout="wide", page_icon="📈")

# =========================================================
# DESIGN PREMIUM - CSS ORIGINAL RESTAURADO
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
            display: block !important;
        }

        .section-divider {
            font-family: 'Inter', sans-serif !important;
            font-size: 12px !important;
            font-weight: 900 !important;
            color: #333 !important;
            letter-spacing: 3px !important;
            text-transform: uppercase !important;
            margin: 60px 0 20px 0 !important;
            border-bottom: 1px solid #111;
            padding-bottom: 10px;
        }

        /* TABELA PC */
        .desktop-view-container { padding-top: 20px !important; }
        .desktop-view-container table {
            width: 100% !important;
            border-collapse: collapse !important;
            background-color: #000000 !important;
            border: none !important;
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
            font-family: 'Inter', sans-serif !important;
        }
        .desktop-view-container td {
            padding: 18px 10px !important;
            border-bottom: 1px solid #111 !important;
            font-size: 15px !important;
            background-color: #000000 !important;
            color: #D1D1D1 !important;
            font-family: 'Inter', sans-serif !important;
            text-align: center !important;
        }
        .desktop-view-container tr:nth-child(even) td { background-color: #050505 !important; }
        .ticker-style { font-weight: 900 !important; color: #FFFFFF !important; }

        /* MOBILE CARDS */
        details.mobile-card {
            background-color: #0a0a0a;
            border: 1px solid #222;
            border-radius: 8px;
            margin-bottom: 10px;
            overflow: hidden;
            font-family: 'Inter', sans-serif;
        }
        summary.m-summary {
            padding: 15px;
            cursor: pointer;
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 5px;
            background-color: #0e0e0e;
        }
        .m-header-top { display: flex; justify-content: space-between; align-items: center; width: 100%; }
        .m-ticker { font-size: 18px; font-weight: 900; color: #fff; }
        .m-price { font-size: 18px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
        .m-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; padding: 15px; background-color: #000; border-top: 1px solid #222;}
        .m-label { color: #555; font-size: 10px; text-transform: uppercase; margin-bottom: 4px; display:block;}
        .m-value { color: #ddd; font-size: 14px; font-weight: 600; font-family: 'JetBrains Mono', monospace; }

        @media (min-width: 769px) { .mobile-wrapper { display: none !important; } .desktop-view-container { display: block !important; } }
        @media (max-width: 768px) { .desktop-view-container { display: none !important; } .mobile-wrapper { display: block !important; } [data-testid="stPopover"] { display: none !important; } }
        
        div[data-testid="stPopover"] button {
            background-color: #000000 !important;
            border: 1px solid #222 !important;
            color: #444 !important;
        }
        div[data-testid="stPopover"] {
            display: flex;
            justify-content: flex-end;
            margin-bottom: -15px;
        }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# DADOS
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

SETORES_ACOMPANHAMENTO = {
    "IBOV": ["^BVSP"],
    "Bancos": ["ITUB4.SA", "BBDC4.SA", "BBAS3.SA", "SANB11.SA", "B3SA3.SA"],
    "Energia": ["EQTL3.SA", "AURE3.SA", "TAEE11.SA", "CPLE3.SA"],
    "Tech": ["TOTS3.SA", "TIMS3.SA", "VIVT3.SA"],
    "Varejo": ["LREN3.SA", "MGLU3.SA", "ASAI3.SA"]
}

# =========================================================
# LÓGICA
# =========================================================
def format_br(val, is_pct=False, moeda_sym=""):
    if pd.isna(val) or (val == 0 and not is_pct): return "-"
    formatted = "{:,.2f}".format(val).replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{moeda_sym} {formatted}" if moeda_sym else (f"{formatted}%" if is_pct else formatted)

def get_stock_data(tickers):
    data_list = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2y")
            if hist.empty: continue
            price_current = float(hist['Close'].iloc[-1])
            price_prev = float(hist['Close'].iloc[-2])
            
            def calculate_pct(days):
                try:
                    target = hist.index[-1] - timedelta(days=days)
                    idx = hist.index.get_indexer([target], method='pad')[0]
                    return ((price_current / float(hist['Close'].iloc[idx])) - 1) * 100
                except: return 0.0

            data_list.append({
                "Ticker": ticker.replace(".SA", ""), "Preço": price_current, 
                "Hoje %": ((price_current/price_prev)-1)*100, "30D %": calculate_pct(30), 
                "12M %": calculate_pct(365), "Original": ticker, "Moeda": "R$"
            })
        except: continue
    return pd.DataFrame(data_list)

def color_pct(val):
    color = "#00FF95" if val > 0.001 else "#FF4B4B" if val < -0.001 else "#555"
    return f'<span style="color: {color}; font-family: \'JetBrains Mono\';">{format_br(val, is_pct=True)}</span>'

# =========================================================
# UI PRINCIPAL
# =========================================================
st.markdown('<span class="main-title">EQUITY MONITOR</span>', unsafe_allow_html=True)
st.markdown(f'<span class="sub-header">B3 REAL-TIME • {datetime.now().strftime("%H:%M:%S")}</span>', unsafe_allow_html=True)

# --- SEÇÃO 1: CARTEIRA ---
st.markdown('<div class="section-divider">CARTEIRA COBERTURA</div>', unsafe_allow_html=True)
df_carteira = get_stock_data(list(MINHA_COBERTURA.keys()))

if not df_carteira.empty:
    with st.popover("⚙️"):
        sort_col = st.selectbox("Ordenar Carteira:", df_carteira.columns, index=0)
        df_carteira = df_carteira.sort_values(by=sort_col, ascending=False)

    # PC View Carteira
    df_v = pd.DataFrame()
    df_v["Ticker"] = df_carteira["Ticker"].apply(lambda x: f'<span class="ticker-style">{x}</span>')
    df_v["Rec."] = [MINHA_COBERTURA[t]["Rec"] for t in df_carteira["Original"]]
    df_v["Alvo"] = [format_br(MINHA_COBERTURA[t]["Alvo"], moeda_sym="R$") for t in df_carteira["Original"]]
    df_v["Preço"] = df_carteira.apply(lambda r: format_br(r["Preço"], moeda_sym="R$"), axis=1)
    df_v["Upside"] = [color_pct((MINHA_COBERTURA[t]["Alvo"]/r["Preço"]-1)*100) for t, r in zip(df_carteira["Original"], df_carteira.to_dict('records'))]
    df_v["Hoje"] = df_carteira["Hoje %"].apply(color_pct)
    df_v["12M"] = df_carteira["12M %"].apply(color_pct)
    
    st.markdown(f'<div class="desktop-view-container">{df_v.to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)

    # Mobile View Carteira
    m_html = ""
    for _, r in df_carteira.iterrows():
        c_price = "#00FF95" if r['Hoje %'] > 0 else "#FF4B4B"
        m_html += f'<details class="mobile-card"><summary class="m-summary"><div class="m-header-top"><span class="m-ticker">{r["Ticker"]}</span><span class="m-price" style="color: {c_price}">R$ {format_br(r["Preço"])}</span></div><div style="font-size:12px;color:#444">Alvo: R$ {format_br(MINHA_COBERTURA[r["Original"]]["Alvo"])}</div></summary><div class="m-grid"><div class="m-item"><span class="m-label">Hoje</span><span class="m-value" style="color:{c_price}">{format_br(r["Hoje %"],True)}</span></div><div class="m-item"><span class="m-label">12M</span><span class="m-value">{format_br(r["12M %"],True)}</span></div></div></details>'
    st.markdown(f'<div class="mobile-wrapper">{m_html}</div>', unsafe_allow_html=True)

# --- SEÇÃO 2: SETORES ---
st.markdown('<div class="section-divider">ACOMPANHAMENTO SETORES</div>', unsafe_allow_html=True)

for setor, tickers in SETORES_ACOMPANHAMENTO.items():
    st.markdown(f'<div style="color:#666; font-size:11px; margin-bottom:10px; font-family:Inter; font-weight:700;">// {setor}</div>', unsafe_allow_html=True)
    df_s = get_stock_data(tickers)
    
    if not df_s.empty:
        # PC View Setor
        df_sv = pd.DataFrame()
        df_sv["Ticker"] = df_s["Ticker"].apply(lambda x: f'<span class="ticker-style">{x}</span>')
        df_sv["Preço"] = df_s.apply(lambda r: format_br(r["Preço"], moeda_sym="R$"), axis=1)
        df_sv["Hoje"] = df_s["Hoje %"].apply(color_pct)
        df_sv["30D"] = df_s["30D %"].apply(color_pct)
        df_sv["12M"] = df_s["12M %"].apply(color_pct)
        st.markdown(f'<div class="desktop-view-container" style="padding-top:0px !important; margin-bottom:30px;">{df_sv.to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)

        # Mobile View Setor
        ms_html = ""
        for _, r in df_s.iterrows():
            c_p = "#00FF95" if r['Hoje %'] > 0 else "#FF4B4B"
            ms_html += f'<details class="mobile-card"><summary class="m-summary"><div class="m-header-top"><span class="m-ticker">{r["Ticker"]}</span><span class="m-price" style="color: {c_p}">R$ {format_br(r["Preço"])}</span></div></summary><div class="m-grid"><div class="m-item"><span class="m-label">Hoje</span><span class="m-value" style="color:{c_p}">{format_br(r["Hoje %"],True)}</span></div><div class="m-item"><span class="m-label">12M</span><span class="m-value">{format_br(r["12M %"],True)}</span></div></div></details>'
        st.markdown(f'<div class="mobile-wrapper" style="padding-top:0px !important;">{ms_html}</div>', unsafe_allow_html=True)

time.sleep(60)
st.rerun()
