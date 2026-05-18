from agent.tools import (
    stock_price,
    stock_fundamentals,
    stock_technicals,
    stock_forecast,
    fetch_articles
)

print("\n=== STOCK PRICE ===")
print(stock_price.invoke({"symbol": "RELIANCE.NS"}))

print("\n=== FUNDAMENTALS ===")
print(stock_fundamentals.invoke({"symbol": "RELIANCE.NS"}))

print("\n=== TECHNICALS ===")
print(stock_technicals.invoke({"symbol": "RELIANCE.NS"}))

print("\n=== FORECAST ===")
print(stock_forecast.invoke({"symbol": "RELIANCE.NS"}))

print("\n=== NEWS ===")
print(fetch_articles.invoke({"query": "RELIANCE.NS"}))