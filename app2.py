import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.title('WASDE Corn Analysis')
string = r'C:\Users\nb153794\OneDrive - The Andersons, Inc\Desktop' \
    r'\Work Projects\wasde analysis\grain Corn.csv'

@st.cache_data
def data_pull(string_path):
    df = pd.read_csv(string_path)
    df['release_date'] = pd.to_datetime(df['release_date'])
    df = df.set_index('release_date')
    return df

data = data_pull(string)
converted_data = data.to_csv().encode('utf-8')
st.download_button('Historical WASDE Corn Data', data=converted_data, file_name='wasde_df.csv', mime='text/csv')
st.plotly_chart(px.line(data))
st.title('Ending Stocks')

st.plotly_chart(px.histogram(data['ending_stocks_total']))
#st.dataframe(data)
st.text('Hey, Kerianne. What is your favorite food?')
