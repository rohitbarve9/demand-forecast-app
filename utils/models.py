import holidays
import pandas as pd
from prophet import Prophet


def forecast(data, conf, periods, freq):
    """
    Forecast future demand with a simple Prophet model.
    """
    
    ## Get list of holidays in data 
    l = min(data.Date.dt.year)
    h = max(data.Date.dt.year)
    us_holidays = holidays.UnitedStates(years=list(range(l,h+1)))
    h = pd.DataFrame(data=us_holidays.values(), index=us_holidays.keys()).reset_index()
    h['lower_window'] = 0
    h['upper_window'] = 1
    h.columns = ['ds', 'holiday', 'lower_window', 'upper_window']

    ## Create Prohet model and predict future demand
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

