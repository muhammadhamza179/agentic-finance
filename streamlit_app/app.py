import streamlit as st
import httpx


def _http_error_message(response: httpx.Response) -> str:
    """Readable message from a failed API response; avoids JSONDecodeError on empty bodies."""
    text = (response.text or "").strip()
    if not text:
        return f"Request failed ({response.status_code} {response.reason_phrase})"
    try:
        data = response.json()
    except ValueError:
        return text
    if isinstance(data, dict):
        detail = data.get("detail")
        if isinstance(detail, list):
            parts = []
            for item in detail:
                if isinstance(item, dict):
                    loc = item.get("loc", [])
                    msg = item.get("msg", "")
                    parts.append(f"{loc}: {msg}".strip(": "))
                else:
                    parts.append(str(item))
            return "; ".join(parts) if parts else text
        if detail is not None:
            return str(detail)
    return text


# Config
API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Financial AI Agent",
    page_icon="📈",
    layout="wide"
)

# ── Session state ──────────────────────────────────────────
if "token" not in st.session_state:
    st.session_state.token = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ── Auth sidebar ───────────────────────────────────────────
with st.sidebar:
    st.title("📈 Financial Agent")
    
    if not st.session_state.token:
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login"):
                r = httpx.post(f"{API_URL}/login",
                               json={"username": username, "password": password})
                if r.status_code == 200:
                    st.session_state.token = r.json()["access_token"]
                    st.success("Logged in!")
                    st.rerun()
                else:
                    st.error(_http_error_message(r) or "Invalid credentials")
        
        with tab2:
            reg_user  = st.text_input("Username", key="reg_user")
            reg_email = st.text_input("Email", key="reg_email")
            reg_pass  = st.text_input("Password", type="password", key="reg_pass")
            if st.button("Register"):
                r = httpx.post(f"{API_URL}/register",
                               json={"username": reg_user,
                                     "email": reg_email,
                                     "password": reg_pass})
                if r.status_code == 200:
                    st.session_state.token = r.json()["access_token"]
                    st.success("Account created!")
                    st.rerun()
                else:
                    st.error(_http_error_message(r) or "Registration failed")
    else:
        st.success("✓ Authenticated")
        if st.button("Logout"):
            st.session_state.token = None
            st.session_state.chat_history = []
            st.rerun()
        
        st.divider()
        st.caption("Quick queries:")
        for q in [
            "What is Apple's current price?",
            "Is Tesla stock risky?",
            "Show my portfolio",
            "What are macro conditions now?"
        ]:
            if st.button(q, key=q):
                st.session_state.quick_query = q

# ── Main area ──────────────────────────────────────────────
if not st.session_state.token:
    st.title("Welcome to your Financial AI Agent")
    st.info("Please login or register in the sidebar to get started.")
    st.stop()

st.title("Financial AI Agent")
st.caption("Ask about stocks, portfolio performance, market conditions, and more.")

# Display chat history
for turn in st.session_state.chat_history:
    with st.chat_message("user"):
        st.write(turn["user"])
    with st.chat_message("assistant"):
        st.write(turn["agent"])
        if turn.get("tools_used"):
            with st.expander("Tools used"):
                st.json(turn["tools_used"])

# ── Portfolio Dashboard ──────────────────────────────────
with st.expander("📊 Portfolio Dashboard"):
    if st.button("Refresh Portfolio"):
        r = httpx.get(
            f"{API_URL}/portfolio",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if r.status_code == 200:
            portfolio = r.json()
            holdings = portfolio.get("data", {}).get("holdings", [])
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Value", f"${portfolio['data']['total_value']:,.2f}")
            col2.metric("Total Cost", f"${portfolio['data']['total_cost']:,.2f}")
            col3.metric("Total P&L", f"${portfolio['data']['total_pnl']:+,.2f}",
                        delta=f"{portfolio['data']['total_pnl_percent']:+.2f}%")
            
            from charts import render_portfolio_pie, render_pnl_bar
            col1, col2 = st.columns(2)
            with col1:
                render_portfolio_pie(holdings)
            with col2:
                render_pnl_bar(holdings)
        else:
            st.error("Failed to load portfolio")

# Query input
query = st.chat_input("Ask about stocks, portfolio, markets...")

# Handle quick query from sidebar buttons
if hasattr(st.session_state, "quick_query"):
    query = st.session_state.quick_query
    del st.session_state.quick_query

if query:
    with st.chat_message("user"):
        st.write(query)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = httpx.post(
                    f"{API_URL}/query",
                    json={"query": query},
                    headers={"Authorization": f"Bearer {st.session_state.token}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    agent_response = data.get("response", "No response")
                    tools_used = data.get("tools_used", [])
                    
                    st.write(agent_response)
                    
                    if tools_used:
                        with st.expander(f"🔧 {len(tools_used)} tool(s) used"):
                            st.json(tools_used)
                    
                    st.session_state.chat_history.append({
                        "user": query,
                        "agent": agent_response,
                        "tools_used": tools_used
                    })
                
                elif response.status_code == 429:
                    st.error("Rate limit reached. Please wait a minute.")
                elif response.status_code == 401:
                    st.error("Session expired. Please login again.")
                    st.session_state.token = None
                else:
                    st.error(f"Error: {response.text}")
            
            except httpx.TimeoutException:
                st.error("Request timed out. The agent is taking too long.")
            except Exception as e:
                st.error(f"Connection error: {e}")