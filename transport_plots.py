import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import pandas as pd

from process import convert_to_alpha3
from mappings import corresponding_cat
from mappings import *


def plot_main_transport_stack(eu27_transport, colors):
    df = eu27_transport.copy()
    df['MainCategory'] = df['Category'].map(main_category_mapping)
    main_grouped = df.groupby(['Year', 'MainCategory'])['Value'].sum().reset_index()
    pivot_main = main_grouped.pivot(index='Year', columns='MainCategory', values='Value').fillna(0)

    main_categories = ['Road', 'Aviation', 'Rail', 'Shipping']
    available_main = [cat for cat in main_categories if cat in pivot_main.columns]
    colors = colors[:len(available_main)]

    fig = px.bar(
        pivot_main,
        x=pivot_main.index,
        y=available_main,
        labels={'value': 'Energy Demand (EJ)'},
        color_discrete_sequence=colors
    )
    fig.update_layout(barmode='stack', yaxis_title='Energy Demand (EJ)', legend_title='Transport mode')
    fig.update_layout(legend_orientation="h", legend_y=-0.2)
    return fig


def plot_transport_pie_charts(eu27_transport, year):
    df = eu27_transport.copy()
    df['SubCategory'] = df['Category'].map(sub_category_mapping)
    sub_data = df.groupby(['Year', 'SubCategory'])['Value'].sum().reset_index()
    year_data = sub_data[sub_data['Year'] == year]
    
    passenger = year_data[year_data['SubCategory'].str.contains('Passenger')]
    freight = year_data[year_data['SubCategory'].str.contains('Freight')]

    col1, col2 = st.columns(2)

    with col1:
        pie_pass = px.pie(
            passenger,
            names='SubCategory',
            values='Value',
            title=f"Passenger Transport Breakdown ({year})",
            color='SubCategory',
            color_discrete_map=transport_sub_colors
        )
        st.plotly_chart(pie_pass)

    with col2:
        pie_freight = px.pie(
            freight,
            names='SubCategory',
            values='Value',
            title=f"Freight Transport Breakdown ({year})",
            color='SubCategory',
            color_discrete_map=transport_sub_colors
        )
        st.plotly_chart(pie_freight)


@st.cache_data
def plot_transport_heatmap(transport_data, target_category):
    title_cat = corresponding_cat(target_category) 
    df = transport_data[
        (transport_data['Category'] == target_category) &
        (transport_data['Country'] != 'EU27')
    ].copy()

    df['iso_alpha'] = df['Country'].apply(convert_to_alpha3)
    years = [2020, 2050]
    zmax = df['Value'].max()

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=[f"{year}" for year in years],
        specs=[[{"type": "choropleth"}, {"type": "choropleth"}]],
        horizontal_spacing=0.05
    )

    for i, year in enumerate(years):
        year_df = df[df['Year'] == year]
        country_values = year_df.groupby('iso_alpha')['Value'].sum().reset_index()

        choropleth = go.Choropleth(
            locations=country_values['iso_alpha'],
            z=country_values['Value'],
            colorscale="RdBu_r",
            zmin=0,
            zmax=zmax,
            colorbar=dict(
                title="Demand (EJ)" if i == 1 else None,
                titlefont=dict(size=18),
                tickfont=dict(size=16),
                len=0.45,
                thickness=12,
                x=0.999,
                y=0.5
            ),
            showscale=(i == 1),
            geo=f'geo{i+1}'
        )

        fig.add_trace(choropleth, row=1, col=i+1)

    # Fix the legend for years 
    for ann in fig.layout.annotations:
        ann.y = 0.75
        ann.font.size = 18

    fig.update_layout(
        title_text=f"{title_cat} demand in 2020 vs 2050",
        title_font=dict(size=26, family="Arial", color="black"),
        title_x=0.5,
        title_y=0.75,
        title_xanchor="center",
        margin=dict(l=20, r=20, t=90, b=10),
        height=1000,
        width=1400,
        geo=dict(
            scope='europe', showland=True, landcolor="white",
            lakecolor="lightblue", bgcolor='white',
            lataxis_range=[35, 70], lonaxis_range=[-15, 35]
        ),
        geo2=dict(
            scope='europe', showland=True, landcolor="white",
            lakecolor="lightblue", bgcolor='white',
            lataxis_range=[35, 70], lonaxis_range=[-15, 35]
        )
    )
    return fig


# ADDED JANUARY 2026: Fuel breakdown for PtX analysis
''' 
import plotly.express as px
def plot_transport_ptx_bars(final_df, selected_country):
    df = final_df[final_df['Country'] == selected_country].copy()
    transport_modes = ['Pass Road', 'Pass Rail', 'Pass Aviation', 'Freight Road', 'Freight Rail', 'Maritime']
    transport_modes = [c for c in transport_modes if c in df.columns]

    # Convert numeric values
    for col in transport_modes:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

    # Filter PtX fuels
    ptx_df = df[df['FuelGroup'].isin(ptx_carriers)]

    # Melt modes for plotting
    ptx_melted = ptx_df.melt(id_vars=['Year','FuelGroup'], value_vars=transport_modes, var_name='Mode', value_name='Value')
    ptx_melted = ptx_melted[ptx_melted['Value'] > 0]

    fig = px.bar(
        ptx_melted,
        x='Year',
        y='Value',
        color='FuelGroup',
        facet_col='Mode',
        title=f'PtX fuels by transport mode for {selected_country}',
        labels={'Value':'Energy Demand (EJ)'}
    )
    fig.update_layout(barmode='stack', height=500)
    return fig

'''