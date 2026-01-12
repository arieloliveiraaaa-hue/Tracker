import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time

# Configuração da página
st.set_page_config(page_title="Equity Monitor Pro", layout="wide", page_icon="📈")

# =========================================================
# DESIGN PREMIUM - CSS
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
            font-size: 14px !important;
            color: #444 !important;
            margin-top: 10px !important;
            margin-bottom: 20px !important;
            text-transform: uppercase !important;
            letter-spacing: 5px !important;
            display: block !important;
        }

        /* TABS MINIMALISTAS */
        .stTabs [data-baseweb="tab-list"] { gap: 24px; background-color: transparent; }
        .stTabs [data-baseweb="tab"] {
            height: 40px; background-color: transparent !important;
            border: none !important; color: #444 !important;
            font-family: 'Inter', sans-serif !important; font-weight: 700 !important;
            text-transform: uppercase; letter-spacing: 1px;
        }
        .stTabs [data-baseweb="tab--active"] { color: #FFFFFF !important; border-bottom: 2px solid #FFFFFF !important; }

        /* TABELA PC */
        .desktop-view-container { padding-top: 20px !important; }
        .desktop-view-container table { width: 100% !important; border-collapse: collapse !important; background-color: #000000 !important; }
        .desktop-view-container th {
            background-color: #000000 !important; color: #FFFFFF !important; font-size: 12px !important;
            font-weight: 700 !important; text-transform: uppercase !important;
            padding: 15px 10px !important; text-align: center !important;
            border-bottom: 2px solid #222 !important; font-family: 'Inter', sans-serif !important;
        }
        .desktop-view-container td {
            padding: 15px 10px !important; border-bottom: 1px solid #111 !important;
            font-size: 14px !important; background-color: #000000 !important;
            color: #D1D1D1 !important; font-family: 'Inter', sans-serif !important; text-align: center !important;
        }
        .desktop-view-container tr:nth-child(even) td { background-color: #050505 !important; }
        .ticker-style { font-weight: 900 !important; color: #FFFFFF !important; }

        /* MOBILE CARDS */
        .mobile-wrapper { padding-top: 20px !important; }
        details.mobile-card { background-color: #0a0a0a; border: 1px solid #222; border-radius: 8px; margin-bottom: 8px; overflow: hidden; font-family: 'Inter', sans-serif; }
        summary.m-summary { padding: 12px; cursor: pointer; list-style: none; display: flex; flex-direction: column; background-color: #0e0e0e; }
        .m-header-top { display: flex; justify-content: space-between; align-items: center; width: 100%; }
        .m-ticker { font-size: 16px; font-weight: 900; color: #fff; }
        .m-price { font-size: 16px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
        .m-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; padding: 12px; background-color: #000; border-top: 1px solid #222;}
        .m-label { color: #555; font-size: 9px; text-transform: uppercase; margin-bottom: 2px; display:block;}
        .m-value { color: #ddd; font-size: 13px; font-weight: 600; font-family: 'JetBrains Mono', monospace; }

        @media (min-width: 769px) { .mobile-wrapper { display: none !important; } .desktop-view-container { display: block !important; } }
        @media (max-width: 768px) { .desktop-view-container { display: none !important; } .mobile-wrapper { display: block !important; } [data-testid="stPopover"] { display: none !important; } }
        
        div[data-testid="stPopover"] button { background-color: #000000 !important; border: 1px solid #222 !important; color: #444 !important; }
        div[data-testid="stPopover"] { display: flex; justify-content: flex-end; margin-bottom: -45px; z-index: 99; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# DICIONÁRIOS DE COBERTURA
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
    "Varejo": ["AZZA3.SA", "LREN3.SA", "CEAB3.SA", "MGLU3.SA", "BHIA3.SA", "ASAI3.SA"],
    "Bancos": ["ITUB4.SA", "BBDC4.SA", "BBAS3.SA", "SANB11.SA", "B3SA3.SA"],
    "Energia": ["EQTL3.SA", "EGIE3.SA", "TAEE11.SA", "CPLE3.SA"],
    "Saúde": ["RDOR3.SA", "HAPV3.SA", "FLRY3.SA"],
    "Petróleo": ["PETR4.SA", "PRIO3.SA", "CSAN3.SA"],
    "Mineração": ["VALE3.SA", "GGBR4.SA", "CSNA3.SA"]
}

# =========================================================
# FUNÇÕES DE APOIO
# =========================================================
def format_br(val, is_pct=False, moeda_sym=""):
    if pd.isna(val) or (val == 0 and not is_pct): return "-"
    formatted = "{:,.2f}".format(val).replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{moeda_sym} {formatted}" if moeda_sym else (f"{formatted}%" if is_pct else formatted)

@st.cache_data(ttl=60)
def get_data(tickers):
    data_list = []
    for t in tickers:
        try:
            s = yf.Ticker(t)
            h = s.history(period="2y")
            if h.empty: continue
            cur = float(h['Close'].iloc[-1])
            prev = float(h['Close'].iloc[-2])
            
            def get_pct(days):
                try:
                    target = h.index[-1] - timedelta(days=days)
                    idx = h.index.get_indexer([target], method='pad')[0]
                    return ((cur / h['Close'].iloc[idx]) - 1) * 100
                except: return 0.0

            data_list.append({
                "Ticker": t.replace(".SA", ""), "Preço": cur, "Hoje %": ((cur/prev)-1)*100,
                "30D %": get_pct(30), "12M %": get_pct(365),
                "Moeda": "R$", "Original": t
            })
        except: continue
    return pd.DataFrame(data_list)

# =========================================================
# INTERFACE
# =========================================================
st.markdown('<span class="main-title">EQUITY MONITOR</span>', unsafe_allow_html=True)
st.markdown(f'<span class="sub-header">{datetime.now().strftime("%d %b %H:%M")}</span>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["CARTEIRA", "SETORES"])

# --- ABA 1: CARTEIRA ---
with tab1:
    df_c = get_data(list(MINHA_COBERTURA.keys()))
    if not df_c.empty:
        with st.popover("⚙️"):
            sort_col = st.selectbox("Ordenar:", df_c.columns, index=0)
            df_c = df_c.sort_values(by=sort_col, ascending=False)

        # Desktop View
        df_v = pd.DataFrame()
        df_v["Ticker"] = df_c["Ticker"].apply(lambda x: f'<span class="ticker-style">{x}</span>')
        df_v["Rec."] = [MINHA_COBERTURA[t]["Rec"] for t in df_c["Original"]]
        df_v["Alvo"] = [format_br(MINHA_COBERTURA[t]["Alvo"], moeda_sym="R$") for t in df_c["Original"]]
        df_v["Preço"] = df_c.apply(lambda r: format_br(r["Preço"], moeda_sym="R$"), axis=1)
        
        def color_pct(v):
            c = "#00FF95" if v > 0 else "#FF4B4B" if v < 0 else "#555"
            return f'<span style="color:{c}; font-family:\'JetBrains Mono\'">{format_br(v, True)}</span>'

        df_v["Hoje"] = df_c["Hoje %"].apply(color_pct)
        df_v["12M"] = df_c["12M %"].apply(color_pct)
        
        st.markdown(f'<div class="desktop-view-container">{df_v.to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)

        # Mobile View
        m_html = ""
        for _, r in df_c.iterrows():
            cp = "#00FF95" if r['Hoje %'] > 0 else "#FF4B4B"
            m_html += f'<details class="mobile-card"><summary class="m-summary"><div class="m-header-top"><span class="m-ticker">{r["Ticker"]}</span><span class="m-price" style="color:{cp}">R$ {format_br(r["Preço"])}</span></div><div style="font-size:11px;color:#444">Alvo: R$ {format_br(MINHA_COBERTURA[r["Original"]]["Alvo"])}</div></summary><div class="m-grid"><div class="m-item"><span class="m-label">Hoje</span><span class="m-value" style="color:{cp}">{format_br(r["Hoje %"],True)}</span></div><div class="m-item"><span class="m-label">12M</span><span class="m-value">{format_br(r["12M %"],True)}</span></div></div></details>'
        st.markdown(f'<div class="mobile-wrapper">{m_html}</div>', unsafe_allow_html=True)

# --- ABA 2: SETORES ---
with tab2:
    setor_sel = st.selectbox("Escolha o Setor:", list(SETORES_ACOMPANHAMENTO.keys()))
    df_s = get_data(SETORES_ACOMPANHAMENTO[setor_sel])
    
    if not df_s.empty:
        # Desktop
        df_sv = pd.DataFrame()
        df_sv["Ticker"] = df_s["Ticker"].apply(lambda x: f'<span class="ticker-style">{x}</span>')
        df_sv["Preço"] = df_s.apply(lambda r: format_br(r["Preço"], moeda_sym="R$"), axis=1)
        df_sv["Hoje"] = df_s["Hoje %"].apply(color_pct)
        df_sv["30D"] = df_s["30D %"].apply(color_pct)
        df_sv["12M"] = df_s["12M %"].apply(color_pct)
        
        st.markdown(f'<div class="desktop-view-container">{df_sv.to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)

        # Mobile
        ms_html = ""
        for _, r in df_s.iterrows():
            cp = "#00FF95" if r['Hoje %'] > 0 else "#FF4B4B"
            ms_html += f'<details class="mobile-card"><summary class="m-summary"><div class="m-header-top"><span class="m-ticker">{r["Ticker"]}</span><span class="m-price" style="color:{cp}">R$ {format_br(r["Preço"])}</span></div></summary><div class="m-grid"><div class="m-item"><span class="m-label">Hoje</span><span class="m-value" style="color:{cp}">{format_br(r["Hoje %"],True)}</span></div><div class="m-item"><span class="m-label">12M</span><span class="m-value">{format_br(r["12M %"],True)}</span></div></div></details>'
        st.markdown(f'<div class="mobile-wrapper">{ms_html}</div>', unsafe_allow_html=True)

time.sleep(120)
st.rerun()
