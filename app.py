import streamlit as st
import pandas as pd
import time
from blockchain import VotingBlockchain

# ---------- Page Config ----------
st.set_page_config(
    page_title="SecureVote — Blockchain Voting",
    page_icon="🗳️",
    layout="wide"
)

# ---------- Custom CSS ----------
st.markdown("""
<style>
    .main-title {
        font-size: 3em;
        font-weight: 800;
        background: linear-gradient(90deg, #00c853, #2196f3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }
    .subtitle { text-align:center; color:#888; margin-bottom: 30px; }
    .stat-box {
        background: #f0f2f6;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        border-left: 5px solid #00c853;
    }
    .stat-box h3 { margin: 0; color: #333; font-size: 2em; }
    .stat-box p { margin: 0; color: #666; }
    .block-card {
        background: #1e1e2e;
        color: #cdd6f4;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        font-family: monospace;
        font-size: 0.85em;
        border-left: 4px solid #00c853;
    }
    div.stButton > button {
        width: 100%;
        height: 3em;
        font-weight: bold;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Session State ----------
if "blockchain" not in st.session_state:
    st.session_state.blockchain = VotingBlockchain(difficulty=3)
if "toast" not in st.session_state:
    st.session_state.toast = None

bc = st.session_state.blockchain
CANDIDATES = ["Alice", "Bob", "Charlie", "Diana"]

# ---------- Header ----------
st.markdown('<div class="main-title">🗳️ SecureVote</div>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Tamper-Proof Voting Powered by Blockchain</p>',
            unsafe_allow_html=True)

# ---------- Tabs ----------
tab_vote, tab_results, tab_explorer = st.tabs(
    ["🗳️ Cast Vote", "📊 Live Results", "🔗 Blockchain Explorer"]
)

# ================= TAB 1: VOTE =================
with tab_vote:
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("Cast Your Vote")
        with st.form("vote_form", clear_on_submit=True):
            voter_id = st.text_input("Voter ID", placeholder="e.g., V001")
            candidate = st.selectbox("Choose Candidate", CANDIDATES)
            submitted = st.form_submit_button("🗳️ Submit Vote")

            if submitted:
                ok, msg = bc.add_vote(voter_id.strip(), candidate)
                st.session_state.toast = (ok, msg)

        if st.session_state.toast:
            ok, msg = st.session_state.toast
            if ok:
                st.success(msg)
            else:
                st.error(msg)

        st.markdown("---")
        st.subheader("⛏️ Mine Pending Votes")
        st.caption(f"Pending votes: **{len(bc.pending_votes)}**")
        if st.button("⛏️ Mine New Block", type="primary"):
            with st.spinner("Mining block... proof of work in progress..."):
                t0 = time.time()
                block = bc.mine_pending()
                elapsed = time.time() - t0
            if block:
                st.success(f"✅ Block #{block.index} mined in {elapsed:.2f}s")
                st.code(f"Hash: {block.hash}\nNonce: {block.nonce}", language="text")
            else:
                st.warning("No pending votes to mine.")

    with col2:
        st.subheader("ℹ️ How It Works")
        st.markdown("""
        1. **Enter your Voter ID** — one vote per ID
        2. **Select a candidate** and submit
        3. Vote is stored as a **pending transaction**
        4. Click **Mine** to seal votes into a block
        5. Block is hashed with **SHA-256** + **Proof of Work**
        6. Once mined, votes are **immutable**

        **Try double voting** — the system rejects it!
        """)

        st.markdown("---")
        st.subheader("🔐 Chain Status")
        valid = bc.is_valid()
        if valid:
            st.success("✅ Chain is VALID — no tampering detected")
        else:
            st.error("❌ Chain INVALID — tampering detected!")

        st.caption(f"Difficulty: {bc.difficulty} leading zeros")
        st.caption(f"Registered voters: {len(bc.voted_ids)}")

# ================= TAB 2: RESULTS =================
with tab_results:
    st.subheader("📊 Live Election Results")

    results = bc.get_results()
    total_votes = sum(results.values())

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="stat-box"><h3>{len(bc.chain)}</h3><p>Blocks</p></div>',
                    unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-box"><h3>{total_votes}</h3><p>Total Votes</p></div>',
                    unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat-box"><h3>{len(bc.pending_votes)}</h3><p>Pending</p></div>',
                    unsafe_allow_html=True)
    with c4:
        status = "✅" if bc.is_valid() else "❌"
        st.markdown(f'<div class="stat-box"><h3>{status}</h3><p>Chain Integrity</p></div>',
                    unsafe_allow_html=True)

    st.markdown("### 🏆 Vote Tally")

    if total_votes == 0:
        st.info("No votes yet. Cast a vote in the first tab!")
    else:
        df = pd.DataFrame({
            "Candidate": list(results.keys()),
            "Votes": list(results.values())
        }).sort_values("Votes", ascending=False)
        df["Percentage"] = (df["Votes"] / total_votes * 100).round(1)

        # Bar chart
        st.bar_chart(df.set_index("Candidate")["Votes"])

        # Leader
        leader = df.iloc[0]
        st.success(f"🥇 Leading: **{leader['Candidate']}** "
                   f"with {leader['Votes']} votes ({leader['Percentage']}%)")

        # Table
        st.dataframe(df, use_container_width=True, hide_index=True)

    if st.button("🔄 Refresh Results"):
        st.rerun()

# ================= TAB 3: EXPLORER =================
with tab_explorer:
    st.subheader("🔗 Blockchain Explorer")
    st.caption("Every block and its votes — fully transparent")

    for block in reversed(bc.chain):
        with st.expander(
            f"📦 Block #{block.index} — {len(block.votes)} vote(s) — {block.hash[:16]}..."
        ):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**Hash:** `{block.hash}`")
                st.markdown(f"**Previous Hash:** `{block.previous_hash}`")
                st.markdown(f"**Nonce:** `{block.nonce}`")
            with col_b:
                st.markdown(f"**Timestamp:** `{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(block.timestamp))}`")
                st.markdown(f"**Vote Count:** `{len(block.votes)}`")

            if block.votes:
                st.markdown("**Votes in this block:**")
                vote_df = pd.DataFrame(block.votes)
                vote_df["timestamp"] = vote_df["timestamp"].apply(
                    lambda t: time.strftime('%H:%M:%S', time.localtime(t))
                )
                st.dataframe(vote_df, use_container_width=True, hide_index=True)
            else:
                st.caption("_Genesis block — no votes_")

    st.markdown("---")
    with st.expander("⚠️ Danger Zone"):
        st.warning("This will erase the entire blockchain. Use only for demo reset.")
        if st.button("🗑️ Reset Blockchain"):
            bc.reset()
            st.session_state.toast = None
            st.success("Blockchain reset. Refresh the page.")
            st.rerun()