# -*- coding: utf-8 -*-
"""
Created on Sat Sep 21 16:10:31 2024

generation routine

"""
import os
import sys
import time
import pandas as pd
import numpy as np
import QuantLib as ql
from tqdm import tqdm
from itertools import product
from datetime import datetime
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
sys.path.append(os.path.join(parent_dir,'train_data'))
sys.path.append(os.path.join(parent_dir,'term_structure'))
from routine_calibration_global import calibrate_heston
from bicubic_interpolation import make_bicubic_functional, bicubic_vol_row
from train_generation_barriers import generate_barrier_features, \
    generate_barrier_options
from settings import model_settings
ms = model_settings()
os.chdir(current_dir)
from routine_historical_collection import collect_historical_data
historical_data = collect_historical_data()

"""
# =============================================================================
                        historical generation routine
"""

r = 0.04
historical_barriers = pd.DataFrame()
for row_i, row in historical_data.iterrows():
    s = row['spot_price']
    g = row['dividend_rate']/100
    dtdate = row['date']
    print_date = dtdate.strftime('%A %d %B %Y')
    calculation_date = ql.Date(dtdate.day,dtdate.month,dtdate.year)
    
                    ###############
                    # CALIBRATION #
                    ###############
                    
    T = ms.derman_coefs.index.astype(int)
    
    atm_volvec = np.array(row[
        [
            '30D', '60D', '3M', '6M', '12M', 
            ]
        ]/100,dtype=float)
    
    atm_volvec = pd.Series(atm_volvec)
    atm_volvec.index = T
    
    K = np.linspace( s*0.9, s*1.1, 10)
    
    derman_ts = ms.make_derman_surface(
        s,K,T,ms.derman_coefs,atm_volvec)
       
    bicubic_vol = make_bicubic_functional(
        derman_ts,K.tolist(),T.tolist())
        
    calibration_dataset =  pd.DataFrame(
        product(
            [s],
            K,
            T,
            ),
        columns=[
            'spot_price', 
            'strike_price',
            'days_to_maturity',
                  ])
    
    calibration_dataset = calibration_dataset.apply(
        bicubic_vol_row, axis = 1, bicubic_vol = bicubic_vol)
    calibration_dataset = calibration_dataset.copy()
    calibration_dataset['risk_free_rate'] = r
    
    heston_parameters, performance_df = calibrate_heston(
            calibration_dataset, 
            s,
            r,
            g,
            calculation_date
            )
    
    test_dataset = calibration_dataset.copy()
    for key in heston_parameters.index[:-1]:
        test_dataset[key] = heston_parameters[key]
    
    test_S = test_dataset['spot_price']
    test_K = test_dataset['strike_price']
    test_T = test_dataset['days_to_maturity']
    expiration_date = np.empty(len(test_T),dtype=object)
    for i,mat in enumerate(test_T):
        expiration_date[i] = calculation_date + ql.Period(
            int(mat),ql.Days)
        
    test_VOLS = test_dataset['volatility']
    w = 'put'
    
    bs_prices = ms.vector_black_scholes(
            test_S,test_K,test_T,r,test_VOLS,w
        )
    test_dataset['np_black_scholes'] = bs_prices
    
    ql_bsps = ms.vector_qlbs(
            test_S,test_K,r,g,
            test_VOLS,w,
            calculation_date, 
            expiration_date
        )
    test_dataset['ql_black_scholes'] = bs_prices
    
    hestons = ms.vector_heston_price(
            test_S,test_K,
            r,g,w,
            heston_parameters['v0'],
            heston_parameters['kappa'],
            heston_parameters['theta'],
            heston_parameters['eta'],
            heston_parameters['rho'],
            calculation_date,
            expiration_date
        )
    test_dataset['ql_heston'] = hestons
    
    pd.set_option("display.max_columns",None)
    print_cols = ['np_black_scholes', 'ql_black_scholes', 'ql_heston']
    print(f"\n{test_dataset[print_cols]}\nspot: {s} | "
          f"{row_i}/{historical_data.shape[0]} | {print_date}\n")
    pd.reset_option("display.max_columns")
    
                ###################
                # DATA GENERATION #
                ###################
    
    T = [
        
        1,2
        
        ]
    K = np.linspace(s*0.8,s*1.2,75)
    
    up_barriers = np.linspace(s*1.01,s*1.19,50)
    down_barriers = np.linspace(s*0.81,s*0.99,50)
    
    down_features = generate_barrier_features(
        s,K,T,down_barriers,'Down', ['Out','In'], ['call','put']
        )
    
    up_features = generate_barrier_features(
        s,K,T,up_barriers,'Up', ['Out','In'], ['call','put']
        )
    
    features = pd.concat([down_features,up_features],ignore_index=True)
    features['barrier_type_name'] = features['updown'] + features['outin']
    
    barrier_options = generate_barrier_options(
        features,calculation_date,heston_parameters, g, r'hist_outputs')
    
    historical_barriers = pd.concat(
        [historical_barriers, barrier_options],ignore_index=True)
    
    print(f"\n{historical_barriers.describe()}\n{print_date}")
    
