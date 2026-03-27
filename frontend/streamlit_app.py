from __future__ import annotations

import os
import streamlit as st

from api_client import APIClient


st.set_page_config(page_title="FinSolve Secure Chat", page_icon="🔐", layout="wide")

API_BASE = os.getenv("RBAC_API_BASE_URL", "http://127.0.0.1:8000")
client = APIClient(base_url=API_BASE)


def init_state() -> None:
    defaults = {
        "access_token": "",
        "refresh_token": "",
        "profile": None,
        "messages": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def do_logout() -> None:
    st.session_state.access_token = ""
    st.session_state.refresh_token = ""
    st.session_state.profile = None
    st.session_state.messages = []


def login_panel() -> None:
    st.title("FinSolve Secure RAG Chat")
    st.caption("Login to access role-restricted document chat with citations.")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", value="finance_user")
        password = st.text_input("Password", type="password", value="FinancePass123!")
        submit = st.form_submit_button("Login")

    if submit:
        try:
            tokens = client.login(username, password)
            st.session_state.access_token = tokens["access_token"]
            st.session_state.refresh_token = tokens["refresh_token"]
            st.session_state.profile = client.profile(st.session_state.access_token)
            st.success("Login successful")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))



def sidebar_profile() -> None:
    p = st.session_state.profile or {}
    st.sidebar.header("Session")
    st.sidebar.write(f"Backend: {API_BASE}")
    st.sidebar.write(f"User: {p.get('username', '-')}")
    st.sidebar.write(f"Role: {p.get('role', '-')}")

    deps = p.get("departments", [])
    st.sidebar.write("Accessible Departments:")
    if deps:
        for d in deps:
            st.sidebar.markdown(f"- {d}")
    else:
        st.sidebar.markdown("- none")

    if st.sidebar.button("Logout"):
        do_logout()
        st.rerun()



def render_messages() -> None:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("meta"):
                with st.expander("Sources and Confidence"):
                    st.write(f"Confidence: {msg['meta'].get('confidence', 0.0)}")
                    sources = msg["meta"].get("sources", [])
                    for idx, src in enumerate(sources, start=1):
                        st.markdown(
                            f"{idx}. **{src.get('source_document')}** | chunk `{src.get('chunk_id')}` | "
                            f"dept `{src.get('department')}` | score `{src.get('retrieval_score')}`"
                        )
                        st.caption(src.get("snippet", ""))



def chat_panel() -> None:
    st.title("FinSolve Secure RAG Chat")
    st.caption("Responses are role-filtered and include source attribution.")

    col1, col2 = st.columns([3, 1])
    with col2:
        top_k = st.slider("Retrieved sources", min_value=3, max_value=8, value=5)

    render_messages()
    prompt = st.chat_input("Ask about company docs...")
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        result = client.chat(st.session_state.access_token, prompt, top_k=top_k)
        answer = result.get("answer", "")
        meta = {
            "confidence": result.get("confidence", 0.0),
            "sources": result.get("sources", []),
        }
        st.session_state.messages.append({"role": "assistant", "content": answer, "meta": meta})

        with st.chat_message("assistant"):
            st.markdown(answer)
            with st.expander("Sources and Confidence"):
                st.write(f"Confidence: {meta['confidence']}")
                for idx, src in enumerate(meta["sources"], start=1):
                    st.markdown(
                        f"{idx}. **{src.get('source_document')}** | chunk `{src.get('chunk_id')}` | "
                        f"dept `{src.get('department')}` | score `{src.get('retrieval_score')}`"
                    )
                    st.caption(src.get("snippet", ""))
    except PermissionError:
        st.warning("Session expired. Please log in again.")
        do_logout()
        st.rerun()
    except Exception as exc:
        st.error(str(exc))


init_state()

if not st.session_state.access_token:
    login_panel()
else:
    try:
        if not st.session_state.profile:
            st.session_state.profile = client.profile(st.session_state.access_token)
        sidebar_profile()
        chat_panel()
    except Exception as exc:
        st.error(f"Session validation failed: {exc}")
        do_logout()
