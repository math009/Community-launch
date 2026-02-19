import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from process import convert_to_alpha3
from mappings import corresponding_cat
from mappings import *
import streamlit as st

'''
This module gives visualization functions specifically focused on energy demand in the 
industry sector across EU27 countries and individual nations. These functions are intended to be used with a Streamlit dashboard to illustrate interactive exploration of sectoral 
and material-based energy use.

Functions included:
- plot_main_industry_bar: Creates a stacked bar chart showing the evolution of industry demand by category over time.
- plot_industry_pie: Displays two side-by-side pie charts showing the breakdown of energy demand by industry category and by fuel/material for a selected year.
- plot_industry_choropleth: Generates choropleth maps for a specific industry category to compare geographic distribution of demand in 2030 and 2050.
'''


# ---- Bar plots ----
def plot_main_industry_bar(eu27_industry, colors):
    industry_grouped = eu27_industry.groupby(['Year', 'Category'])['Value'].sum().reset_index()
    pivot_industry = industry_grouped.pivot(index='Year', columns='Category', values='Value').fillna(0)

    fig = px.bar(
        pivot_industry,
        x=pivot_industry.index,
        y=pivot_industry.columns.tolist(),
        labels={'value': 'Energy Demand (EJ)'},
        color_discrete_sequence=colors
    )
    fig.update_layout(barmode='stack',yaxis_title='Energy Demand (EJ)',legend_title='Industry Sector')
    fig.update_layout(legend_orientation="h", legend_y=-0.2)
    return fig


# ---- Pie charts ----
@st.cache_data
def plot_industry_pie(industry_df, year):
    data_year = industry_df[industry_df['Year'] == year].copy()
    data_year = data_year[(data_year['Category'] != "Overall Demand") &(data_year['Material'] != "Overall Demand")]
    cat_data = data_year.groupby('Category')['Value'].sum().reset_index()
    mat_data = data_year.groupby('Material')['Value'].sum().reset_index()

    col1, col2 = st.columns(2)

    with col1:
        fig_cat = px.pie(
            cat_data,
            names='Category',
            values='Value',
            title=f"Industry Categories ({year})",
            color='Category',
            color_discrete_map=industry_category_colors
        )
        st.plotly_chart(fig_cat)

    with col2:
        fig_mat = px.pie(
            mat_data,
            names='Material',
            values='Value',
            title=f"Industry Fuel/Material Use ({year})",
            color='Material',
            color_discrete_map=industry_fuel_colors
        )
        st.plotly_chart(fig_mat)


# ---- Heatmap ----
@st.cache_data
def plot_industry_choropleth(industry_df, target_industry_category):
    filtered_industry_data = industry_df[(industry_df['Category'] == target_industry_category) & (industry_df['Country'] != 'EU27')].copy()
    filtered_industry_data['iso_alpha'] = filtered_industry_data['Country'].apply(convert_to_alpha3)

    years_to_plot = [2030, 2050]
    color_range = [0, filtered_industry_data['Value'].max()]

    fig_cat_industry = make_subplots(
        rows=1, cols=2,
        subplot_titles=[f"{year}" for year in years_to_plot],
        specs=[[{"type": "choropleth"}, {"type": "choropleth"}]],
        horizontal_spacing=0.05
    )

    for i, year in enumerate(years_to_plot):
        year_data = filtered_industry_data[filtered_industry_data['Year'] == year]
        demand_by_country = year_data.groupby('iso_alpha')['Value'].sum().reset_index()

        choropleth = go.Choropleth(
            locations=demand_by_country['iso_alpha'],
            z=demand_by_country['Value'],
            colorscale="RdBu_r",
            colorbar=dict(
                title="Demand (EJ)" if i == 1 else None,
                titlefont=dict(size=18),
                tickfont=dict(size=16), 
                len=0.45,
                thickness=12,
                x=0.999,
                y=0.5
            ),
            zmin=color_range[0],
            zmax=color_range[1],
            showscale=(i == 1),
            geo=f'geo{i+1}'
        )

        fig_cat_industry.add_trace(choropleth, row=1, col=i+1)

    # Fix the legend for years 
    for ann in fig_cat_industry.layout.annotations:
        ann.y = 0.75
        ann.font.size = 18


    fig_cat_industry.update_layout(
        title_text=f"{target_industry_category} demand in 2030 vs 2050",
        title_font=dict(size=26, family="Arial", color="black"),
        title_x=0.5,
        title_y = 0.75,
        title_xanchor="center",
        height=1000,
        width=1400,
        margin=dict(l=20, r=20, t=90, b=10),
        geo=dict(
            scope='europe',
            showland=True, landcolor="white",
            lakecolor="lightblue", bgcolor='white',
            lataxis_range=[35, 70],
            lonaxis_range=[-15, 35]
        ),
        geo2=dict(
            scope='europe',
            showland=True, landcolor="white",
            lakecolor="lightblue", bgcolor='white',
            lataxis_range=[35, 70],
            lonaxis_range=[-15, 35]
        )
    )

    return fig_cat_industry