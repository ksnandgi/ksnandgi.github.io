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
        st.title("Finance Tracker Login")
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

# When running on Streamlit Cloud, actual files may be ephemeral.
# We'll still use CSVs, but you can download them regularly as backup.

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
        # try to parse date-like columns if present
        for col in ["date", "start_date", "created_at"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="ignore")
        return df
    else:
        return pd.DataFrame(columns=columns)


def save_df(df: pd.DataFrame, path: Path):
    df.to_csv(path, index=False)


def ensure_files():
    # create empty files if not exist
    if not TRANSACTIONS_FILE.exists():
        save_df(pd.DataFrame(columns=TRANSACTION_COLUMNS), TRANSACTIONS_FILE)
    if not DEBTS_FILE.exists():
        save_df(pd.DataFrame(columns=DEBT_COLUMNS), DEBTS_FILE)


def main():
    st.set_page_config(
        page_title="Personal Finance Tracker",
        page_icon="💰",
        layout="wide",
    )

    ensure_files()

    st.sidebar.title("Personal Finance Tracker")
    menu = st.sidebar.radio(
        "Go to",
        ["Add Entry", "Summary Dashboard", "Transactions", "Debts & EMIs", "Savings Overview", "Help"],
    )

    transactions = load_df(TRANSACTIONS_FILE, TRANSACTION_COLUMNS)
    debts = load_df(DEBTS_FILE, DEBT_COLUMNS)

    # 🔽 Backup buttons in sidebar
    with st.sidebar.expander("Backup Data (CSV)"):
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

    if menu == "Add Entry":
        page_add_entry(transactions, debts)
    elif menu == "Summary Dashboard":
        page_summary(transactions, debts)
    elif menu == "Transactions":
        page_transactions(transactions)
    elif menu == "Debts & EMIs":
        page_debts(transactions, debts)
    elif menu == "Savings Overview":
        page_savings(transactions)
    else:
        page_help()


def page_add_entry(transactions: pd.DataFrame, debts: pd.DataFrame):
    st.header("Add New Entry")

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

    if st.button("Save Entry"):
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
        st.success("Entry saved successfully.")


def page_summary(transactions: pd.DataFrame, debts: pd.DataFrame):
    st.header("Summary Dashboard")

    if transactions.empty:
        st.info("No transactions yet. Add your first entry in 'Add Entry' page.")
        return

    df = transactions.copy()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

    total_income = df.loc[df["type"] == "Income", "amount"].sum()
    total_expense = df.loc[df["type"] == "Expense", "amount"].sum()
    total_debt_paid = df.loc[df["type"] == "Debt Payment", "amount"].sum()
    total_savings = df.loc[df["type"] == "Savings Deposit", "amount"].sum()

    net_balance = total_income - (total_expense + total_debt_paid + total_savings)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Income", f"Rs {total_income:,.0f}")
    c2.metric("Total Expenses", f"Rs {total_expense:,.0f}")
    c3.metric("Debt Paid", f"Rs {total_debt_paid:,.0f}")
    c4.metric("Savings Deposited", f"Rs {total_savings:,.0f}")
    c5.metric("Net Balance", f"Rs {net_balance:,.0f}")

    st.markdown("---")
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Expenses by Category")
        expense_df = df[df["type"] == "Expense"]
        if not expense_df.empty:
            cat_summary = (
                expense_df.groupby("category")["amount"]
                .sum()
                .sort_values(ascending=False)
            )
            st.bar_chart(cat_summary)
        else:
            st.caption("No expenses recorded yet.")

    with col_right:
        st.subheader("Savings by Type")
        savings_df = df[df["type"] == "Savings Deposit"]
        if not savings_df.empty:
            sav_summary = (
                savings_df.groupby("savings_type")["amount"]
                .sum()
                .sort_values(ascending=False)
            )
            st.bar_chart(sav_summary)
        else:
            st.caption("No savings recorded yet.")

    st.markdown("---")
    st.subheader("Monthly Cash Flow")

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["year_month"] = df["date"].dt.to_period("M").astype(str)

        month_summary = (
            df.pivot_table(
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


def page_transactions(transactions: pd.DataFrame):
    st.header("All Transactions")

    if transactions.empty:
        st.info("No transactions yet.")
        return

    df = transactions.copy()
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date

    st.dataframe(df.sort_values("date", ascending=False), use_container_width=True)


def page_debts(transactions: pd.DataFrame, debts: pd.DataFrame):
    st.header("Debts and EMIs")

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

        if st.button("Save Debt"):
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
                st.success("Debt saved or updated successfully.")

    st.markdown("### Current Debts Summary")

    if debts.empty:
        st.info("No debts added yet.")
        return

    df_debts = debts.copy()

    df_tx = transactions.copy()
    df_tx["amount"] = pd.to_numeric(df_tx["amount"], errors="coerce").fillna(0)
    debt_payments = (
        df_tx[df_tx["type"] == "Debt Payment"]
        .groupby("debt_name")["amount"]
        .sum()
    )

    df_debts["paid_so_far"] = df_debts["debt_name"].map(debt_payments).fillna(0.0)
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

    st.markdown("### Payoff Progress")
    for _, row in df_debts.iterrows():
        st.write(
            f"{row['debt_name']} - Paid: Rs {row['paid_so_far']:,.0f} / Rs {row['start_amount']:,.0f}"
        )
        st.progress(min(max(row["progress"], 0.0), 1.0))


def page_savings(transactions: pd.DataFrame):
    st.header("Savings Overview")

    if transactions.empty:
        st.info("No transactions yet.")
        return

    df = transactions.copy()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

    savings_df = df[df["type"] == "Savings Deposit"]
    if savings_df.empty:
        st.info("No savings deposits recorded yet.")
        return

    st.subheader("Savings by Type and Account")
    group = (
        savings_df.groupby(["savings_type", "account"])["amount"]
        .sum()
        .reset_index()
        .sort_values("amount", ascending=False)
    )
    st.dataframe(group, use_container_width=True)

    st.subheader("Total Savings")
    total_savings = savings_df["amount"].sum()
    st.metric("Total Saved", f"Rs {total_savings:,.0f}")


def page_help():
    st.header("How to Use This App")

    st.markdown(
        """
1. **Add Entry**  
   - Income: salary, freelance, gift, etc.  
   - Expense: daily spending (food, rent, petrol, etc.)  
   - Debt Payment: EMIs, credit card payments.  
   - Savings Deposit: money moved to FD, SIP, emergency fund, etc.

2. **Summary Dashboard**  
   - Shows totals of Income, Expenses, Debt Paid, Savings.  
   - Net Balance = Income - (Expenses + Debt + Savings).  
   - Charts for expenses by category, savings by type, and monthly trends.

3. **Debts and EMIs**  
   - First add each loan with original amount, interest, EMI.  
   - Whenever you pay any EMI, log it as *Debt Payment* in **Add Entry**.  
   - The app tracks paid so far and remaining balance.

4. **Savings Overview**  
   - Shows how much you have saved by type and by account (bank, SIP, etc.).

5. **Backup**  
   - Use the sidebar **Backup Data (CSV)** section to download:  
     - `transactions.csv`  
     - `debts.csv`  
   - Store them in Google Drive or phone storage for safety.
"""
    )


if __name__ == "__main__":
    main()
