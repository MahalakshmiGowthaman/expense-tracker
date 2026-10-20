import os
import streamlit as st
import pandas as pd
import plotly.express as px

DATA_FILE = "expenses.csv"
COLUMNS = ["Date", "Category", "Amount", "Description"]
CATEGORIES = ["Food", "Travel", "Shopping", "Bills", "Other"]

st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💰",
    layout="wide"
)


def load_data():
    """Read expenses.csv. If it doesn't exist yet, create an empty one with headers."""
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        pd.DataFrame(columns=COLUMNS).to_csv(DATA_FILE, index=False)
    return pd.read_csv(DATA_FILE)


def make_label(df):
    """Build a readable 'date | category | amount | description' label for each row."""
    return (
        df["Date"].astype(str) + " | " +
        df["Category"].astype(str) + " | " +
        df["Amount"].astype(str) + " | " +
        df["Description"].astype(str)
    )


st.title("💰 Expense Tracker Dashboard")
st.caption("Track your daily expenses in a simple and clean way")

# ---------------- ADD EXPENSE ----------------
date = st.date_input("Date")
category = st.selectbox("Category", CATEGORIES)
amount = st.number_input("Amount", min_value=0.0, step=1.0)
description = st.text_input("Description")

if st.button("Add Expense"):
    if amount == 0 or description.strip() == "":
        st.warning("Please enter valid Amount and Description")
    else:
        new_data = pd.DataFrame({
            "Date": [date],
            "Category": [category],
            "Amount": [amount],
            "Description": [description.strip()]
        })
        all_data = pd.concat([load_data(), new_data], ignore_index=True)
        all_data.to_csv(DATA_FILE, index=False)
        st.success("Expense Added Successfully")
        st.rerun()

# ---------------- LOAD DATA ----------------
df = load_data()
df["Date"] = pd.to_datetime(df["Date"])
df["Amount"] = pd.to_numeric(df["Amount"])
df = df[::-1].reset_index(drop=True)  # newest first

# ---------------- MONTHLY FILTER ----------------
st.markdown("---")
st.subheader("🗓️ Filter by Month")

df["Month"] = df["Date"].dt.to_period("M").astype(str)
months = ["All"] + sorted(df["Month"].unique().tolist(), reverse=True)
selected_month = st.selectbox("Select Month", months)

if selected_month != "All":
    filtered_df = df[df["Month"] == selected_month]
else:
    filtered_df = df

# ---------------- METRICS ----------------
col1, col2, col3 = st.columns(3)
col1.metric("Total Expenses", f"₹ {filtered_df['Amount'].sum():,.0f}")
col2.metric("Transactions", len(filtered_df))
col3.metric(
    "Highest Expense",
    f"₹ {filtered_df['Amount'].max():,.0f}" if len(filtered_df) > 0 else "₹ 0"
)

st.markdown("---")

# ---------------- SHOW DATA ----------------
st.subheader("📋 All Expenses")
display_df = filtered_df.drop(columns=["Month"]).copy()
display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d")
st.dataframe(display_df, width="stretch", hide_index=True)

# ---------------- DOWNLOAD BUTTON ----------------
csv = display_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Download Expenses as CSV",
    data=csv,
    file_name=f"expenses_{selected_month}.csv",
    mime="text/csv"
)

st.markdown("---")

# ---------------- DELETE EXPENSE ----------------
st.subheader("Delete Expense")

df_for_ops = load_data()

if df_for_ops.empty:
    st.info("No expenses to delete yet.")
else:
    labels = make_label(df_for_ops)
    # select by row number, so identical-looking rows are never deleted together
    del_idx = st.selectbox(
        "Select expense to delete",
        df_for_ops.index,
        format_func=lambda i: labels[i]
    )

    if st.button("Delete Selected Expense"):
        df_for_ops = df_for_ops.drop(index=del_idx)
        df_for_ops.to_csv(DATA_FILE, index=False)
        st.success("Expense deleted successfully!")
        st.rerun()

# ---------------- EDIT EXPENSE ----------------
st.subheader("Edit Expense")

df_edit = load_data()

if df_edit.empty:
    st.info("No expenses to edit yet.")
else:
    labels = make_label(df_edit)
    edit_idx = st.selectbox(
        "Select expense to edit",
        df_edit.index,
        format_func=lambda i: labels[i]
    )
    selected_row = df_edit.loc[edit_idx]

    current_cat = selected_row["Category"]
    cat_index = CATEGORIES.index(current_cat) if current_cat in CATEGORIES else 0

    new_date = st.date_input("Edit Date", value=pd.to_datetime(selected_row["Date"]))
    new_category = st.selectbox("Edit Category", CATEGORIES, index=cat_index)
    new_amount = st.number_input("Edit Amount", value=float(selected_row["Amount"]), min_value=0.0, step=1.0)
    new_description = st.text_input("Edit Description", value=str(selected_row["Description"]))

    if st.button("Update Expense"):
        df_edit.loc[edit_idx, "Date"] = new_date.strftime("%Y-%m-%d")
        df_edit.loc[edit_idx, "Category"] = new_category
        df_edit.loc[edit_idx, "Amount"] = new_amount
        df_edit.loc[edit_idx, "Description"] = new_description
        df_edit.to_csv(DATA_FILE, index=False)
        st.success("Expense Updated Successfully!")
        st.rerun()

# ---------------- CHARTS ----------------
st.markdown("---")
st.subheader("📊 Category Wise Spending")

if len(filtered_df) > 0:
    col1, col2 = st.columns(2)
    category_data = filtered_df.groupby("Category")["Amount"].sum().reset_index()

    # Bar chart
    bar_fig = px.bar(
        category_data,
        x="Category",
        y="Amount",
        color="Category",
        title="Spending by Category (Bar)",
        text_auto=True
    )
    col1.plotly_chart(bar_fig, width="stretch")

    # Pie chart
    pie_fig = px.pie(
        category_data,
        names="Category",
        values="Amount",
        title="Spending by Category (Pie)",
        hole=0.3
    )
    col2.plotly_chart(pie_fig, width="stretch")
else:
    st.info("No data available for selected month.")
