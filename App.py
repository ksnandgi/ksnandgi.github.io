import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date, datetime
import math

# ================= PASSWORD =================
PASSWORD = "CHANGE_THIS_PASSWORD"

def login():
    if "auth" not in st.session_state:
        st.session_state.auth = False
    if not st.session_state.auth:
        st.title("🔐 Finance Tracker Login")
        pwd = st.text_input("Password", type="password")
        if st.button("Login"):
            if pwd == PASSWORD:
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Incorrect password")
        st.stop()

login()

# ================= FILES ====================
BASE = Path(".")
TX_FILE = BASE / "transactions.csv"
BUDGET_FILE = BASE / "budgets.csv"
RECUR_FILE = BASE / "recurring.csv"

TX_COLS = ["date","type","category","description","amount"]
BUDGET_COLS = ["category","monthly_budget"]
RECUR_COLS = ["name","type","category","amount","day"]

def load(path, cols):
    if path.exists():
        df = pd.read_csv(path)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        return df
    return pd.DataFrame(columns=cols)

def save(df, path):
    df.to_csv(path, index=False)

if not TX_FILE.exists(): save(pd.DataFrame(columns=TX_COLS), TX_FILE)
if not BUDGET_FILE.exists(): save(pd.DataFrame(columns=BUDGET_COLS), BUDGET_FILE)
if not RECUR_FILE.exists(): save(pd.DataFrame(columns=RECUR_COLS), RECUR_FILE)

tx = load(TX_FILE, TX_COLS)
budgets = load(BUDGET_FILE, BUDGET_COLS)
recurring = load(RECUR_FILE, RECUR_COLS)

# ================= STATE ====================
if "tab" not in st.session_state:
    st.session_state.tab = "Summary"

# ================= MONTH FILTER =============
months = ["All time"]
if not tx.empty:
    months += sorted(tx["date"].dt.to_period("M").astype(str).unique(), reverse=True)

month = st.sidebar.selectbox("📅 Month", months)

def filter_month(df, m):
    if m == "All time":
        return df
    df["ym"] = df["date"].dt.to_period("M").astype(str)
    return df[df["ym"] == m]

tx_m = filter_month(tx.copy(), month)

# ================= HELPERS ==================
def total(t):
    return tx_m[tx_m.type == t].amount.sum()

today = pd.Timestamp(date.today())
tx_today = tx[tx.date.dt.date == today.date()]

# ================= NET WORTH ================
def net_worth(df):
    df = df.copy()
    df["ym"] = df["date"].dt.to_period("M")
    p = df.pivot_table(index="ym", columns="type", values="amount", aggfunc="sum").fillna(0)
    p["NetWorth"] = (
        p.get("Income",0).cumsum()
        + p.get("Savings",0).cumsum()
        - p.get("Expense",0).cumsum()
        - p.get("Debt",0).cumsum()
    )
    return p.reset_index()

nw = net_worth(tx)

# ================= UI =======================
st.set_page_config("Finance Tracker", "💰", layout="wide")
st.title("💰 Personal Finance Tracker")

tabs = ["Summary","Add Entry","Transactions","Budgets","Recurring","Help"]
icons = ["📊","➕","📜","🎯","🔁","ℹ️"]
tab_objs = st.tabs([f"{i} {t}" for i,t in zip(icons,tabs)])
T = dict(zip(tabs, tab_objs))

# ================= SUMMARY ==================
with T["Summary"]:
    st.session_state.tab = "Summary"

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Income", f"₹{total('Income'):,.0f}")
    c2.metric("Expense", f"₹{total('Expense'):,.0f}")
    c3.metric("Debt", f"₹{total('Debt'):,.0f}")
    c4.metric("Savings", f"₹{total('Savings'):,.0f}")

    st.subheader("📅 Today")
    d1,d2,d3 = st.columns(3)
    d1.metric("Expense", f"₹{tx_today[tx_today.type=='Expense'].amount.sum():,.0f}")
    d2.metric("Debt", f"₹{tx_today[tx_today.type=='Debt'].amount.sum():,.0f}")
    d3.metric("Savings", f"₹{tx_today[tx_today.type=='Savings'].amount.sum():,.0f}")

    st.subheader("🚨 Alerts")
    for _, b in budgets.iterrows():
        spent = tx_m[(tx_m.type=="Expense")&(tx_m.category==b.category)].amount.sum()
        if spent >= b.monthly_budget:
            st.error(f"{b.category} budget exceeded")
        elif spent >= 0.8*b.monthly_budget:
            st.warning(f"{b.category} budget 80% used")

    if total("Expense")+total("Debt")+total("Savings") > total("Income"):
        st.error("Negative cash flow this month")

    st.subheader("📈 Charts")
    st.bar_chart(tx_m.groupby("type")["amount"].sum())
    st.bar_chart(tx_m[tx_m.type=="Expense"].groupby("category")["amount"].sum())

    st.subheader("💰 Net Worth")
    if not nw.empty:
        st.line_chart(nw.set_index("ym")["NetWorth"])
        st.metric("Current Net Worth", f"₹{nw.iloc[-1].NetWorth:,.0f}")

    st.subheader("⚡ Quick Add Expense")
    with st.form("quick"):
        qa = st.number_input("Amount", 0.0)
        qc = st.text_input("Category")
        if st.form_submit_button("Add"):
            tx = pd.concat([tx, pd.DataFrame([{
                "date": today,
                "type": "Expense",
                "category": qc,
                "description": "Quick",
                "amount": qa
            }])])
            save(tx, TX_FILE)
            st.rerun()

# ================= ADD ENTRY ================
with T["Add Entry"]:
    with st.form("add"):
        t = st.selectbox("Type", ["Expense","Income","Debt","Savings"])
        a = st.number_input("Amount", 0.0)
        c = st.text_input("Category")
        d = st.text_input("Description")
        if st.form_submit_button("Save"):
            tx = pd.concat([tx, pd.DataFrame([{
                "date": today,
                "type": t,
                "category": c,
                "description": d,
                "amount": a
            }])])
            save(tx, TX_FILE)
            st.session_state.tab = "Summary"
            st.rerun()

# ================= TRANSACTIONS =============
with T["Transactions"]:
    st.dataframe(tx_m.sort_values("date", ascending=False))

# ================= BUDGETS ==================
with T["Budgets"]:
    with st.form("budget"):
        bc = st.text_input("Category")
        ba = st.number_input("Monthly Budget", 0.0)
        if st.form_submit_button("Save"):
            budgets = budgets[budgets.category != bc]
            budgets = pd.concat([budgets, pd.DataFrame([{"category":bc,"monthly_budget":ba}])])
            save(budgets, BUDGET_FILE)
            st.rerun()

    for _, b in budgets.iterrows():
        spent = tx_m[(tx_m.category==b.category)&(tx_m.type=="Expense")].amount.sum()
        st.progress(min(spent/b.monthly_budget,1))

# ================= RECURRING ================
with T["Recurring"]:
    with st.form("rec"):
        n = st.text_input("Name")
        t = st.selectbox("Type", ["Income","Expense","Debt","Savings"])
        c = st.text_input("Category")
        a = st.number_input("Amount", 0.0)
        d = st.number_input("Day of Month", 1, 28)
        if st.form_submit_button("Add"):
            recurring = pd.concat([recurring, pd.DataFrame([{
                "name":n,"type":t,"category":c,"amount":a,"day":d
            }])])
            save(recurring, RECUR_FILE)
            st.rerun()

    st.dataframe(recurring)

# ================= HELP =====================
with T["Help"]:
    st.markdown("""
### Included Features
- Summary-first dashboard
- Alerts & budgets
- Debt + savings tracking
- Net worth graph
- Recurring entries
- Mobile-friendly

This is a complete personal finance system.
""")

# ================= BACKUP ===================
st.sidebar.markdown("### 📦 Backup")
st.sidebar.download_button(
    "Download transactions.csv",
    tx.to_csv(index=False),
    "transactions.csv"
)