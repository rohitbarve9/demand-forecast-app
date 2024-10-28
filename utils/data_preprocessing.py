import pandas as pd


def load_and_process_data(path):
    """
    Load and process the data.
    """

    data = pd.read_csv(path)
    data = data.dropna()
    data['Date'] = pd.to_datetime(data['Date'])
    data['Order_Demand'] = pd.to_numeric(data['Order_Demand'].str.extract('(\d+)').iloc[:, 0])
    
    ## Consolidate order data for each day 
    data = data.groupby(['Warehouse', 'Product_Code', 'Product_Category', 'Date'])['Order_Demand'].sum().reset_index()
    
    return data



def aggregate_insert_data(data, warehouse, productcode, freq):
    """
    Insert missing dates and aggregate based on sampling frequency
    """

    data = data[(data.Warehouse == warehouse) & (data.Product_Code == productcode)]
    data.set_index('Date', inplace=True)
    df = data.resample(freq)['Order_Demand'].sum().reset_index()
    df['Warehouse'] = warehouse
    df['Product_Code'] = productcode
    
    return df

