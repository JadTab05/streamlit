import streamlit as st
import pandas as pd
import io

st.title('Générateur de Préfacts pour tous les sous-traitants !')
 
uploaded_file = st.file_uploader("Veuillez upload le fichier de préfact entier", type=['csv', 'xlsx'])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.write("Data Preview:")
        st.dataframe(df)

        # Convert and Check the Date Column
        if 'Grouped Services Commitment Date' in df.columns:
            df['Grouped Services Commitment Date'] = pd.to_datetime(df['Grouped Services Commitment Date'], errors='coerce')  # Convert to datetime
        else:
            st.error("The uploaded file does not contain a 'Grouped Services Commitment Date' column.")
            st.stop()  # Stop the app if the column is not present

        # Date Range
        min_date = df['Grouped Services Commitment Date'].min().date()
        max_date = df['Grouped Services Commitment Date'].max().date()

        # User chooses a date range
        start_date = st.date_input("Start date", min_value=min_date, max_value=max_date, value=min_date)
        end_date = st.date_input("End date", min_value=min_date, max_value=max_date, value=max_date)

        # Apply the date range filter
        filtered_df = df[(df['Grouped Services Commitment Date'] >= pd.Timestamp(start_date)) & 
                         (df['Grouped Services Commitment Date'] <= pd.Timestamp(end_date))]

        # Display the filtered data
        st.write("Filtered Data Preview:")
        st.dataframe(filtered_df)

        # Get all unique suppliers from the file
        if 'Supplier Name' in df.columns:
            unique_suppliers = filtered_df['Supplier Name'].unique()
        else:
            st.error("Il manque la colonne Supplier Name")
            st.stop()  # Stop the app if the column is not present

        # Step 6: Function to convert DataFrame to Excel for download
        def to_excel(df, sheet_name='Sheet1'):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            processed_data = output.getvalue()
            return processed_data

        # Generate Excel files for each unique supplier in the filtered DataFrame
        excel_files = {}
        
        for supplier in unique_suppliers:
            temp_df = filtered_df[filtered_df['Supplier Name'] == supplier]
            if not temp_df.empty:  # Only create an Excel file if there's data for the supplier
                # Create a filename using the supplier name and date range
                file_name = f"{supplier}_{start_date.strftime('%Y-%m-%d')}_to_{end_date.strftime('%Y-%m-%d')}.xlsx"
                excel_files[file_name] = to_excel(temp_df)

        # Step 7: Provide download links for each filtered dataset
        if excel_files:
            for file_name, data in excel_files.items():
                st.download_button(
                    label=f"Download {file_name}",
                    data=data,
                    file_name=file_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.write("Aucune donnée")

    except Exception as e:
        st.error(f"Error processing file: {e}")

else:
    st.write("Veuillez upload le fichier pour commencer.")
