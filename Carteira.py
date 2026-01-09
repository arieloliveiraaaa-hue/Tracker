import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="Monitor de Ações", layout="wide")

# =========================================================
# ESPAÇO PARA MANUTENÇÃO MANUAL DE RECOMENDAÇÕES
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
# =========================================================

refresh_interval = 60

# =========================================================
# VISUAL (dark + clean + mobile friendly)
# =========================================================
st.markdown(
    """
    <style>
      :root{
        --bg:#070A0F;
        --panel:#0B1220;
        --panel2:#0F172A;
        --text:#E5E7EB;
        --muted:#9CA3AF;
        --border:#1F2937;
      }

      [data-testid="stAppViewContainer"] { background: var(--bg); }
      [data-testid="stHeader"] { background: rgba(0,0,0,0); }
      [data-testid="stSidebar"] { display: none; } /* remove sidebar */
      .block-container { padding-top: 1.25rem; padding-bottom: 2rem; max-width: 1400px; }

      /* Typography */
      h1,h2,h3,h4,h5,h6,p,span,div { color: var(--text); }
      .stCaption, small { color: var(--muted) !important; }

      /* Header card */
      .top-card{
        background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 16px 18px;
        margin-bottom: 14px;
      }
      .top-title{
        font-size: 26px;
        font-weight: 750;
        margin: 0;
        letter-spacing: 0.2px;
      }
      .top-sub{
        margin: 6px 0 0 0;
        font-size: 13px;
        color: var(--muted);
      }

      /* Mobile padding + font */
      @media (max-width: 768px){
        .block-container { padding-left: 0.75rem; padding-right: 0.75rem; }
        .top-title{ font-size: 22px; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

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
                except:
                    return 0.0

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
        except:
            continue
    return pd.DataFrame(data_list)

# Top header (clean, investment-like)
st.markdown(
    f"""
    <div class="top-card">
      <div class="top-title">Monitor de ações</div>
      <div class="top-sub">Atualização automática: {datetime.now().strftime('%H:%M:%S')}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sem edição de ticker (remove sidebar)
lista_tickers = list(MINHA_COBERTURA.keys())

df = get_stock_data(lista_tickers)

if not df.empty:
    df_view = df.copy()

    df_view["Preço"] = df.apply(lambda r: format_br(r["Preço"], moeda_sym=r["Moeda"]), axis=1)
    df_view["Preço-Alvo"] = df.apply(lambda r: format_br(r["Preço-Alvo"], moeda_sym=r["Moeda"]), axis=1)
    df_view["Mkt Cap (MM)"] = df.apply(lambda r: format_br(r["Mkt Cap (MM)"], moeda_sym=r["Moeda"]), axis=1)

    cols_pct = ["Upside", "Hoje %", "30 Dias %", "6 Meses %", "12 Meses %", "YTD %", "5 Anos %"]
    for col in cols_pct:
        df_view[col] = df[col].apply(lambda x: format_br(x, is_pct=True))
    df_view["Vol (MM)"] = df["Vol (MM)"].apply(lambda x: format_br(x))

    def style_rows(row):
        styles = [''] * len(row)
        for col_name in cols_pct:
            val = df.loc[row.name, col_name]
            idx = df_view.columns.get_loc(col_name)
            if col_name == "Upside":
                if val > 20: styles[idx] = 'color: #00ff00'
                elif val < 0: styles[idx] = 'color: #ff4b4b'
            else:
                if val > 0.01: styles[idx] = 'color: #00ff00'
                elif val < -0.01: styles[idx] = 'color: #ff4b4b'
        return styles

    base_table_styles = [
        {"selector": "th", "props": [("background-color", "#0F172A"), ("color", "#9CA3AF"),
                                    ("border-bottom", "1px solid #1F2937"), ("font-weight", "600")]},
        {"selector": "td", "props": [("background-color", "#0B1220"), ("color", "#E5E7EB"),
                                    ("border-bottom", "1px solid #111827")]},
    ]

    df_final = (
        df_view.style
        .apply(style_rows, axis=1)
        .set_table_styles(base_table_styles)
        .set_properties(**{"border-color": "#1F2937"})
    )

    st.dataframe(
        df_final,
        use_container_width=True,
        hide_index=True,
        column_order=(
            "Ticker", "Preço", "Recomendação", "Preço-Alvo", "Upside",
            "Hoje %", "30 Dias %", "6 Meses %", "12 Meses %", "YTD %", "5 Anos %",
            "Vol (MM)", "Mkt Cap (MM)"
        ),
        height=(len(df) + 1) * 36
    )

    time.sleep(refresh_interval)
    st.rerun()
