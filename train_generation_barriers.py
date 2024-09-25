#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 10 17:55:16 2024

"""

import os
import sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.append('term_structure')
sys.path.append('contract_details')
sys.path.append('misc')
import QuantLib as ql
import numpy as np
from settings import model_settings
import pandas as pd
import time
pd.set_option("display.max_columns",None)
pd.reset_option("display.max_rows")
ms = model_settings()
from tqdm import tqdm
from routine_calibration_testing import heston_parameters
calculation_date = ms.calculation_date
day_count = ms.day_count



def price_barrier_option(t,k,calculation_date,barrier_type_name,barrier):
    if barrier_type_name == 'UpOut':
        barrierType = ql.Barrier.UpOut
    elif barrier_type_name == 'DownOut':
        barrierType = ql.Barrier.DownOut
    elif barrier_type_name == 'UpIn':
        barrierType = ql.Barrier.UpIn
    elif barrier_type_name == 'DownIn':
        barrierType = ql.Barrier.DownIn
    else:
        print('barrier flag error')
    expiration_date = calculation_date + ql.Period(int(t), ql.Days)
    exercise = ql.EuropeanExercise(expiration_date)
    payoff = ql.PlainVanillaPayoff(ql.Option.Call, k)
    barrierOption = ql.BarrierOption(barrierType, barrier, rebate, payoff, exercise)
    barrierOption.setPricingEngine(engine)
    barrier_price = barrierOption.NPV()
    return barrier_price

"""
# Geometric Asian Option
rng = "pseudorandom" # could use "lowdiscrepancy"
numPaths = 100000

engine = ql.MCDiscreteArithmeticAPHestonEngine(hestonProcess, rng, requiredSamples=numPaths)
"""


import pandas as pd
from itertools import product
def generate_features(K,T,s):
    features = pd.DataFrame(
        product(
            [s],
            K,
            T,
            ),
        columns=[
            "spot_price", 
            "strike_price",
            "days_to_maturity",
                  ])
    return features

start = time.time()



s = ms.s

rebate = 0.

spotHandle = ql.QuoteHandle(ql.SimpleQuote(s))

v0, kappa, theta, sigma, rho = heston_parameters['v0'].iloc[0],heston_parameters['kappa'].iloc[0],\
    heston_parameters['theta'].iloc[0],heston_parameters['sigma'].iloc[0],heston_parameters['rho'].iloc[0]

flatRateTs = ms.make_ts_object(0.04)
flatDividendTs = ms.make_ts_object(0.04)

hestonProcess = ql.HestonProcess(
    flatRateTs, flatDividendTs, spotHandle, v0, kappa, theta, sigma, rho)

hestonModel = ql.HestonModel(hestonProcess)

engine = ql.FdHestonBarrierEngine(hestonModel)


"""
# =============================================================================
                    generating OTM call barrier options
"""


# T = ms.T
T = [1]

n_strikes = 20

down_k_spread = 0.01
up_k_spread = down_k_spread


n_barriers = 5
barrier_spread = 0.005
n_barrier_spreads = 5




"""
# =============================================================================
                                up options
"""

up_K = np.linspace(
    s, 
    s*(1+up_k_spread),
    n_strikes)
initial_up_features = generate_features(up_K,T,s)
up_features = pd.DataFrame()
up_bar = tqdm(
    desc="ups",
    total=initial_up_features.shape[0],
    unit='sets',
    leave=True)
for i, row in initial_up_features.iterrows():
    
    s = row['spot_price']
    k = row['strike_price']
    t = row['days_to_maturity']
    
    col_names = [
        'spot_price', 'strike_price', 'days_to_maturity','barrier','outin','w']
    strike_wise_np = np.zeros((n_barriers,len(col_names)),dtype=float)
    
    strike_wise_out = pd.DataFrame(strike_wise_np).copy()
    strike_wise_in = pd.DataFrame(strike_wise_np).copy()
    strike_wise_out.columns = col_names
    strike_wise_in.columns = col_names
    
    strike_wise_out['strike_price'] = k
    strike_wise_in['strike_price'] = k
    strike_wise_out['spot_price'] = s
    strike_wise_in['spot_price'] = s
    strike_wise_out['days_to_maturity'] = t
    strike_wise_in['days_to_maturity'] = t
    
    strike_wise_out['w'] = 'call'
    strike_wise_out['updown'] = 'Up'
    strike_wise_out['outin'] = 'Out'
    
    strike_wise_in['w'] = 'call'
    strike_wise_in['updown'] = 'Up'
    strike_wise_in['outin'] = 'In'
    
    barriers = np.linspace(
        k*(1+barrier_spread),
        k*(1+n_barrier_spreads*barrier_spread),
        n_barriers
        )
    
    strike_wise_in['barrier'] = barriers
    strike_wise_out['barrier'] = barriers
    
    strike_wise = pd.concat(
        [strike_wise_in, strike_wise_out],
        ignore_index=True)
    
    up_features = pd.concat(
        [up_features, strike_wise],
        ignore_index=True
        )
    up_bar.update(1)
up_bar.close()
    
"""
# =============================================================================
                                down options
"""

down_K = np.linspace(
    s*(1-down_k_spread),
    s,
    n_strikes
    )
initial_down_features = generate_features(down_K,T,s)
down_features = pd.DataFrame()
down_bar = tqdm(
    desc="downs",
    total=initial_down_features.shape[0],
    unit='sets',
    leave=True)
for i, row in initial_down_features.iterrows():
    
    s = row['spot_price']
    k = row['strike_price']
    t = row['days_to_maturity']
    
    col_names = [
        'spot_price', 'strike_price', 'days_to_maturity','barrier','outin','w']
    strike_wise_np = np.zeros((n_barriers,len(col_names)),dtype=float)
    
    strike_wise_out = pd.DataFrame(strike_wise_np).copy()
    strike_wise_in = pd.DataFrame(strike_wise_np).copy()
    strike_wise_out.columns = col_names
    strike_wise_in.columns = col_names
    
    strike_wise_out['strike_price'] = k
    strike_wise_in['strike_price'] = k
    strike_wise_out['spot_price'] = s
    strike_wise_in['spot_price'] = s
    strike_wise_out['days_to_maturity'] = t
    strike_wise_in['days_to_maturity'] = t
    
    strike_wise_out['w'] = 'put'
    strike_wise_out['updown'] = 'Down'
    strike_wise_out['outin'] = 'Out'
    
    strike_wise_in['w'] = 'put'
    strike_wise_in['updown'] = 'Down'
    strike_wise_in['outin'] = 'In'
    
    barriers = np.linspace(
        k*(1-barrier_spread),
        k*(1-n_barrier_spreads*barrier_spread),
        n_barriers
        )
    
    strike_wise_in['barrier'] = barriers
    strike_wise_out['barrier'] = barriers
    
    strike_wise = pd.concat(
        [strike_wise_in, strike_wise_out],
        ignore_index=True)
    
    down_features = pd.concat(
        [down_features, strike_wise],
        ignore_index=True
        )
    down_bar.update(1)
down_bar.close()
    
    
"""  
# =============================================================================
"""

features = pd.concat(
    [up_features,down_features],
    ignore_index=True)

features['barrier_type_name'] = features['updown'] + features['outin'] 
features['sigma'] = heston_parameters['sigma'].iloc[0]
features['theta'] = heston_parameters['theta'].iloc[0]
features['kappa'] = heston_parameters['kappa'].iloc[0]
features['rho'] = heston_parameters['rho'].iloc[0]
features['v0'] = heston_parameters['v0'].iloc[0]

features['barrier_price'] = np.nan
pricing_bar = tqdm(
    desc="pricing",
    total=features.shape[0],
    unit='contracts',
    leave=True)
for i, row in features.iterrows():
    barrier_type_name = row['barrier_type_name']
    barrier = row['barrier']
    s = row['spot_price']
    k = row['strike_price']
    t = row['days_to_maturity']
    calculation_date = ms.calculation_date
    barrier_price = price_barrier_option(
        t, k, calculation_date, barrier_type_name, barrier)
    features.at[i,'barrier_price'] = barrier_price
    pricing_bar.update(1)
pricing_bar.close()

training_data = features.copy()


training_data = ms.noisyfier(training_data)

pd.set_option("display.max_columns",None)
print(f'\n{training_data}\n')
pd.reset_option("display.max_columns")
