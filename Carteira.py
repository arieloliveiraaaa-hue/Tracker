import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import requests

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
        .block-container { padding: 1rem 5rem !important; }
        @media (max-width: 768px) { .block-container { padding: 1rem 0.5rem !important; } }
        .stTabs [data-baseweb="tab-list"] { gap: 20px; background-color: transparent; }
        .stTabs [data-baseweb="tab"] {
            height: 40px; background-color: transparent !important; border: none !important;
            color: #444 !important; font-family: 'Inter', sans-serif !important;
            font-size: 13px !important; text-transform: uppercase; letter-spacing: 2px;
        }
        .stTabs [aria-selected="true"] { color: #FFFFFF !important; border-bottom: 2px solid #FFFFFF !important; }
        .main-title {
            font-family: 'Inter', sans-serif !important; font-size: 60px !important;
            font-weight: 900 !important; color: #FFFFFF !important; letter-spacing: -4px !important;
            line-height: 1 !important; display: block !important; margin-top: 20px;
        }
        .sub-header {
            font-family: 'JetBrains Mono', monospace !important; font-size: 15px !important;
            color: #444 !important; margin-top: 10px !important; margin-bottom: 30px !important;
            text-transform: uppercase !important; letter-spacing: 5px !important; display: block !important;
        }
        .desktop-view-container { padding-top: 40px !important; }
        .desktop-view-container table { width: 100% !important; border-collapse: collapse !important; background-color: #000000 !important; }
        .desktop-view-container th {
            background-color: #000000 !important; color: #FFFFFF !important; font-size: 13px !important;
            font-weight: 700 !important; text-transform: uppercase !important; padding: 20px 10px !important;
            text-align: center !important; border-bottom: 2px solid #222 !important;
        }
        .desktop-view-container td {
            padding: 18px 10px !important; border-bottom: 1px solid #111 !important;
            font-size: 15px !important; color: #D1D1D1 !important; text-align: center !important;
        }
        .sector-divider-row td {
            background-color: #0a0a0a !important; color: #FFFFFF !important; font-weight: 700 !important;
            text-align: left !important; padding: 12px 20px !important; font-size: 11px !important;
            letter-spacing: 3px !important; text-transform: uppercase !important; border-top: 2px solid #222 !important;
        }
        .ticker-style { font-weight: 900 !important; color: #FFFFFF !important; }
        .mobile-wrapper { padding-top: 30px !important; }
        .mobile-sector-label {
            background-color: #111; color: #fff; font-size: 11px; letter-spacing: 2px;
            text-transform: uppercase; padding: 10px; margin: 20px 0 10px 0; border-left: 3px solid #fff;
        }
        details.mobile-card { background-color: #0a0a0a; border: 1px solid #222; border-radius: 8px; margin-bottom: 10px; overflow: hidden; }
        summary.m-summary { padding: 15px; cursor: pointer; list-style: none; display: flex; flex-direction: column; background-color: #0e0e0e; }
        .m-header-top { display: flex; justify-content: space-between; align-items: center; width: 100%; }
        .m-ticker { font-size: 18px; font-weight: 900; color: #fff; }
        .m-price { font-size: 18px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
        .m-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; padding: 15px; background-color: #000; border-top: 1px solid #222;}
        .m-label { color: #555; font-size: 10px; text-transform: uppercase; margin-bottom: 4px; display:block;}
        .m-value { color: #ddd; font-size: 14px; font-weight: 600; font-family: 'JetBrains Mono', monospace; }
        @media (min-width: 769px) { .mobile-wrapper { display: none !important; } .desktop-view-container { display: block !important; } }
        @media (max-width: 768px) { .desktop-view-container { display: none !important; } .mobile-wrapper { display: block !important; } }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# LÓGICA DE DADOS - ESTABILIZADA
# =========================================================

# Criar uma sessão com headers de navegador real
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

MINHA_COBERTURA = {
    "TOTS3.SA": {"Rec": "Compra", "Alvo": 48.00},
    "VIVT3.SA": {"Rec": "Compra", "Alvo": 38.00},
    "CPLE3.SA": {"Rec": "Neutro", "Alvo": 11.00},
    "AXIA3.SA": {"Rec": "Compra", "Alvo": 59.00}, 
    "ENGI3.SA": {"Rec": "Compra", "Alvo": 46.00},
    "TAEE11.SA": {"Rec": "Compra", "Alvo": 34.00},
    "EQTL3.SA": {"Rec": "Compra", "Alvo": 35.00},
    "RDOR3.SA": {"Rec": "Compra", "Alvo": 34.00},
    "HAPV3.SA": {"Rec": "Compra", "Alvo": 6.80},
}

SETORES_ACOMPANHAMENTO = {
    "IBOV": ["^BVSP"],
    "Energia": ["AXIA3.SA", "EQTL3.SA", "TAEE11.SA", "CPLE3.SA", "EGIE3.SA", "ENGI11.SA"],
    "Bancos": ["ITUB4.SA", "BBDC4.SA", "BBAS3.SA", "BPAC11.SA", "SANB11.SA"],
    "Consumo/Varejo": ["LREN3.SA", "MGLU3.SA", "ASAI3.SA", "GMAT3.SA", "ABEV3.SA"],
    "Tech/Telecom": ["TOTS3.SA", "VIVT3.SA", "TIMS3.SA", "LWSA3.SA"],
    "Commodities": ["VALE3.SA", "PETR4.SA", "CSNA3.SA", "GGBR4.SA", "SUZB3.SA"]
}

def format_br(val, is_pct=False, moeda_sym=""):
    if pd.isna(val) or val == 0: return "-" if not is_pct else "0,00%"
    formatted = "{:,.2f}".format(val).replace(",", "X").replace(".", ",").replace("X", ".")
    if is_pct: return f"{formatted}%"
    return f"{moeda_sym} {formatted}" if moeda_sym else formatted

def color_pct(val):
    color = "#00FF95" if val > 0.05 else "#FF4B4B" if val < -0.05 else "#D1D1D1"
    return f'<span style="color: {color}; font-family: \'JetBrains Mono\';">{format_br(val, is_pct=True)}</span>'

def get_stock_data(tickers):
    data_list = []
    for ticker in tickers:
        try:
            # Pegamos um período maior para garantir que o cálculo de 12 meses funcione
            stock = yf.Ticker(ticker, session=session)
            hist = stock.history(period="2y", auto_adjust=True)
            
            if hist.empty or len(hist) < 2: continue
            
            price_current = float(hist['Close'].iloc[-1])
            price_prev = float(hist['Close'].iloc[-2])
            
            # Cálculo de variações usando o histórico (mais seguro que .info)
            def get_var(days):
                try:
                    target = hist.index[-1] - timedelta(days=days)
                    idx = hist.index.get_indexer([target], method='pad')[0]
                    return ((price_current / hist['Close'].iloc[idx]) - 1) * 100
                except: return 0.0

            dados_manuais = MINHA_COBERTURA.get(ticker, {"Rec": "-", "Alvo": 0.0})
            
            data_list.append({
                "Ticker": ticker.replace(".SA", ""),
                "Preço": price_current,
                "Rec": dados_manuais["Rec"],
                "Alvo": dados_manuais["Alvo"],
                "Upside": (dados_manuais["Alvo"]/price_current - 1)*100 if dados_manuais["Alvo"] > 0 else 0,
                "Hoje %": ((price_current / price_prev) - 1) * 100,
                "30D %": get_var(30),
                "12M %": get_var(365),
                "Moeda": "R$" if ".SA" in ticker or "^" in ticker else "$"
            })
        except: continue
    return pd.DataFrame(data_list)

# =========================================================
# INTERFACE
# =========================================================

tab1, tab2 = st.tabs(["COBERTURA", "SETORES"])

with tab1:
    st.markdown('<span class="main-title">EQUITY MONITOR</span>', unsafe_allow_html=True)
    st.markdown(f'<span class="sub-header">{datetime.now().strftime("%d %b %Y | %H:%M")}</span>', unsafe_allow_html=True)
    
    df_cob = get_stock_data(list(MINHA_COBERTURA.keys()))
    
    if not df_cob.empty:
        df_view = pd.DataFrame()
        df_view["Ticker"] = df_cob["Ticker"].apply(lambda x: f'<span class="ticker-style">{x}</span>')
        df_view["Rec"] = df_cob["Rec"]
        df_view["Preço"] = df_cob.apply(lambda r: format_br(r["Preço"], moeda_sym=r["Moeda"]), axis=1)
        df_view["Alvo"] = df_cob.apply(lambda r: format_br(r["Alvo"], moeda_sym=r["Moeda"]), axis=1)
        df_view["Upside"] = df_cob["Upside"].apply(color_pct)
        df_view["Hoje"] = df_cob["Hoje %"].apply(color_pct)
        df_view["12M"] = df_cob["12M %"].apply(color_pct)
        
        st.markdown(f'<div class="desktop-view-container">{df_view.to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)
    else:
        st.error("Conexão com Yahoo Finance instável. Tente atualizar a página em alguns segundos.")

with tab2:
    st.markdown('<span class="main-title">SETORES</span>', unsafe_allow_html=True)
    
    all_tickers = [t for sublist in SETORES_ACOMPANHAMENTO.values() for t in sublist]
    df_all = get_stock_data(list(set(all_tickers)))
    
    if not df_all.empty:
        pc_html = '<div class="desktop-view-container"><table><thead><tr><th>Ticker</th><th>Preço</th><th>Hoje</th><th>30D</th><th>12M</th></tr></thead><tbody>'
        
        for setor, tickers in SETORES_ACOMPANHAMENTO.items():
            pc_html += f'<tr class="sector-divider-row"><td colspan="5">{setor}</td></tr>'
            t_list = [t.replace(".SA", "") for t in tickers]
            df_sub = df_all[df_all['Ticker'].isin(t_list)]
            
            for _, r in df_sub.iterrows():
                pc_html += f"""<tr>
                    <td><span class="ticker-style">{r['Ticker']}</span></td>
                    <td>{format_br(r['Preço'], moeda_sym=r['Moeda'])}</td>
                    <td>{color_pct(r['Hoje %'])}</td>
                    <td>{color_pct(r['30D %'])}</td>
                    <td>{color_pct(r['12M %'])}</td>
                </tr>"""
        
        pc_html += "</tbody></table></div>"
        st.markdown(pc_html, unsafe_allow_html=True)

time.sleep(60)
st.rerun()
