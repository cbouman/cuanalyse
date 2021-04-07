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


#%% Set mapbox token and initial values
token = 'pk.eyJ1IjoiY2JvdW1hbiIsImEiOiJja21yc2EzN2QwNnF1MnZwY2Rud2trd2ZzIn0.VXaw06x8f-yirKrjed8Meg'
px.set_mapbox_access_token(token)
wijknaam = 'Wijk 01 Stadskern'
calc = 'std'
verkiezing = 'TK'

#%% Read totaal
df_tot = pd.read_csv('totaal.csv')

df_tot_i = df_tot[df_tot['verkiezing'] == verkiezing]
df_tot_i  = df_tot_i[df_tot_i['wijknaam'] == wijknaam]
geo_df = gpd.read_file('Amersfoort_wijken2019.geojson').to_crs(epsg=4326).merge(df_tot, on='wijkcode').drop(labels=['wijknaam_y'], axis=1)
geo_df = geo_df.rename(columns={'0': '2021(%)','Unnamed:0': 'ID','wijknaam_x': 'wijknaam'})
geo_df = geo_df.replace(-99999999, np.nan)
geo_df['2021(%)'] = geo_df['(%) wijk'].fillna(0)
geo_df = geo_df[~(geo_df.is_empty)]

#Set min and max for slider
minyear = geo_df['jaar'].min().astype(int)
maxyear = geo_df['jaar'].max().astype(int)

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


# #%% Create piechart for leeftijd
# fig1 = go.Figure(data=[go.Pie(
#     labels= df_lt.loc[0,['18-24', '25-44', '45-64', '65+']].index,
#     values= df_lt.loc[0,['18-24', '25-44', '45-64', '65+']],
#     title='Leeftijd',
#     )],
#     )

# fig1.update_traces(hole=.3, hoverinfo="label+percent")


#%% Create barchart for wijkresultaten
fig2 = go.Figure(data=[go.Bar(
    x=df_tot_i['jaar'].astype(int).astype(str),
    y=df_tot_i['(%) wijk'],
    marker_color='#87B2D5')
    ])

fig2.update_layout(height=300, margin={'l': 10, 'b': 0, 'r': 10, 't': 30}, template='plotly_white', title='Verloop van '+str(wijknaam), yaxis_title='Aantal stemmen (%)')
fig2.update_xaxes(ticks='outside', tickson='boundaries')

#%% Define app components
app.layout = html.Div([
    html.H1('Analyse verkiezingen CU Amersfoort'),
    html.Div([
        dcc.Markdown('''
                     Dit dashboard is gemaakt om inzicht te geven in de verkiezingsresultaten van ChristenUnie Amersfoort.
                     Er kan per wijk bekeken worden wat de gemiddelde verkiezingsuitslag was over de geselecteerde verkiezingen en periodes. Ook kan de standaarddeviatie bekeken worden. 
                     Dit laat zien welke wijk het meest afwijkt over de jaren. Door te klikken op een wijk op de kaart krijg je rechts een staafgrafiek met de resultaten per verkiezing.''')]),
    #Radiobuttons for view of choropleth
    html.Div([
        html.H3('Wat wil je op de kaart zien?'),
        dcc.RadioItems(id='beeld',
                       options=[
                           {'label': 'Gemiddeld percentage per wijk', 'value': 'mean'},
                           {'label': 'Standaarddeviatie per wijk', 'value': 'std'}
                           ],
                       value='mean')
        ], style={'width':600, 'display': 'inline-block', 'padding': 10}),
    
    #Checklist for verkiezingssoort
    html.Div([
        html.H3('Welke verkiezingen?'),
        dcc.Checklist(id='checklist',
                      options=[
                          {'label': 'Tweede Kamer', 'value': 'TK'},
                          {'label': 'Gemeenteraad', 'value': 'GR'},
                          {'label': 'Provinciaal', 'value': 'PS'},
                          {'label': 'Europarlement', 'value': 'EP'}
                          ],
                      labelStyle={'display': 'inline-block'},
                      value=[verkiezing])
        ], style={'width':600, 'display': 'inline-block', 'padding': 10}),
    
    #Rangeslider
    html.Div([
        html.H3('Welke periode?'),
        dcc.RangeSlider(id='rangeslider',
                        min=minyear,
                        max=maxyear,
                        marks={str(year): str(year) for year in geo_df['jaar'].unique().astype(int)},
                        step=None,
                        value=[minyear, maxyear])
        ], style={'width':1200, 'display': 'inline-block', 'padding': 10}),
    
    html.Div([
        dcc.Graph(id="choropleth")
        ], style={'width': 800, 'display': 'inline-block', 'padding': 10}),
    
            
    html.Div([
        dcc.Graph(id='horizontal-bars',
                  figure = fig2)
        ],
        #Define style of this html block
        style={'width': 400, 'display': 'inline-block', 'padding': 10}),
    ])
                      
#%% Define callback for choropleth map
@app.callback(
    dash.dependencies.Output('choropleth', 'figure'),
    [dash.dependencies.Input('checklist', 'value'),
      dash.dependencies.Input('beeld', 'value'),
      dash.dependencies.Input('rangeslider', 'value')])

def update_choropleth(verkiezing, calc, timespan):
    df = geo_df[['geometry', 'wijknaam', 'jaar', 'verkiezing', '(%) wijk']]
    df = geo_df[(geo_df['jaar'].between(timespan[0],timespan[1]))]
    if type(verkiezing) == 'str':
        dff = df[(df['verkiezing'] == verkiezing)]
    elif type(verkiezing) == list:
        dff = df[(df['verkiezing'].isin(verkiezing))]
        
    if calc == 'mean':
        dff['mean'] = dff.groupby('wijkcode')['(%) wijk'].transform('mean').round(2).dropna()
        dff = dff.drop_duplicates(subset='wijkcode')
        dff = dff.dropna(subset= ['mean'])
        fig = px.choropleth_mapbox(dff, 
                                   geojson=dff.geometry, 
                                   locations= dff.index,
                                   color=dff['mean'],
                                   labels={'mean':'Gemiddelde uitslag:' +str(timespan[0])+'-'+str(timespan[1])},
                                   hover_data=['wijknaam'],
                                   range_color=(dff['mean'].min(), dff['mean'].max()),
                                   center={"lat": 52.1651, "lon": 5.3826},
                                   mapbox_style='light',
                                   zoom=10.50,
                                   opacity=0.50,
                                   color_continuous_scale='Blues')   
    elif calc == 'std':
        dff['std'] = dff.groupby('wijkcode')['(%) wijk'].transform('std').round(2).dropna()
        dff = dff.drop_duplicates(subset='wijkcode')
        dff = dff.dropna(subset=['std'])
        fig = px.choropleth_mapbox(dff, 
                                   geojson=dff.geometry, 
                                   locations= dff.index,
                                   color=dff['std'],
                                   labels={'std':'Standaarddeviatie:' +str(timespan[0])+'-'+str(timespan[1])},
                                   hover_data=['wijknaam'],
                                   range_color=(dff['std'].min(), dff['std'].max()),
                                   center={"lat": 52.1651, "lon": 5.3826},
                                   mapbox_style='light',
                                   zoom=10.50,
                                   opacity=0.50,
                                   color_continuous_scale='Blues')
        
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":10,"t":30,"l":10,"b":10})
    fig.update_traces(marker_line_width=1)
    return (fig)
#%% Define callback based on choropleth map and filtering
@app.callback(
    dash.dependencies.Output('horizontal-bars', 'figure'),
    [dash.dependencies.Input('choropleth', 'clickData'),
     dash.dependencies.Input('checklist', 'value'),
     dash.dependencies.Input('rangeslider', 'value')])

def update_bars(clickData, value, timespan):
    wijknaam = clickData['points'][0]['customdata'][0]
    verkiezing = value
    
    df = df_tot[np.isin(df_tot, verkiezing).any(axis=1)]
    df = df[df['wijknaam'] == wijknaam]
    df = df[(df['jaar'].between(timespan[0], timespan[1]))]
    df['jaar'] = df['jaar'].astype(int).astype(str)
    
    fig2 = go.Figure(data=[go.Bar(
        x=df['jaar'],
        y=df['(%) wijk'],
        marker_color='#87B2D5',
        hovertext=df['verkiezing'])
        ])
    fig2.update_layout(height=300, margin={'l': 10, 'b': 0, 'r': 10, 't': 30}, template='plotly_white', title='Verloop van '+str(wijknaam), yaxis_title='Aantal stemmen (%)')
    fig2.update_xaxes(
        ticks='outside',
        tickson='boundaries')
    return fig2



#%% Run app
    
if __name__ == '__main__':
    app.run_server(debug=False)
