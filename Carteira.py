import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
from io import BytesIO
import html

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
# VISUAL (dark + profissional + responsivo)
# =========================================================
st.markdown(
    """
    <style>
      :root{
        --bg:#05070C;
        --panel:#0B1220;
        --panel2:#0F172A;
        --text:#E5E7EB;
        --muted:#9CA3AF;
        --border:rgba(255,255,255,0.10);
        --pos:#22C55E;
        --neg:#EF4444;
        --accent:#60A5FA;
      }

      [data-testid="stAppViewContainer"]{
        background: radial-gradient(1200px 600px at 10% 0%, rgba(96,165,250,0.10), rgba(0,0,0,0)) , var(--bg);
      }
      [data-testid="stHeader"]{ background: rgba(0,0,0,0); }
      [data-testid="stSidebar"]{ display:none; }
      .block-container{ padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1400px; }

      /* Hero */
      .hero{
        border: 1px solid var(--border);
        background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
        border-radius: 22px;
        padding: 16px 16px;
        margin-bottom: 12px;
        box-shadow: 0 18px 55px rgba(0,0,0,0.45);
      }
      .hero-top{ display:flex; align-items:center; justify-content:space-between; gap:12px; }
      .brand{ display:flex; align-items:center; gap:10px; }
      .mark{
        width: 38px; height: 38px; border-radius: 14px;
        background: radial-gradient(circle at 30% 30%, rgba(96,165,250,0.35), rgba(34,197,94,0.16));
        border: 1px solid rgba(255,255,255,0.12);
      }
      .hero-title{ margin:0; font-size: 26px; font-weight: 800; letter-spacing: 0.2px; color: var(--text); }
      .hero-sub{ margin: 4px 0 0 0; font-size: 13px; color: var(--muted); }
      .pill{
        font-size: 12px; color: var(--muted);
        padding: 7px 10px; border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.10);
        background: rgba(255,255,255,0.03);
        white-space: nowrap;
      }

      /* Action bar */
      .hint{
        font-size: 12px;
        color: var(--muted);
        margin-top: 8px;
      }

      /* Download button */
      .stDownloadButton button{
        width: 100% !important;
        background: linear-gradient(180deg, rgba(96,165,250,0.22), rgba(96,165,250,0.12)) !important;
        color: var(--text) !important;
        border: 1px solid rgba(96,165,250,0.35) !important;
        border-radius: 14px !important;
        padding: 0.60rem 0.90rem !important;
      }
      .stDownloadButton button:hover{ border-color: rgba(96,165,250,0.60) !important; }

      /* Dataframe container (escuro) */
      div[data-testid="stDataFrame"]{
        border: 1px solid var(--border);
        background: rgba(255,255,255,0.02);
        border-radius: 18px;
        padding: 6px;
      }

      /* Mobile */
      .desktop-only{ display:block; }
      .mobile-only{ display:none; }

      .cards{
        display:grid;
        grid-template-columns: 1fr;
        gap: 10px;
      }
      .card{
        border: 1px solid var(--border);
        background: linear-gradient(180deg, rgba(11,18,32,0.92), rgba(11,18,32,0.70));
        border-radius: 18px;
        padding: 12px;
      }
      .card-head{ display:flex; justify-content:space-between; align-items:baseline; gap:10px; margin-bottom: 8px; }
      .tkr{ font-size: 15px; font-weight: 800; letter-spacing: 0.2px; color: var(--text); }
      .rec{ font-size: 12px; color: var(--muted); }
      .kv{ display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 6px 10px; }
      .k{ font-size: 11px; color: var(--muted); }
      .v{ font-size: 13px; font-weight: 700; color: var(--text); }
      .pos{ color: var(--pos); font-weight: 800; }
      .neg{ color: var(--neg); font-weight: 800; }

      @media (max-width: 768px){
        .block-container{ padding-left: 0.75rem; padding-right: 0.75rem; }
        .hero-title{ font-size: 22px; }
        .pill{ display:none; }

        .desktop-only{ display:none; }
        .mobile-only{ display:block; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

def format_br(val, is_pct=False, moeda_sym=""):
    if pd.isna(val): return "-"
    formatted = "{:,.2f}".format(float(val)).replace(",", "X").replace(".", ",").replace("X", ".")
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
            hist = hist[hist["Close"] > 0].dropna()

            price_current = float(hist["Close"].iloc[-1])
            price_prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else price_current

            info = stock.info
            moeda = info.get("currency", "BRL")
            simbolo = "$" if moeda == "USD" else "R$" if moeda == "BRL" else moeda

            dados_manuais = MINHA_COBERTURA.get(ticker, {"Rec": "-", "Alvo": 0.0})
            preco_alvo = float(dados_manuais["Alvo"])
            upside = (preco_alvo / price_current - 1) * 100 if preco_alvo > 0 else 0.0

            def calculate_pct(days_ago=None, is_ytd=False):
                try:
                    target_date = datetime(datetime.now().year, 1, 1) if is_ytd else datetime.now() - timedelta(days=days_ago)
                    target_ts = pd.Timestamp(target_date).tz_localize(hist.index.tz)
                    idx = hist.index.get_indexer([target_ts], method="pad")[0]
                    return ((price_current / float(hist["Close"].iloc[idx])) - 1) * 100
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
                "Vol (MM)": float(info.get("regularMarketVolume", 0)) / 1_000_000,
                "Mkt Cap (MM)": float(info.get("marketCap", 0)) / 1_000_000 if info.get("marketCap") else 0,
            })
        except:
            continue

    return pd.DataFrame(data_list)

# Excel sem openpyxl (gera .xls via SpreadsheetML XML)
def df_to_xls_bytes(df: pd.DataFrame, sheet_name: str = "Monitor") -> bytes:
    def cell(v):
        if pd.isna(v):
            return '<Cell><Data ss:Type="String"></Data></Cell>'
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return f'<Cell><Data ss:Type="Number">{float(v)}</Data></Cell>'
        return f'<Cell><Data ss:Type="String">{html.escape(str(v))}</Data></Cell>'

    cols = df.columns.tolist()
    header = "".join(cell(c) for c in cols)

    rows = []
    for _, r in df.iterrows():
        rows.append("<Row>" + "".join(cell(r[c]) for c in cols) + "</Row>")
    rows_xml = "".join(rows)

    xml = f"""<?xml version="1.0"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:x="urn:schemas-microsoft-com:office:excel"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
  <Worksheet ss:Name="{html.escape(sheet_name)}">
    <Table>
      <Row>{header}</Row>
      {rows_xml}
    </Table>
  </Worksheet>
</Workbook>
"""
    return xml.encode("utf-8-sig")

# =========================
# HEADER
# =========================
now_str = datetime.now().strftime("%H:%M:%S")
st.markdown(
    f"""
    <div class="hero">
      <div class="hero-top">
        <div class="brand">
          <div class="mark"></div>
          <div>
            <div class="hero-title">Monitor de Ações</div>
            <div class="hero-sub">Atualização automática • {now_str}</div>
            <div class="hint">Dica: clique no nome da coluna para ordenar (↑↓).</div>
          </div>
        </div>
        <div class="pill">Cobertura: {len(MINHA_COBERTURA)} tickers</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

lista_tickers = list(MINHA_COBERTURA.keys())
df = get_stock_data(lista_tickers)

if not df.empty:
    # Botão de download (único controle)
    c1, c2 = st.columns([3.0, 1.2], vertical_alignment="bottom")
    with c2:
        export_cols = [
            "Ticker", "Moeda", "Preço", "Recomendação", "Preço-Alvo", "Upside",
            "Hoje %", "30 Dias %", "6 Meses %", "12 Meses %", "YTD %", "5 Anos %",
            "Vol (MM)", "Mkt Cap (MM)"
        ]
        xls_bytes = df_to_xls_bytes(df[export_cols], sheet_name="Monitor")
        st.download_button(
            "Baixar Excel",
            data=xls_bytes,
            file_name=f"monitor_acoes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xls",
            mime="application/vnd.ms-excel",
            use_container_width=True,
        )

    # =========================
    # DESKTOP: st.dataframe (sorting por coluna)
    # =========================
    col_order = (
        "Ticker", "Moeda", "Preço", "Recomendação", "Preço-Alvo", "Upside",
        "Hoje %", "30 Dias %", "6 Meses %", "12 Meses %", "YTD %", "5 Anos %",
        "Vol (MM)", "Mkt Cap (MM)"
    )

    cols_pct = ["Upside", "Hoje %", "30 Dias %", "6 Meses %", "12 Meses %", "YTD %", "5 Anos %"]

    def style_rows(row):
        styles = ["background-color: #0B1220; color: #E5E7EB;"] * len(row)
        for col_name in cols_pct:
            try:
                val = float(row[col_name])
            except:
                val = 0.0
            idx = row.index.get_loc(col_name)
            if col_name == "Upside":
                if val > 20:
                    styles[idx] += "color: #22C55E; font-weight: 800;"
                elif val < 0:
                    styles[idx] += "color: #EF4444; font-weight: 800;"
            else:
                if val > 0.01:
                    styles[idx] += "color: #22C55E; font-weight: 800;"
                elif val < -0.01:
                    styles[idx] += "color: #EF4444; font-weight: 800;"
        return styles

    df_show = df[list(col_order)].copy()

    # Styler: escuro + cores (mantém valores numéricos para ordenar corretamente)
    styler = (
        df_show.style
        .apply(style_rows, axis=1)
        .set_table_styles([
            {"selector": "th", "props": [
                ("background-color", "#0F172A"),
                ("color", "#9CA3AF"),
                ("border-bottom", "1px solid rgba(255,255,255,0.10)"),
                ("font-weight", "700"),
            ]},
            {"selector": "td", "props": [
                ("border-bottom", "1px solid rgba(255,255,255,0.06)"),
            ]},
        ])
    )

    st.markdown('<div class="desktop-only">', unsafe_allow_html=True)
    st.dataframe(
        styler,
        use_container_width=True,
        hide_index=True,
        column_order=col_order,
        height=(len(df_show) + 1) * 36,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # =========================
    # MOBILE: cards (sem scroll horizontal)
    # =========================
    st.markdown('<div class="mobile-only">', unsafe_allow_html=True)

    card_blocks = []
    for _, r in df.iterrows():
        tkr = r["Ticker"]
        rec = r["Recomendação"]
        moeda = r["Moeda"]

        preco = format_br(r["Preço"], moeda_sym=moeda)
        alvo = format_br(r["Preço-Alvo"], moeda_sym=moeda)

        upside_v = float(r["Upside"])
        hoje_v = float(r["Hoje %"])
        d30_v = float(r["30 Dias %"])
        ytd_v = float(r["YTD %"])

        def cls(col, v):
            if col == "Upside":
                return "pos" if v > 20 else "neg" if v < 0 else ""
            return "pos" if v > 0.01 else "neg" if v < -0.01 else ""

        card_blocks.append(
            f"""
            <div class="card">
              <div class="card-head">
                <div class="tkr">{tkr}</div>
                <div class="rec">{rec}</div>
              </div>
              <div class="kv">
                <div><div class="k">Preço</div><div class="v">{preco}</div></div>
                <div><div class="k">Preço-alvo</div><div class="v">{alvo}</div></div>

                <div><div class="k">Upside</div><div class="v"><span class="{cls('Upside', upside_v)}">{format_br(upside_v, is_pct=True)}</span></div></div>
                <div><div class="k">Hoje</div><div class="v"><span class="{cls('Hoje %', hoje_v)}">{format_br(hoje_v, is_pct=True)}</span></div></div>

                <div><div class="k">30 dias</div><div class="v"><span class="{cls('30 Dias %', d30_v)}">{format_br(d30_v, is_pct=True)}</span></div></div>
                <div><div class="k">YTD</div><div class="v"><span class="{cls('YTD %', ytd_v)}">{format_br(ytd_v, is_pct=True)}</span></div></div>
              </div>
            </div>
            """
        )

    st.markdown(f'<div class="cards">{"".join(card_blocks)}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    time.sleep(refresh_interval)
    st.rerun()
