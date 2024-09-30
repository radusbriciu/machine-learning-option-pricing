# -*- coding: utf-8 -*-
"""
Created on Wed Sep 25 19:58:27 2024

"""

import QuantLib as ql
import pandas as pd
import numpy as np
from settings import model_settings
ms = model_settings()



def test_heston_calibration(
        calibration_dataset, heston_parameters,calculation_date,r,g
        ):
    test_dataset = calibration_dataset.copy()
    for i, row in test_dataset.iterrows():
        s = row['spot_price']
        k = row['strike_price']
        moneyness = k-s
        if moneyness < 0:
            test_dataset.at[i,'w'] = 'put'
        else:
            test_dataset.at[i,'w'] = 'call'
            
    s = test_dataset['spot_price']
    k = test_dataset['strike_price']
    t = test_dataset['days_to_maturity']
    volatility = test_dataset['volatility']
    w = test_dataset['w']
    v0 = heston_parameters['v0']
    kappa = heston_parameters['kappa']
    theta = heston_parameters['theta']
    eta = heston_parameters['eta']
    rho = heston_parameters['rho']
    
    expiration_dates = []
    for mat in t:
        expiration_dates.append(calculation_date + ql.Period(int(mat),ql.Days))

    test_dataset['ql_heston_price'] = ms.vector_black_scholes(
        s, k, t, r, volatility, w)
    
    test_dataset['ql_black_scholes'] = ms.vector_qlbs(
        s, k, r, 0.00, volatility, w, calculation_date, expiration_dates)
    
    test_dataset['numpy_black_scholes'] = ms.vector_heston_price(
        s, k, r, 0.00, w, v0, kappa, theta, eta, rho, calculation_date, 
        expiration_dates)
        
    print_test = test_dataset[
        ['w', 'spot_price','strike_price', 'days_to_maturity', 
         'ql_heston_price', 'ql_black_scholes','numpy_black_scholes']].copy()
    
    print_test['relative_error'] = \
         (print_test['ql_heston_price']/print_test['numpy_black_scholes'])-1
         
    test_avg = np.average(np.abs(np.array(print_test['relative_error'])))
    test_avg_print = f"{round(test_avg*100,4)}%"
    
    heston_parameters['relative_error'] = test_avg
    
    pd.set_option("display.max_columns",None)
    print(f"\ncalibration test:\n{print_test}\n"
          f"repricing average absolute relative error: {test_avg_print}"
          f"\n{heston_parameters}\n")
    pd.reset_option("display.max_columns")
    
    return heston_parameters


