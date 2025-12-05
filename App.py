import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date, datetime

# ---------- SIMPLE PASSWORD PROTECTION ----------
PASSWORD = "Blackbird@786"  # 🔴 CHANGE THIS to your own strong password


def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("Finance Tracker Login 🔐")
        pwd = st.text_input("Enter password", type="password")
        if st.button("Login"):
            if pwd == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password")
        st.stop()  # stop here until password is correct


check_password()
# ---------- END PASSWORD PROTECTION ----------

TRANSACTIONS_FILE = Path("transactions.csv")
DEBTS_FILE = Path("debts.csv")

TRANSACTION_COLUMNS = [
    "date",
    "type",          # Income, Expense, Debt Payment, Savings Deposit
    "category",      # expense category or income source
    "description",
    "amount",
    "mode",          # Cash, UPI, Card, Bank Transfer, Other
    "debt_name",     # for debt payment
    "savings_type",  # for savings deposit
    "account",       # which bank / fund
    "created_at",
]

DEBT_COLUMNS = [
    "debt_name",
    "lender",
    "start_amount",
    "interest_rate",
    "emi",
    "start_date",
    "notes",
]


def load_df(path: Path, columns):
    if path.exists():
        df = pd.read_csv(path)
        for col in ["date", "start_date", "created_at"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="ignore")
        return df
    else:
        return pd.DataFrame(columns=columns)


def save_df(df: pd.DataFrame, path: Path):
    df.to_csv(path, index=False)


def ensure_files():
    if not TRANSACTIONS_FILE.exists():
        save_df(pd.DataFrame(columns=TRANSACTION_COLUMNS), TRANSACTIONS_FILE)
    if not DEBTS_FILE.exists():
        save_df(pd.DataFrame(columns=DEBT_COLUMNS), DEBTS_FILE)


def get_month_options(transactions: pd.DataFrame):
    """
    Returns list like ["All time", "2025-12", "2025-11", ...]
    """
    if transactions.empty or "date" not in transactions.columns:
        return ["All time"]

    df = transactions.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    if df.empty:
        return ["All time"]

    df["year_month"] = df["date"].dt.to_period("M").astype(str)
    months = sorted(df["year_month"].unique(), reverse=True)
    return ["All time"] + months


def filter_by_month(transactions: pd.DataFrame, selected_month: str):
    """
    Filter transactions to selected month.
    If "All time" is selected, return original.
    """
    if selected_month == "All time" or transactions.empty or "date" not in transactions.columns:
        return transactions

    df = transactions.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["year_month"] = df["date"].dt.to_period("M").astype(str)
    return df[df["year_month"] == selected_month]


def main():
    st.set_page_config(
        page_title="Personal Finance Tracker",
        page_icon="💰",
        layout="wide",
    )

    ensure_files()

    transactions = load_df(TRANSACTIONS_FILE, TRANSACTION_COLUMNS)
    debts = load_df(DEBTS_FILE, DEBT_COLUMNS)

    # ---------- SIDEBAR ----------
    st.sidebar.title("💰 Finance Cockpit")

    # Month filter (global)
    month_options = get_month_options(transactions)
    selected_month = st.sidebar.selectbox("Filter by month", month_options)
    if selected_month == "All time":
        st.sidebar.caption("Showing data for all time.")
    else:
        st.sidebar.caption(f"Showing data for: **{selected_month}**")

    menu = st.sidebar.radio(
        "Navigate",
        ["Add Entry", "Summary Dashboard", "Transactions", "Debts & EMIs", "Savings Overview", "Help"],
    )

    # Backup buttons in sidebar
    st.sidebar.markdown("---")
    with st.sidebar.expander("📦 Backup Data (CSV)"):
        if not transactions.empty:
            tx_csv = transactions.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download transactions.csv",
                tx_csv,
                "transactions.csv",
                "text/csv",
            )
        else:
            st.caption("No transactions to download yet.")

        if not debts.empty:
            debt_csv = debts.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download debts.csv",
                debt_csv,
                "debts.csv",
                "text/csv",
            )
        else:
            st.caption("No debts to download yet.")

    # Filtered df for month-aware pages
    tx_filtered = filter_by_month(transactions, selected_month)

    # ---------- ROUTING ----------
    if menu == "Add Entry":
        page_add_entry(transactions, debts)
    elif menu == "Summary Dashboard":
        page_summary(transactions, tx_filtered, debts, selected_month)
    elif menu == "Transactions":
        page_transactions(tx_filtered, selected_month)
    elif menu == "Debts & EMIs":
        page_debts(transactions, tx_filtered, debts, selected_month)
    elif menu == "Savings Overview":
        page_savings(tx_filtered, selected_month)
    else:
        page_help()


# ---------- PAGES ----------

def page_add_entry(transactions: pd.DataFrame, debts: pd.DataFrame):
    st.header("➕ Add New Entry")

    col1, col2 = st.columns(2)
    with col1:
        t_type = st.selectbox(
            "Type",
            ["Expense", "Income", "Debt Payment", "Savings Deposit"],
        )
        t_date = st.date_input("Date", value=date.today())
        amount = st.number_input("Amount", min_value=0.0, step=100.0)

    with col2:
        mode = st.selectbox("Mode", ["UPI", "Cash", "Card", "Bank Transfer", "Other"])
        description = st.text_input("Description / Notes", "")

    category = ""
    debt_name = ""
    savings_type = ""
    account = ""

    if t_type == "Expense":
        st.subheader("Expense Details")
        category = st.selectbox(
            "Category",
            [
                "Food",
                "Groceries",
                "Rent",
                "Bills & Utilities",
                "Travel",
                "Medical",
                "Education",
                "Shopping",
                "Entertainment",
                "Others",
            ],
        )
    elif t_type == "Income":
        st.subheader("Income Details")
        category = st.text_input("Source (Salary / Freelance / Gift etc.)", "")
    elif t_type == "Debt Payment":
        st.subheader("Debt Payment Details")
        if len(debts) > 0:
            debt_name = st.selectbox("Select Debt", debts["debt_name"].unique())
        else:
            st.info("You have no debts added yet. Go to 'Debts & EMIs' page to add one.")
            debt_name = st.text_input("Debt Name (temporary)", "")
        category = "Debt Payment"
    elif t_type == "Savings Deposit":
        st.subheader("Savings Details")
        savings_type = st.selectbox(
            "Savings Type",
            ["Emergency Fund", "SIP / Investment", "Fixed Deposit", "Gold", "Others"],
        )
        account = st.text_input("Account / Instrument (Bank, Fund name etc.)", "")
        category = "Savings"

    if st.button("💾 Save Entry"):
        if amount <= 0:
            st.error("Amount must be greater than 0.")
            return

        new_row = {
            "date": pd.to_datetime(t_date),
            "type": t_type,
            "category": category,
            "description": description,
            "amount": float(amount),
            "mode": mode,
            "debt_name": debt_name,
            "savings_type": savings_type,
            "account": account,
            "created_at": datetime.now(),
        }

        transactions = pd.concat(
            [transactions, pd.DataFrame([new_row])],
            ignore_index=True,
        )
        save_df(transactions, TRANSACTIONS_FILE)
        st.success("Entry saved successfully ✅")


def page_summary(all_tx: pd.DataFrame, tx_filtered: pd.DataFrame, debts: pd.DataFrame, selected_month: str):
    st.header("📊 Summary Dashboard")

    if all_tx.empty:
        st.info("No transactions yet. Add your first entry in 'Add Entry' page.")
        return

    # Prepare data
    df_all = all_tx.copy()
    df_all["amount"] = pd.to_numeric(df_all["amount"], errors="coerce").fillna(0)

    df_sel = tx_filtered.copy()
    df_sel["amount"] = pd.to_numeric(df_sel["amount"], errors="coerce").fillna(0)

    # All-time metrics
    all_income = df_all.loc[df_all["type"] == "Income", "amount"].sum()
    all_expense = df_all.loc[df_all["type"] == "Expense", "amount"].sum()
    all_debt_paid = df_all.loc[df_all["type"] == "Debt Payment", "amount"].sum()
    all_savings = df_all.loc[df_all["type"] == "Savings Deposit", "amount"].sum()
    all_net = all_income - (all_expense + all_debt_paid + all_savings)

    # Selected-period metrics
    sel_income = df_sel.loc[df_sel["type"] == "Income", "amount"].sum()
    sel_expense = df_sel.loc[df_sel["type"] == "Expense", "amount"].sum()
    sel_debt_paid = df_sel.loc[df_sel["type"] == "Debt Payment", "amount"].sum()
    sel_savings = df_sel.loc[df_sel["type"] == "Savings Deposit", "amount"].sum()
    sel_net = sel_income - (sel_expense + sel_debt_paid + sel_savings)

    label_period = "All time" if selected_month == "All time" else selected_month

    # Top row: selected period metrics
    st.subheader(f"Overview for: {label_period}")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Income", f"₹ {sel_income:,.0f}")
    c2.metric("Expenses", f"₹ {sel_expense:,.0f}")
    c3.metric("Debt Paid", f"₹ {sel_debt_paid:,.0f}")
    c4.metric("Savings", f"₹ {sel_savings:,.0f}")
    c5.metric("Net Balance", f"₹ {sel_net:,.0f}")

    # Second row: all-time snapshot (mini)
    st.caption("All-time snapshot")
    c6, c7, c8 = st.columns(3)
    c6.metric("All-time Income", f"₹ {all_income:,.0f}")
    c7.metric("All-time Debt Paid", f"₹ {all_debt_paid:,.0f}")
    c8.metric("All-time Net Worth Flow", f"₹ {all_net:,.0f}")

    st.markdown("---")

    # Tabs for insights / charts
    tab1, tab2, tab3 = st.tabs(["💡 Insights", "📈 Charts", "📅 Monthly Trend"])

    # ---------- INSIGHTS TAB ----------
    with tab1:
        st.subheader("Smart Insights")

        # Approx daily burn rate for period
        if not df_sel.empty:
            df_sel["date"] = pd.to_datetime(df_sel["date"], errors="coerce")
            dmin, dmax = df_sel["date"].min(), df_sel["date"].max()
            day_diff = (dmax - dmin).days + 1
            total_spend = sel_expense + sel_debt_paid + sel_savings
            daily_burn = total_spend / max(day_diff, 1)
        else:
            daily_burn = 0
            total_spend = 0

        colA, colB = st.columns(2)
        with colA:
            st.metric("Daily Burn (Expense + Debt + Savings)", f"₹ {daily_burn:,.0f}")
        with colB:
            if sel_income > 0:
                savings_rate = (sel_savings / sel_income) * 100
                debt_share = (sel_debt_paid / sel_income) * 100
            else:
                savings_rate = 0
                debt_share = 0
            st.metric("Savings Rate (of income)", f"{savings_rate:,.1f}%")

        # Simple "financial vibe" score (0–100)
        score = 50
        if sel_income > 0:
            margin_ratio = sel_net / sel_income
            savings_ratio = sel_savings / sel_income
            score = 50 + margin_ratio * 30 + savings_ratio * 20
        score = max(0, min(100, score))

        st.markdown("### Financial Health Score (experimental)")
        st.progress(score / 100)
        if score >= 75:
            st.success("Looking strong! You’re controlling your money, not the other way around 😎")
        elif score >= 50:
            st.info("Decent zone. A bit more control on expenses and steady savings will push you higher 👍")
        else:
            st.warning("Alert zone. Try to reduce expenses or debt for this period and boost savings a little 🚀")

    # ---------- CHARTS TAB ----------
    with tab2:
        st.subheader("Breakdown Charts")

        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("#### Expenses by Category")
            expense_df = df_sel[df_sel["type"] == "Expense"]
            if not expense_df.empty:
                cat_summary = (
                    expense_df.groupby("category")["amount"]
                    .sum()
                    .sort_values(ascending=False)
                )
                st.bar_chart(cat_summary)
            else:
                st.caption("No expenses in this period.")

        with col_right:
            st.markdown("#### Savings by Type")
            savings_df = df_sel[df_sel["type"] == "Savings Deposit"]
            if not savings_df.empty:
                sav_summary = (
                    savings_df.groupby("savings_type")["amount"]
                    .sum()
                    .sort_values(ascending=False)
                )
                st.bar_chart(sav_summary)
            else:
                st.caption("No savings in this period.")

    # ---------- MONTHLY TREND TAB ----------
    with tab3:
        st.subheader("Monthly Cash Flow (All time)")

        if "date" in df_all.columns:
            df_all["date"] = pd.to_datetime(df_all["date"], errors="coerce")
            df_all = df_all.dropna(subset=["date"])
            df_all["year_month"] = df_all["date"].dt.to_period("M").astype(str)

            month_summary = (
                df_all.pivot_table(
                    index="year_month",
                    columns="type",
                    values="amount",
                    aggfunc="sum",
                )
                .fillna(0)
                .sort_index()
            )

            st.line_chart(month_summary)
        else:
            st.caption("No date information available.")


def page_transactions(tx_filtered: pd.DataFrame, selected_month: str):
    label_period = "All time" if selected_month == "All time" else selected_month
    st.header(f"📜 Transactions – {label_period}")

    if tx_filtered.empty:
        st.info("No transactions for this period.")
        return

    df = tx_filtered.copy()
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date

    st.dataframe(df.sort_values("date", ascending=False), use_container_width=True)


def page_debts(all_tx: pd.DataFrame, tx_filtered: pd.DataFrame, debts: pd.DataFrame, selected_month: str):
    st.header("💳 Debts and EMIs")

    # Form to add new debt
    with st.expander("Add or Update a Debt"):
        col1, col2 = st.columns(2)
        with col1:
            debt_name = st.text_input("Debt Name (e.g., Education Loan SBI)")
            lender = st.text_input("Lender / Bank", "")
            start_amount = st.number_input("Original Loan Amount", min_value=0.0, step=1000.0)
        with col2:
            interest_rate = st.number_input("Interest Rate (% per year)", min_value=0.0, step=0.1)
            emi = st.number_input("EMI (monthly)", min_value=0.0, step=500.0)
            start_date = st.date_input("Start Date", value=date.today())
        notes = st.text_area("Notes", "")

        if st.button("💾 Save Debt"):
            if debt_name.strip() == "" or start_amount <= 0:
                st.error("Debt name and original amount are required.")
            else:
                new_debt = {
                    "debt_name": debt_name.strip(),
                    "lender": lender,
                    "start_amount": float(start_amount),
                    "interest_rate": float(interest_rate),
                    "emi": float(emi),
                    "start_date": pd.to_datetime(start_date),
                    "notes": notes,
                }

                existing_idx = debts.index[debts["debt_name"] == debt_name.strip()].tolist()
                if existing_idx:
                    debts.loc[existing_idx[0]] = new_debt
                else:
                    debts = pd.concat([debts, pd.DataFrame([new_debt])], ignore_index=True)

                save_df(debts, DEBTS_FILE)
                st.success("Debt saved or updated successfully ✅")

    st.markdown("### Current Debts Summary")

    if debts.empty:
        st.info("No debts added yet.")
        return

    df_debts = debts.copy()

    # All-time debt payments for balance
    df_all_tx = all_tx.copy()
    df_all_tx["amount"] = pd.to_numeric(df_all_tx["amount"], errors="coerce").fillna(0)
    debt_payments_all = (
        df_all_tx[df_all_tx["type"] == "Debt Payment"]
        .groupby("debt_name")["amount"]
        .sum()
    )

    df_debts["paid_so_far"] = df_debts["debt_name"].map(debt_payments_all).fillna(0.0)
    df_debts["balance"] = df_debts["start_amount"] - df_debts["paid_so_far"]
    df_debts["progress"] = (df_debts["paid_so_far"] / df_debts["start_amount"]).fillna(0.0)

    show_cols = [
        "debt_name",
        "lender",
        "start_amount",
        "paid_so_far",
        "balance",
        "interest_rate",
        "emi",
        "start_date",
    ]
    st.dataframe(df_debts[show_cols], use_container_width=True)

    st.markdown("### Payoff Progress (All time)")
    for _, row in df_debts.iterrows():
        st.write(
            f"{row['debt_name']} - Paid: ₹ {row['paid_so_far']:,.0f} / ₹ {row['start_amount']:,.0f}"
        )
        st.progress(min(max(row["progress"], 0.0), 1.0))

    # Selected period debt payments (futuristic insight)
    st.markdown("---")
    label_period = "All time" if selected_month == "All time" else selected_month
    st.subheader(f"Debt Payments in {label_period}")

    df_sel = tx_filtered.copy()
    df_sel["amount"] = pd.to_numeric(df_sel["amount"], errors="coerce").fillna(0)
    sel_debt_pay = df_sel[df_sel["type"] == "Debt Payment"]
    if sel_debt_pay.empty:
        st.caption("No debt payments logged for this period.")
    else:
        grp = (
            sel_debt_pay.groupby("debt_name")["amount"]
            .sum()
            .reset_index()
            .sort_values("amount", ascending=False)
        )
        st.dataframe(grp, use_container_width=True)


def page_savings(tx_filtered: pd.DataFrame, selected_month: str):
    label_period = "All time" if selected_month == "All time" else selected_month
    st.header(f"🏦 Savings Overview – {label_period}")

    if tx_filtered.empty:
        st.info("No transactions for this period.")
        return

    df = tx_filtered.copy()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

    savings_df = df[df["type"] == "Savings Deposit"]
    if savings_df.empty:
        st.info("No savings deposits recorded for this period.")
        return

    st.subheader("Savings by Type and Account")
    group = (
        savings_df.groupby(["savings_type", "account"])["amount"]
        .sum()
        .reset_index()
        .sort_values("amount", ascending=False)
    )
    st.dataframe(group, use_container_width=True)

    st.subheader("Total Savings in this Period")
    total_savings = savings_df["amount"].sum()
    st.metric("Total Saved", f"₹ {total_savings:,.0f}")


def page_help():
    st.header("ℹ️ How to Use This App")

    st.markdown(
        """
### 1. Month Filter (top-left sidebar)
- Choose **All time** or a specific month (e.g. `2025-12`).
- All main pages (Summary, Transactions, Debts, Savings) adapt to this filter.

### 2. Add Entry  
- **Income**: salary, freelance, gift, etc.  
- **Expense**: daily spending (food, rent, petrol, etc.)  
- **Debt Payment**: EMIs, credit card payments.  
- **Savings Deposit**: money moved to FD, SIP, emergency fund, etc.

### 3. Summary Dashboard  
- Shows **selected-period** metrics + **all-time** snapshot.  
- Smart insights:
  - Daily burn rate (expense + debt + savings).
  - Savings rate (how much of income is going to savings).
  - Experimental **Financial Health Score**.

### 4. Debts and EMIs  
- Add each loan with original amount, interest, EMI.  
- Whenever you pay any EMI, log it as *Debt Payment* in **Add Entry**.  
- All-time progress bars show how close you are to being debt-free.  
- You can also see what you paid towards debt in the **selected period**.

### 5. Savings Overview  
- Shows how much you saved in the chosen period, grouped by type and account.  

### 6. Backup  
- Use sidebar **📦 Backup Data (CSV)** to download:
  - `transactions.csv`  
  - `debts.csv`  
- Store them in Google Drive / phone for safety.

This is your personal **finance cockpit** – income, expenses, debt and savings in one futuristic view 🚀
"""
    )


if __name__ == "__main__":
    main()
