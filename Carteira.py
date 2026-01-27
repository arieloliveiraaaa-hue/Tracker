import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time

# Configuração da página
st.set_page_config(page_title="Equity Monitor Pro", layout="wide", page_icon="📈")

# =========================================================
# DESIGN PREMIUM - CSS AJUSTADO (ESPAÇAMENTO E ORDEM)
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

        /* MENU TOPO */
        .top-nav {
            display: flex;
            gap: 18px;
            align-items: center;
            justify-content: flex-start;
            margin-bottom: 18px;
            font-family: 'JetBrains Mono', monospace !important;
            text-transform: uppercase !important;
            letter-spacing: 4px !important;
            font-size: 12px !important;
        }
        .top-nav a {
            color: #444 !important;
            text-decoration: none !important;
            padding-bottom: 6px;
            border-bottom: 1px solid transparent;
        }
        .top-nav a.active {
            color: #FFFFFF !important;
            border-bottom: 1px solid #222;
        }

        .main-title {
            font-family: 'Inter', sans-serif !important;
            font-size: 60px !important;
            font-weight: 900 !important;
            color: #FFFFFF !important;
            letter-spacing: -4px !important;
            line-height: 1 !important;
            display: block !important;
        }
        
        @media (max-width: 768px) { .main-title { font-size: 32px !important; text-align: center; } }

        .sub-header {
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 15px !important;
            color: #444 !important;
            margin-top: 10px !important;
            margin-bottom: 30px !important;
            text-transform: uppercase !important;
            letter-spacing: 5px !important;
            display: block !important;
        }

        /* TABELA PC - COM PADDING PARA NÃO CORTAR O BOTÃO */
        .desktop-view-container {
            padding-top: 40px !important;
        }

        .desktop-view-container table {
            width: 100% !important;
            border-collapse: collapse !important;
            background-color: #000000 !important;
            border: none !important;
        }

        .desktop-view-container th {
            background-color: #000000 !important;
            color: #FFFFFF !important;
            font-size: 13px !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            padding: 20px 10px !important;
            text-align: center !important;
            border-bottom: 2px solid #222 !important;
            font-family: 'Inter', sans-serif !important;
        }

        .desktop-view-container td {
            padding: 18px 10px !important;
            border-bottom: 1px solid #111 !important;
            font-size: 15px !important;
            background-color: #000000 !important;
            color: #D1D1D1 !important;
            font-family: 'Inter', sans-serif !important;
            text-align: center !important;
        }

        .desktop-view-container tr:nth-child(even) td { background-color: #050505 !important; }
        .ticker-style { font-weight: 900 !important; color: #FFFFFF !important; }

        /* LINHA DE SETOR NA TABELA */
        .sector-row td{
            text-align: left !important;
            font-family: 'JetBrains Mono', monospace !important;
            text-transform: uppercase !important;
            letter-spacing: 5px !important;
            color: #444 !important;
            background-color: #000000 !important;
            border-top: 2px solid #222 !important;
            border-bottom: 1px solid #111 !important;
            padding: 16px 10px !important;
        }

        /* MOBILE CARDS - ESPAÇAMENTO AJUSTADO */
        .mobile-wrapper {
            padding-top: 30px !important;
        }

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
        .m-ticker { font-size: 18px; font-weight: 900; color: #fff; }
        .m-price { font-size: 18px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
        .m-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; padding: 15px; background-color: #000; border-top: 1px solid #222;}
        .m-label { color: #555; font-size: 10px; text-transform: uppercase; margin-bottom: 4px; display:block;}
        .m-value { color: #ddd; font-size: 14px; font-weight: 600; font-family: 'JetBrains Mono', monospace; }

        /* --- MOBILE: HEADER DE SETOR (NOVO) --- */
        .m-sector {
            margin: 14px 0 10px 0;
            padding: 10px 12px;
            border-top: 2px solid #222;
            border-bottom: 1px solid #111;
            color: #444;
            background-color: #000;
            font-family: 'JetBrains Mono', monospace;
            text-transform: uppercase;
            letter-spacing: 5px;
            font-size: 11px;
        }

        /* RESPONSIVIDADE E BOTÃO POPOVER */
        @media (min-width: 769px) { .mobile-wrapper { display: none !important; } .desktop-view-container { display: block !important; } }
        @media (max-width: 768px) { .desktop-view-container { display: none !important; } .mobile-wrapper { display: block !important; } [data-testid="stPopover"] { display: none !important; } }
        
        div[data-testid="stPopover"] button {
            background-color: #000000 !important;
            border: 1px solid #222 !important;
            color: #444 !important;
            padding: 5px 12px !important;
        }
        
        div[data-testid="stPopover"] {
            display: flex;
            justify-content: flex-end;
            margin-bottom: -10px; /* Ajustado para não sobrepor */
        }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# LÓGICA DE DADOS
# =========================================================
MINHA_COBERTURA = {
    "^BVSP": {"Rec": "-", "Alvo": 0},
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

SETORES_ACOMPANHAMENTO = {
    "IBOV": ["^BVSP"],
    "Varejo e Bens de Consumo": ["AZZA3.SA", "LREN3.SA", "CEAB3.SA", "GUAR3.SA", "TFCO4.SA", "VIVA3.SA", "SBFG3.SA", "MELI", "MGLU3.SA", "BHIA3.SA", "ASAI3.SA", "GMAT3.SA", "PCAR3.SA", "SMFT3.SA", "NATU3.SA", "AUAU3.SA", "VULC3.SA", "ALPA4.SA"],
    "Farmácias e Farmacêuticas": ["RADL3.SA", "PGMN3.SA", "PNVL3.SA", "DMVF3.SA", "PFRM3.SA", "HYPE3.SA", "BLAU3.SA"],
    "Shoppings": ["MULT3.SA", "ALOS3.SA", "IGTI11.SA"],
    "Agronegócio e Proteínas": ["AGRO3.SA", "SLCE3.SA", "ABEV3.SA", "MDIA3.SA", "JBS", "MBRF3.SA", "BEEF3.SA", "SMTO3.SA", "KEPL3.SA"],
    "Bens de Capital": ["WEGE3.SA", "EMBJ3.SA", "LEVE3.SA", "TUPY3.SA", "MYPK3.SA", "FRAS3.SA", "RAPT4.SA", "POMO4.SA"],
    "Transporte e Logística": ["RENT3.SA", "MOVI3.SA", "VAMO3.SA", "RAIL3.SA", "SIMH3.SA"],
    "Bancos e Financeiras": ["ITUB4.SA", "BBDC4.SA", "BBAS3.SA", "SANB11.SA", "NU", "BPAC11.SA", "XP", "INTR", "PAGS", "BRSR6.SA", "B3SA3.SA", "BBSE3.SA", "PSSA3.SA", "CXSE3.SA"],
    "Educação": ["YDUQ3.SA", "COGN3.SA", "ANIM3.SA", "SEER3.SA"],
    "Energia Elétrica": ["AXIA3.SA", "AURE3.SA", "EQTL3.SA", "EGIE3.SA", "TAEE11.SA", "ENEV3.SA", "CMIG4.SA", "CPLE3.SA", "CPFE3.SA", "ENGI11.SA", "ISA4.SA", "ALUP11.SA"],
    "Água e Saneamento": ["SBSP3.SA", "SAPR11.SA", "CSMG3.SA", "ORVR3.SA"],
    "Concessões": ["MOTV3.SA", "ECOR3.SA"],
    "Saúde": ["RDOR3.SA", "HAPV3.SA", "ODPV3.SA", "MATD3.SA", "FLRY3.SA"],
    "Tech e Telecom": ["VIVT3.SA", "TIMS3.SA", "TOTS3.SA", "LWSA3.SA"],
    "Construção e Real Estate": ["EZTC3.SA", "CYRE3.SA", "MRVE3.SA", "MDNE3.SA", "TEND3.SA", "MTRE3.SA", "PLPL3.SA", "DIRR3.SA", "CURY3.SA", "JHSF3.SA"],
    "Serviços": ["OPCT3.SA", "GGPS3.SA"],
    "Petróleo, Gás e Distribuição": ["PETR4.SA", "PRIO3.SA", "BRAV3.SA", "RECV3.SA", "CSAN3.SA", "VBBR3.SA", "UGPA3.SA"],
    "Mineração e Siderurgia": ["VALE3.SA", "CSNA3.SA", "USIM5.SA", "GGBR4.SA", "GOAU4.SA", "CMIN3.SA", "BRAP4.SA"],
    "Papel, Celulose e Químicos": ["SUZB3.SA", "KLBN11.SA", "RANI3.SA", "UNIP6.SA", "DEXP3.SA"]
}

def format_br(val, is_pct=False, moeda_sym=""):
    if pd.isna(val) or (val == 0 and not is_pct): return "-"
    formatted = "{:,.2f}".format(val).replace(",", "X").replace(".", ",").replace("X", ".")
    if is_pct: return f"{formatted}%"
    if moeda_sym: return f"{moeda_sym} {formatted}"
    return formatted

@st.cache_data(ttl=60, show_spinner=False)
def get_stock_data(tickers):
    def moeda_simbolo(t):
        if t.endswith(".SA") or t == "^BVSP":
            return "R$"
        return "$"

    def calc_pct_from_series(close_s: pd.Series, price_current: float, days_ago=None, is_ytd=False):
        try:
            if close_s.empty:
                return 0.0
            close_s = close_s.dropna()
            if close_s.empty:
                return 0.0

            if is_ytd:
                target_date = datetime(datetime.now().year, 1, 1)
            else:
                target_date = datetime.now() - timedelta(days=days_ago)

            ts = pd.Timestamp(target_date)
            idx = close_s.index.get_indexer([ts], method="pad")[0]
            base = float(close_s.iloc[idx])
            if base <= 0:
                return 0.0
            return ((price_current / base) - 1) * 100
        except:
            return 0.0

    data_list = []
    if not tickers:
        return pd.DataFrame()

    CHUNK = 60
    for i in range(0, len(tickers), CHUNK):
        chunk = tickers[i:i+CHUNK]
        try:
            raw = yf.download(
                tickers=chunk,
                period="6y",
                auto_adjust=True,
                group_by="ticker",
                threads=True,
                progress=False,
            )
        except:
            continue

        if isinstance(raw.columns, pd.MultiIndex):
            if "Close" in raw.columns.get_level_values(0):
                close_df = raw["Close"]
                vol_df = raw["Volume"] if "Volume" in raw.columns.get_level_values(0) else None
            else:
                close_df = raw.xs("Close", axis=1, level=1, drop_level=False)
                close_df.columns = close_df.columns.get_level_values(0)
                vol_df = raw.xs("Volume", axis=1, level=1, drop_level=False) if ("Volume" in raw.columns.get_level_values(1)) else None
                if vol_df is not None:
                    vol_df.columns = vol_df.columns.get_level_values(0)
        else:
            close_df = raw[["Close"]].rename(columns={"Close": chunk[0]})
            vol_df = raw[["Volume"]].rename(columns={"Volume": chunk[0]}) if "Volume" in raw.columns else None

        for ticker in chunk:
            try:
                if ticker not in close_df.columns:
                    continue

                hist_close = close_df[ticker].dropna()
                if hist_close.empty:
                    continue

                price_current = float(hist_close.iloc[-1])
                price_prev_close = float(hist_close.iloc[-2]) if len(hist_close) > 1 else price_current

                simbolo = moeda_simbolo(ticker)

                dados_manuais = MINHA_COBERTURA.get(ticker, {"Rec": "-", "Alvo": 0.0})
                preco_alvo = float(dados_manuais["Alvo"])
                upside = (preco_alvo / price_current - 1) * 100 if preco_alvo > 0 else 0.0

                vol_mm = 0.0
                if vol_df is not None and ticker in vol_df.columns:
                    hist_vol = vol_df[ticker].dropna()
                    if not hist_vol.empty:
                        vol_mm = float(hist_vol.iloc[-1]) / 1_000_000

                data_list.append({
                    "Ticker": ticker.replace(".SA", ""),
                    "Moeda": simbolo,
                    "Preço": price_current,
                    "Recomendação": dados_manuais["Rec"],
                    "Preço-Alvo": preco_alvo,
                    "Upside": upside,
                    "Hoje %": ((price_current / price_prev_close) - 1) * 100,
                    "30 Dias %": calc_pct_from_series(hist_close, price_current, days_ago=30),
                    "6 Meses %": calc_pct_from_series(hist_close, price_current, days_ago=180),
                    "12 Meses %": calc_pct_from_series(hist_close, price_current, days_ago=365),
                    "YTD %": calc_pct_from_series(hist_close, price_current, is_ytd=True),
                    "Vol (MM)": vol_mm,
                })
            except:
                continue

    return pd.DataFrame(data_list)

def color_pct(val):
    color = "#00FF95" if val > 0.001 else "#FF4B4B" if val < -0.001 else "#555"
    return f'<span style="color: {color}; font-family: \'JetBrains Mono\';">{format_br(val, is_pct=True)}</span>'

def display_ticker_key(ticker: str) -> str:
    return ticker.replace(".SA", "")

# =========================================================
# MENU (PÁGINAS)
# =========================================================
if "page" not in st.session_state:
    st.session_state.page = "Cobertura"

st.markdown('<div class="top-nav">', unsafe_allow_html=True)

choice = st.radio(
    "Menu",
    ["Cobertura", "Setores"],
    horizontal=True,
    key="__nav_page",
    label_visibility="collapsed",
    index=0 if st.session_state.page == "Cobertura" else 1
)

st.session_state.page = choice
st.markdown("</div>", unsafe_allow_html=True)

page = "setores" if st.session_state.page == "Setores" else "cobertura"

st.markdown("""
<style>
div[data-testid="stRadio"] > div { gap: 18px !important; }
div[data-testid="stRadio"] label { margin: 0 !important; }
div[data-testid="stRadio"] label > div:first-child { display:none !important; }
div[data-testid="stRadio"] label > div:last-child {
    font-family: 'JetBrains Mono', monospace !important;
    text-transform: uppercase !important;
    letter-spacing: 4px !important;
    font-size: 12px !important;
    color: #444 !important;
    padding-bottom: 6px !important;
    border-bottom: 1px solid transparent !important;
}
div[data-testid="stRadio"] label[data-checked="true"] > div:last-child {
    color: #FFFFFF !important;
    border-bottom: 1px solid #222 !important;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# UI
# =========================================================
if page == "setores":
    st.markdown('<span class="main-title">EQUITY MONITOR</span>', unsafe_allow_html=True)
    st.markdown(f'<span class="sub-header">TERMINAL DE DADOS • {datetime.now().strftime("%d %b %Y | %H:%M:%S")}</span>', unsafe_allow_html=True)

    ordered_pairs = []
    seen = set()
    all_tickers = []
    for sector, tickers in SETORES_ACOMPANHAMENTO.items():
        for t in tickers:
            ordered_pairs.append((sector, t))
            if t not in seen:
                all_tickers.append(t)
                seen.add(t)

    df = get_stock_data(all_tickers)

    if not df.empty:
        df_map = {row["Ticker"]: row for _, row in df.iterrows()}
        cols = ["Ticker", "Preço", "Hoje", "30D", "6M", "12M", "Vol (MM)"]
        thead = f"<thead><tr>{''.join([f'<th>{c}</th>' for c in cols])}</tr></thead>"

        tbody = "<tbody>"
        for sector, tickers in SETORES_ACOMPANHAMENTO.items():
            tbody += f'<tr class="sector-row"><td colspan="{len(cols)}">{sector}</td></tr>'
            for t in tickers:
                k = display_ticker_key(t)
                if k not in df_map: continue
                r = df_map[k]
                tbody += f"<tr><td><span class='ticker-style'>{r['Ticker']}</span></td><td><span>{format_br(r['Preço'], moeda_sym=r['Moeda'])}</span></td><td>{color_pct(float(r['Hoje %']))}</td><td>{color_pct(float(r['30 Dias %']))}</td><td>{color_pct(float(r['6 Meses %']))}</td><td>{color_pct(float(r['12 Meses %']))}</td><td>{format_br(float(r['Vol (MM)']))}</td></tr>"
        tbody += "</tbody>"

        st.markdown(f'<div class="desktop-view-container"><table>{thead}{tbody}</table></div>', unsafe_allow_html=True)

        mobile_html_cards = ""
        last_sector = None
        for sector, t in ordered_pairs:
            k = display_ticker_key(t)
            if k not in df_map: continue
            row = df_map[k]
            c_price = "#00FF95" if float(row['Hoje %']) > 0 else "#FF4B4B" if float(row['Hoje %']) < 0 else "#FFFFFF"
            if sector != last_sector:
                mobile_html_cards += f'<div class="m-sector">{sector}</div>'
                last_sector = sector
            mobile_html_cards += f"<details class='mobile-card'><summary class='m-summary'><div class='m-header-top'><span class='m-ticker'>{row['Ticker']}</span><span class='m-price' style='color: {c_price}'>{row['Moeda']} {format_br(row['Preço'])}</span></div><div class='m-header-sub' style='display:flex; justify-content:space-between; font-size:12px; color:#444;'><span>{sector}</span><span>▼</span></div></summary><div class='m-grid'><div class='m-item'><span class='m-label'>Hoje</span><span class='m-value' style='color:{c_price}'>{format_br(row['Hoje %'], is_pct=True)}</span></div><div class='m-item'><span class='m-label'>12M</span><span class='m-value'>{format_br(row['12 Meses %'], is_pct=True)}</span></div></div></details>"
        st.markdown(f'<div class="mobile-wrapper">{mobile_html_cards}</div>', unsafe_allow_html=True)
        time.sleep(60); st.rerun()

else:
    st.markdown('<span class="main-title">EQUITY MONITOR</span>', unsafe_allow_html=True)
    st.markdown(f'<span class="sub-header">TERMINAL DE DADOS • {datetime.now().strftime("%d %b %Y | %H:%M:%S")}</span>', unsafe_allow_html=True)

    df = get_stock_data(list(MINHA_COBERTURA.keys()))

    if not df.empty:
        # --- FORÇAR ^BVSP NO TOPO (PESO 0) E O RESTO EM ORDEM ALFABÉTICA (PESO 1) ---
        df['top_priority'] = df['Ticker'].apply(lambda x: 0 if x == "^BVSP" else 1)
        df = df.sort_values(by=['top_priority', 'Ticker'], ascending=[True, True]).drop(columns=['top_priority'])

        # Omitimos o popover de ordenação automática para não quebrar a regra de "BVSP no topo" solicitada
        df_view = pd.DataFrame()
        df_view["Ticker"] = df["Ticker"].apply(lambda x: f'<span class="ticker-style">{x}</span>')
        df_view["Rec."] = df["Recomendação"]
        df_view["Alvo"] = df.apply(lambda r: f'<span>{format_br(r["Preço-Alvo"], moeda_sym=r["Moeda"])}</span>', axis=1)
        df_view["Preço"] = df.apply(lambda r: f'<span>{format_br(r["Preço"], moeda_sym=r["Moeda"])}</span>', axis=1)
        df_view["Upside"] = df["Upside"].apply(color_pct)
        df_view["Hoje"] = df["Hoje %"].apply(color_pct)
        df_view["30D"] = df["30 Dias %"].apply(color_pct)
        df_view["6M"] = df["6 Meses %"].apply(color_pct)
        df_view["12M"] = df["12 Meses %"].apply(color_pct)
        df_view["Vol (MM)"] = df["Vol (MM)"].apply(lambda x: format_br(x))

        st.markdown(f'<div class="desktop-view-container">{df_view.to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)

        mobile_html_cards = ""
        for _, row in df.iterrows():
            c_price = "#00FF95" if row['Hoje %'] > 0 else "#FF4B4B" if row['Hoje %'] < 0 else "#FFFFFF"
            mobile_html_cards += f"<details class='mobile-card'><summary class='m-summary'><div class='m-header-top'><span class='m-ticker'>{row['Ticker']}</span><span class='m-price' style='color: {c_price}'>{row['Moeda']} {format_br(row['Preço'])}</span></div><div class='m-header-sub' style='display:flex; justify-content:space-between; font-size:12px; color:#444;'><span>Alvo: {row['Moeda']} {format_br(row['Preço-Alvo'])}</span><span>▼</span></div></summary><div class='m-grid'><div class='m-item'><span class='m-label'>Hoje</span><span class='m-value' style='color:{c_price}'>{format_br(row['Hoje %'], is_pct=True)}</span></div><div class='m-item'><span class='m-label'>Upside</span><span class='m-value'>{format_br(row['Upside'], is_pct=True)}</span></div><div class='m-item'><span class='m-label'>Rec.</span><span class='m-value'>{row['Recomendação']}</span></div><div class='m-item'><span class='m-label'>12M</span><span class='m-value'>{format_br(row['12 Meses %'], is_pct=True)}</span></div></div></details>"
        st.markdown(f'<div class="mobile-wrapper">{mobile_html_cards}</div>', unsafe_allow_html=True)
        time.sleep(60); st.rerun()
