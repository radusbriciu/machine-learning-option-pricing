# -*- coding: utf-8 -*-
"""
Created on Tue Sep 17 15:46:57 2024

@author: boomelage
"""

import os
import sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.append('term_structure')
sys.path.append('contract_details')
sys.path.append('misc')
import pandas as pd
from settings import model_settings
from tqdm import tqdm
import numpy as np
import QuantLib as ql
from routine_calibration_global import \
    heston_parameters, performance_df, calibration_dataset
ms = model_settings()
s = ms.s

"""
checking calibration accuracy
"""

test_features = calibration_dataset.copy()
test_features['dividend_rate'] = 0.02
test_features['risk_free_rate'] = 0.04
test_features['sigma'] = heston_parameters['sigma'].iloc[0]
test_features['theta'] = heston_parameters['theta'].iloc[0]
test_features['kappa'] = heston_parameters['kappa'].iloc[0]
test_features['rho'] = heston_parameters['rho'].iloc[0]
test_features['v0'] = heston_parameters['v0'].iloc[0]
test_features['heston_price'] = 0.00
test_features['w'] = 'call'
progress_bar = tqdm(
    desc="pricing",total=test_features.shape[0],unit= "contracts")

for i, row in test_features.iterrows():
    s = row['spot_price']
    k = row['strike_price']
    t = int(row['days_to_maturity'])
    r = row['risk_free_rate']
    g = row['dividend_rate']
    v0 = row['v0']
    kappa = row['kappa']
    theta = row['theta']
    sigma = row['sigma']
    rho = row['rho']
    w = row['w']
    
    date = ms.calculation_date + ql.Period(t,ql.Days)
    option_type = ql.Option.Call if w == 'call' else ql.Option.Put
    
    payoff = ql.PlainVanillaPayoff(option_type, k)
    exercise = ql.EuropeanExercise(date)
    european_option = ql.VanillaOption(payoff, exercise)
    flat_ts = ms.make_ts_object(r)
    dividend_ts = ms.make_ts_object(g)
    
    heston_process = ql.HestonProcess(
        flat_ts,dividend_ts, 
        ql.QuoteHandle(ql.SimpleQuote(s)), 
        v0, kappa, theta, sigma, rho)
    
    heston_model = ql.HestonModel(heston_process)
    
    engine = ql.AnalyticHestonEngine(heston_model)
    
    european_option.setPricingEngine(engine)
    
    h_price = european_option.NPV()
    progress_bar.update(1)
    test_features.at[i, 'heston_price'] = h_price


progress_bar.close()

test_features.at[0,'heston_price']

black_scholes_prices = performance_df['black_scholes']
calibration_prices = performance_df['heston']
test_prices = test_features['heston_price']
error = test_prices/calibration_prices - 1
error_series = pd.DataFrame({'absRelError':error})

error_df = pd.concat(
    [
      black_scholes_prices,
      calibration_prices,
      test_prices,
      error_series
      ],
    axis = 1
    )
error_df

error_df.rename(columns={'heston': 'calibration_price', 
                    'heston_price': 'test_price'}, inplace=True)

avg = np.average(error_df['absRelError'])*100
print(f"\nerrors:\n{error_df}")
print(f"average absolute relative calibration testing error: {round(avg,4)}%")
