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


def string_format(value):
    return f'{value:,}'.replace('.0', '')

def build_last_week_destination_table(clean_data):
    df = clean_data.copy()
    df = df.set_index(df['report_date'])
    last_week = df.index.unique()[-1].strftime('%Y-%m-%d')
    last_week_df = df[df.index == last_week]
    
    lst = []
    for i in last_week_df['grain'].unique():
        comm_df = last_week_df[last_week_df['grain'] == i].copy()
        grouped_df = comm_df[['destination', 'metric ton']].groupby('destination').sum()
        grouped_df = grouped_df.rename(columns={'metric ton': i})
        lst.append(grouped_df)
    
    out_df = pd.concat(lst, axis=1).sort_index()
    out_df = out_df.reindex(sorted(out_df.columns), axis=1)
    
    wheat_all = out_df.iloc[:, -4:].sum(axis=1)
    wheat_all = [i if i != 0 else np.nan for i in wheat_all]
    out_df.columns = [i[-3:] if 'WHEAT' in i else i for i in out_df.columns.astype(str)]
    out_df.insert(3, 'WHEAT-ALL', wheat_all)
    out_df.loc['GRAND TOTAL'] = out_df.sum(numeric_only=True)
    out_df = out_df.fillna(0)
    
    #out_df.to_csv(r'C:\Users\nb153794\OneDrive - The Andersons, Inc\Desktop\Work Projects' \
    #              fr'\Weekly Grain Inspections\Historical Weekly Destination Snapshots\grain_{last_week}.csv')
    
    out_df = out_df.applymap(string_format).reset_index()
    
    return out_df, last_week

dest_sum_df, last_week_string = build_last_week_destination_table(clean_df)

def weekly_sum_snapshot(clean_data):
    df = clean_data.copy()
    
    dct = {}
    for i in df['report_date'].unique():
        date_df = df[df['report_date'] == i].copy()
        grouped_df = date_df.groupby('grain')['metric ton'].sum()
        dct[i] = grouped_df
    
    out_df = pd.DataFrame(dct).T
    out_df['WHEAT-ALL'] = out_df.iloc[:, -4:].sum(axis=1)
    
    save_date = out_df.index[-1].strftime('%Y-%m-%d')
    
    #out_df.to_csv(r'\week_ending_{save_date}.csv')
    
    return out_df

historical_snapshot_df = weekly_sum_snapshot(clean_df)

def crop_year(grain, date):
    if 'WHEAT' in grain:
        if date.month <= 5:
            return date.year
        else:
            return date.year + 1
    else:
        if date.month <= 8:
            return date.year
        else:
            return date.year + 1

def build_inspection_dct(clean_data):
    df = clean_data.copy()
    df['crop_year'] = df.apply(lambda x: crop_year(x['grain'], x['report_date']), axis=1)

    dct = {}
    for i in df['grain'].unique():
        grain_df = df[df['grain'] == i].copy()
        in_dct = {}
        for j in grain_df['crop_year'].unique()[1:]:
            year_df = grain_df[grain_df['crop_year'] == j].copy()
            summed = year_df.groupby('report_date')['metric ton'].sum()
            in_dct[j] = summed.values
            
        dff = pd.DataFrame.from_dict(in_dct, orient='index').T
        dct[i] = dff
    
    dct['WHEAT-ALL'] = dct['WHEAT-HRW'] + dct['WHEAT-HRS'] + dct['WHEAT-SRW'] + dct['WHEAT-SWW'] #+ dct['WHEAT-HDWH']

    return dct

annual_inspections_dct = build_inspection_dct(clean_df)

for i, j in annual_inspections_dct.items():
    st.title(i)
    st.write(j)
