import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

def load_data(uploaded_file):
    """Load CSV data from the uploaded file."""
    df = pd.read_csv(uploaded_file, usecols=['User ID', 'Start Date', 'End Date', 'Zone', 'Type'])
    df['Start Date'] = pd.to_datetime(df['Start Date'])
    df['End Date'] = pd.to_datetime(df['End Date']).fillna(pd.to_datetime('today')).dt.date
    return df

def filter_data(df, zone_filter, type_filter):
    """Filter data based on selected zone and type."""
    if zone_filter != "All":
        df = df[df['Zone'] == zone_filter]
    if type_filter != "All":
        df = df[df['Type'] == type_filter]
    return df

def create_presence_df(filtered_df):
    """Create a DataFrame indicating user presence over time."""
    date_range_list = []
    for index, row in filtered_df.iterrows():
        start_date = row['Start Date']
        end_date = row['End Date']
        date_range = pd.date_range(start=start_date, end=end_date)
        for date in date_range:
            date_range_list.append({'Date': date, 'User ID': row['User ID']})
    return pd.DataFrame(date_range_list)

def compute_time_series(df):
    """Compute time series metrics from presence DataFrame."""
    df = df[['Date', 'User ID']]
    pivot_df = df.pivot_table(index='Date', columns='User ID', aggfunc=lambda x: 1, fill_value=0)
    months_active_per_user = pivot_df.cumsum(axis=0) / 30.0
    TS = months_active_per_user.replace(0, np.nan).apply(pd.Series.describe, axis=1)
    TS.index = pd.to_datetime(TS.index)  # Ensure the index is datetime
    TS = TS[TS.index.day == 1]  # Retain only the first day of each month
    return TS

def plot_data(data):
    """Create and display the time series plot."""
    plt.figure(figsize=(14, 7))
    sns.set_theme(style='whitegrid')

    # Ensure the 'Date' column is used as the x-axis
    sns.lineplot(x=data['Date'], y=data['mean'], marker='o', color='royalblue', label='Mean', linewidth=2.5)
    plt.plot(data['Date'], data['25%'], marker='o', color='orange', linestyle='--', label='Q1', linewidth=1.5)
    plt.plot(data['Date'], data['50%'], marker='o', color='green', linestyle='--', label='Median', linewidth=1.5)
    plt.plot(data['Date'], data['75%'], marker='o', color='red', linestyle='--', label='Q3', linewidth=1.5)
    plt.fill_between(data['Date'], data['25%'], data['75%'], color='lightgrey', alpha=0.5, label='Interquartile Range')

    # Adding title and labels
    plt.title('Evolution of Retention Duration Over Time', fontsize=18)
    plt.xlabel('Date', fontsize=14)
    plt.ylabel('Value', fontsize=14)
    plt.grid(visible=True)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    st.pyplot(plt)

def to_excel(df):
    """Convert DataFrame to an Excel file in memory."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=True, sheet_name='Sheet1')
    processed_data = output.getvalue()
    return processed_data

# Main Streamlit App
st.title('User Retention Analysis App')

# File upload for CSV
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file:
    st.write("File uploaded successfully!")
    
    try:
        df = load_data(uploaded_file)
        st.write("Data loaded successfully!")
        st.dataframe(df.head())  # Show a preview of the data

        # Create filters for Zone and Type
        zone_options = df['Zone'].unique().tolist() + ['All']
        type_options = df['Type'].unique().tolist() + ['All']

        zone_filter = st.selectbox("Select Zone:", zone_options, index=zone_options.index('All'))
        type_filter = st.selectbox("Select Type:", type_options, index=type_options.index('All'))

        # Filter data
        filtered_df = filter_data(df, zone_filter, type_filter)
        st.write("Data filtered successfully!")

        # Create presence DataFrame
        presence_df = create_presence_df(filtered_df)

        # Compute time series data
        time_series_data = compute_time_series(presence_df)

        # Reset index for plotting and ensure 'Date' is a column
        time_series_data.reset_index(inplace=True)
        time_series_data['Date'] = pd.to_datetime(time_series_data['Date'])  # Ensure 'Date' is datetime

        # Plot data
        st.write("Generating plot...")
        plot_data(time_series_data)

        # Download button for Excel
        st.write("Download the time series data as an Excel file:")
        excel_file = to_excel(time_series_data)
        st.download_button(
            label="Download Excel",
            data=excel_file,
            file_name='time_series_data.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.warning("Please upload a CSV file to get started.")
