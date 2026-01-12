import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time

# Configuração da página
st.set_page_config(page_title="Equity Monitor Pro", layout="wide", page_icon="📈")

# =========================================================
# DESIGN PREMIUM - CSS FORÇADO E RESPONSIVO (COM ACCORDION)
# =========================================================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=JetBrains+Mono:wght@500;700&display=swap');

        /* Fundo Total Negro */
        .stApp {
            background-color: #000000 !important;
        }

        header, footer, #MainMenu {visibility: hidden;}

        /* Container Principal */
        .block-container {
            padding: 3rem 5rem !important;
        }
        
        @media (max-width: 768px) {
            .block-container { padding: 1rem 0.5rem !important; }
        }

        /* TÍTULO PRINCIPAL */
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
        
        @media (max-width: 768px) {
            .main-title { font-size: 32px !important; letter-spacing: -2px !important; text-align: center; }
        }

        /* TERMINAL DE DADOS */
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
        
        @media (max-width: 768px) {
            .sub-header { font-size: 10px !important; margin-bottom: 20px !important; letter-spacing: 1px !important; text-align: center; }
        }

        /* =========================================================================
           ESTILOS DA VERSÃO DESKTOP (TABELA) - INTACTO
           ========================================================================= */
        table {
            width: 100% !important;
            border-collapse: collapse !important;
            background-color: #000000 !important;
            border: none !important;
        }

        th {
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
        }

        td {
            padding: 22px 15px !important;
            border-bottom: 1px solid #111 !important;
            font-size: 16px !important;
            background-color: #000000 !important;
            color: #D1D1D1 !important;
            font-family: 'Inter', sans-serif !important;
            text-align: center !important;
        }

        tr:nth-child(even) td { background-color: #050505 !important; }

        .ticker-style { font-weight: 900 !important; color: #FFFFFF !important; font-size: 18px !important; }
        .price-target-style { font-weight: 800 !important; color: #FFFFFF !important; font-family: 'JetBrains Mono', monospace !important; }

        /* =========================================================================
           ESTILOS DA VERSÃO MOBILE (ACCORDION/MINIMIZADO)
           ========================================================================= */
        
        /* O container do accordion */
        details.mobile-card {
            background-color: #0a0a0a;
            border: 1px solid #222;
            border-radius: 8px;
            margin-bottom: 10px;
            overflow: hidden;
            font-family: 'Inter', sans-serif;
            transition: all 0.3s ease;
        }

        /* O cabeçalho visível (Resumo) */
        summary.m-summary {
            padding: 15px;
            cursor: pointer;
            list-style: none; /* Remove a seta padrão feia */
            display: flex;
            flex-direction: column;
            gap: 5px;
            background-color: #0e0e0e;
        }

        /* Remove a seta padrão no Chrome/Safari */
        summary.m-summary::-webkit-details-marker {
            display: none;
        }

        .m-header-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 100%;
        }

        .m-header-sub {
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 100%;
            font-size: 12px;
            color: #666;
            font-family: 'JetBrains Mono', monospace;
        }

        .m-ticker { font-size: 18px; font-weight: 900; color: #fff; }
        .m-price { font-size: 18px; font-weight: 700; color: #fff; font-family: 'JetBrains Mono', monospace; }
        
        /* Área expandida */
        .m-content {
            padding: 15px;
            border-top: 1px solid #222;
            background-color: #000;
        }

        .m-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        
        .m-item { display: flex; flex-direction: column; }
        .m-label { color: #555; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
        .m-value { color: #ddd; font-size: 14px; font-weight: 600; font-family: 'JetBrains Mono', monospace; }

        /* Indicador visual de abrir/fechar (opcional, um pequeno + ou seta customizada via CSS se quisesse, mas deixei limpo) */

        /* =========================================================================
           CONTROLE DE VISIBILIDADE
           ========================================================================= */
        @media (min-width: 769px) {
            .mobile-view-container { display: none !important; }
            .desktop-view-container { display: block !important; }
        }

        @media (max-width: 768px) {
            .mobile-view-container { display: block !important; }
            .desktop-view-container { display: none !important; }
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

            ticker_visual = ticker.replace(".SA", "")

            data_list.append({
                "Ticker": ticker_visual, 
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
                "Vol (MM)": float(info.get('regularMarketVolume', 0)) / 1_000_000 if info else 0,
                "Mkt Cap (MM)": float(info.get('marketCap', 0)) / 1_000_000 if info and info.get('marketCap') else 0
            })
        except Exception:
            continue
    return pd.DataFrame(data_list)

# =========================================================
# RENDERIZAÇÃO FINAL
# =========================================================

# Título
st.markdown('<span class="main-title">EQUITY MONITOR</span>', unsafe_allow_html=True)
st.markdown(f'<span class="sub-header">TERMINAL DE DADOS • {datetime.now().strftime("%d %b %Y | %H:%M:%S")} • B3 REAL-TIME</span>', unsafe_allow_html=True)

lista_tickers = list(MINHA_COBERTURA.keys())
df = get_stock_data(lista_tickers)

if not df.empty:
    
    # -----------------------------------------------------
    # VERSÃO DESKTOP
    # -----------------------------------------------------
    df_desktop = pd.DataFrame()
    df_desktop["Ticker"] = df["Ticker"].apply(lambda x: f'<span class="ticker-style">{x}</span>')
    df_desktop["Preço"] = df.apply(lambda r: f'<span>{format_br(r["Preço"], moeda_sym=r["Moeda"])}</span>', axis=1)
    df_desktop["Recomendação"] = df["Recomendação"]
    df_desktop["Preço-Alvo"] = df.apply(lambda r: f'<span class="price-target-style">{format_br(r["Preço-Alvo"], moeda_sym=r["Moeda"])}</span>', axis=1)

    def color_pct(val, is_upside=False):
        color = "#00FF95" if val > 0.001 else "#FF4B4B" if val < -0.001 else "#555"
        weight = "700" if is_upside else "500"
        return f'<span style="color: {color}; font-weight: {weight}; font-family: \'JetBrains Mono\';">{format_br(val, is_pct=True)}</span>'

    df_desktop["Upside"] = df["Upside"].apply(lambda x: color_pct(x, True))
    df_desktop["Hoje %"] = df["Hoje %"].apply(color_pct)
    df_desktop["30 Dias %"] = df["30 Dias %"].apply(color_pct)
    df_desktop["6 Meses %"] = df["6 Meses %"].apply(color_pct)
    df_desktop["12 Meses %"] = df["12 Meses %"].apply(color_pct)
    df_desktop["YTD %"] = df["YTD %"].apply(color_pct)
    df_desktop["5 Anos %"] = df["5 Anos %"].apply(color_pct)
    df_desktop["Vol (MM)"] = df["Vol (MM)"].apply(lambda x: format_br(x))
    df_desktop["Mkt Cap (MM)"] = df.apply(lambda r: format_br(r["Mkt Cap (MM)"], moeda_sym=r["Moeda"]), axis=1)

    html_table = df_desktop.to_html(escape=False, index=False)

    # -----------------------------------------------------
    # VERSÃO MOBILE (ACCORDION HTML5)
    # -----------------------------------------------------
    mobile_html_cards = ""
    
    for index, row in df.iterrows():
        color_upside = "#00FF95" if row['Upside'] > 0 else "#FF4B4B" if row['Upside'] < 0 else "#666"
        color_day = "#00FF95" if row['Hoje %'] > 0 else "#FF4B4B" if row['Hoje %'] < 0 else "#666"
        
        # Formata Strings
        str_preco = f"{row['Moeda']} {format_br(row['Preço'])}"
        str_alvo = f"Alvo: {row['Moeda']} {format_br(row['Preço-Alvo'])}"
        
        # Monta o bloco HTML
        card = f"""
        <details class="mobile-card">
            <summary class="m-summary">
                <div class="m-header-top">
                    <span class="m-ticker">{row['Ticker']}</span>
                    <span class="m-price">{str_preco}</span>
                </div>
                <div class="m-header-sub">
                    <span>{str_alvo}</span>
                    <span style="font-size:10px;">▼ ver mais</span>
                </div>
            </summary>
            <div class="m-content">
                <div class="m-grid">
                    <div class="m-item">
                        <span class="m-label">Variação Hoje</span>
                        <span class="m-value" style="color: {color_day}">{format_br(row['Hoje %'], is_pct=True)}</span>
                    </div>
                    <div class="m-item">
                        <span class="m-label">Upside</span>
                        <span class="m-value" style="color: {color_upside}">{format_br(row['Upside'], is_pct=True)}</span>
                    </div>
                    <div class="m-item">
                        <span class="m-label">Recomendação</span>
                        <span class="m-value" style="color: #FFF">{row['Recomendação']}</span>
                    </div>
                    <div class="m-item">
                        <span class="m-label">Vol (MM)</span>
                        <span class="m-value">{format_br(row['Vol (MM)'])}</span>
                    </div>
                    <div class="m-item">
                        <span class="m-label">YTD %</span>
                        <span class="m-value">{color_pct(row['YTD %'])}</span>
                    </div>
                    <div class="m-item">
                        <span class="m-label">12 Meses %</span>
                        <span class="m-value">{color_pct(row['12 Meses %'])}</span>
                    </div>
                </div>
            </div>
        </details>
        """
        mobile_html_cards += card

    # Renderização Condicional
    st.markdown(f'<div class="desktop-view-container">{html_table}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="mobile-view-container">{mobile_html_cards}</div>', unsafe_allow_html=True)
    
    time.sleep(refresh_interval)
    st.rerun()
else:
    st.warning("Nenhum dado encontrado. Verifique sua conexão ou os Tickers informados.")
