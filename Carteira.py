import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time

# Configuração da página
st.set_page_config(page_title="Equity Monitor Pro", layout="wide", page_icon="📈")

# =========================================================
# DESIGN PREMIUM - CSS FORÇADO E RESPONSIVO
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
            margin-bottom: 0px !important;
            line-height: 1 !important;
            display: block !important;
        }
        
        @media (max-width: 768px) { .main-title { font-size: 32px !important; text-align: center; } }

        .sub-header {
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 15px !important;
            color: #444 !important;
            margin-top: 10px !important;
            margin-bottom: 60px !important;
            text-transform: uppercase !important;
            letter-spacing: 5px !important;
            display: block !important;
        }
        
        @media (max-width: 768px) { .sub-header { font-size: 10px !important; text-align: center; } }

        /* ESTILOS MOBILE */
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

        summary.m-summary::-webkit-details-marker { display: none; }
        .m-header-top { display: flex; justify-content: space-between; align-items: center; width: 100%; }
        .m-header-sub { display: flex; justify-content: space-between; align-items: center; width: 100%; font-size: 12px; color: #666; font-family: 'JetBrains Mono', monospace; }
        .m-ticker { font-size: 18px; font-weight: 900; color: #fff; }
        .m-price { font-size: 18px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
        .m-content { padding: 15px; border-top: 1px solid #222; background-color: #000; }
        .m-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        .m-item { display: flex; flex-direction: column; }
        .m-label { color: #555; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
        .m-value { color: #ddd; font-size: 14px; font-weight: 600; font-family: 'JetBrains Mono', monospace; }

        /* AJUSTE TABELA NATIVA STREAMLIT (PC) PARA ALINHAMENTO CENTRAL */
        [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
            text-align: center !important;
        }

        @media (min-width: 769px) { .mobile-wrapper { display: none !important; } }
        @media (max-width: 768px) { .desktop-view-container { display: none !important; } }
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

refresh_interval = 60

def format_br(val, is_pct=False, moeda_sym=""):
    if pd.isna(val) or (val == 0 and not is_pct): return "-"
    formatted = "{:,.2f}".format(val).replace(",", "X").replace(".", ",").replace("X", ".")
    if is_pct: return f"{formatted}%"
    if moeda_sym: return f"{moeda_sym} {formatted}"
    return formatted

def get_stock_data(tickers):
    data_list = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="6y", auto_adjust=True)
            if hist.empty: continue
            hist = hist[hist['Close'] > 0].dropna()
            price_current = float(hist['Close'].iloc[-1])
            price_prev_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else price_current
            info = stock.info
            moeda = info.get('currency', 'BRL') if info else 'BRL'
            simbolo = "$" if moeda == "USD" else "R$" if moeda == "BRL" else moeda
            dados_manuais = MINHA_COBERTURA.get(ticker, {"Rec": "-", "Alvo": 0.0})
            preco_alvo = dados_manuais["Alvo"]
            upside = (preco_alvo / price_current - 1) * 100 if preco_alvo > 0 else 0.0

            def calculate_pct(days_ago=None, is_ytd=False):
                try:
                    target_date = datetime(datetime.now().year, 1, 1) if is_ytd else datetime.now() - timedelta(days=days_ago)
                    target_ts = pd.Timestamp(target_date).tz_localize(hist.index.tz)
                    idx = hist.index.get_indexer([target_ts], method='pad')[0]
                    return ((price_current / float(hist['Close'].iloc[idx])) - 1) * 100
                except: return 0.0

            data_list.append({
                "Ticker": ticker.replace(".SA", ""), "Moeda": simbolo, "Preço": price_current,
                "Recomendação": dados_manuais["Rec"], "Preço-Alvo": preco_alvo,
                "Upside": upside, "Hoje %": ((price_current / price_prev_close) - 1) * 100,
                "30 Dias %": calculate_pct(days_ago=30), "6 Meses %": calculate_pct(days_ago=180),
                "12 Meses %": calculate_pct(days_ago=365), "YTD %": calculate_pct(is_ytd=True),
                "5 Anos %": calculate_pct(days_ago=1825),
                "Vol (MM)": float(info.get('regularMarketVolume', 0)) / 1_000_000 if info else 0,
                "Mkt Cap (MM)": float(info.get('marketCap', 0)) / 1_000_000 if info and info.get('marketCap') else 0
            })
        except: continue
    return pd.DataFrame(data_list)

# =========================================================
# RENDERIZAÇÃO
# =========================================================

st.markdown('<span class="main-title">EQUITY MONITOR</span>', unsafe_allow_html=True)
st.markdown(f'<span class="sub-header">TERMINAL DE DADOS • {datetime.now().strftime("%d %b %Y | %H:%M:%S")} • B3 REAL-TIME</span>', unsafe_allow_html=True)

df = get_stock_data(list(MINHA_COBERTURA.keys()))

if not df.empty:
    # --- VERSÃO PC (Ordenável) ---
    # Para permitir ordenação, usamos st.dataframe com column_config para manter o estilo
    st.markdown('<div class="desktop-view-container">', unsafe_allow_html=True)
    
    # Criamos uma versão formatada para exibição que aceita ordenação
    df_pc = df.copy()
    
    st.dataframe(
        df_pc,
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker"),
            "Preço": st.column_config.NumberColumn("Preço", format="R$ %.2f"),
            "Preço-Alvo": st.column_config.NumberColumn("Alvo", format="R$ %.2f"),
            "Upside": st.column_config.NumberColumn("Upside %", format="%.2f%%"),
            "Hoje %": st.column_config.NumberColumn("Hoje %", format="%.2f%%"),
            "30 Dias %": st.column_config.NumberColumn("30D %", format="%.2f%%"),
            "6 Meses %": st.column_config.NumberColumn("6M %", format="%.2f%%"),
            "12 Meses %": st.column_config.NumberColumn("12M %", format="%.2f%%"),
            "YTD %": st.column_config.NumberColumn("YTD %", format="%.2f%%"),
            "Vol (MM)": st.column_config.NumberColumn("Vol (MM)", format="%.2f"),
        },
        hide_index=True,
        use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # --- VERSÃO MOBILE ---
    mobile_html_cards = ""
    for _, row in df.iterrows():
        color_price = "#00FF95" if row['Hoje %'] > 0 else "#FF4B4B" if row['Hoje %'] < 0 else "#FFFFFF"
        color_upside = "#00FF95" if row['Upside'] > 0 else "#FF4B4B" if row['Upside'] < 0 else "#666"
        
        mobile_html_cards += f"""
        <details class="mobile-card">
            <summary class="m-summary">
                <div class="m-header-top">
                    <span class="m-ticker">{row['Ticker']}</span>
                    <span class="m-price" style="color: {color_price}">{row['Moeda']} {format_br(row['Preço'])}</span>
                </div>
                <div class="m-header-sub">
                    <span>Alvo: {row['Moeda']} {format_br(row['Preço-Alvo'])}</span>
                    <span style="font-size:10px; color:#444;">▼ DETALHES</span>
                </div>
            </summary>
            <div class="m-content">
                <div class="m-grid">
                    <div class="m-item"><span class="m-label">Hoje</span><span class="m-value" style="color:{color_price}">{format_br(row['Hoje %'], is_pct=True)}</span></div>
                    <div class="m-item"><span class="m-label">Upside</span><span class="m-value" style="color:{color_upside}">{format_br(row['Upside'], is_pct=True)}</span></div>
                    <div class="m-item"><span class="m-label">Rec.</span><span class="m-value" style="color:#FFF">{row['Recomendação']}</span></div>
                    <div class="m-item"><span class="m-label">Vol (MM)</span><span class="m-value">{format_br(row['Vol (MM)'])}</span></div>
                    <div class="m-item"><span class="m-label">YTD</span><span class="m-value">{format_br(row['YTD %'], is_pct=True)}</span></div>
                    <div class="m-item"><span class="m-label">12M</span><span class="m-value">{format_br(row['12 Meses %'], is_pct=True)}</span></div>
                </div>
            </div>
        </details>"""

    st.markdown(f'<div class="mobile-wrapper">{mobile_html_cards}</div>', unsafe_allow_html=True)
    
    time.sleep(refresh_interval)
    st.rerun()
