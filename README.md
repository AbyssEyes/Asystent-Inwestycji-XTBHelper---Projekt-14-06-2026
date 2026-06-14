# Terminal Analizy Rynku Kapitałowego

Aplikacja Streamlit służy do analizy instrumentów giełdowych (akcje i ETF), porównywania koszyków aktywów oraz symulacji inwestycji z uwzględnieniem prowizji i przeliczeń walutowych do PLN.

## Zakres funkcjonalny

1. **Mapowanie instrumentów**
   - Po wpisaniu nazwy spółki aplikacja automatycznie dodaje odpowiadające instrumenty z rynku USA i Europy oraz powiązane ETF-y.
2. **Analiza pojedynczego instrumentu**
   - Oblicza stopę zwrotu, zmienność roczną, wskaźnik Sharpe’a oraz sumę dywidend.
   - Prezentuje wykres ceny, rozkład stóp zwrotu, skumulowaną stopę zwrotu i boxplot.
3. **Porównanie koszyka**
   - Umożliwia porównanie wielu instrumentów na jednym wykresie i w tabeli parametrów.
4. **Symulacja inwestycji**
   - Obsługuje wpłatę jednorazową oraz wpłaty miesięczne.
   - Uwzględnia prowizję od wpłaty i prowizję od wypłaty.
   - Pokazuje wynik netto po kosztach oraz przebieg inwestycji w czasie.
5. **Przeliczenie walut do PLN**
   - Dane instrumentów notowanych w USD i EUR są przeliczane do PLN z użyciem kursów walutowych.
   - Dla notowań w PLN kurs wynosi 1.

## Architektura kodu (`app.py`)

### 1. Importy i stałe
- Biblioteki: `streamlit`, `yfinance`, `pandas`, `numpy`, `matplotlib`, `seaborn`.
- Stałe progowe:
  - `EXCELLENT_RETURN_THRESHOLD_PCT`
  - `NEUTRAL_RETURN_THRESHOLD_PCT`

### 2. Klasa `Asset`
Model pojedynczego instrumentu:
- `ticker` – symbol giełdowy,
- `name` – nazwa wyświetlana w GUI,
- `asset_type` – typ (np. Akcja, ETF).

### 3. Funkcja `format_xtb`
Formatuje nazwę instrumentu do czytelnej postaci rynkowej (np. oznaczenie rynku USA/PL).

### 4. Klasa `FinancialEngine`
Centralna warstwa logiki biznesowej i danych.

#### Słowniki konfiguracyjne
- `market_map` – mapowanie nazw spółek na tickery i ETF-y.
- `ai_profiles` – opisy instrumentów do raportów tekstowych.
- `default_fx_rates`, `fx_tickers`, cache walutowy i cache kursów FX.

#### Metody
- `infer_currency(ticker)`
  - Szacuje walutę instrumentu na podstawie symbolu.
- `get_currency(ticker)`
  - Ustala walutę instrumentu (z fallbackiem i cache).
- `get_fx_series_to_pln(currency, index, period)`
  - Pobiera lub odtwarza serię kursów waluty do PLN.
- `get_data(ticker, period, interval, convert_to_pln=True)`
  - Pobiera notowania z Yahoo Finance,
  - oczyszcza i porządkuje dane,
  - opcjonalnie przelicza `Close` i `Dividends` na PLN.
- `calculate_metrics(df)`
  - Oblicza stopy zwrotu, zmienność, Sharpe’a i dywidendy.
- `generate_ai_report(...)`
  - Tworzy tekstowy raport analityczny na podstawie trendu i metryk.

### 5. Konfiguracja GUI
- `st.set_page_config(...)` ustawia parametry strony.
- Aplikacja używa kolorów pobieranych z motywu Streamlit (`theme.*`), aby poprawnie działać z różnymi stylami.
- Stylizacja metryk, zakładek i sekcji raportowych jest oparta o zmienne motywu.

### 6. Zarządzanie stanem sesji
- W `st.session_state` przechowywany jest `FinancialEngine` oraz aktywny portfel instrumentów.

### 7. Zakładki aplikacji

#### Zakładka: Informacje o projekcie
Opis przeznaczenia aplikacji i zakresu funkcjonalnego.

#### Zakładka: Analiza pojedynczego instrumentu
- Wybór instrumentu i interwału.
- Obliczenie metryk.
- Raport tekstowy.
- Wykresy i eksport danych CSV.

#### Zakładka: Porównanie koszyka
- Wybór co najmniej dwóch instrumentów.
- Wykres porównawczy skumulowanych stóp zwrotu.
- Tabela metryk porównawczych.

#### Zakładka: Symulacja inwestycji
- Wybór trybu wpłat.
- Parametry prowizji wpłaty i wypłaty.
- Wyliczenie:
  - kapitału wpłaconego brutto,
  - kapitału zainwestowanego netto,
  - wartości portfela brutto,
  - wartości po wypłacie netto,
  - stopy zwrotu netto,
  - maksymalnego obsunięcia.
- Wizualizacja przebiegu wartości portfela.

## Uruchomienie lokalne

1. Zainstaluj zależności:
   ```bash
   pip install -r requirements.txt
   ```
2. Uruchom aplikację:
   ```bash
   streamlit run app.py
   ```

## Walidacja

Szybka kontrola poprawności składni:

```bash
python -m compileall app.py
```
