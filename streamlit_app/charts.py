# streamlit_app/charts.py

import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

def render_price_chart(history: list[dict], symbol: str):
    """
    Renders a candlestick chart from get_daily_history() output.
    Candlestick shows open/high/low/close — more information than a line chart.
    """
    if not history:
        st.warning("No price history available")
        return
    
    dates  = [h["date"]  for h in history]
    opens  = [h["open"]  for h in history]
    highs  = [h["high"]  for h in history]
    lows   = [h["low"]   for h in history]
    closes = [h["close"] for h in history]
    
    fig = go.Figure(data=[go.Candlestick(
        x=dates,
        open=opens, high=highs, low=lows, close=closes,
        increasing_line_color="#00CC88",
        decreasing_line_color="#FF4444"
    )])
    
    fig.update_layout(
        title=f"{symbol} — 30-Day Price History",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        xaxis_rangeslider_visible=False,  # Cleaner without the range slider
        height=400,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_portfolio_pie(holdings: list[dict]):
    """Pie chart of portfolio allocation by current value."""
    if not holdings:
        st.info("No holdings to display")
        return
    
    symbols = [h["symbol"] for h in holdings]
    values  = [h["current_value"] for h in holdings]
    
    fig = px.pie(
        names=symbols,
        values=values,
        title="Portfolio Allocation",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(height=350)
    
    st.plotly_chart(fig, use_container_width=True)


def render_pnl_bar(holdings: list[dict]):
    """Bar chart showing P&L per holding — green = profit, red = loss."""
    if not holdings:
        return
    
    symbols = [h["symbol"] for h in holdings]
    pnls    = [h["pnl"]    for h in holdings]
    colors  = ["#00CC88" if p >= 0 else "#FF4444" for p in pnls]
    
    fig = go.Figure(go.Bar(
        x=symbols, y=pnls,
        marker_color=colors,
        text=[f"${p:+.2f}" for p in pnls],
        textposition="outside"
    ))
    
    fig.update_layout(
        title="Profit & Loss by Position",
        yaxis_title="P&L (USD)",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)