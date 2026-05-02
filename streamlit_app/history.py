# streamlit_app/history.py

import streamlit as st
import httpx

def render_history_sidebar(api_url: str, token: str):
    """Render past queries in the sidebar with timestamps."""
    
    st.sidebar.divider()
    st.sidebar.subheader("📝 Chat History")
    
    try:
        r = httpx.get(
            f"{api_url}/history",
            headers={"Authorization": f"Bearer {token}"},
            params={"limit": 10}
        )
        
        if r.status_code != 200:
            st.sidebar.caption("Could not load history")
            return
        
        history = r.json().get("queries", [])
        
        if not history:
            st.sidebar.caption("No history yet — ask a question!")
            return
        
        for item in history:
            timestamp = item.get("created_at", "")[:16].replace("T", " ")
            preview = item.get("user_input", "")[:40] + "..."
            
            with st.sidebar.expander(f"🕐 {timestamp}"):
                st.caption(f"**Q:** {item['user_input']}")
                st.caption(f"**A:** {item['agent_response'][:100]}...")
    
    except Exception as e:
        st.sidebar.caption(f"History error: {e}")