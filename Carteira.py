import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time

# Configuração da página
st.set_page_config(page_title="Equity Monitor Pro", layout="wide", page_icon="📈")

# =========================================================
# DESIGN PREMIUM DARK (ELEGANT & MODERN)
# =========================================================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        /* Fundo total da aplicação */
        .stApp {
            background-color: #0A0A0B;
        }

        /* Esconder elementos nativos que poluem o visual */
        header, footer, #MainMenu {visibility: hidden;}

        .block-container {
            padding: 2rem 3rem;
            max-width: 100%;
        }

        /* Título Estilizado */
        .main-title {
            font-family: 'Inter', sans-serif;
            font-size: 32px;
            font-weight: 700;
            color: #FFFFFF;
            letter-spacing: -1px;
            margin-bottom: 0px;
        }

        .sub-header {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: #4A4A4E;
            margin-bottom: 30px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        /* REMOÇÃO DA FAIXA BRANCA E ESTILIZAÇÃO DA TABELA */
        /* Forçamos o container do DataFrame a ser transparente ou preto */
        div[data-testid="stDataFrame"] {
            background-color: #0A0A0B !important;
            border: 1px solid #1E1E21;
            border-radius: 8px;
            overflow: hidden;
        }

        /* Customização via seletor de dados para garantir que não haja fundo branco */
        div[data-testid="stTable"] {
            background-color: #0A0A0B !important;
        }

        /* Ajuste de scrollbar para modo dark */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #0A0A0B;
        }
        ::-webkit-scrollbar-thumb {
            background: #262629;
            border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #333336;
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
# RENDERIZAÇÃO E ESTILIZAÇÃO DE TABELA
# =========================================================

st.markdown('<p class="main-title">Equity Monitor</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-header">Terminal de Dados • {datetime.now().strftime("%d %b %Y | %H:%M:%S")} • Real-time Stream</p>', unsafe_allow_html=True)

lista_tickers = list(MINHA_COBERTURA.keys())
df = get_stock_data(lista_tickers)

if not df.empty:
    df_view = df.copy()
    
    # Formatação de valores
    df_view["Preço"] = df.apply(lambda r: format_br(r["Preço"], moeda_sym=r["Moeda"]), axis=1)
    df_view["Preço-Alvo"] = df.apply(lambda r: format_br(r["Preço-Alvo"], moeda_sym=r["Moeda"]), axis=1)
    df_view["Mkt Cap (MM)"] = df.apply(lambda r: format_br(r["Mkt Cap (MM)"], moeda_sym=r["Moeda"]), axis=1)
    
    cols_pct = ["Upside", "Hoje %", "30 Dias %", "6 Meses %", "12 Meses %", "YTD %", "5 Anos %"]
    for col in cols_pct:
        df_view[col] = df[col].apply(lambda x: format_br(x, is_pct=True))
    df_view["Vol (MM)"] = df["Vol (MM)"].apply(lambda x: format_br(x))

    # ESTILIZAÇÃO DAS LINHAS (Zebra Striping e Cores)
    def style_rows(row):
        # Alternância de cores de fundo (Cinza escuro e Preto)
        bg_color = '#131316' if row.name % 2 == 0 else '#0A0A0B'
        
        # Estilo base
        base = f'background-color: {bg_color}; color: #D1D1D1; font-family: "JetBrains Mono", monospace; font-size: 13px;'
        styles = [base] * len(row)
        
        for col_name in cols_pct:
            val = df.loc[row.name, col_name]
            idx = df_view.columns.get_loc(col_name)
            
            if val > 0.001:
                color = "#00E676"  # Verde esmeralda moderno
            elif val < -0.001:
                color = "#FF5252"  # Vermelho suave moderno
            else:
                color = "#888888"
            
            styles[idx] = f'background-color: {bg_color}; color: {color}; font-family: "JetBrains Mono", monospace; font-size: 13px; font-weight: 500;'
            
        return styles

    # Aplicando o estilo
    df_styled = df_view.style.apply(style_rows, axis=1)

    # Configuração dos headers
    df_styled.set_table_styles([
        {'selector': 'th', 'props': [
            ('background-color', '#0A0A0B'),
            ('color', '#5F5F64'),
            ('font-family', 'Inter, sans-serif'),
            ('font-weight', '600'),
            ('font-size', '11px'),
            ('text-transform', 'uppercase'),
            ('letter-spacing', '1px'),
            ('border-bottom', '1px solid #1E1E21'),
            ('padding', '15px 10px')
        ]},
        {'selector': 'td', 'props': [('padding', '12px 10px')]}
    ])

    st.dataframe(
        df_styled,
        use_container_width=True,
        hide_index=True,
        column_order=(
            "Ticker", "Preço", "Recomendação", "Preço-Alvo", "Upside",
            "Hoje %", "30 Dias %", "6 Meses %", "12 Meses %", "YTD %", "5 Anos %",
            "Vol (MM)", "Mkt Cap (MM)"
        ),
        height=(len(df) + 1) * 48
    )
    
    time.sleep(refresh_interval)
    st.rerun()
