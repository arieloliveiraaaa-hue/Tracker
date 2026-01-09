import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time

# Configuração da página
st.set_page_config(page_title="Monitor Pro", layout="wide", page_icon="📈")

# =========================================================
# DESIGN MODERNO / PROFESSIONAL / DARK MODE
# =========================================================
st.markdown("""
    <style>
        /* Importando Fontes Modernas (Inter para texto, Roboto Mono para números) */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Roboto+Mono:wght@400;700&display=swap');

        /* === CONFIGURAÇÕES GERAIS DA PÁGINA === */
        .stApp {
            background-color: #050505; /* Preto quase absoluto */
            color: #E0E0E0;
        }

        /* Remove a barra de decoração superior do Streamlit */
        header {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* Ajuste de Espaçamento */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 1rem;
            padding-left: 2rem;
            padding-right: 2rem;
            max-width: 100%;
        }

        /* === TIPOGRAFIA === */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }
        
        /* === CABEÇALHO PERSONALIZADO === */
        .header-container {
            border-bottom: 1px solid #333;
            padding-bottom: 15px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
        }
        
        .header-title {
            font-size: 28px;
            font-weight: 700;
            background: -webkit-linear-gradient(45deg, #ffffff, #a0a0a0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.5px;
            margin: 0;
        }
        
        .header-meta {
            font-family: 'Roboto Mono', monospace;
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }

        /* === ESTILIZAÇÃO DA TABELA (DATAFRAME) === */
        /* Força a tabela a ter fundo escuro e remove bordas brancas */
        .stDataFrame {
            background-color: transparent !important;
        }
        
        /* Ajuste fino nos headers da tabela (se visíveis via CSS nativo) */
        div[data-testid="stVerticalBlock"] > div {
            background-color: transparent;
        }

        /* Barra de progresso ou loading */
        .stProgress > div > div > div > div {
            background-color: #333;
        }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# DADOS (LÓGICA INTACTA)
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
# FUNÇÕES DE CÁLCULO E FORMATAÇÃO (INTACTAS)
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
# RENDERIZAÇÃO
# =========================================================

# HTML personalizado para o Título (Mais limpo e moderno)
st.markdown(f"""
    <div class="header-container">
        <div>
            <h1 class="header-title">EQUITY MONITOR</h1>
        </div>
        <div class="header-meta">
            LIVE DATA • {datetime.now().strftime('%H:%M:%S')} • B3/NYSE
        </div>
    </div>
""", unsafe_allow_html=True)

lista_tickers = list(MINHA_COBERTURA.keys())
df = get_stock_data(lista_tickers)

if not df.empty:
    df_view = df.copy()
    
    # Aplicação da formatação (Strings)
    df_view["Preço"] = df.apply(lambda r: format_br(r["Preço"], moeda_sym=r["Moeda"]), axis=1)
    df_view["Preço-Alvo"] = df.apply(lambda r: format_br(r["Preço-Alvo"], moeda_sym=r["Moeda"]), axis=1)
    df_view["Mkt Cap (MM)"] = df.apply(lambda r: format_br(r["Mkt Cap (MM)"], moeda_sym=r["Moeda"]), axis=1)
    
    cols_pct = ["Upside", "Hoje %", "30 Dias %", "6 Meses %", "12 Meses %", "YTD %", "5 Anos %"]
    for col in cols_pct:
        df_view[col] = df[col].apply(lambda x: format_br(x, is_pct=True))
    
    df_view["Vol (MM)"] = df["Vol (MM)"].apply(lambda x: format_br(x))

    # ESTILIZAÇÃO AVANÇADA DO DATAFRAME (PANDAS STYLER)
    # Aqui definimos as cores de fundo, bordas e fontes da tabela
    def style_rows(row):
        # Cor padrão para todas as células (Cinza muito escuro/Preto) e fonte monospace
        base_style = 'background-color: #111111; color: #e0e0e0; font-family: "Roboto Mono", monospace; border-bottom: 1px solid #222;'
        styles = [base_style] * len(row)
        
        for col_name in cols_pct:
            val = df.loc[row.name, col_name]
            idx = df_view.columns.get_loc(col_name)
            
            # Lógica de Cores (Verde Neon / Vermelho Neon / Cinza)
            color_style = base_style
            if col_name == "Upside":
                if val > 20: 
                    color_style += 'color: #00FF99; font-weight: 700;' # Verde Neon Forte
                elif val < 0: 
                    color_style += 'color: #FF4B4B; font-weight: 700;' # Vermelho Forte
                else:
                    color_style += 'color: #aaaaaa;'
            else:
                if val > 0.01: 
                    color_style += 'color: #00FF99;'
                elif val < -0.01: 
                    color_style += 'color: #FF4B4B;'
                else:
                    color_style += 'color: #aaaaaa;'
            
            styles[idx] = color_style
            
        return styles

    # Aplicando headers customizados via Pandas Style properties
    df_final = df_view.style.apply(style_rows, axis=1)
    
    # Customização global da tabela via Pandas Styler
    df_final.set_properties(**{
        'text-align': 'right',
        'padding': '10px'
    })
    
    # Customização do Hover (passar o mouse)
    df_final.set_table_styles([
        {'selector': 'th', 'props': [
            ('background-color', '#000000'),
            ('color', '#888'),
            ('font-family', 'Inter, sans-serif'),
            ('font-size', '12px'),
            ('text-transform', 'uppercase'),
            ('border-bottom', '2px solid #333'),
            ('text-align', 'right')
        ]},
        {'selector': 'tr:hover', 'props': [('background-color', '#1a1a1a !important')]} 
    ])

    st.dataframe(
        df_final,
        use_container_width=True,
        hide_index=True,
        column_order=(
            "Ticker", "Preço", "Recomendação", "Preço-Alvo", "Upside",
            "Hoje %", "30 Dias %", "6 Meses %", "12 Meses %", "YTD %", "5 Anos %",
            "Vol (MM)", "Mkt Cap (MM)"
        ),
        height=(len(df) + 1) * 45 # Altura levemente maior para melhor respiro
    )
    
    time.sleep(refresh_interval)
    st.rerun()
