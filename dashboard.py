import plotly
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Set page config
st.set_page_config(page_title="Expenditure Analysis Dashboard", layout="wide")

# Title
st.title("Expenditure Analysis Dashboard")

# File uploader
uploaded_file = st.file_uploader("Upload your transactions file (CSV format)", type=["csv"])

if uploaded_file is not None:
    # Read the CSV file
    df = pd.read_csv(uploaded_file)
    
    # Convert 'Date' to datetime
    try:
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
    except KeyError:
        st.error("CSV must contain a 'Date' column.")
        st.stop()
    except ValueError:
        st.error("Invalid date format in 'Date' column. Expected format: dd/mm/yyyy")
        st.stop()
    
    required_columns = ['Transaction Details', 'Amount', 'Tags']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        st.error(f"CSV is missing required columns: {', '.join(missing_cols)}")
        st.stop()
    
    # Clean 'Tags' by removing '#?? '
    df['Tags'] = df['Tags'].str.replace(r'#\?\?\s*', '', regex=True)
    
    # Automatic categorization based on 'Transaction Details'
    categories_keywords = {
        'Food and Dining': ['swiggy', 'zomato', 'ubereats', 'heisetasse', 'restaurant', 'hotel', 'food', 'dining', 'taco bell', 'domi', 'bakers', 'coffee', 'leons', 'hang out', 'third wave', 'churrolto', 'ushodaya', 'tibbs', 'koi', 'ding dong', 'cara cara'],
        'Groceries': ['grocery', 'bigbasket', 'grofers', 'supermarket', 'milk', 'vegetables', 'blinkit', 'zepto', 'kpn', 'ushodaya'],
        'Transfers': ['money sent'],
        'Shopping': ['amazon', 'flipkart', 'myntra', 'shopping', 'clothing', 'electronics', 'diverse retails', 'westside', 'techmash'],
        'Travel & Stay': ['uber', 'ola', 'rapido', 'hyderabad metro', 'brevistay'],
        'Entertainment': ['netflix', 'prime', 'hotstar', 'movie', 'cinema', 'subscription', 'apple media', 'spotify'],
        'Fuel': ['fuel', 'petrol'],
        'Loan': ["Vatturi Paritosh"],
        'Investments/ Savings': ['icclgroww'],
        'Money Received': ['received from']
    }
    
    def categorize_transaction(details, tags):
        details_lower = str(details).lower()
        for category, keywords in categories_keywords.items():
            for keyword in keywords:
                if keyword in details_lower:
                    return category
        if 'Money Received' in tags:
            return 'Money Received'
        return 'Other'
    
    # Apply auto-categorization
    df['Category'] = df.apply(lambda row: categorize_transaction(row['Transaction Details'], row['Tags']), axis=1)
    
    # Store df in session state for editing
    if 'df' not in st.session_state:
        st.session_state.df = df
    
    df = st.session_state.df
    
    # Display raw data with color coding
    if st.checkbox("Show raw data"):
        st.subheader("Raw Data")
        def color_row(row):
            if row['Amount'] > 0:
                return ['color: green'] * len(row)
            elif row['Amount'] < 0:
                return ['color: red'] * len(row)
            else:
                return [''] * len(row)
        st.dataframe(df.style.apply(color_row, axis=1), use_container_width=True)
    
    # Sidebar for filters
    st.sidebar.header("Filters")
    
    # Date range filter
    min_date = df['Date'].min().date()
    max_date = df['Date'].max().date()
    start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)
    df_filtered = df[(df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)]
    
    # Category filter (multi-select)
    all_categories = sorted(df['Category'].unique())
    selected_categories = st.sidebar.multiselect("Select Categories", all_categories, default=all_categories)
    if selected_categories:
        df_filtered = df_filtered[df_filtered['Category'].isin(selected_categories)]
    
    # Amount range filter
    min_amount = float(df['Amount'].min())
    max_amount = float(df['Amount'].max())
    amount_range = st.sidebar.slider("Amount range", min_amount, max_amount, (min_amount, max_amount))
    df_filtered = df_filtered[(df_filtered['Amount'] >= amount_range[0]) & (df_filtered['Amount'] <= amount_range[1])]
    
    # Compute credits and debits
    credits = df_filtered[df_filtered['Amount'] > 0]['Amount'].sum()
    debits = abs(df_filtered[df_filtered['Amount'] < 0]['Amount'].sum())
    
    # Display credited and debited at the top with color
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<h2 style='color: green;'>Total Credited: ₹{credits:,.2f}</h2>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<h2 style='color: red;'>Total Debited: ₹{debits:,.2f}</h2>", unsafe_allow_html=True)
    
    # Prepare expenditures dataframe
    exp_df = df_filtered[df_filtered['Amount'] < 0].copy()
    exp_df['Abs Amount'] = -exp_df['Amount']
    
    # Visual 1: Pie chart of expenditures by Tags
    st.subheader("Expenditures by Tags (Pie Chart)")
    tag_sum = exp_df.groupby('Tags')['Abs Amount'].sum().reset_index()
    fig_pie_tags = px.pie(tag_sum, values='Abs Amount', names='Tags', title="Breakdown by Tags")
    fig_pie_tags.update_traces(textinfo='value+label')
    st.plotly_chart(fig_pie_tags, use_container_width=True)
    
    # Visual 2: Pie chart of expenditures by auto Category
    st.subheader("Expenditures by Auto Category (Pie Chart)")
    category_sum = exp_df.groupby('Category')['Abs Amount'].sum().reset_index()
    fig_pie_cat = px.pie(category_sum, values='Abs Amount', names='Category', title="Breakdown by Auto Categories")
    fig_pie_cat.update_traces(textinfo='value+label')
    st.plotly_chart(fig_pie_cat, use_container_width=True)
    
    # Visual 3: Bar chart of expenditures by Tags
    st.subheader("Expenditures by Tags (Bar Chart)")
    fig_bar_tags = px.bar(tag_sum, x='Tags', y='Abs Amount', title="Bar Chart by Tags")
    st.plotly_chart(fig_bar_tags, use_container_width=True)
    
    # Visual 4: Bar chart of expenditures by Category
    st.subheader("Expenditures by Auto Category (Bar Chart)")
    fig_bar_cat = px.bar(category_sum, x='Category', y='Abs Amount', title="Bar Chart by Auto Categories")
    st.plotly_chart(fig_bar_cat, use_container_width=True)
    
    # Visual 5: Time series line chart of daily expenditures
    st.subheader("Daily Expenditures Over Time")
    daily_sum = exp_df.resample('D', on='Date')['Abs Amount'].sum().reset_index()
    fig_line = px.line(daily_sum, x='Date', y='Abs Amount', title="Daily Total Expenditures")
    st.plotly_chart(fig_line, use_container_width=True)
    
    # Visual 6: Scatter plot of individual transactions (all, with colors)
    st.subheader("Individual Transactions (Scatter Plot)")
    fig_scatter = px.scatter(df_filtered, x='Date', y='Amount', color='Category', 
                             hover_data=['Transaction Details', 'Tags'], title="Transactions by Date and Amount")
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Table of top debits
    st.subheader("Top 10 Debits")
    top_tx = exp_df.sort_values('Abs Amount', ascending=False).head(10)
    def color_debit(row):
        return ['color: red'] * len(row)
    st.dataframe(top_tx[['Date', 'Transaction Details', 'Abs Amount', 'Tags', 'Category']].style.apply(color_debit, axis=1))
    
    # Unclassified transactions editor
    uncat = exp_df[exp_df['Category'] == 'Other'].copy()
    if not uncat.empty:
        st.subheader("Unclassified Transactions (Assign Category)")
        categories_list = list(categories_keywords.keys())
        edited_uncat = st.data_editor(
            uncat[['Date', 'Transaction Details', 'Abs Amount', 'Tags', 'Category']],
            column_config={
                "Category": st.column_config.SelectboxColumn(
                    "Category",
                    options=categories_list,
                    required=True,
                )
            },
            disabled=["Date", "Transaction Details", "Abs Amount", "Tags"],
            hide_index=False,
            key="uncat_editor"
        )
        if st.button("Update Categories"):
            for idx, row in edited_uncat.iterrows():
                if row['Category'] != 'Other':
                    st.session_state.df.loc[idx, 'Category'] = row['Category']
            st.rerun()
else:
    st.info("Please upload a CSV file to begin analysis. The file should have columns: Date, Transaction Details, Amount, Tags.")