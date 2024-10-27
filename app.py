import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from prophet import Prophet 
import holidays

def aggregate_insert_data(data, warehouse, productcode, freq='D'):
    data = data[(data.Warehouse == warehouse) & (data.Product_Code == productcode)]
    data.set_index('Date', inplace=True)
    df = data.resample(freq)['Order_Demand'].sum().reset_index()
    
    df['Warehouse'] = warehouse
    df['Product_Code'] = productcode
    
    return df

def forecast(data, conf, periods, freq):
    
    l = min(data.Date.dt.year)
    h = max(data.Date.dt.year)
    us_holidays = holidays.UnitedStates(years=list(range(l,h+1)))
    h = pd.DataFrame(data=us_holidays.values(), index=us_holidays.keys()).reset_index()
    h['lower_window'] = 0
    h['upper_window'] = 1
    h.columns = ['ds', 'holiday', 'lower_window', 'upper_window']

    model = Prophet(interval_width=conf, holidays=h)

    cols = {'Date': 'ds', 'Order_Demand': 'y'}
    data = data.rename(columns=cols)
    model.fit(data)
    future = model.make_future_dataframe(periods=periods, freq=freq) 
    forecast = model.predict(future)

    forecast.loc[forecast.yhat<=0, 'yhat'] = 0
    forecast.loc[forecast.yhat_lower<=0, 'yhat_lower'] = 0
    forecast.loc[forecast.yhat_upper<=0, 'yhat_upper'] = 0
    
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]



# Read data from CSV
data = pd.read_csv('./product_demand_data.csv')
data = data.dropna()
data['Date'] = pd.to_datetime(data['Date'])
data['Order_Demand'] = pd.to_numeric(data['Order_Demand'].str.extract('(\d+)').iloc[:, 0])
# Consolidate order demand numbers for each product in each warehouse for each date
data = data.groupby(['Warehouse', 'Product_Code', 'Product_Category', 'Date'])['Order_Demand'].sum().reset_index()

# Streamlit app layout
st.title("Demand Forecasting Dashboard")

# Dropdown for selecting warehouse
warehouses = data['Warehouse'].unique()
selected_warehouse = st.selectbox("Select Warehouse", warehouses, index=0)

# Filter product codes based on the selected warehouse
product_codes = data[data['Warehouse'] == selected_warehouse]['Product_Code'].unique()
selected_product = st.selectbox("Select Product Code", product_codes, index=0)

# Dropdown for selecting frequency
frequency_labels = ['Daily', 'Weekly', 'Monthly', 'Yearly']
frequency_mapping = {'Daily': 'D', 'Weekly': 'W', 'Monthly': 'M', 'Yearly': 'Y'}
selected_frequency = st.selectbox("Select Frequency", frequency_labels, index=2)
selected_freq_code = frequency_mapping[selected_frequency]

# Toggle button for view mode or forecast mode
mode = st.radio("Select Mode", ("View Mode", "Forecast Mode"))

# Aggregate data based on selections
aggregated_data = aggregate_insert_data(data, selected_warehouse, selected_product, selected_freq_code)

if mode == "View Mode":
    # Create a Plotly figure for actual data
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=aggregated_data['Date'],
        y=aggregated_data['Order_Demand'],
        mode='lines+markers',
        name='Order Demand (Known)',
        marker=dict(color='blue', size=8),
    ))
    
    # Update layout
    fig.update_layout(
        title=f'Demand for {selected_product} at {selected_warehouse} ({selected_frequency})',
        xaxis_title='Date',
        yaxis_title='Order Demand',
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True),
        template='plotly_white'
    )
    
    # Show Plotly graph in Streamlit
    st.plotly_chart(fig)

else:  # Forecast Mode
    # Numeric input for forecast parameters
    confidence_level = st.number_input("Confidence Level (0.0 to 1.0)", min_value=0.0, max_value=1.0, value=0.95, step=0.01)
    forecast_periods = st.number_input("Number of periods to forecast", min_value=1, value=30)

    # Prepare data for forecasting
    forecast_data = aggregated_data[['Date', 'Order_Demand']]
    
    # Forecast the data
    forecast_results = forecast(forecast_data, confidence_level, forecast_periods, selected_freq_code)
    
    # Create a Plotly figure for forecasted data
    fig = go.Figure()
    
    # Plot known points
    fig.add_trace(go.Scatter(
        x=aggregated_data['Date'],
        y=aggregated_data['Order_Demand'],
        mode='lines+markers',
        name='Order Demand (Known)',
        marker=dict(color='blue', size=8),
    ))
    
    # Plot forecasted points
    fig.add_trace(go.Scatter(
        x=forecast_results.iloc[-1*forecast_periods:]['ds'],
        y=forecast_results.iloc[-1*forecast_periods:]['yhat'],
        mode='lines+markers',
        name='Forecasted Order Demand',
        marker=dict(color='orange', size=8),
    ))
    
    # Add uncertainty intervals
    fig.add_traces([
        go.Scatter(
            x=forecast_results.iloc[-1*forecast_periods:]['ds'],
            y=forecast_results.iloc[-1*forecast_periods:]['yhat_lower'],
            mode='lines',
            line=dict(width=0),
            name='Lower Bound',
            showlegend=False,
        ),
        go.Scatter(
            x=forecast_results.iloc[-1*forecast_periods:]['ds'],
            y=forecast_results.iloc[-1*forecast_periods:]['yhat_upper'],
            mode='lines',
            line=dict(width=0),
            name='Upper Bound',
            fill='tonexty',
            fillcolor='rgba(255,165,0,0.2)',  # Light orange for uncertainty
            showlegend=False,
        ),
    ])
    
    # Update layout
    fig.update_layout(
        title=f'Forecast for {selected_product} at {selected_warehouse} ({selected_frequency})',
        xaxis_title='Date',
        yaxis_title='Forecasted Order Demand',
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True),
        template='plotly_white'
    )
    
    # Show Plotly graph in Streamlit
    st.plotly_chart(fig)
