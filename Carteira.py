import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time

# Configuração da página
st.set_page_config(page_title="Equity Monitor Pro", layout="wide", page_icon="📈")

# =========================================================
# DESIGN PREMIUM - RESTAURADO E INTEGRAL
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

        /* --- ESTILOS DA TABELA PC (RESTAURADOS) --- */
        .desktop-view-container table {
            width: 100% !important;
            border-collapse: collapse !important;
            background-color: #000000 !important;
            border: none !important;
            margin-top: 20px;
        }

        .desktop-view-container th {
            background-color: #000000 !important;
            color: #FFFFFF !important;
            font-size: 14px !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 1.5px !important;
            padding: 25px 15px !important;
            text-align: center !important;
            border-bottom: 2px solid #333 !important;
            font-family: 'Inter', sans-serif !important;
            cursor: pointer;
        }

        .desktop-view-container td {
            padding: 22px 15px !important;
            border-bottom: 1px solid #111 !important;
            font-size: 16px !important;
            background-color: #000000 !important;
            color: #D1D1D1 !important;
            font-family: 'Inter', sans-serif !important;
            text-align: center !important;
        }

        .desktop-view-container tr:nth-child(even) td { background-color: #050505 !important; }
        
        .ticker-style { font-weight: 900 !important; color: #FFFFFF !important; font-size: 18px !important; }
        .price-target-style { font-weight: 800 !important; color: #FFFFFF !important; font-family: 'JetBrains Mono', monospace !important; }

        /* --- ESTILOS MOBILE --- */
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

        /* CONTROLE DE VISIBILIDADE RIGOROSO */
        @media (min-width: 769px) {
            .mobile-wrapper { display: none !important; }
            .desktop-view-container { display: block !important; }
        }

        @media (max-width: 768px) {
            .desktop-view-container { display: none !important; }
            .mobile-wrapper { display: block !important; }
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

# Inicialização do estado de ordenação
if 'sort_col' not in st.session_state:
    st.session_state.sort_col = 'Ticker'
    st.session_state.sort_ascending = True

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
    
    # --- LOGICA DE ORDENAÇÃO (PC) ---
    cols = st.columns(len(df.columns))
    # Para manter o layout intacto, usamos botões invisíveis ou pequenos seletores para ordenar sem quebrar o visual
    with st.expander("⚙️ ORDENAR TABELA"):
        sort_col = st.selectbox("Ordenar por:", df.columns, index=0)
        sort_order = st.radio("Ordem:", ["Crescente", "Decrescente"], horizontal=True)
        df = df.sort_values(by=sort_col, ascending=(sort_order == "Crescente"))

    # --- VERSÃO PC (HTML ORIGINAL RESTAURADO) ---
    df_view = pd.DataFrame()
    df_view["Ticker"] = df["Ticker"].apply(lambda x: f'<span class="ticker-style">{x}</span>')
    df_view["Preço"] = df.apply(lambda r: f'<span>{format_br(r["Preço"], moeda_sym=r["Moeda"])}</span>', axis=1)
    df_view["Recomendação"] = df["Recomendação"]
    df_view["Preço-Alvo"] = df.apply(lambda r: f'<span class="price-target-style">{format_br(r["Preço-Alvo"], moeda_sym=r["Moeda"])}</span>', axis=1)

    def color_pct(val, is_upside=False):
        color = "#00FF95" if val > 0.001 else "#FF4B4B" if val < -0.001 else "#555"
        weight = "700" if is_upside else "500"
        return f'<span style="color: {color}; font-weight: {weight}; font-family: \'JetBrains Mono\';">{format_br(val, is_pct=True)}</span>'

    df_view["Upside"] = df["Upside"].apply(lambda x: color_pct(x, True))
    df_view["Hoje %"] = df["Hoje %"].apply(color_pct)
    df_view["30 Dias %"] = df["30 Dias %"].apply(color_pct)
    df_view["6 Meses %"] = df["6 Meses %"].apply(color_pct)
    df_view["12 Meses %"] = df["12 Meses %"].apply(color_pct)
    df_view["YTD %"] = df["YTD %"].apply(color_pct)
    df_view["5 Anos %"] = df["5 Anos %"].apply(color_pct)
    df_view["Vol (MM)"] = df["Vol (MM)"].apply(lambda x: format_br(x))
    df_view["Mkt Cap (MM)"] = df.apply(lambda r: format_br(r["Mkt Cap (MM)"], moeda_sym=r["Moeda"]), axis=1)

    html_table = df_view.to_html(escape=False, index=False)
    st.markdown(f'<div class="desktop-view-container">{html_table}</div>', unsafe_allow_html=True)

    # --- VERSÃO MOBILE (CARDS COM COR DINÂMICA NO PREÇO) ---
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
    
    time.sleep(10) # Reduzi para 10s para teste mais rápido, mude para 60 se preferir
    st.rerun()
