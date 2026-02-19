import os 
import pandas as pd
import pycountry
import streamlit as st 
from mappings import iso_to_country

@st.cache_data
def format_country_name(code):
    if code != "EU27":
        name = iso_to_country.get(code, code) 
    else:
        name = "European Union"
        
    return f"{name} ({code})" 


@st.cache_data
def load_transport_data(filepath):
    df = pd.read_csv(filepath)
    df['Year'] = df['Year'].astype(int)
    return df

@st.cache_data
def load_industry_data(filepath):
    industry_data = []
    industry_files = [f for f in os.listdir(filepath) if f.endswith(".xlsx")]

    for file_name in industry_files:
        year, country = file_name.replace(".xlsx", "").split("_")
        file_path = os.path.join(filepath, file_name)
        df = pd.read_excel(file_path, index_col=0)
        df = df.apply(pd.to_numeric, errors='coerce').fillna(0)

        for material in df.index:
            for sector in df.columns:
                industry_data.append({
                    "Year": int(year),
                    "Country": country,
                    "Category": sector,
                    "Material": material.strip(),
                    "Value": df.loc[material, sector] * 3.6 * 0.000001 # Convert to EJ 
                })

    return pd.DataFrame(industry_data)

@st.cache_data
def process_ptx_excel(df):
    # Select sector columns
    sector_cols = [c for c in df.columns if c not in ['FuelGroup', 'Year']]
    
    # Create a long dataframe
    df_long = df.melt(id_vars=['FuelGroup', 'Year'], 
                      value_vars=sector_cols, 
                      var_name='Sector', 
                      value_name='Demand_EJ')

    # Use streamlite sum instead of the Overall Demand row 
    df_long = df_long[df_long['FuelGroup'] != 'Overall Demand']
    df_long['Demand_EJ'] = pd.to_numeric(df_long['Demand_EJ'], errors='coerce').fillna(0)
    return df_long


# Load all excel files from Outputs into one Dataframe
@st.cache_data
def load_combined_outputs(folder_path):
    all_data = []
    if not os.path.exists(folder_path):
        return pd.DataFrame()
        
    files = [f for f in os.listdir(folder_path) if f.endswith(('.xlsx', '.csv'))]
    for file in files:
        # Extract country code (e.g., DE, FR, EU27) from 'PtX_demand_DE.xlsx'
        country_code = file.split('_')[-1].split('.')[0]
        file_path = os.path.join(folder_path, file)
        df = pd.read_csv(file_path) if file.endswith('.csv') else pd.read_excel(file_path)
        
        # Identify sector columns
        sector_cols = [c for c in df.columns if c not in ['FuelGroup', 'Year']]
        
        # Transform wide to long format
        df_long = df.melt(id_vars=['FuelGroup', 'Year'], 
                          value_vars=sector_cols, 
                          var_name='Sector', 
                          value_name='Value')
        
        # Remove pre-calculated subtotals to prevent double counting in plots
        df_long = df_long[df_long['FuelGroup'] != 'Overall Demand']
        df_long['Country'] = country_code
        all_data.append(df_long)
        
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()



def convert_to_alpha3(iso2):
    try:
        return pycountry.countries.get(alpha_2=iso2).alpha_3
    except:
        return None