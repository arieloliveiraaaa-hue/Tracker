import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time

# Configuração da página
st.set_page_config(page_title="Equity Monitor Pro", layout="wide", page_icon="📈")

# =========================================================
# DESIGN PREMIUM - CSS REFINADO (TÍTULOS E CONTRASTE)
# =========================================================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=JetBrains+Mono:wght@500;700&display=swap');

        /* Fundo da Página */
        .stApp {
            background-color: #000000;
        }

        header, footer, #MainMenu {visibility: hidden;}

        /* Container Principal */
        .block-container {
            padding: 3rem 5rem !important;
        }

        /* TÍTULO PRINCIPAL - Aumentado e com mais peso */
        .main-title {
            font-family: 'Inter', sans-serif;
            font-size: 64px; /* Aumentado para destaque total */
            font-weight: 900;
            color: #FFFFFF;
            letter-spacing: -3px;
            margin-bottom: 0px;
            line-height: 1.1;
        }

        /* TERMINAL DE DADOS - Mantido menor para contraste de hierarquia */
        .sub-header {
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            color: #555;
            margin-top: 5px;
            margin-bottom: 50px;
            text-transform: uppercase;
            letter-spacing: 4px;
        }

        /* ESTILIZAÇÃO DA TABELA */
        table {
            width: 100%;
            border-collapse: collapse;
            background-color: #000000 !important;
            color: #D1D1D1;
            font-family: 'Inter', sans-serif;
            border: none !important;
        }

        /* TÍTULOS DAS COLUNAS - Corrigido para não ficar apagado */
        th {
            background-color: #000000 !important;
            color: #EEEEEE !important; /* Branco com alto contraste */
            font-size: 13px !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            padding: 20px 15px !important;
            text-align: right !important;
            border-bottom: 2px solid #222 !important;
        }

        th:first-child, td:first-child { text-align: left !important; }

        td {
            padding: 20px 15px !important;
            border-bottom: 1px solid #111 !important;
            font-size: 16px;
            background-color: #000000 !important;
        }

        /* Efeito de Zebra sutil */
        tr:nth-child(even) td {
            background-color: #070707 !important;
        }

        /* DESTAQUES */
        .ticker-style {
            font-weight: 800 !important;
            color: #FFFFFF !important;
            font-size: 18px !important;
        }

        .price-target-style {
            font-weight: 700 !important;
            color: #FFFFFF !important; /* Mais destaque para o Alvo */
            font-family: 'JetBrains Mono', monospace;
        }

        .price-current-style {
            font-family: 'JetBrains Mono', monospace;
            font-weight: 500;
            color: #CCC;
        }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# LÓGICA DE DADOS (MANTIDA 100% ORIGINAL)
# =========================================================
MINHA_COBERTURA = {
    "TOTS3.SA": {"Rec": "Compra", "Alvo": 48.00},
    "VIVT3.SA": {"Rec": "Compra", "Alvo": 38.00},
    "CPLE3.SA": {"Rec": "Neutro", "Alvo": 11.00},
    "AXIA6": {"Rec": "Compra", "Alvo": 59.00},
    "ENGI3": {"Rec": "Compra", "Alvo": 46.00},
    "TAEE11": {"Rec": "Compra", "Alvo": 34.00},
    "EQTL3": {"Rec": "Compra", "Alvo": 35.00},
    "RDOR3": {"Rec": "Compra", "Alvo": 34.00},
    "HAPV3": {"Rec": "Compra", "Alvo": 64.80},
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
            moeda = info.get('currency', 'BRL')
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
                "Ticker": ticker,
                "Moeda": simbolo,
                "Preço": price_current,
                "Recomendação": dados_manuais["Rec"],
                "Preço-Alvo": preco_alvo,
                "Upside": upside,
                "Hoje %": ((price_current / price_prev_close) - 1) * 100,
                "30 Dias %": calculate_pct(days_ago=30),
                "6 Meses %": calculate_pct(days_ago=180),
                "12 Meses %": calculate_pct(days_ago=365),
                "YTD %": calculate_pct(is_ytd=True),
                "5 Anos %": calculate_pct(days_ago=1825),
                "Vol (MM)": float(info.get('regularMarketVolume', 0)) / 1_000_000,
                "Mkt Cap (MM)": float(info.get('marketCap', 0)) / 1_000_000 if info.get('marketCap') else 0
            })
        except: continue
    return pd.DataFrame(data_list)

# =========================================================
# RENDERIZAÇÃO
# =========================================================

st.markdown('<p class="main-title">EQUITY MONITOR</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-header">Terminal de Dados • {datetime.now().strftime("%d %b %Y | %H:%M:%S")} • B3 Real-time Stream</p>', unsafe_allow_html=True)

lista_tickers = list(MINHA_COBERTURA.keys())
df = get_stock_data(lista_tickers)

if not df.empty:
    df_view = pd.DataFrame()
    
    # Destaques visuais via HTML
    df_view["Ticker"] = df["Ticker"].apply(lambda x: f'<span class="ticker-style">{x}</span>')
    df_view["Preço"] = df.apply(lambda r: f'<span class="price-current-style">{format_br(r["Preço"], moeda_sym=r["Moeda"])}</span>', axis=1)
    df_view["Recomendação"] = df["Recomendação"]
    df_view["Preço-Alvo"] = df.apply(lambda r: f'<span class="price-target-style">{format_br(r["Preço-Alvo"], moeda_sym=r["Moeda"])}</span>', axis=1)

    # Lógica de cores
    def color_pct(val, is_upside=False):
        color = "#00FF95" if val > 0.001 else "#FF4B4B" if val < -0.001 else "#666"
        weight = "700" if (is_upside or abs(val) > 10) else "400"
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

    # Renderização final
    st.write(df_view.to_html(escape=False, index=False), unsafe_allow_html=True)
    
    time.sleep(refresh_interval)
    st.rerun()
