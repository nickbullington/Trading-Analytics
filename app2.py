import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.title('WASDE Corn Analysis')

@st.cache_data
def pull_inspection_data(string, year_lst):
    df_lst = []
    for i in year_lst:
        file_path = string + '/CY' + i + '.csv'
        df = pd.read_csv(file_path, usecols=["Thursday", "Grain", "Class", "Destination", "Metric Ton"])
        df_lst.append(df)
    out_df = pd.concat(df_lst, axis=0)
    return out_df
    
def clean_data(data):
    df = data.copy()
    df.columns = [i.lower() for i in df.columns.astype(str)]
    df['report_date'] = pd.to_datetime(df['thursday'], format='%Y%m%d')
    df = df[['report_date', 'grain', 'class', 'destination', 'metric ton']].reset_index(drop=True)
    df['grain'] = [i + '-' + j if i == 'WHEAT' else i for i, j in zip(df['grain'], df['class'])]
    df = df[df['grain'].isin(['CORN', 'SORGHUM', 'SOYBEANS',
                              'WHEAT-HRS', 'WHEAT-HRW', 'WHEAT-SRW', 'WHEAT-SWW', 'WHEAT-HDWH'])].copy()
    
    return df
    
string = 'https://fgisonline.ams.usda.gov/ExportGrainReport'
year_lst = ['2019', '2020', '2021', '2022', '2023']
raw_df = pull_inspection_data(string, year_lst)
clean_df = clean_data(raw_df)


converted_data = clean_df.to_csv().encode('utf-8')
st.download_button('Historical WASDE Corn Data', data=converted_data, file_name='wasde_df.csv', mime='text/csv')


#st.plotly_chart(px.line(data))
#st.title('Ending Stocks')

#st.plotly_chart(px.histogram(data['ending_stocks_total']))
#st.dataframe(data)
#st.text('Hey, Kerianne. What is your favorite food?')
