import requests
import pandas as pd
from model_settings import ms
from historical_av_key_collector import keys_df
"""
https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&outputsize=full&apikey=demo
"""
symbol = r'SPY'

url = str(
	'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol='+
	symbol+'&outputsize=full&apikey='+
	ms.av_key)


r = requests.get(url)
spots = pd.Series(pd.DataFrame(r.json()['Time Series (Daily)']).transpose()['4. close'].squeeze())
spots = pd.to_numeric(spots,errors='coerce')
spots.index = pd.to_datetime(spots.index,format='%Y-%m-%d')
spots = spots[~spots.index.isin(keys_df['date'])]
spots.index = spots.index.strftime('%Y-%m-%d')
print(spots)
