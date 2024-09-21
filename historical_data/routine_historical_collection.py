# -*- coding: utf-8 -*-
"""
Created on Sat Sep 21 13:54:06 2024

@author: boomelage
"""
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
sys.path.append(os.path.join(parent_dir,'term_Structure'))
import pandas as pd
import numpy as np
from settings import model_settings
ms = model_settings()


os.chdir(current_dir)
csvs = ms.csvs


# pd.set_option("display.max_rows",None)
pd.set_option("display.max_columns",None)

pd.reset_option("display.max_rows")
# pd.reset_option("display.max_columns")


historical_impvols = pd.DataFrame()
for file in csvs:
    raw = pd.read_csv(file)
    raw.columns = raw.loc[2]
    
    
    df = raw.loc[4:].reset_index(drop=True)
    
    df = df.replace(0,np.nan).dropna(subset=['Mid Price'])
    
    df.columns
    
    df.rename(columns={
        'SPX Index' : 'date', 
        '30 Day IVOL at 100.0% Moneyness LIVE':'30D',
        '60 Day IVOL at 100.0% Moneyness LIVE':"60D",
        '3 Month 100% Moneyness Implied Volatility':"3M",
        '6 Month IVOL at 100.0% Moneyness LIVE':"6M",
        '1 Year 100% Moneyness Implied Volatility':"12M",
        '18 Month IVOL at 100.0% Moneyness LIVE':"18M",
        '24 Month IVOL at 100.0% Moneyness LIVE':"24M", 
        'BEst Div Yld':"dividend_rate",
        'End of Day Risk Free Rate Mid':"risk_free_rate", 
        'Mid Price':"spot_price",
        }, inplace=True)
    # Assuming 'df' is your DataFrame

    df = df.astype({
        # 'date': 'datetime64ns',     # Convert 'column1' to integer
        # 'column2': 'float',   # Convert 'column2' to float
        # 'column3': 'category' # Convert 'column3' to categorical
    })

    df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y',errors='coerce')
    df = df.infer_objects(copy=False) 
    df[df.columns[1:]] = df[df.columns[1:]].astype(float)
    df.iloc[:, 1:] = df.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')
    
    historical_impvols = pd.concat([historical_impvols,df],ignore_index=True)

historical_impvols

trading_day = historical_impvols.loc[0]

trading_day


