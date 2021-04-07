# -*- coding: utf-8 -*-
"""
Created on Sat Mar 27 13:32:57 2021

@author: ChristianBouman
"""

import plotly.express as px
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import geopandas as gpd
import os
import numpy as np

#Set directory
#os.chdir('C:\\Users\\Christian Bouman\\Documents\\2021\\CU\\Analyse campagne')

#%% Define stylesheets and app server
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

#%% Link uitslag 2021 to buurten
df_21 = pd.read_csv('cu21_tot_loc.csv')
geo_df = gpd.read_file('Amersfoort_wijken2019.geojson').to_crs(epsg=4326).merge(df_21, on='wijkcode').drop(labels=['wijknaam_y'], axis=1)
geo_df = geo_df.rename(columns={'0': '2021(%)','Unnamed:0': 'ID','wijknaam_x': 'wijknaam'})
geo_df = geo_df.replace(-99999999, np.nan)
geo_df['2021(%)'] = geo_df['(%) wijk'].fillna(0)
geo_df = geo_df[~(geo_df.is_empty)]

#%% Read totaal
df_tot = pd.read_csv('totaal.csv')
wijknaam = 'Wijk 01 Stadskern'
verkiezing = 'TK'
df_tot_i = df_tot[df_tot['verkiezing'] == verkiezing]
df_tot_i  = df_tot_i[df_tot_i['wijknaam'] == wijknaam]

#%% Get count of leeftijd
df_lt = geo_df[['wijknaam', 'wijkcode', 'aantal_inw', 'percentage', 'percenta_1', 'percenta_2', 'percenta_3', 'percenta_4', '2021(%)']]
df_lt['corr_percenta_1'] = 0.7*df_lt['percenta_1']
df_lt['sum_corr'] = df_lt.loc[:, ['percenta_2', 'percenta_3', 'percenta_4', 'corr_percenta_1']].sum(axis=1)

# Benaderde aantallen
df_lt['P_18_24'] = (df_lt['percenta_1']/df_lt['sum_corr'])*df_lt['aantal_inw']*df_lt['2021(%)']/100
df_lt['P_25_44'] = (df_lt['percenta_2']/df_lt['sum_corr'])*df_lt['aantal_inw']*df_lt['2021(%)']/100
df_lt['P_45_64'] = (df_lt['percenta_3']/df_lt['sum_corr'])*df_lt['aantal_inw']*df_lt['2021(%)']/100
df_lt['P_65_EO'] = (df_lt['percenta_4']/df_lt['sum_corr'])*df_lt['aantal_inw']*df_lt['2021(%)']/100

#Benaderde som
df_lt['tot_18_24'] = df_lt['P_18_24'].sum().round(0)
df_lt['tot_25_44'] = df_lt['P_25_44'].sum()
df_lt['tot_45_64'] = df_lt['P_45_64'].sum()
df_lt['tot_65_EO'] = df_lt['P_65_EO'].sum()

df_lt = df_lt.loc[:, ['wijknaam', 'wijkcode', 'tot_18_24', 'tot_25_44', 'tot_45_64', 'tot_65_EO']]
df_lt = df_lt.rename(columns={'tot_18_24': '18-24', 'tot_25_44': '25-44', 'tot_45_64':'45-64', 'tot_65_EO':'65+'})

#%% Create choropleth figure

fig = px.choropleth_mapbox(geo_df, 
                     geojson=geo_df.geometry, 
                     locations= geo_df.index,
                     color=geo_df['2021(%)'],
                     labels={'2021 (%)':'Uitslag 2021'},
                     hover_data=['wijknaam', '2021(%)'],
                     range_color=(geo_df['2021(%)'].min(), geo_df['2021(%)'].max()),
                     center={"lat": 52.17808, "lon": 5.39717},
                     mapbox_style='carto-positron',
                     zoom=10,
                     opacity=0.50,
                     color_continuous_scale='Blues')

fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.update_traces(marker_line_width=1)

#%% Create piechart for leeftijd
fig1 = go.Figure(data=[go.Pie(
    labels= df_lt.loc[0,['18-24', '25-44', '45-64', '65+']].index,
    values= df_lt.loc[0,['18-24', '25-44', '45-64', '65+']],
    title='Leeftijd',
    )],
    )

fig1.update_traces(hole=.3, hoverinfo="label+percent")


#%% Create barchart for wijkresultaten
fig2 = go.Figure(data=[go.Bar(
    x=df_tot_i['jaar'],
    y=df_tot_i['(%) wijk'],)
    ])

fig2.update_layout(height=300, margin={'l': 40, 'b': 40, 'r': 10, 't': 40}, template='plotly_white', title='Verloop van '+str(wijknaam), yaxis_title='Aantal stemmen (%)')
fig2.update_layout(barmode='group')

#%% Define app components
app.layout = html.Div([
    html.Div([
        dcc.Graph(id="choropleth",
                  figure = fig)
        ], style={'width': 600, 'display': 'inline-block', 'padding': 10}),
    
    html.Div([
        dcc.Graph(id='piechart-leeftijd',
                  figure=fig1)
        ], style={'width': 400, 'display': 'inline-block'}),
    
    html.Div([
        dcc.Checklist(id='checklist',
            options=[
                {'label': 'Tweede Kamer', 'value': 'TK'},
                {'label': 'Gemeenteraad', 'value': 'GR'},
                {'label': 'Europarlement', 'value': 'EP'}
                ],
            value=[verkiezing],
            labelStyle={'display': 'inline-block'})
        ], style={'width':800, 'display': 'inline-block', 'padding': 10}),
            
    html.Div([
        dcc.Graph(id='horizontal-bars',
                  figure = fig2)
        ],
        #Define style of this html block
        style={'width': 800, 'display': 'inline-block', 'padding': 10}),
    ])
                      
#%% Define callback based on choropleth map and filtering
@app.callback(
    dash.dependencies.Output('horizontal-bars', 'figure'),
    [dash.dependencies.Input('choropleth', 'clickData'),
     dash.dependencies.Input('checklist', 'value')])

def update_bars(clickData, value):
    wijknaam = clickData['points'][0]['customdata'][0]
    verkiezing = value
    df = df_tot[np.isin(df_tot, verkiezing).any(axis=1)]
    df = df[df['wijknaam'] == wijknaam]
    df['jaar'] = df['jaar'].astype(int).astype(str)
    
    fig2 = go.Figure(data=[go.Bar(
        name=str(wijknaam)+' resultaten',
        x=df['jaar'],
        y=df['(%) wijk'],)
        ])
    fig2.update_layout(height=300, margin={'l': 40, 'b': 40, 'r': 10, 't': 40}, template='plotly_white', title='Verloop van '+str(wijknaam), yaxis_title='Aantal stemmen (%)')
    fig2.update_layout(barmode='group')
    fig2.update_xaxes(
        ticks='outside',
        tickson='boundaries')
    return fig2



#%% Run app
    
if __name__ == '__main__':
    app.run_server(debug=False)
