import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time

# Configuração da página (Wide layout)
st.set_page_config(page_title="Monitor Pro", layout="wide", page_icon="📈")

# =========================================================
# ESTILIZAÇÃO CSS (VISUAL DARK / CLEAN / INVESTIMENTO)
# =========================================================
st.markdown("""
    <style>
        /* Fundo Preto Absoluto */
        .stApp {
            background-color: #000000;
        }
        
        /* Ajuste do Header para sumir ou ficar transparente */
        header[data-testid="stHeader"] {
            background-color: transparent;
            visibility: hidden;
        }
        
        /* Títulos e Textos */
        h1, h2, h3, p, div, span {
            color: #E0E0E0 !important;
            font-family: 'Roboto', sans-serif;
        }
        
        /* Estilização da Tabela (DataFrame) */
        .stDataFrame {
            border: 1px solid #333;
        }
        
        /* Remove padding excessivo do topo */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        
        /* Customização do título principal */
        .main-header {
            font-size: 24px;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 5px;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .update-tag {
            font-size: 14px;
            color: #666;
            font-family: monospace;
        }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# DADOS E CONFIGURAÇÕES
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

# =========================================================
# FUNÇÕES (LÓGICA MANTIDA ORIGINAL)
# =========================================================
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
# EXECUÇÃO PRINCIPAL
# =========================================================

# Cabeçalho customizado HTML
st.markdown(f"""
    <div class="main-header">
        <span>MARKET MONITOR</span>
        <span class="update-tag">UPDATED: {datetime.now().strftime('%H:%M:%S')}</span>
    </div>
""", unsafe_allow_html=True)

# Tickers direto da constante (Sem Sidebar)
lista_tickers = list(MINHA_COBERTURA.keys())

df = get_stock_data(lista_tickers)

if not df.empty:
    df_view = df.copy()
    
    # Formatação (Mantida)
    df_view["Preço"] = df.apply(lambda r: format_br(r["Preço"], moeda_sym=r["Moeda"]), axis=1)
    df_view["Preço-Alvo"] = df.apply(lambda r: format_br(r["Preço-Alvo"], moeda_sym=r["Moeda"]), axis=1)
    df_view["Mkt Cap (MM)"] = df.apply(lambda r: format_br(r["Mkt Cap (MM)"], moeda_sym=r["Moeda"]), axis=1)
    
    cols_pct = ["Upside", "Hoje %", "30 Dias %", "6 Meses %", "12 Meses %", "YTD %", "5 Anos %"]
    for col in cols_pct:
        df_view[col] = df[col].apply(lambda x: format_br(x, is_pct=True))
    
    df_view["Vol (MM)"] = df["Vol (MM)"].apply(lambda x: format_br(x))

    # Estilização Cores (Mantida)
    def style_rows(row):
        styles = ['background-color: #000000'] * len(row) # Fundo preto nas células
        for col_name in cols_pct:
            val = df.loc[row.name, col_name]
            idx = df_view.columns.get_loc(col_name)
            # Mantendo as cores neon originais que funcionam bem no preto
            if col_name == "Upside":
                if val > 20: styles[idx] = 'color: #00ff00; font-weight: bold;'
                elif val < 0: styles[idx] = 'color: #ff4b4b; font-weight: bold;'
            else:
                if val > 0.01: styles[idx] = 'color: #00ff00;'
                elif val < -0.01: styles[idx] = 'color: #ff4b4b;'
        return styles

    df_final = df_view.style.apply(style_rows, axis=1)

    st.dataframe(
        df_final,
        use_container_width=True,
        hide_index=True,
        column_order=(
            "Ticker", "Preço", "Recomendação", "Preço-Alvo", "Upside",
            "Hoje %", "30 Dias %", "6 Meses %", "12 Meses %", "YTD %", "5 Anos %",
            "Vol (MM)", "Mkt Cap (MM)"
        ),
        height=(len(df) + 1) * 35 + 3 # Ajuste fino da altura
    )
    
    time.sleep(refresh_interval)
    st.rerun()
