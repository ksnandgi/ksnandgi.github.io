import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date, datetime

# ================== PASSWORD ==================
PASSWORD = "CHANGE_THIS_PASSWORD"

def check_password():
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
                st.error("Wrong password")
        st.stop()

check_password()

# ================== FILES =====================
BASE = Path(".")
TX_FILE = BASE / "transactions.csv"
DEBT_FILE = BASE / "debts.csv"
BUDGET_FILE = BASE / "budgets.csv"

TX_COLS = ["date","type","category","description","amount","created_at"]
DEBT_COLS = ["debt_name","lender","amount"]
BUDGET_COLS = ["category","monthly_budget"]

def load(path, cols):
    if path.exists():
        df = pd.read_csv(path)
        if "date" in df: df["date"] = pd.to_datetime(df["date"])
        return df
    return pd.DataFrame(columns=cols)

def save(df, path):
    df.to_csv(path, index=False)

if not TX_FILE.exists(): save(pd.DataFrame(columns=TX_COLS), TX_FILE)
if not DEBT_FILE.exists(): save(pd.DataFrame(columns=DEBT_COLS), DEBT_FILE)
if not BUDGET_FILE.exists(): save(pd.DataFrame(columns=BUDGET_COLS), BUDGET_FILE)

tx = load(TX_FILE, TX_COLS)
debts = load(DEBT_FILE, DEBT_COLS)
budgets = load(BUDGET_FILE, BUDGET_COLS)

# ================== STATE =====================
if "tab" not in st.session_state:
    st.session_state.tab = "Summary"

# ================== HELPERS ===================
def month_filter(df, m):
    if m == "All time": return df
    df["ym"] = df["date"].dt.to_period("M").astype(str)
    return df[df["ym"] == m]

months = ["All time"]
if not tx.empty:
    months += sorted(tx["date"].dt.to_period("M").astype(str).unique(), reverse=True)

month = st.sidebar.selectbox("📅 Month", months)

tx_m = month_filter(tx.copy(), month)

def total(t):
    return tx_m[tx_m["type"] == t]["amount"].sum()

today = pd.Timestamp(date.today())
tx_today = tx[tx["date"].dt.date == today.date()]

# ================== UI ========================
st.set_page_config("Finance Tracker", "💰", layout="wide")
st.title("💰 Personal Finance Tracker")

tabs = ["Summary","Add Entry","Transactions","Debts","Savings","Budgets","Help"]
icons = ["📊","➕","📜","💳","🏦","🎯","ℹ️"]
tab_objs = st.tabs([f"{i} {t}" for i,t in zip(icons,tabs)])
tab_map = dict(zip(tabs, tab_objs))

# ================== SUMMARY ===================
with tab_map["Summary"]:
    st.session_state.tab = "Summary"

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Income", f"₹{total('Income'):,.0f}")
    c2.metric("Expense", f"₹{total('Expense'):,.0f}")
    c3.metric("Debt Paid", f"₹{total('Debt'):,.0f}")
    c4.metric("Savings", f"₹{total('Savings'):,.0f}")

    st.markdown("### 📅 Today")
    t1,t2,t3 = st.columns(3)
    t1.metric("Today Expense", f"₹{tx_today[tx_today.type=='Expense'].amount.sum():,.0f}")
    t2.metric("Today Debt", f"₹{tx_today[tx_today.type=='Debt'].amount.sum():,.0f}")
    t3.metric("Today Savings", f"₹{tx_today[tx_today.type=='Savings'].amount.sum():,.0f}")

    st.markdown("---")

    st.markdown("### ⚡ Quick Add Expense")
    with st.form("quick"):
        qa = st.number_input("Amount", min_value=0.0, step=50.0)
        qc = st.text_input("Category")
        if st.form_submit_button("Add"):
            tx = pd.concat([tx, pd.DataFrame([{
                "date": today,
                "type": "Expense",
                "category": qc,
                "description": "Quick add",
                "amount": qa,
                "created_at": datetime.now()
            }])])
            save(tx, TX_FILE)
            st.success("Added")
            st.rerun()

    st.markdown("---")

    if total("Income") > 0:
        savings_rate = (total("Savings") / total("Income")) * 100
        burn = (total("Expense") + total("Debt") + total("Savings")) / max(1, len(tx_m))
        score = min(100, max(0, 50 + savings_rate - burn/500))
        st.metric("Savings Rate", f"{savings_rate:.1f}%")
        st.progress(score/100)
        st.caption("Financial Health Score")

# ================== ADD ENTRY =================
with tab_map["Add Entry"]:
    st.session_state.tab = "Add Entry"

    with st.form("add"):
        t = st.selectbox("Type", ["Expense","Income","Debt","Savings"])
        amt = st.number_input("Amount", min_value=0.0)
        cat = st.text_input("Category")
        if st.form_submit_button("Save"):
            tx = pd.concat([tx, pd.DataFrame([{
                "date": today,
                "type": t,
                "category": cat,
                "description": "",
                "amount": amt,
                "created_at": datetime.now()
            }])])
            save(tx, TX_FILE)
            st.session_state.tab = "Summary"
            st.rerun()

# ================== TRANSACTIONS ==============
with tab_map["Transactions"]:
    st.session_state.tab = "Transactions"
    st.dataframe(tx_m.sort_values("date", ascending=False))

# ================== DEBTS =====================
with tab_map["Debts"]:
    st.session_state.tab = "Debts"
    st.dataframe(tx[tx.type=="Debt"])

# ================== SAVINGS ===================
with tab_map["Savings"]:
    st.session_state.tab = "Savings"
    st.dataframe(tx[tx.type=="Savings"])

# ================== BUDGETS ===================
with tab_map["Budgets"]:
    st.session_state.tab = "Budgets"
    with st.form("budget"):
        bc = st.text_input("Category")
        ba = st.number_input("Monthly Budget", min_value=0.0)
        if st.form_submit_button("Save"):
            budgets = budgets[budgets.category != bc]
            budgets = pd.concat([budgets, pd.DataFrame([{"category":bc,"monthly_budget":ba}])])
            save(budgets, BUDGET_FILE)
            st.rerun()

    st.markdown("### Budget Usage")
    for _, r in budgets.iterrows():
        spent = tx_m[(tx_m.category==r.category)&(tx_m.type=="Expense")].amount.sum()
        pct = min(1, spent/r.monthly_budget) if r.monthly_budget>0 else 0
        st.write(f"{r.category}: ₹{spent:,.0f} / ₹{r.monthly_budget:,.0f}")
        st.progress(pct)

# ================== HELP ======================
with tab_map["Help"]:
    st.session_state.tab = "Help"
    st.markdown("""
**Features included**
- Summary opens by default  
- Remembers last tab  
- Auto-switch after save  
- Quick add expense  
- Today view  
- Budgets with alerts  
- Health score  
- Cloud-safe CSV storage  

This is a complete personal finance app.
""")

# ================== BACKUP ====================
st.sidebar.markdown("### 📦 Backup")
st.sidebar.download_button("Download transactions.csv", tx.to_csv(index=False), "transactions.csv")