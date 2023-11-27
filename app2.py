
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.title('United States Weekly Export Inspections')

st.text('revisions from previous week will go here')

@st.cache_data(ttl=20*60)
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
    df = df.sort_values(by='report_date')
    df = df[['report_date', 'grain', 'class', 'destination', 'metric ton']].reset_index(drop=True)
    df['grain'] = [i + '-' + j if i == 'WHEAT' else i for i, j in zip(df['grain'], df['class'])]
    df = df[df['grain'].isin(['CORN', 'SORGHUM', 'SOYBEANS',
                              'WHEAT-HRS', 'WHEAT-HRW', 'WHEAT-SRW', 'WHEAT-SWW'])].copy() #'WHEAT-HDWH'
    
    return df
    
string = 'https://fgisonline.ams.usda.gov/ExportGrainReport'
year_lst = ['2019', '2020', '2021', '2022', '2023']
raw_df = pull_inspection_data(string, year_lst)
clean_df = clean_data(raw_df)


converted_data = clean_df.to_csv(index=False).encode('utf-8')
dates = clean_df['report_date'].dt.date.unique()
start_date = dates[0]
end_date = dates[-1]
second_to_last = dates[-2]
st.download_button(f'Raw Historical Export Inspections Data From {start_date} to {end_date}',
                   data=converted_data,
                   file_name=f'export_inspections_{start_date}_{end_date}.csv',
                   mime='text/csv')


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
    
    out_df = out_df.map(string_format).reset_index()
    
    return out_df, last_week

dest_sum_df, last_week_string = build_last_week_destination_table(clean_df)

converted_dest_sum_df = dest_sum_df.to_csv(index=False).encode('utf-8')
st.download_button(f'Weekly Summary by Destination From {second_to_last} to {end_date}',
                   data=converted_dest_sum_df,
                   file_name='converted_dest_sum_df.csv',
                   mime='text/csv')

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

def build_charts(inspections_dct, estimated_exports_dct, dest_sum_df):
    # use inspections by week dct to build regular and cumulative charts.
    # output: dict where keys are commodity and values are tuples of figures
    
    fig_dct = {}
    
    dest_fig = go.Figure(data=[go.Table(
        columnwidth = [710, 300, 400, 400, 500, 300, 300, 300, 300],
        header=dict(values=list(dest_sum_df.columns),
                    line_color='darkslategray',
                    fill_color='lightgrey',
                    align='center',
                    font_size=10,
                    height=20),
        cells=dict(values=dest_sum_df.T,
                   line_color='darkslategray',
                   fill_color='white',
                   font_size=13,
                   align='center',
                   height=20))])
    dest_fig.update_layout(title='Export Inspections Summary (metric tons)', height=len(dest_sum_df) * 31, width=650)
    
    fig_dct['dest_sum_table'] = dest_fig
    
    for i in inspections_dct.keys():
        df = inspections_dct[i]
        
        if i == 'SOYBEANS':
            df = df.loc[:, 2021:].copy()
        
        commodity_export_projection = estimated_exports_dct[i]
        
        cumsum_df = round(df.cumsum(), 2)
        cumsum_df['average'] = round(cumsum_df.iloc[:, :-1].mean(axis=1), 2)
        
        df['average'] = round(df.iloc[:, :-1].mean(axis=1), 2)
        fig = px.line(df, title=f'Weekly Export Inspections: {i.upper()}')
        fig.update_layout(xaxis_title="Week of Crop Marketing Year",
                          yaxis_title="Exports (metric tons)",
                          legend_title="Crop Mkt Year")
        fig['data'][-2]['line']['color'] = 'rgb(0, 0, 0)' #set color to black
        fig['data'][-2]['line']['width'] = 5
        fig['data'][-1]['line']['dash'] = 'dot'
        fig['data'][-1]['line']['width'] = 4
        fig['data'][-1]['line']['color'] = 'rgb(128, 128, 128)'
        
        trimmed_cumsum = cumsum_df.iloc[:-1, :].copy()
        sumfig = px.line(trimmed_cumsum, title=f'Cumulative Export Inspections: {i.upper()}')
        sumfig.update_layout(xaxis_title="Week of Crop Marketing Year",
                             yaxis_title="Cumulative Exports (metric tons)",
                             legend_title='Crop Mkt Year')
        sumfig['data'][-2]['line']['color'] = 'rgb(0, 0, 0)' #set color of current year data to red
        sumfig['data'][-2]['line']['width'] = 5 #set weight of current year data line
        sumfig['data'][-1]['line']['dash'] = 'dot'
        sumfig['data'][-1]['line']['width'] = 4
        sumfig['data'][-1]['line']['color'] = 'rgb(128, 128, 128)'
        sumfig.add_scatter(x=[51],
                           y=[commodity_export_projection],
                           marker=dict(color='black', size=10),
                           name='projected final exports')
        
        fig_dct[f'weekly_{i.upper()}'] = fig
        fig_dct[f'cumulative_{i.upper()}'] = sumfig
    return fig_dct

est_exports_dct = {'SOYBEANS': 45800000,
                   'CORN': 55000000,
                   'SORGHUM': 5000000,
                   'WHEAT-HRS': 5500000,
                   'WHEAT-HRW': 500000,
                   'WHEAT-SRW': 2000000,
                   'WHEAT-SWW': 3500000,
                   'WHEAT-ALL': 22000000,
                   'WHEAT-HDWH': 2000000}

fig_dct = build_charts(annual_inspections_dct, est_exports_dct, dest_sum_df)

def add_alpha(old_file):
    if 'dest' in old_file:
        file = f'a{old_file}'
    if 'WHEAT-ALL' in old_file:
        file = f'b{old_file}'
    if 'WHEAT-HRW' in old_file:
        file = f'c{old_file}'
    if 'WHEAT-HRS' in old_file:
        file = f'd{old_file}'
    if 'WHEAT-SRW' in old_file:
        file = f'e{old_file}'
    if 'WHEAT-SWW' in old_file:
        file = f'f{old_file}'
    if 'WHEAT-HDWH' in old_file:
        file = f'g{old_file}'
    if 'CORN' in old_file:
        file = f'h{old_file}'
    if 'SORGHUM' in old_file:
        file = f'i{old_file}'
    if 'SOYBEANS' in old_file:
        file = f'j{old_file}' 
    return file

new_fig_dct = {add_alpha(k):v for k, v in fig_dct.items()}
new_fig_dct = dict(sorted(new_fig_dct.items()))

for i, j in new_fig_dct.items():
    st.write(j)
