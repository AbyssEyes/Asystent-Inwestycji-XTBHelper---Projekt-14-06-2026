import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

EXCELLENT_RETURN_THRESHOLD_PCT = 10.0
NEUTRAL_RETURN_THRESHOLD_PCT = 0.0

class Asset:
    def __init__(self, ticker: str, name: str, asset_type: str):
        self.ticker = ticker.upper()
        self.name = name
        self.asset_type = asset_type

def format_xtb(ticker: str, base_name: str) -> str:
    ticker_upper = ticker.upper()
    if "." not in ticker_upper:
        return f"{ticker_upper}.US - {base_name}"
    elif ticker_upper.endswith(".WA"):
        return f"{ticker_upper.replace('.WA', '.PL')} - {base_name}"
    else:
        return f"{ticker_upper} - {base_name}"

class FinancialEngine:
    def __init__(self):
        self.default_fx_rates = {"USD": 4.00, "EUR": 4.30}
        self.fx_tickers = {"USD": "USDPLN=X", "EUR": "EURPLN=X"}
        self.currency_cache = {}
        self.fx_cache = {}
        self.market_map = {
            "nvidia": ("NVDA", "NVIDIA Corp", "NVD.DE", "NVIDIA Corp", [("SMH", "VanEck Semiconductor ETF"), ("QDVE.DE", "iShares S&P 500 Tech")]),
            "nvda": ("NVDA", "NVIDIA Corp", "NVD.DE", "NVIDIA Corp", [("SMH", "VanEck Semiconductor ETF"), ("QDVE.DE", "iShares S&P 500 Tech")]),
            "apple": ("AAPL", "Apple Inc", "APC.DE", "Apple Inc", [("XLK", "Technology Select Sector"), ("QDVE.DE", "iShares Tech Sector")]),
            "aapl": ("AAPL", "Apple Inc", "APC.DE", "Apple Inc", [("XLK", "Technology Select Sector"), ("QDVE.DE", "iShares Tech Sector")]),
            "microsoft": ("MSFT", "Microsoft Corp", "MSF.DE", "Microsoft Corp", [("XLK", "Tech Select Sector"), ("QDVE.DE", "iShares Tech Sector")]),
            "msft": ("MSFT", "Microsoft Corp", "MSF.DE", "Microsoft Corp", [("XLK", "Tech Select Sector"), ("QDVE.DE", "iShares Tech Sector")]),
            "amazon": ("AMZN", "Amazon.com Inc", "AMZ.DE", "Amazon.com Inc", [("XLY", "Consumer Discretionary")]),
            "amzn": ("AMZN", "Amazon.com Inc", "AMZ.DE", "Amazon.com Inc", [("XLY", "Consumer Discretionary")]),
            "meta": ("META", "Meta Platforms", "FB2A.DE", "Meta Platforms", [("XLC", "Communication Services")]),
            "facebook": ("META", "Meta Platforms", "FB2A.DE", "Meta Platforms", [("XLC", "Communication Services")]),
            "google": ("GOOGL", "Alphabet Inc", "ABEA.DE", "Alphabet Inc", [("XLC", "Communication Services")]),
            "alphabet": ("GOOGL", "Alphabet Inc", "ABEA.DE", "Alphabet Inc", [("XLC", "Communication Services")]),
            "tesla": ("TSLA", "Tesla Inc", "TL0.DE", "Tesla Inc", [("XLY", "Consumer Discretionary")]),
            "tsla": ("TSLA", "Tesla Inc", "TL0.DE", "Tesla Inc", [("XLY", "Consumer Discretionary")]),
            "netflix": ("NFLX", "Netflix Inc", "NFC.DE", "Netflix Inc", [("XLC", "Communication Services"), ("PBS", "Invesco Media ETF")]),
            "nflx": ("NFLX", "Netflix Inc", "NFC.DE", "Netflix Inc", [("XLC", "Communication Services")]),
            "cd projekt": ("CDR.WA", "CD Projekt SA", "2CD.DE", "CD Projekt SA", [("ETFW20L.WA", "Beta ETF WIG20TR")]),
            "cdr": ("CDR.WA", "CD Projekt SA", "2CD.DE", "CD Projekt SA", [("ETFW20L.WA", "Beta ETF WIG20TR")]),
            "orlen": ("PKN.WA", "ORLEN SA", "PKN.DE", "ORLEN SA", [("ETFW20L.WA", "Beta ETF WIG20TR")]),
            "dino": ("DNP.WA", "Dino Polska SA", "DNP.DE", "Dino Polska SA", [("ETFW20L.WA", "Beta ETF WIG20TR")])
        }

        self.ai_profiles = {
            "NVDA": "Lider na rynku procesorów graficznych (GPU) i układów sztucznej inteligencji. Dostarcza kluczową infrastrukturę dla modeli AI.",
            "NVD.DE": "Europejski odpowiednik notowań NVIDIA Corp., wyceniany w walucie Euro na giełdzie Xetra.",
            "AAPL": "Globalny gigant technologiczny produkujący elektronikę użytkową (iPhone, Mac) oraz rozwijający rentowny ekosystem usług cyfrowych.",
            "APC.DE": "Europejski odpowiednik notowań Apple Inc., wyceniany w walucie Euro na giełdzie Xetra.",
            "MSFT": "Dominuje w sektorze oprogramowania, chmury obliczeniowej (Azure) oraz integracji AI z biznesem.",
            "AMZN": "Lider branży e-commerce oraz największy na świecie dostawca usług w chmurze (AWS).",
            "META": "Właściciel platform Facebook, Instagram, WhatsApp. Lider rynku reklamy cyfrowej z naciskiem na rozwój AI.",
            "GOOGL": "Dominator rynku wyszukiwarek internetowych i cyfrowej reklamy (Google, YouTube) oraz innowator AI.",
            "TSLA": "Pionier rynku samochodów elektrycznych (EV) oraz tehnologii autonomicznego prowadzenia i magazynowania czystej energii.",
            "NFLX": "Największa na świecie platforma streamingowa. Rewolucjonizuje dystrybucję filmów i seriali oryginalnych.",
            "CDR.WA": "Największe polskie studio produkujące gry wideo, znane głównie z serii 'Wiedźmin' oraz 'Cyberpunk 2077'.",
            "PKN.WA": "Największy polski koncern multienergetyczny, posiadający rafinerie i sieć detaliczną w regionie CEE.",
            "DNP.WA": "Polska sieć supermarketów, najszybciej rozwijająca się firma w sektorze handlu detalicznego na rodzimym rynku.",
            "SPY": "Najpopularniejszy fundusz ETF śledzący indeks S&P 500. Daje ekspozycję na 500 największych amerykańskich przedsiębiorstw.",
            "QQQ": "Fundusz ETF oparty na indeksie Nasdaq-100. Skupia się na Big Tech i innowacjach.",
            "SMH": "VanEck Semiconductor ETF. Inwestuje w największe globalne spółki z branży układów scalonych i półprzewodników.",
            "QDVE.DE": "iShares S&P 500 Information Technology. Europejski fundusz skupiający się na potężnym amerykańskim sektorze technologicznym.",
            "XLK": "Technology Select Sector SPDR Fund. Oferuje ekspozycję na technologiczne i informatyczne spółki z indeksu S&P 500.",
            "XLY": "Consumer Discretionary Select Sector SPDR Fund. Fundusz śledzący spółki z sektora dóbr luksusowych i konsumpcyjnych.",
            "XLC": "Communication Services Select Sector SPDR Fund. Inwestuje w największych gigantów mediów, rozrywki i komunikacji internetowej.",
            "PBS": "Invesco Dynamic Media ETF. Specjalistyczny fundusz skupiający się wyłącznie na dynamicznych spółkach medialnych.",
            "ETFW20L.WA": "Beta ETF WIG20TR. Polski fundusz śledzący indeks 20 największych i najbardziej płynnych spółek z Giełdy Papierów Wartościowych w Warszawie."
        }

    def infer_currency(self, ticker: str) -> str:
        ticker_upper = ticker.upper()
        if ticker_upper.endswith(".WA"):
            return "PLN"
        if ticker_upper.endswith(".DE"):
            return "EUR"
        return "USD"

    def get_currency(self, ticker: str) -> str:
        ticker_upper = ticker.upper()
        if ticker_upper in self.currency_cache:
            return self.currency_cache[ticker_upper]
        inferred_currency = self.infer_currency(ticker_upper)
        try:
            fast_info = yf.Ticker(ticker_upper).fast_info
            currency = str(fast_info.get("currency", inferred_currency)).upper()
            if currency not in {"PLN", "USD", "EUR"}:
                currency = inferred_currency
        except Exception:
            currency = inferred_currency
        self.currency_cache[ticker_upper] = currency
        return currency

    def get_fx_series_to_pln(self, currency: str, index: pd.DatetimeIndex, period: str) -> pd.Series:
        if currency == "PLN":
            return pd.Series(1.0, index=index)
        cache_key = (currency, period)
        if cache_key not in self.fx_cache:
            fx_ticker = self.fx_tickers.get(currency)
            if fx_ticker is None:
                self.fx_cache[cache_key] = pd.Series(dtype=float)
            else:
                try:
                    fx_hist = yf.Ticker(fx_ticker).history(period=period, interval="1d")
                    if fx_hist.empty:
                        self.fx_cache[cache_key] = pd.Series(dtype=float)
                    else:
                        fx_df = fx_hist[["Close"]].dropna()
                        fx_df.index = pd.to_datetime(fx_df.index, utc=True).tz_localize(None).normalize()
                        fx_df = fx_df[~fx_df.index.duplicated(keep="last")].sort_index()
                        self.fx_cache[cache_key] = fx_df["Close"]
                except Exception:
                    self.fx_cache[cache_key] = pd.Series(dtype=float)
        fx_base = self.fx_cache[cache_key]
        if fx_base.empty:
            fallback_rate = self.default_fx_rates.get(currency, 1.0)
            return pd.Series(fallback_rate, index=index)
        fx_on_dates = fx_base.reindex(index.normalize()).ffill().bfill()
        if fx_on_dates.isna().all():
            fallback_rate = self.default_fx_rates.get(currency, 1.0)
            return pd.Series(fallback_rate, index=index)
        return pd.Series(fx_on_dates.values, index=index)

    def get_data(self, ticker: str, period: str, interval: str = "1d", convert_to_pln: bool = True) -> pd.DataFrame:
        if not ticker:
            return pd.DataFrame()
        try:
            ticker_data = yf.Ticker(ticker)
            hist = ticker_data.history(period=period, interval=interval)
            
            if hist.empty:
                return pd.DataFrame()
                
            df = pd.DataFrame(hist[['Close', 'Dividends']])
            df = df.dropna(subset=['Close'])
            
            df.index = pd.to_datetime(df.index, utc=True)
            df = df[~df.index.duplicated(keep='last')]
            df = df.sort_index()
            
            if df.index.tzinfo is not None:
                df.index = df.index.tz_localize(None)

            currency = self.get_currency(ticker)
            df["Currency"] = currency
            if convert_to_pln:
                fx_series = self.get_fx_series_to_pln(currency, df.index, period)
                df["FX_to_PLN"] = fx_series
                df["Close"] = df["Close"] * fx_series
                df["Dividends"] = df["Dividends"] * fx_series
            else:
                df["FX_to_PLN"] = 1.0

            return df
        except Exception:
            return pd.DataFrame()

    def calculate_metrics(self, df: pd.DataFrame):
        df['Daily_Return'] = df['Close'].pct_change()
        df['Cumulative_Return'] = (1 + df['Daily_Return']).cumprod() - 1
        
        avg_daily = df['Daily_Return'].mean()
        volatility = df['Daily_Return'].std()
        
        annual_return = avg_daily * 252
        annual_volatility = volatility * np.sqrt(252)
        sharpe = (annual_return - 0.02) / annual_volatility if annual_volatility > 0 else 0
        
        total_divs = df['Dividends'].sum() if 'Dividends' in df.columns else 0
        
        return annual_return, annual_volatility, sharpe, total_divs

    def generate_ai_report(self, ticker: str, df: pd.DataFrame, sharpe: float, total_return: float) -> str:
        description = self.ai_profiles.get(ticker.upper(), "Instrument finansowy notowany na globalnych rynkach giełdowych.")
        
        momentum = "neutralne"
        if len(df) > 5:
            last_price = df['Close'].iloc[-1]
            old_price = df['Close'].iloc[-5]
            short_trend = ((last_price - old_price) / old_price) * 100
            if short_trend > 2:
                momentum = f"silne wzrostowe (+{short_trend:.1f}%)"
            elif short_trend < -2:
                momentum = f"spadkowe (korekta {short_trend:.1f}%)"
            else:
                momentum = f"konsolidacyjne"

        verdict = ""
        if sharpe >= 1.0 and total_return > 0:
            verdict = "🟢 <b>Ocena analityczna:</b> Wysoka jakość relacji zysku do ryzyka. Instrument prezentuje korzystny profil inwestycyjny."
        elif sharpe > 0 and total_return > 0:
            verdict = "🟡 <b>Ocena analityczna:</b> Wynik dodatni przy standardowym ryzyku rynkowym. Profil instrumentu można uznać za umiarkowanie korzystny."
        else:
            verdict = "🔴 <b>Ocena analityczna:</b> Podwyższone ryzyko lub niekorzystny wynik. Wymagana ostrożność i dodatkowa analiza."

        return f"<b>Charakterystyka instrumentu:</b> {description}<br><br><b>Momentum rynku:</b> W końcowej fazie analizowanego okresu zaobserwowano trend <b>{momentum}</b>.<br><br>{verdict}"

st.set_page_config(page_title="Terminal Analizy Rynku Kapitałowego", layout="wide", page_icon="📈")

primary_color = st.get_option("theme.primaryColor") or "#4f46e5"
background_color = st.get_option("theme.backgroundColor") or "#ffffff"
secondary_background_color = st.get_option("theme.secondaryBackgroundColor") or "#f5f7fb"
text_color = st.get_option("theme.textColor") or "#111827"
muted_text_color = "#6b7280"
positive_color = "#059669"
negative_color = "#dc2626"

st.markdown("""
    <style>
    .stApp { background-color: var(--background-color); color: var(--text-color); }
    .stApp [data-testid="stHeader"] { background-color: transparent; }
    .stMetric {
        background-color: var(--secondary-background-color);
        padding: 12px;
        border-radius: 10px;
        border: 1px solid color-mix(in srgb, var(--text-color) 18%, transparent);
    }
    div[data-testid="stMetricValue"] { color: var(--text-color); font-weight: 600; }
    div[data-testid="stMetricDelta"] svg { fill: currentColor; }
    .stTabs [data-baseweb="tab-list"] { gap: 6px; }
    .stTabs [data-baseweb="tab"] {
        min-height: 42px;
        border-radius: 8px 8px 0 0;
        padding: 8px 16px;
        border: 1px solid color-mix(in srgb, var(--text-color) 18%, transparent);
        border-bottom: none;
        color: color-mix(in srgb, var(--text-color) 72%, transparent);
        background-color: var(--secondary-background-color);
    }
    .stTabs [aria-selected="true"] {
        border-top: 2px solid var(--primary-color);
        color: var(--text-color);
        font-weight: 600;
    }
    div[data-testid="stSidebar"] {
        background-color: var(--secondary-background-color);
        border-right: 1px solid color-mix(in srgb, var(--text-color) 18%, transparent);
    }
    .stDataFrame { border-radius: 8px; }
    h1, h2, h3, h4 { color: var(--text-color) !important; }
    .ai-box {
        background-color: var(--secondary-background-color);
        border-left: 4px solid var(--primary-color);
        padding: 14px 16px;
        border-radius: 8px;
        margin-top: 14px;
        margin-bottom: 14px;
    }
    .ai-header {
        color: var(--primary-color);
        font-weight: 600;
        font-size: 1rem;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .period-label {
        font-weight: 600;
        color: color-mix(in srgb, var(--text-color) 70%, transparent);
        font-size: 0.82rem;
        text-transform: uppercase;
        margin-bottom: -32px;
        z-index: 10;
        position: relative;
    }
    </style>
    """, unsafe_allow_html=True)

sns.set_theme(style="darkgrid", rc={
    "axes.facecolor": secondary_background_color,
    "figure.facecolor": background_color,
    "text.color": text_color,
    "axes.labelcolor": muted_text_color,
    "xtick.color": muted_text_color,
    "ytick.color": muted_text_color,
    "grid.color": "#d1d5db",
    "grid.linestyle": "-"
})

st.title("Terminal Analizy Rynku Kapitałowego")
st.caption("Ocena ekspozycji | Analiza ryzyka | Symulacja inwestycji | Wyniki w PLN")

st.session_state.engine = FinancialEngine()
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {
        "SPY": Asset("SPY", format_xtb("SPY", "SPDR S&P 500 ETF Trust"), "ETF"),
        "QQQ": Asset("QQQ", format_xtb("QQQ", "Invesco QQQ Trust Nasdaq 100"), "ETF")
    }

with st.sidebar:
    st.header("Zarządzanie koszykiem")
    search_query = st.text_input("Wyszukaj spółkę bazową (np. tesla, orlen):").lower().strip()
    if search_query:
        matched_key = next((key for key in st.session_state.engine.market_map.keys() if key in search_query), None)
        if matched_key:
            t_usa, name_usa, t_eu, name_eu, etfs = st.session_state.engine.market_map[matched_key]
            
            st.session_state.portfolio[t_usa] = Asset(t_usa, format_xtb(t_usa, name_usa), "Akcja")
            st.session_state.portfolio[t_eu] = Asset(t_eu, format_xtb(t_eu, name_eu), "Akcja")
            for etf_ticker, etf_name in etfs:
                st.session_state.portfolio[etf_ticker] = Asset(etf_ticker, format_xtb(etf_ticker, etf_name), "ETF")
                
            st.success(f"Dodano spółkę {t_usa} oraz powiązane instrumenty ETF.")

    st.divider()
    st.subheader("Interwał danych")
    interval_options = {
        "1 Dzień (Standard)": "1d",
        "1 Godzina (Max 730 dni)": "1h",
        "15 Minut (Max 60 dni)": "15m",
        "5 Minut (Max 60 dni)": "5m",
        "1 Minuta (Max 7 dni)": "1m"
    }
    selected_interval_label = st.selectbox("Rozdzielczość notowań:", list(interval_options.keys()))
    selected_interval = interval_options[selected_interval_label]

ticker_options = list(st.session_state.portfolio.keys())
display_options = {t: st.session_state.portfolio[t].name for t in ticker_options}

xtb_opts = {
    "1M": "1mo", "3M": "3mo", "6M": "6mo", "YTD": "ytd", "1Y": "1y", "3Y": "3y", "5Y": "5y", "MAX": "max"
}

tab1, tab2, tab3, tab4 = st.tabs(["Informacje o projekcie", "Analiza pojedynczego instrumentu", "Porównanie koszyka", "Symulacja inwestycji"])

with tab1:
    st.markdown("""
    ## Przegląd aplikacji
    
    Aplikacja wspiera analizę instrumentów giełdowych i funduszy ETF na podstawie danych rynkowych z Yahoo Finance.
    Wyniki wartościowe są prezentowane w walucie PLN z uwzględnieniem kursów walutowych.
    
    ### Zakres funkcjonalny
    1. Automatyczne mapowanie spółek na instrumenty notowane na kilku rynkach oraz powiązane ETF-y.
    2. Analiza pojedynczego instrumentu: stopa zwrotu, zmienność, wskaźnik Sharpe'a i dywidendy.
    3. Analiza porównawcza koszyka instrumentów w jednolitym horyzoncie czasowym.
    4. Symulacja inwestycji jednorazowych i regularnych z uwzględnieniem prowizji wpłaty i wypłaty.
    5. Raporty tekstowe wspierające interpretację wyników.
    """)

with tab2:
    st.markdown("<div class='period-label'>HORYZONT CZASOWY ANALIZY</div>", unsafe_allow_html=True)
    selected_period_label_t2 = st.radio("Okres T2:", options=list(xtb_opts.keys()), horizontal=True, label_visibility="collapsed", key="radio_tab2")
    selected_period_t2 = xtb_opts[selected_period_label_t2]
    
    st.divider()
    col_sel, col_tech = st.columns([3, 1])
    with col_sel:
        selected_ticker = st.selectbox("Wybierz instrument bazowy / ETF:", options=ticker_options, format_func=lambda x: display_options[x])
    with col_tech:
        st.write("")
        st.write("")
        show_sma = st.toggle("Pokaż średnie kroczące SMA (50/200)")
    
    if selected_ticker:
        asset = st.session_state.portfolio[selected_ticker]
        with st.spinner("Przetwarzanie danych rynkowych..."):
            data = st.session_state.engine.get_data(asset.ticker, period=selected_period_t2, interval=selected_interval)
            
        if data.empty or len(data) < 2:
            st.error(f"Niewystarczająca liczba notowań dla interwału „{selected_interval_label}” w wybranym okresie.")
        else:
            ann_ret, ann_vol, sharpe, total_divs = st.session_state.engine.calculate_metrics(data)
            total_return = data['Cumulative_Return'].iloc[-1] * 100
            
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Stopa zwrotu (okres)", f"{total_return:.2f}%", delta=f"{total_return:.2f}%")
            c2.metric("Oczekiwany zwrot roczny", f"{ann_ret*100:.2f}%", delta=f"{ann_ret*100:.2f}%")
            c3.metric("Zmienność roczna", f"{ann_vol*100:.2f}%", delta="odchylenie standardowe", delta_color="off")
            c4.metric("Wskaźnik Sharpe’a", f"{sharpe:.2f}", delta="zysk/ryzyko", delta_color="off")
            c5.metric("Dywidendy (PLN)", f"{total_divs:.2f} zł", delta="wartość skumulowana", delta_color="normal" if total_divs > 0 else "off")
            
            ai_text = st.session_state.engine.generate_ai_report(asset.ticker, data, sharpe, total_return)
            
            st.markdown(f"""
<div class="ai-box">
    <div class="ai-header">Raport analityczny</div>
    <div style="color: {text_color}; font-size: 0.95rem; line-height: 1.6;">
        {ai_text}
    </div>
</div>
""", unsafe_allow_html=True)
            
            fig, axes = plt.subplots(2, 2, figsize=(15, 9))
            fig.patch.set_facecolor(background_color)
            
            x_seq = np.arange(len(data))
            step = max(1, len(data) // 6)
            tick_positions = x_seq[::step]
            tick_labels = [data.index[i].strftime('%Y-%m-%d') for i in tick_positions]
            
            axes[0, 0].plot(x_seq, data['Close'], color=primary_color, linewidth=1.6, label='Cena zamknięcia (PLN)')
            axes[0, 0].fill_between(x_seq, data['Close'], data['Close'].min(), color=primary_color, alpha=0.1)
            
            if show_sma and len(data) > 50:
                sma50 = data['Close'].rolling(window=50).mean()
                axes[0, 0].plot(x_seq, sma50, color="#f59e0b", linewidth=1.5, linestyle='--', label='SMA 50')
                if len(data) > 200:
                    sma200 = data['Close'].rolling(window=200).mean()
                    axes[0, 0].plot(x_seq, sma200, color="#db2777", linewidth=1.5, linestyle='--', label='SMA 200')
                axes[0, 0].legend(facecolor=secondary_background_color, edgecolor=muted_text_color, labelcolor=text_color)
                
            axes[0, 0].set_title(f"Kurs instrumentu: {asset.name}", color=text_color, fontsize=11)
            axes[0, 0].set_ylabel("Cena [PLN]", color=muted_text_color)
            axes[0, 0].set_xticks(tick_positions)
            axes[0, 0].set_xticklabels(tick_labels, rotation=15)
            
            sns.histplot(ax=axes[0, 1], data=data['Daily_Return'].dropna(), kde=True, color=primary_color, bins=30)
            axes[0, 1].set_title("Rozkład dziennych stóp zwrotu", color=text_color, fontsize=11)
            
            profit_color = positive_color if total_return >= 0 else negative_color
            axes[1, 0].plot(x_seq, data['Cumulative_Return'] * 100, color=profit_color, linewidth=2)
            axes[1, 0].set_title("Skumulowana stopa zwrotu (%)", color=text_color, fontsize=11)
            axes[1, 0].set_xticks(tick_positions)
            axes[1, 0].set_xticklabels(tick_labels, rotation=15)
            
            sns.boxplot(ax=axes[1, 1], x=data['Daily_Return'].dropna(), color="#9ca3af")
            axes[1, 1].set_title("Rozrzut i wartości skrajne (boxplot)", color=text_color, fontsize=11)
            
            for ax in axes.flat:
                ax.set_facecolor(secondary_background_color)
                ax.tick_params(colors=muted_text_color, labelsize=9)
            
            plt.tight_layout()
            st.pyplot(fig)
            
            csv = data.to_csv().encode('utf-8')
            st.download_button(label="Eksportuj dane instrumentu do CSV", data=csv, file_name=f'{asset.ticker}_data.csv', mime='text/csv')

with tab3:
    st.markdown("<div class='period-label'>HORYZONT CZASOWY PORÓWNANIA</div>", unsafe_allow_html=True)
    selected_period_label_t3 = st.radio("Okres T3:", options=list(xtb_opts.keys()), horizontal=True, label_visibility="collapsed", key="radio_tab3")
    selected_period_t3 = xtb_opts[selected_period_label_t3]
    
    st.divider()
    selected_to_compare = st.multiselect(
        "Wybierz koszyk instrumentów (minimum 2):", 
        options=ticker_options, 
        format_func=lambda x: display_options[x],
        default=["SPY", "QQQ"] if "SPY" in ticker_options else []
    )
    
    if len(selected_to_compare) >= 2:
        with st.spinner("Pobieranie danych porównawczych..."):
            comparison_rows = []
            palette = [primary_color, "#059669", "#f59e0b", "#dc2626", "#7c3aed"]
            
            fig_comp, ax_comp = plt.subplots(figsize=(14, 6))
            fig_comp.patch.set_facecolor(background_color)
            ax_comp.set_facecolor(secondary_background_color)
            
            longest_index = None
            
            for idx, t in enumerate(selected_to_compare):
                df = st.session_state.engine.get_data(t, period=selected_period_t3, interval=selected_interval)
                if not df.empty and len(df) >= 2:
                    ann_ret, ann_vol, sharpe, _ = st.session_state.engine.calculate_metrics(df)
                    total_return = df['Cumulative_Return'].iloc[-1] * 100
                    
                    if longest_index is None or len(df) > len(longest_index):
                        longest_index = df.index
                    
                    x_seq = np.arange(len(df))
                    color = palette[idx % len(palette)]
                    asset_display_name = st.session_state.portfolio[t].name
                    ax_comp.plot(x_seq, df['Cumulative_Return'] * 100, label=asset_display_name, linewidth=2, color=color)
                    
                    comparison_rows.append({
                        "Instrument (Ekspozycja)": asset_display_name,
                        "Zwrot (%)": round(total_return, 2),
                        "Zmienność roczna (%)": round(ann_vol * 100, 2),
                        "Sharpe Ratio": round(sharpe, 2)
                    })
            
            if comparison_rows and longest_index is not None:
                step = max(1, len(longest_index) // 8)
                tick_positions = np.arange(len(longest_index))[::step]
                tick_labels = [longest_index[i].strftime('%Y-%m-%d') for i in tick_positions]
                
                ax_comp.set_xticks(tick_positions)
                ax_comp.set_xticklabels(tick_labels, rotation=15)
                
                best_by_sharpe = max(comparison_rows, key=lambda x: x["Sharpe Ratio"])
                best_by_return = max(comparison_rows, key=lambda x: x["Zwrot (%)"])
                
                ai_compare_text = ""
                if best_by_sharpe["Instrument (Ekspozycja)"] == best_by_return["Instrument (Ekspozycja)"]:
                    ai_compare_text = f"🟢 <b>Wniosek:</b> Instrument <b>{best_by_sharpe['Instrument (Ekspozycja)']}</b> osiągnął jednocześnie najwyższą stopę zwrotu (+{best_by_sharpe['Zwrot (%)']}%) i najlepszą relację zysku do ryzyka (Sharpe: {best_by_sharpe['Sharpe Ratio']})."
                else:
                    ai_compare_text = f"🟡 <b>Wniosek:</b> Najwyższą stopę zwrotu osiągnął <b>{best_by_return['Instrument (Ekspozycja)']}</b> (+{best_by_return['Zwrot (%)']}%), natomiast najlepszą stabilność wyników prezentuje <b>{best_by_sharpe['Instrument (Ekspozycja)']}</b> (Sharpe: {best_by_sharpe['Sharpe Ratio']})."

                st.markdown(f"""
<div class="ai-box">
    <div class="ai-header">Raport porównawczy</div>
    <div style="color: {text_color}; font-size: 0.95rem; line-height: 1.6;">
{ai_compare_text}
    </div>
</div>
""", unsafe_allow_html=True)

                ax_comp.set_title(f"Dynamika stopy zwrotu instrumentów | Okres: {selected_period_label_t3}", fontsize=13, fontweight='bold', color=text_color)
                ax_comp.set_ylabel("Stopa zwrotu (%)", color=muted_text_color)
                ax_comp.tick_params(colors=muted_text_color)
                legend = ax_comp.legend(loc="upper left", facecolor=secondary_background_color, edgecolor=muted_text_color)
                plt.setp(legend.get_texts(), color=text_color, fontsize=9)
                st.pyplot(fig_comp)
                
                comp_df = pd.DataFrame(comparison_rows).set_index("Instrument (Ekspozycja)")
                st.markdown("#### Tabela parametrów koszyka")
                st.dataframe(comp_df, use_container_width=True)
            else:
                st.error("Brak danych umożliwiających obliczenie porównania.")
    else:
        st.info("Wybierz co najmniej dwa instrumenty, aby wygenerować analizę porównawczą.")

with tab4:
    st.markdown("<div class='period-label'>HORYZONT CZASOWY SYMULACJI</div>", unsafe_allow_html=True)
    selected_period_label_t4 = st.radio("Okres T4:", options=list(xtb_opts.keys()), horizontal=True, label_visibility="collapsed", key="radio_tab4")
    selected_period_t4 = xtb_opts[selected_period_label_t4]

    st.divider()
    simulation_mode = st.radio("Model wpłat:", ["Wpłata jednorazowa", "Wpłaty miesięczne"], horizontal=True)
    fee_col1, fee_col2 = st.columns(2)
    with fee_col1:
        deposit_fee_pct = st.number_input("Prowizja od wpłaty (%)", min_value=0.0, max_value=10.0, value=0.5, step=0.1)
    with fee_col2:
        withdrawal_fee_pct = st.number_input("Prowizja od wypłaty (%)", min_value=0.0, max_value=10.0, value=0.5, step=0.1)
    selected_for_sim = st.multiselect(
        "Wybierz instrumenty do symulacji:",
        options=ticker_options,
        format_func=lambda x: display_options[x],
        default=[ticker_options[0]] if ticker_options else []
    )

    if selected_for_sim:
        with st.spinner("Pobieranie danych do symulacji..."):
            simulation_data = {}
            for ticker in selected_for_sim:
                sim_df = st.session_state.engine.get_data(ticker, period=selected_period_t4, interval="1d")
                if not sim_df.empty and len(sim_df) >= 2:
                    simulation_data[ticker] = sim_df

        if len(simulation_data) != len(selected_for_sim):
            st.warning("Część instrumentów pominięto z powodu niewystarczających danych historycznych.")

        if simulation_data:
            common_start = max(df.index.min() for df in simulation_data.values())
            common_end = min(df.index.max() for df in simulation_data.values())

            if common_start >= common_end:
                st.error("Brak wspólnego zakresu dat między wybranymi instrumentami.")
            else:
                combined_index = pd.DatetimeIndex([])
                for df in simulation_data.values():
                    combined_index = combined_index.union(pd.DatetimeIndex(df.loc[common_start:common_end].index))

                if simulation_mode == "Wpłata jednorazowa":
                    one_time_amount = st.number_input("Kwota wpłaty brutto (PLN):", min_value=100.0, value=5000.0, step=100.0)
                    one_time_date = st.date_input(
                        "Data wpłaty:",
                        value=common_start.date(),
                        min_value=common_start.date(),
                        max_value=common_end.date()
                    )
                    transaction_dates = [pd.Timestamp(one_time_date)]
                    transaction_amount = float(one_time_amount)
                else:
                    monthly_amount = st.number_input("Miesięczna wpłata brutto (PLN):", min_value=50.0, value=500.0, step=50.0)
                    payment_months = st.number_input("Liczba miesięcy wpłat:", min_value=2, max_value=120, value=12, step=1)
                    month_start_dates = list(pd.date_range(start=common_start, end=common_end, freq='MS'))
                    transaction_dates = month_start_dates[-payment_months:] if len(month_start_dates) >= payment_months else month_start_dates
                    transaction_amount = float(monthly_amount)

                    if not transaction_dates:
                        st.warning("Wybrany horyzont wpłat nie mieści się w zakresie dostępnych danych.")

                if transaction_dates:
                    allocation_per_asset = 1 / len(simulation_data)
                    invested_gross_delta = pd.Series(0.0, index=combined_index)
                    invested_net_delta = pd.Series(0.0, index=combined_index)
                    portfolio_value = pd.Series(0.0, index=combined_index)
                    deposit_fee_ratio = deposit_fee_pct / 100

                    for tx_date in transaction_dates:
                        execution_candidates = combined_index[combined_index >= tx_date]
                        if len(execution_candidates) > 0:
                            exec_date = execution_candidates[0]
                            invested_gross_delta.loc[exec_date] += transaction_amount
                            invested_net_delta.loc[exec_date] += transaction_amount * (1 - deposit_fee_ratio)

                    for ticker, df_ticker in simulation_data.items():
                        close_series = df_ticker['Close'].loc[common_start:common_end].reindex(combined_index).ffill()
                        shares_delta = pd.Series(0.0, index=combined_index)

                        for tx_date in transaction_dates:
                            candidates = close_series.loc[close_series.index >= tx_date].dropna()
                            if len(candidates) > 0:
                                exec_date = candidates.index[0]
                                exec_price = candidates.iloc[0]
                                if exec_price > 0:
                                    net_transaction_amount = transaction_amount * (1 - deposit_fee_ratio)
                                    shares_delta.loc[exec_date] += (net_transaction_amount * allocation_per_asset) / exec_price

                        cumulative_shares = shares_delta.cumsum()
                        portfolio_value = portfolio_value.add(cumulative_shares * close_series, fill_value=0.0)

                    invested_gross_cumulative = invested_gross_delta.cumsum()
                    invested_net_cumulative = invested_net_delta.cumsum()
                    result_df = pd.DataFrame({
                        "Kapitał wpłacony brutto": invested_gross_cumulative,
                        "Kapitał zainwestowany netto": invested_net_cumulative,
                        "Wartość portfela brutto": portfolio_value
                    }).dropna()

                    if not result_df.empty and result_df["Kapitał wpłacony brutto"].iloc[-1] > 0:
                        result_df["Wartość po wypłacie netto"] = result_df["Wartość portfela brutto"] * (1 - (withdrawal_fee_pct / 100))
                        result_df["Stopa zwrotu netto %"] = (
                            (result_df["Wartość po wypłacie netto"] - result_df["Kapitał wpłacony brutto"])
                            / result_df["Kapitał wpłacony brutto"]
                        ) * 100

                        total_paid_gross = result_df["Kapitał wpłacony brutto"].iloc[-1]
                        total_invested_net = result_df["Kapitał zainwestowany netto"].iloc[-1]
                        final_value_gross = result_df["Wartość portfela brutto"].iloc[-1]
                        withdrawal_fee_amount = final_value_gross * (withdrawal_fee_pct / 100)
                        final_value_net = result_df["Wartość po wypłacie netto"].iloc[-1]
                        total_return_pct = result_df["Stopa zwrotu netto %"].iloc[-1]
                        total_deposit_fee = total_paid_gross - total_invested_net
                        positive_values = result_df["Wartość portfela brutto"] > 0
                        rolling_max = result_df["Wartość portfela brutto"].where(positive_values).cummax()
                        valid_rolling_max = rolling_max.where(rolling_max > 0)
                        drawdown_series = (result_df["Wartość portfela brutto"] / valid_rolling_max) - 1
                        max_drawdown = drawdown_series.min(skipna=True) * 100 if drawdown_series.notna().any() else np.nan

                        sc1, sc2, sc3 = st.columns(3)
                        sc1.metric("Wpłacono brutto (PLN)", f"{total_paid_gross:.2f} zł")
                        sc2.metric("Prowizje wpłat (PLN)", f"{total_deposit_fee:.2f} zł")
                        sc3.metric("Prowizja wypłaty (PLN)", f"{withdrawal_fee_amount:.2f} zł")
                        sc4, sc5, sc6 = st.columns(3)
                        sc4.metric("Wartość końcowa netto (PLN)", f"{final_value_net:.2f} zł")
                        sc5.metric("Wynik netto (%)", f"{total_return_pct:.2f}%", delta=f"{total_return_pct:.2f}%")
                        sc6.metric("Maksymalne obsunięcie (%)", f"{max_drawdown:.2f}%" if pd.notna(max_drawdown) else "N/A")

                        asset_rank = []
                        for ticker, df_ticker in simulation_data.items():
                            close_sub = df_ticker['Close'].loc[common_start:common_end]
                            first_price = close_sub.iloc[0]
                            if first_price > 0:
                                last_price = close_sub.iloc[-1]
                                if last_price > 0:
                                    asset_rank.append((display_options[ticker], ((last_price / first_price) - 1) * 100))
                        best_asset = max(asset_rank, key=lambda x: x[1]) if asset_rank else None
                        drawdown_text = f"{max_drawdown:.2f}%" if pd.notna(max_drawdown) else "brak danych"

                        if total_return_pct >= EXCELLENT_RETURN_THRESHOLD_PCT:
                            if best_asset:
                                ai_sim_text = f"🟢 <b>Ocena:</b> Symulacja osiągnęła dodatni wynik netto <b>{total_return_pct:.2f}%</b>. Największy wkład wzrostowy wniósł instrument <b>{best_asset[0]}</b> ({best_asset[1]:.2f}%)."
                            else:
                                ai_sim_text = f"🟢 <b>Ocena:</b> Symulacja osiągnęła dodatni wynik netto <b>{total_return_pct:.2f}%</b>."
                        elif total_return_pct >= NEUTRAL_RETURN_THRESHOLD_PCT:
                            ai_sim_text = f"🟡 <b>Ocena:</b> Wynik końcowy netto jest dodatni, ale umiarkowany (<b>{total_return_pct:.2f}%</b>). Warto przeanalizować dłuższy horyzont lub inną strukturę koszyka."
                        else:
                            ai_sim_text = f"🔴 <b>Ocena:</b> Symulacja zakończyła się wynikiem ujemnym <b>{total_return_pct:.2f}%</b>. Największe obsunięcie kapitału wyniosło <b>{drawdown_text}</b>."

                        st.markdown(f"""
<div class="ai-box">
    <div class="ai-header">Podsumowanie symulacji</div>
    <div style="color: {text_color}; font-size: 0.95rem; line-height: 1.6;">
        {ai_sim_text}
    </div>
</div>
""", unsafe_allow_html=True)

                        st.write("#### Przebieg wartości portfela w czasie")
                        fig_sim, (ax_sim1, ax_sim2) = plt.subplots(2, 1, figsize=(14, 7), sharex=True)
                        fig_sim.patch.set_facecolor(background_color)

                        x_idx = np.arange(len(result_df))
                        step = max(1, len(result_df) // 8)
                        tick_positions = x_idx[::step]
                        tick_labels = [result_df.index[i].strftime('%Y-%m-%d') for i in tick_positions]

                        ax_sim1.set_facecolor(secondary_background_color)
                        ax_sim1.plot(x_idx, result_df["Kapitał wpłacony brutto"], color=muted_text_color, linestyle='--', label='Wpłaty brutto')
                        line_color = positive_color if total_return_pct >= 0 else negative_color
                        ax_sim1.plot(x_idx, result_df["Wartość po wypłacie netto"], color=line_color, linewidth=2, label='Wartość netto po prowizji wypłaty')
                        ax_sim1.fill_between(x_idx, result_df["Wartość po wypłacie netto"], result_df["Kapitał wpłacony brutto"], color=line_color, alpha=0.08)
                        ax_sim1.set_title("Kapitał wpłacony i wartość końcowa netto", color=text_color, fontsize=11)
                        ax_sim1.set_ylabel("Wartość [PLN]", color=muted_text_color)
                        ax_sim1.tick_params(colors=muted_text_color, labelsize=9)
                        legend_sim = ax_sim1.legend(loc="upper left", facecolor=secondary_background_color, edgecolor=muted_text_color)
                        plt.setp(legend_sim.get_texts(), color=text_color, fontsize=9)

                        ax_sim2.set_facecolor(secondary_background_color)
                        ax_sim2.plot(x_idx, result_df["Stopa zwrotu netto %"], color=primary_color, linewidth=1.8)
                        ax_sim2.axhline(0, color=muted_text_color, linestyle='--', linewidth=1)
                        ax_sim2.set_title("Dynamika stopy zwrotu netto (%)", color=text_color, fontsize=11)
                        ax_sim2.tick_params(colors=muted_text_color, labelsize=9)
                        ax_sim2.set_xticks(tick_positions)
                        ax_sim2.set_xticklabels(tick_labels, rotation=20)

                        plt.tight_layout()
                        st.pyplot(fig_sim)
                    else:
                        st.error("Nie udało się obliczyć symulacji dla podanych parametrów.")
        else:
            st.error("Brak danych rynkowych wymaganych do wykonania symulacji.")
    else:
        st.info("Wybierz co najmniej jeden instrument, aby uruchomić symulację.")
