import streamlit as st
import pandas as pd
import sqlite3
import datetime
import calendar
import re
import google.generativeai as genai # Correct library for Google's API

# --- Database functions ---
# Function to create a connection to the SQLite database
def get_db_connection():
    conn = sqlite3.connect('finance_tracker.db')
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    return conn

# Function to initialize the database tables
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            date TEXT,
            description TEXT,
            amount REAL,
            category TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY,
            category TEXT,
            budget REAL
        )
    ''')
    conn.commit()
    conn.close()

# Function to add a new transaction to the database
def add_transaction(date, description, amount, category):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO transactions (date, description, amount, category) VALUES (?, ?, ?, ?)',
              (date, description, amount, category))
    conn.commit()
    conn.close()

# Function to load all transactions from the database
def load_transactions():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
    conn.close()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df

# Function to add or update a budget
def add_budget(category, budget):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO budgets (category, budget) VALUES (?, ?)',
              (category, budget))
    conn.commit()
    conn.close()

# Function to load all budgets
def load_budgets():
    conn = get_db_connection()
    budgets_dict = pd.read_sql_query("SELECT category, budget FROM budgets", conn)
    conn.close()
    if not budgets_dict.empty:
        return budgets_dict.set_index('category')['budget'].to_dict()
    return {}

# --- LLM Functions (AI for categorization) ---
# Function to automatically categorize a transaction using a language model
def categorize_transaction(description):
    # Import the API key from a separate, secure file
    # Ensure a file named 'secret.py' exists in your project with the key defined
    try:
        from secret import API_KEY as api_key
    except ImportError:
        api_key = "" # Fallback if secret.py is not found
        st.warning("API categorization is disabled. Please create a 'secret.py' file with your API key to enable it.")

    if not api_key:
        return "Other" # Return 'Other' if no key is provided
    
    try:
        # Configure the Google Generative AI client with the provided API key
        genai.configure(api_key=api_key)
        
        # Use a single prompt to get the category
        prompt = f"Categorize the following transaction description into one of these categories: Food, Transportation, Housing, Entertainment, Bills, Other. Only respond with the category name.\n\nTransaction: {description}"
        
        model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
        response = model.generate_content(prompt)

        category = response.text
        # Remove any leading/trailing whitespace or special characters
        category = re.sub(r'[^a-zA-Z\s]', '', category).strip()
        # Fallback to 'Other' if the model gives an unexpected response
        if category not in ["Food", "Transportation", "Housing", "Entertainment", "Bills", "Other"]:
            return "Other"
        return category
    except Exception as e:
        st.error(f"Error with categorization service: {e}")
        return "Other" # Default to 'Other' if there's an API error

# --- Main app layout ---
st.set_page_config(layout="wide", page_title="Personal Finance Tracker")

# Initialize the database when the app starts
init_db()

# --- Sidebar for user input and filtering ---
with st.sidebar:
    st.title("Settings")

    st.header("Add a Transaction")
    with st.form("transaction_form", clear_on_submit=True):
        date = st.date_input("Date", datetime.date.today())
        description = st.text_input("Description")
        amount = st.number_input("Amount", min_value=0.01, format="%.2f")

        # Automatically predict category if description is provided
        predicted_category = "Other"
        if description:
             predicted_category = categorize_transaction(description)
        
        st.info(f"Predicted category: **{predicted_category}**")

        category = st.selectbox("Category", ["Food", "Transportation", "Housing", "Entertainment", "Bills", "Other"], index=["Food", "Transportation", "Housing", "Entertainment", "Bills", "Other"].index(predicted_category))
        
        submitted = st.form_submit_button("Add Transaction")
        if submitted:
            add_transaction(date, description, amount, category)
            st.success("Transaction added successfully!")

    st.header("Set Monthly Budgets")
    with st.form("budget_form", clear_on_submit=True):
        budget_category = st.selectbox("Category", ["Food", "Transportation", "Housing", "Entertainment", "Bills", "Other"])
        budget_amount = st.number_input("Monthly Budget", min_value=0.0, format="%.2f")
        submitted_budget = st.form_submit_button("Set Budget")
        if submitted_budget:
            add_budget(budget_category, budget_amount)
            st.success(f"Monthly budget for {budget_category} set to ${budget_amount:,.2f}.")
    
    st.header("Filter Transactions")
    all_transactions_df = load_transactions()
    
    with st.expander("Show Filters", expanded=True):
        # Create a list of all unique categories for the filter
        all_categories = list(all_transactions_df['category'].unique()) if not all_transactions_df.empty else ["Food", "Transportation", "Housing", "Entertainment", "Bills", "Other"]
        selected_categories = st.multiselect("Filter by Category", all_categories, default=all_categories)
        
        min_date = st.date_input("Start Date", value=datetime.date(2023, 1, 1), key='start_date')
        max_date = st.date_input("End Date", value=datetime.date.today(), key='end_date')

# --- Main content area with tabs ---
st.header("Personal Finance Dashboard")

# Filter the transactions based on the user's selections
if not all_transactions_df.empty:
    transactions_df = all_transactions_df[
        (all_transactions_df['category'].isin(selected_categories)) &
        (all_transactions_df['date'].dt.date >= min_date) &
        (all_transactions_df['date'].dt.date <= max_date)
    ]
else:
    transactions_df = pd.DataFrame()


tab1, tab2 = st.tabs(["📊 Dashboard", "📜 Transaction History"])

with tab1:
    budgets = load_budgets()

    if not transactions_df.empty:
        # Data processing for charts and tips
        transactions_df['month'] = transactions_df['date'].dt.to_period('M')
        transactions_df['month_str'] = transactions_df['date'].dt.strftime("%Y-%m")
        current_month_str = datetime.date.today().strftime("%Y-%m")
        
        # Spending by category
        spending_by_category = transactions_df[transactions_df['month_str'] == current_month_str].groupby('category')['amount'].sum().reset_index()

        # Monthly spending over time
        monthly_spending = transactions_df.groupby('month_str')['amount'].sum().reset_index()
        monthly_spending['month_str'] = pd.to_datetime(monthly_spending['month_str']).dt.date
        
        # Display charts in columns for a better layout
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Spending by Category (This Month)")
            st.bar_chart(spending_by_category, x='category', y='amount')
            
        with col2:
            st.subheader("Monthly Spending Over Time")
            st.line_chart(monthly_spending, x='month_str', y='amount')

        # Budget vs Actual Spending
        st.subheader("Budget vs. Actual Spending (This Month)")
        
        budget_comparison = []
        for category, budget in budgets.items():
            actual_spending = spending_by_category[spending_by_category['category'] == category]['amount'].sum()
            remaining = budget - actual_spending
            budget_comparison.append({
                'Category': category,
                'Budget': budget,
                'Actual Spending': actual_spending,
                'Remaining': remaining
            })
        
        budget_df = pd.DataFrame(budget_comparison)
        if not budget_df.empty:
            st.dataframe(budget_df, use_container_width=True)
        else:
            st.info("No budgets have been set yet.")
            
        # Financial Tips section
        st.subheader("Financial Tips")
        
        over_budget_categories = [row['Category'] for index, row in budget_df.iterrows() if row['Remaining'] < 0]
        if over_budget_categories:
            st.warning(f"🚨 **Warning:** You are over budget in the following categories: {', '.join(over_budget_categories)}. Consider cutting back on non-essential spending.")
        else:
            st.success("🎉 **Great job!** You are on track with your spending this month.")
    else:
        st.info("No transactions found. Use the sidebar to get started.")

with tab2:
    st.subheader("Transaction History")
    # Use an expander to make the transaction history collapsible
    with st.expander("View filtered transactions", expanded=True):
        if not transactions_df.empty:
            st.dataframe(transactions_df, use_container_width=True)
        else:
            st.info("No transactions to display based on your filters.")
