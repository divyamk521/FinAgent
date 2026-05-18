from __future__ import annotations

import requests
import yfinance as yf
from langchain_core.tools import tool

from config import config

#latest news
@tool
def fetch_articles(query: str, language: str = "en", page_size: int = 5) -> str:
    """
    Fetch real-time financial news articles about a company, index, or topic.
    """

    if not config.FINLIGHT_API_KEY:
        return "⚠️ FINLIGHT_API_KEY not set. Cannot fetch articles."

    url = "https://api.finlight.me/v2/articles"

    headers = {
        "X-API-KEY": config.FINLIGHT_API_KEY,
        "Content-Type": "application/json",
        "accept": "application/json",
    }

    payload = {
        "query": query,
        "language": language,
        "pageSize": page_size,
    }

    try:
        resp = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=10
        )

        resp.raise_for_status()

        articles = resp.json().get("articles", [])

    except Exception as e:
        return f"Error fetching articles: {e}"

    if not articles:
        return f"No recent news found for '{query}'."

    lines = [f"Recent headlines for **{query}**:\n"]

    for a in articles:
        title = a.get("title", "No title")
        source = a.get("source", "Unknown")
        summary = a.get("summary", "")
        link = a.get("url", "")

        lines.append(
            f"• **{title}** ({source})\n"
            f"  {summary}\n"
            f"  {link}"
        )

    return "\n".join(lines)

#stock prices
@tool
def stock_price(symbol: str) -> str:
    """
    Get current stock price, day range, 52-week range, and volume.

    Use when the user asks:
    - What is the current price of a stock?
    - How is [stock] trading today?

    Args:
        symbol: Ticker symbol e.g. 'AAPL', 'RELIANCE.NS' (add .NS for NSE stocks).

    Returns:
        Current price snapshot.
    """
    try:
        info = yf.Ticker(symbol).info
        price = info.get("currentPrice") or info.get("regularMarketPrice", "N/A")
        currency = info.get("currency", "INR")
        name = info.get("longName", symbol)
        return (
            f"**{name} ({symbol})**\n"
            f"Price: {currency} {price}\n"
            f"Prev Close: {info.get('previousClose', 'N/A')}  |  "
            f"Day: {info.get('dayLow', 'N/A')} – {info.get('dayHigh', 'N/A')}\n"
            f"52-Week: {info.get('fiftyTwoWeekLow', 'N/A')} – {info.get('fiftyTwoWeekHigh', 'N/A')}\n"
            f"Volume: {info.get('volume', 'N/A')}"
        )
    except Exception as e:
        return f"Error fetching price for {symbol}: {e}"

# Fundamentals

@tool
def stock_fundamentals(symbol: str) -> str:
    """
    Get key financial fundamentals: PE, EPS, market cap, margins, etc.

    Use when the user asks:
    - Is [stock] a good long-term investment?
    - What are the financials / valuation metrics?

    Args:
        symbol: Ticker symbol e.g. 'MSFT', 'TCS.NS'.

    Returns:
        Key fundamental metrics.
    """
    try:
        info = yf.Ticker(symbol).info
        fields = {
            "Market Cap":        info.get("marketCap"),
            "P/E Ratio (TTM)":   info.get("trailingPE"),
            "Forward P/E":       info.get("forwardPE"),
            "EPS (TTM)":         info.get("trailingEps"),
            "Revenue (TTM)":     info.get("totalRevenue"),
            "Gross Margin":      info.get("grossMargins"),
            "Operating Margin":  info.get("operatingMargins"),
            "Net Profit Margin": info.get("profitMargins"),
            "Return on Equity":  info.get("returnOnEquity"),
            "Debt/Equity":       info.get("debtToEquity"),
            "Current Ratio":     info.get("currentRatio"),
            "Dividend Yield":    info.get("dividendYield"),
            "Beta":              info.get("beta"),
        }
        lines = [f"**Fundamentals — {info.get('longName', symbol)} ({symbol})**\n"]
        for k, v in fields.items():
            if v is not None:
                v = f"{v:.2f}" if isinstance(v, float) and v < 10 else f"{v:,.2f}" if isinstance(v, (int, float)) else v
                lines.append(f"• {k}: {v}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching fundamentals for {symbol}: {e}"

#  Technicals 

@tool
def stock_technicals(symbol: str) -> str:
    """
    Get technical indicators: 50/200-day MA, RSI, momentum trend.

    Use when the user asks:
    - Is now a good time to buy/sell [stock]?
    - Moving averages, RSI, support/resistance.

    Args:
        symbol: Ticker symbol e.g. 'GOOGL', 'HDFCBANK.NS'.

    Returns:
        Technical indicator summary.
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period="6mo")

        current = info.get("currentPrice") or info.get("regularMarketPrice")
        ma50 = info.get("fiftyDayAverage")
        ma200 = info.get("twoHundredDayAverage")

        rsi_val = "N/A"
        if not hist.empty and len(hist) >= 15:
            delta = hist["Close"].diff()
            gain = delta.clip(lower=0).rolling(14).mean()
            loss = (-delta.clip(upper=0)).rolling(14).mean()
            rsi_val = f"{(100 - (100 / (1 + gain / loss))).iloc[-1]:.1f}"

        trend = "N/A"
        if current and ma50 and ma200:
            if current > ma50 > ma200:
                trend = "📈 Bullish (price > 50MA > 200MA)"
            elif current < ma50 < ma200:
                trend = "📉 Bearish (price < 50MA < 200MA)"
            else:
                trend = "↔️ Mixed / Sideways"

        return (
            f"**Technicals — {info.get('longName', symbol)} ({symbol})**\n"
            f"Current Price: {current}\n"
            f"50-Day MA: {ma50}\n"
            f"200-Day MA: {ma200}\n"
            f"RSI (14): {rsi_val}\n"
            f"Trend Signal: {trend}"
        )
    except Exception as e:
        return f"Error fetching technicals for {symbol}: {e}"

#  Analyst forecast 
@tool
def stock_forecast(symbol: str, market: str = "NSE") -> str:
    """
    Get analyst forecast / price target data.

    Uses yfinance by default; falls back to Jina+TradingView if JINA_API_KEY is set.

    Use when the user asks:
    - Price target for [stock]?
    - Analyst buy/sell/hold consensus?

    Args:
        symbol: Ticker symbol e.g. 'TSLA', 'RELIANCE'.
        market: 'NASDAQ' or 'NSE' (only used with Jina path).

    Returns:
        Analyst forecasts and price targets.
    """
    if not config.JINA_API_KEY:
        try:
            info = yf.Ticker(symbol).info
            return (
                f"**Analyst Forecast — {info.get('longName', symbol)} ({symbol})**\n"
                f"Consensus: {info.get('recommendationKey', 'N/A').upper()}\n"
                f"Price Target — Mean: {info.get('targetMeanPrice', 'N/A')}  "
                f"|  Low: {info.get('targetLowPrice', 'N/A')}  "
                f"|  High: {info.get('targetHighPrice', 'N/A')}\n"
                f"Number of Analysts: {info.get('numberOfAnalystOpinions', 'N/A')}\n"
                f"_(Set JINA_API_KEY for richer TradingView data)_"
            )
        except Exception as e:
            return f"Error fetching forecast for {symbol}: {e}"

#     url = f"https://r.jina.ai/https://www.tradingview.com/symbols/{market.upper()}-{symbol}/forecast/"
    tv_symbol = symbol.split(".")[0]
    url = (
    f"https://r.jina.ai/"
    f"https://www.tradingview.com/symbols/"
    f"{market.upper()}-{tv_symbol}/forecast/"
        )

        
    try:
        resp = requests.get(url, headers={"Authorization": f"Bearer {config.JINA_API_KEY}"}, timeout=15)
        resp.raise_for_status()
        return resp.text[:3000]
    except Exception as e:
        return f"Error fetching forecast via Jina: {e}"


#  Exported list to use in agents file
ALL_TOOLS = [
    fetch_articles,
    stock_price,
    stock_fundamentals,
    stock_technicals,
    stock_forecast,
]

