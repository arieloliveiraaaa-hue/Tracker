import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time

# Mantendo configuração original
st.set_page_config(page_title="Monitor de Ações", layout="wide")

# =========================================================
# CSS CUSTOMIZADO (MODERNIZAÇÃO & MOBILE FRIENDLY)
# =========================================================
st.markdown("""
<style>
    /* Importando fonte estilo 'Bloomberg Terminal' / Moderna */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    /* Fundo geral escuro e fontes */
    .stApp {
        background-color: #0e1117;
        font-family: 'Inter', sans-serif;
    }
    
    /* Remove padding excessivo do topo */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Estilização do Grid de Cards */
    .stock-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
        gap: 15px;
        margin-bottom: 30px;
    }

    /* Card individual */
    .stock-card {
        background-color: #1c1c1c;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 15px;
        color: white;
        transition: transform 0.2s;
    }
    .stock-card:hover {
        border-color: #555;
    }

    /* Tipografia dentro do card */
    .card-ticker { font-size: 1.2rem; font-weight: 700; color: #e0e0e0; }
    .card-price { font-size: 1.5rem; font-weight: 600; margin: 5px 0; }
    .card-meta { font-size: 0.85rem; color: #888; display: flex; justify-content: space-between; margin-top: 8px;}
    
    /* Cores de variação */
    .positive { color: #00ff7f; } /* Verde neon */
    .negative { color: #ff4b4b; } /* Vermelho neon */
    .neutral  { color: #b0b0b0; }

    /* Esconde elementos padrão do Streamlit que poluem o visual */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Melhoria visual da tabela */
    [data-testid="stDataFrame"] {
        border: 1px solid #333;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# DADOS (MANTIDOS)
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
# FUNÇÕES (LÓGICA MANTIDA)
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
                "Ticker": ticker.replace(".SA", ""), # Limpeza visual
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
# UI PRINCIPAL
# =========================================================

# Cabeçalho Simples
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("<h2 style='margin:0; padding:0; color:white;'>Monitor de Mercado</h2>", unsafe_allow_html=True)
with c2:
    st.markdown(f"<div style='text-align:right; color:#666; font-size:0.9rem; margin-top:10px;'>Atualizado: {datetime.now().strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)

st.markdown("---")

# Removido input manual da sidebar, usando direto o dict
lista_tickers = list(MINHA_COBERTURA.keys())
df = get_stock_data(lista_tickers)

if not df.empty:
    # --- 1. VISUALIZAÇÃO EM CARDS (MOBILE FRIENDLY) ---
    # Isso resolve o problema de ter que rolar a tabela no celular para ver o básico
    
    html_cards = '<div class="stock-grid">'
    for idx, row in df.iterrows():
        pct_dia = row["Hoje %"]
        color_class = "positive" if pct_dia > 0 else "negative" if pct_dia < 0 else "neutral"
        sinal = "+" if pct_dia > 0 else ""
        
        # Formatação para o card
        preco_fmt = format_br(row["Preço"], moeda_sym=row["Moeda"])
        pct_fmt = f"{sinal}{format_br(pct_dia)}%"
        upside_val = row["Upside"]
        upside_cls = "positive" if upside_val > 0 else "neutral"
        upside_fmt = f"Upside: {format_br(upside_val)}%"
        
        html_cards += f"""
        <div class="stock-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="card-ticker">{row['Ticker']}</span>
                <span style="font-size:0.8rem; background:#333; padding:2px 6px; border-radius:4px;">{row['Recomendação']}</span>
            </div>
            <div class="card-price">{preco_fmt}</div>
            <div style="font-size:1rem; font-weight:500;" class="{color_class}">
                {pct_fmt} <span style="font-size:0.7rem; color:#666;">(Hoje)</span>
            </div>
            <div class="card-meta">
                <span>Alvo: {format_br(row['Preço-Alvo'])}</span>
                <span class="{upside_cls}">{upside_fmt}</span>
            </div>
        </div>
        """
    html_cards += '</div>'
    st.markdown(html_cards, unsafe_allow_html=True)

    # --- 2. TABELA DETALHADA (MODO COMPLETO) ---
    st.markdown("<h5 style='color:#888; margin-top:20px; margin-bottom:10px;'>Análise Detalhada</h5>", unsafe_allow_html=True)

    df_view = df.copy()
    
    # Formatação Visual
    df_view["Preço"] = df.apply(lambda r: format_br(r["Preço"], moeda_sym=r["Moeda"]), axis=1)
    df_view["Preço-Alvo"] = df.apply(lambda r: format_br(r["Preço-Alvo"], moeda_sym=r["Moeda"]), axis=1)
    df_view["Mkt Cap (MM)"] = df.apply(lambda r: format_br(r["Mkt Cap (MM)"], moeda_sym=r["Moeda"]), axis=1)
    
    cols_pct = ["Upside", "Hoje %", "30 Dias %", "6 Meses %", "12 Meses %", "YTD %", "5 Anos %"]
    for col in cols_pct:
        df_view[col] = df[col].apply(lambda x: format_br(x, is_pct=True))
    df_view["Vol (MM)"] = df["Vol (MM)"].apply(lambda x: format_br(x))

    # Lógica de Cores da Tabela
    def style_rows(row):
        styles = ['background-color: #161a24'] * len(row) # Fundo levemente diferente para linhas
        for col_name in cols_pct:
            val = df.loc[row.name, col_name]
            idx = df_view.columns.get_loc(col_name)
            if col_name == "Upside":
                if val > 20: styles[idx] = 'color: #00ff7f; font-weight:bold' # Verde
                elif val < 0: styles[idx] = 'color: #ff4b4b' # Vermelho
            else:
                if val > 0.01: styles[idx] = 'color: #00ff7f'
                elif val < -0.01: styles[idx] = 'color: #ff4b4b'
        return styles

    df_final = df_view.style.apply(style_rows, axis=1)

    st.dataframe(
        df_final,
        use_container_width=True,
        hide_index=True,
        column_order=(
            "Ticker", "Preço", "Recomendação", "Upside",
            "Hoje %", "YTD %", "12 Meses %", "Vol (MM)", "Mkt Cap (MM)"
        ),
        height=(len(df) + 1) * 38
    )
    
    time.sleep(refresh_interval)
    st.rerun()
