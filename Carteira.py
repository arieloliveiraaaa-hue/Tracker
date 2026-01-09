import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
from io import BytesIO

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
# VISUAL (dark + "site" + responsivo)
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
        --border:#1F2937;
        --pos:#22C55E;
        --neg:#EF4444;
        --accent:#60A5FA;
      }

      /* App */
      [data-testid="stAppViewContainer"]{ background: radial-gradient(1200px 600px at 10% 0%, rgba(96,165,250,0.08), rgba(0,0,0,0)) , var(--bg); }
      [data-testid="stHeader"]{ background: rgba(0,0,0,0); }
      [data-testid="stSidebar"]{ display:none; } /* remove sidebar */
      .block-container{ padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1400px; }

      /* Widgets (deixar escuro) */
      .stButton button, .stDownloadButton button{
        background: linear-gradient(180deg, rgba(96,165,250,0.22), rgba(96,165,250,0.12)) !important;
        color: var(--text) !important;
        border: 1px solid rgba(96,165,250,0.30) !important;
        border-radius: 12px !important;
        padding: 0.55rem 0.85rem !important;
      }
      .stButton button:hover, .stDownloadButton button:hover{
        border-color: rgba(96,165,250,0.55) !important;
      }

      /* Selectbox dark */
      [data-baseweb="select"] > div{
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
      }
      [data-baseweb="select"] *{ color: var(--text) !important; }

      /* Header card */
      .hero{
        border: 1px solid rgba(255,255,255,0.08);
        background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
        border-radius: 22px;
        padding: 18px 18px;
        margin-bottom: 12px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.35);
      }
      .hero-top{
        display:flex; align-items:center; justify-content:space-between; gap:12px;
      }
      .brand{
        display:flex; align-items:center; gap:10px;
      }
      .mark{
        width: 36px; height: 36px; border-radius: 12px;
        background: radial-gradient(circle at 30% 30%, rgba(96,165,250,0.35), rgba(34,197,94,0.18));
        border: 1px solid rgba(255,255,255,0.10);
      }
      .hero-title{
        margin:0; font-size: 26px; font-weight: 780; letter-spacing: 0.2px;
        color: var(--text);
      }
      .hero-sub{
        margin: 4px 0 0 0; font-size: 13px; color: var(--muted);
      }
      .pill{
        font-size: 12px; color: var(--muted);
        padding: 6px 10px; border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.10);
        background: rgba(255,255,255,0.03);
        white-space: nowrap;
      }

      /* Desktop table (HTML) */
      .desktop-only{ display:block; }
      .mobile-only{ display:none; }

      .table-wrap{
        border: 1px solid rgba(255,255,255,0.08);
        background: rgba(255,255,255,0.02);
        border-radius: 18px;
        overflow: hidden;
      }
      table.fin{
        width: 100%;
        border-collapse: collapse;
      }
      table.fin thead th{
        position: sticky; top: 0;
        background: linear-gradient(180deg, rgba(15,23,42,0.92), rgba(15,23,42,0.70));
        color: var(--muted);
        text-align: left;
        font-size: 12px;
        font-weight: 650;
        padding: 10px 12px;
        border-bottom: 1px solid rgba(255,255,255,0.08);
        backdrop-filter: blur(6px);
      }
      table.fin tbody td{
        padding: 10px 12px;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        color: var(--text);
        font-size: 13px;
      }
      table.fin tbody tr:hover td{
        background: rgba(96,165,250,0.06);
      }
      .pos{ color: var(--pos); font-weight: 650; }
      .neg{ color: var(--neg); font-weight: 650; }
      .muted{ color: var(--muted); }

      /* Mobile cards */
      .cards{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
      }
      .card{
        border: 1px solid rgba(255,255,255,0.08);
        background: linear-gradient(180deg, rgba(11,18,32,0.92), rgba(11,18,32,0.70));
        border-radius: 18px;
        padding: 12px 12px;
      }
      .card-head{
        display:flex; justify-content:space-between; align-items:baseline; gap:10px;
        margin-bottom: 8px;
      }
      .tkr{ font-size: 14px; font-weight: 750; letter-spacing: 0.2px; }
      .rec{ font-size: 12px; color: var(--muted); }
      .kv{
        display:grid;
        grid-template-columns: repeat(2, minmax(0,1fr));
        gap: 6px 10px;
      }
      .k{ font-size: 11px; color: var(--muted); }
      .v{ font-size: 13px; font-weight: 650; color: var(--text); }

      @media (max-width: 768px){
        .block-container{ padding-left: 0.75rem; padding-right: 0.75rem; }
        .hero-title{ font-size: 22px; }
        .pill{ display:none; }

        .desktop-only{ display:none; }
        .mobile-only{ display:block; }
        .cards{ grid-template-columns: 1fr; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

def format_br(val, is_pct=False, moeda_sym=""):
    if pd.isna(val) or (val == 0 and not is_pct):
        return "-"
    formatted = "{:,.2f}".format(val).replace(",", "X").replace(".", ",").replace("X", ".")
    if is_pct:
        return f"{formatted}%"
    if moeda_sym:
        return f"{moeda_sym} {formatted}"
    return formatted

def get_stock_data(tickers):
    data_list = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="6y", auto_adjust=True)
            if hist.empty:
                continue
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
                    target_date = (
                        datetime(datetime.now().year, 1, 1)
                        if is_ytd
                        else datetime.now() - timedelta(days=days_ago)
                    )
                    target_ts = pd.Timestamp(target_date).tz_localize(hist.index.tz)
                    idx = hist.index.get_indexer([target_ts], method="pad")[0]
                    return ((price_current / float(hist["Close"].iloc[idx])) - 1) * 100
                except:
                    return 0.0

            data_list.append(
                {
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
                    "Mkt Cap (MM)": float(info.get("marketCap", 0)) / 1_000_000
                    if info.get("marketCap")
                    else 0,
                }
            )
        except:
            continue
    return pd.DataFrame(data_list)

# Header (mais “site”)
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
    # =========================
    # Controles (mais aparentes)
    # =========================
    sort_options = {
        "Upside (maior→menor)": "Upside",
        "Hoje % (maior→menor)": "Hoje %",
        "30 Dias % (maior→menor)": "30 Dias %",
        "6 Meses % (maior→menor)": "6 Meses %",
        "12 Meses % (maior→menor)": "12 Meses %",
        "YTD % (maior→menor)": "YTD %",
        "5 Anos % (maior→menor)": "5 Anos %",
        "Vol (MM) (maior→menor)": "Vol (MM)",
        "Mkt Cap (MM) (maior→menor)": "Mkt Cap (MM)",
    }

    c1, c2 = st.columns([2.2, 1.0], vertical_alignment="bottom")
    with c1:
        sort_label = st.selectbox("Ordenar:", list(sort_options.keys()), index=0)
    with c2:
        # Excel export (numérico, sem formatação string)
        df_export = df.copy()
        df_export = df_export[
            [
                "Ticker", "Moeda", "Preço", "Recomendação", "Preço-Alvo", "Upside",
                "Hoje %", "30 Dias %", "6 Meses %", "12 Meses %", "YTD %", "5 Anos %",
                "Vol (MM)", "Mkt Cap (MM)"
            ]
        ]
        bio = BytesIO()
        with pd.ExcelWriter(bio, engine="openpyxl") as writer:
            df_export.to_excel(writer, index=False, sheet_name="Monitor")
        bio.seek(0)
        st.download_button(
            "Baixar Excel",
            data=bio.getvalue(),
            file_name=f"monitor_acoes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    sort_col = sort_options[sort_label]
    df = df.sort_values(sort_col, ascending=False, kind="mergesort").reset_index(drop=True)

    # =========================
    # View formatada (BR)
    # =========================
    df_view = df.copy()
    df_view["Preço"] = df.apply(lambda r: format_br(r["Preço"], moeda_sym=r["Moeda"]), axis=1)
    df_view["Preço-Alvo"] = df.apply(lambda r: format_br(r["Preço-Alvo"], moeda_sym=r["Moeda"]), axis=1)
    df_view["Mkt Cap (MM)"] = df.apply(lambda r: format_br(r["Mkt Cap (MM)"], moeda_sym=r["Moeda"]), axis=1)

    cols_pct = ["Upside", "Hoje %", "30 Dias %", "6 Meses %", "12 Meses %", "YTD %", "5 Anos %"]
    for col in cols_pct:
        df_view[col] = df[col].apply(lambda x: format_br(x, is_pct=True))
    df_view["Vol (MM)"] = df["Vol (MM)"].apply(lambda x: format_br(x))

    col_order = [
        "Ticker", "Preço", "Recomendação", "Preço-Alvo", "Upside",
        "Hoje %", "30 Dias %", "6 Meses %", "12 Meses %", "YTD %", "5 Anos %",
        "Vol (MM)", "Mkt Cap (MM)"
    ]

    def cls_for(col, val):
        if col == "Upside":
            return "pos" if val > 20 else "neg" if val < 0 else ""
        if col in cols_pct:
            return "pos" if val > 0.01 else "neg" if val < -0.01 else ""
        return ""

    # =========================
    # DESKTOP: tabela escura (HTML)
    # =========================
    headers_html = "".join([f"<th>{h}</th>" for h in col_order])

    rows_html = []
    for i in range(len(df)):
        tds = []
        for col in col_order:
            cell = df_view.loc[i, col]
            klass = cls_for(col, float(df.loc[i, col])) if col in cols_pct else ""
            if klass:
                tds.append(f"<td><span class='{klass}'>{cell}</span></td>")
            else:
                tds.append(f"<td>{cell}</td>")
        rows_html.append("<tr>" + "".join(tds) + "</tr>")
    body_html = "".join(rows_html)

    st.markdown(
        f"""
        <div class="desktop-only">
          <div class="table-wrap">
            <table class="fin">
              <thead><tr>{headers_html}</tr></thead>
              <tbody>{body_html}</tbody>
            </table>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # =========================
    # MOBILE: cards (sem “jogar pro lado”)
    # =========================
    card_blocks = []
    for i in range(len(df)):
        tkr = df_view.loc[i, "Ticker"]
        rec = df_view.loc[i, "Recomendação"]
        preco = df_view.loc[i, "Preço"]
        alvo = df_view.loc[i, "Preço-Alvo"]
        upside = df_view.loc[i, "Upside"]
        hoje = df_view.loc[i, "Hoje %"]
        d30 = df_view.loc[i, "30 Dias %"]
        ytd = df_view.loc[i, "YTD %"]

        cls_up = cls_for("Upside", float(df.loc[i, "Upside"]))
        cls_hj = cls_for("Hoje %", float(df.loc[i, "Hoje %"]))
        cls_30 = cls_for("30 Dias %", float(df.loc[i, "30 Dias %"]))
        cls_ytd = cls_for("YTD %", float(df.loc[i, "YTD %"]))

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

                <div><div class="k">Upside</div><div class="v"><span class="{cls_up}">{upside}</span></div></div>
                <div><div class="k">Hoje</div><div class="v"><span class="{cls_hj}">{hoje}</span></div></div>

                <div><div class="k">30 dias</div><div class="v"><span class="{cls_30}">{d30}</span></div></div>
                <div><div class="k">YTD</div><div class="v"><span class="{cls_ytd}">{ytd}</span></div></div>
              </div>
            </div>
            """
        )

    st.markdown(
        f"""
        <div class="mobile-only">
          <div class="cards">
            {''.join(card_blocks)}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    time.sleep(refresh_interval)
    st.rerun()
