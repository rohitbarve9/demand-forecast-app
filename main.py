from utils.data_preprocessing import load_and_process_data, aggregate_insert_data
from utils.models import forecast
import streamlit as st
import plotly.graph_objects as go


def main():

    ## Load processed data
    data = load_and_process_data("./data/product_demand_data.csv")
    
    ## Setup Streamlit app
    st.title("Demand Forecasting Dashboard")
    warehouses = data['Warehouse'].unique()
    selected_warehouse = st.selectbox("Select Warehouse", warehouses, index=0)
    product_codes = data[data['Warehouse'] == selected_warehouse]['Product_Code'].unique()
    selected_product = st.selectbox("Select Product Code", product_codes, index=0)
    frequency_labels = ['Daily', 'Weekly', 'Monthly', 'Yearly']
    frequency_mapping = {'Daily': 'D', 'Weekly': 'W', 'Monthly': 'ME', 'Yearly': 'Y'}
    selected_frequency = st.selectbox("Select Frequency", frequency_labels, index=2)
    selected_freq_code = frequency_mapping[selected_frequency]
    mode = st.radio("Select Mode", ("View Mode", "Forecast Mode"))

    ## Filter data, Insert missing dates and Aggregate on sampling frequency
    aggregated_data = aggregate_insert_data(data, selected_warehouse, selected_product, selected_freq_code)

    ## Create display
    if mode == "View Mode":
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=aggregated_data['Date'],
            y=aggregated_data['Order_Demand'],
            mode='lines+markers',
            name='Order Demand (Known)',
            marker=dict(color='blue', size=8)))
        fig.update_layout(
            title=f'Demand for {selected_product} at {selected_warehouse} ({selected_frequency})',
            xaxis_title='Date',
            yaxis_title='Order Demand',
            xaxis=dict(showgrid=True),
            yaxis=dict(showgrid=True),
            template='plotly_white')
        st.plotly_chart(fig)
    else:  
        confidence_level = st.number_input("Confidence Level (0.0 to 1.0)", min_value=0.0, max_value=1.0, value=0.95, step=0.01)
        forecast_periods = st.number_input("Number of periods to forecast", min_value=1, value=30)
        
        # Prepare forecast
        forecast_results = forecast(aggregated_data[['Date', 'Order_Demand']], confidence_level, forecast_periods, selected_freq_code)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=aggregated_data['Date'],
            y=aggregated_data['Order_Demand'],
            mode='lines+markers',
            name='Order Demand (Known)',
            marker=dict(color='blue', size=8)))
        fig.add_trace(go.Scatter(
            x=forecast_results.iloc[-1*forecast_periods:]['ds'],
            y=forecast_results.iloc[-1*forecast_periods:]['yhat'],
            mode='lines+markers',
            name='Forecasted Order Demand',
            marker=dict(color='orange', size=8)))
        fig.add_traces([
            go.Scatter(
                x=forecast_results.iloc[-1*forecast_periods:]['ds'],
                y=forecast_results.iloc[-1*forecast_periods:]['yhat_lower'],
                mode='lines',
                line=dict(width=0),
                name='Lower Bound',
                showlegend=False),
            go.Scatter(
                x=forecast_results.iloc[-1*forecast_periods:]['ds'],
                y=forecast_results.iloc[-1*forecast_periods:]['yhat_upper'],
                mode='lines',
                line=dict(width=0),
                name='Upper Bound',
                fill='tonexty',
                fillcolor='rgba(255,165,0,0.2)', 
                showlegend=False)])
        fig.update_layout(
            title=f'Forecast for {selected_product} at {selected_warehouse} ({selected_frequency})',
            xaxis_title='Date',
            yaxis_title='Forecasted Order Demand',
            xaxis=dict(showgrid=True),
            yaxis=dict(showgrid=True),
            template='plotly_white')
        st.plotly_chart(fig)



if __name__ == "__main__":
    main()