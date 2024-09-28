# -*- coding: utf-8 -*-
"""
Created on Thu Sep 26 17:33:55 2024

@author: boomelage
"""

import os
import sys
import numpy as np
import pandas as pd
import time
from datetime import datetime
from itertools import product

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from settings import model_settings

ms = model_settings()

os.chdir(current_dir)

start = time.time()

pd.reset_option('display.max_rows')

def generate_initial_barrier_features(s,T,K,outins,updown,ws):
    features = pd.DataFrame(
        product(
            [s],
            T,
            K,
            [updown],
            outins,
            ws
            ),
        columns=[
            'spot_price', 
            'days_to_maturity',
            'strike_price',
            'updown',
            'outin',
            'w'
                  ])
    return features

"""
# =============================================================================
"""


def generate_barrier_options(
        n_strikes, down_k_spread, up_k_spread,
        n_barriers, barrier_spread, n_barrier_spreads,
        calculation_date, T, s, g, heston_parameters, file_path
        ):

    K = np.linspace(
        s*(1-down_k_spread),
        s*(1+up_k_spread),
        n_strikes
        )
    
    outins = [
        
        'Out',
        'In'
        
        ]
    
    ws = [
        
          'call',
          'put'
          
          ]
    
    
    """
    up features
    """
    
    initial_up_features = generate_initial_barrier_features(
        s,T,K,outins,'Up',ws)
    
    initial_up_features
    
    up_features = pd.DataFrame()
    
    for i, row in initial_up_features.iterrows():
        s = row['spot_price']
        k = row['strike_price']
        t = row['days_to_maturity']
        barriers = np.linspace(
            s*(1+barrier_spread),
            s*(1+barrier_spread*n_barrier_spreads),
            n_barriers
            )    
        
        up_subset =  pd.DataFrame(
            product(
                [s],
                [t],
                [k],
                ['Up'],
                outins,
                ws,
                barriers
                ),
            columns=[
                'spot_price', 
                'days_to_maturity',
                'strike_price',
                'updown',
                'outin',
                'w',
                'barrier'
                      ])
        
        up_subset['barrier_type_name'] = up_subset['updown']+up_subset['outin']
        
        print(f"\n{up_subset}\n")
    
        up_features = pd.concat(
            [up_features, up_subset],
            ignore_index = True)    
    
    """
    down features
    """
    
    initial_down_features = generate_initial_barrier_features(
        s,T,K,outins,'Down',ws)
    
    initial_down_features
    
    down_features = pd.DataFrame()
    
    for i, row in initial_down_features.iterrows():
        s = row['spot_price']
        k = row['strike_price']
        t = row['days_to_maturity']
        outin = row['outin']
        w = row['w']
        
        
        barriers = np.linspace(
            s*(1-barrier_spread*n_barrier_spreads),
            s*(1-barrier_spread),
            n_barriers
            )    
        
        down_subset =  pd.DataFrame(
            product(
                [s],
                [t],
                [k],
                ['Down'],
                [outin],
                [w],
                barriers
                ),
            columns=[
                'spot_price', 
                'days_to_maturity',
                'strike_price',
                'updown',
                'outin',
                'w',
                'barrier'
                      ])
        
        
        down_subset['barrier_type_name'] = down_subset['updown']+down_subset['outin']
        
        print(f"\n{down_subset}\n")
        
        down_features = pd.concat(
            [down_features, down_subset],
            ignore_index = True)    
            
    
    
    features = pd.concat([down_features,up_features],ignore_index=True)
    
    features['eta'] = heston_parameters['eta'].iloc[0]
    features['theta'] = heston_parameters['theta'].iloc[0]
    features['kappa'] = heston_parameters['kappa'].iloc[0]
    features['rho'] = heston_parameters['rho'].iloc[0]
    features['v0'] = heston_parameters['v0'].iloc[0]
    features['heston_price'] = np.nan
    features['heston_price'] = np.nan
    features['barrier_price'] = np.nan
    
    pricing_bar = ms.make_tqdm_bar(
        desc="pricing",total=features.shape[0],unit='contracts',leave=False)
    
    for i, row in features.iterrows():
        
        barrier_type_name = row['barrier_type_name']
        barrier = row['barrier']
        s = row['spot_price']
        k = row['strike_price']
        t = row['days_to_maturity']
        w = row['w']
        r = 0.04
        rebate = 0.
        
        v0 = heston_parameters['v0'].iloc[0]
        kappa = heston_parameters['kappa'].iloc[0] 
        theta = heston_parameters['theta'].iloc[0] 
        eta = heston_parameters['eta'].iloc[0] 
        rho = heston_parameters['rho'].iloc[0]
        
        heston_price = ms.ql_heston_price(
            s,k,t,r,g,w,v0,kappa,theta,eta,rho,calculation_date
            )
        features.at[i,'heston_price'] = heston_price
        
        barrier_price = ms.ql_barrier_price(
                s,k,t,r,g,calculation_date,w,
                barrier_type_name,barrier,rebate,
                v0, kappa, theta, eta, rho)
    
        features.at[i,'barrier_price'] = barrier_price
        
        pricing_bar.update(1)
    pricing_bar.close()
    
    training_data = features.copy()
    
    training_data = ms.noisyfier(training_data)
    
    pd.set_option("display.max_columns",None)
    print(f'\n{training_data}\n')
    print(f'\n{training_data.describe()}')
    pd.reset_option("display.max_columns")
    
    file_date = datetime(
        calculation_date.year(), 
        calculation_date.month(), 
        calculation_date.dayOfMonth())
    date_tag = file_date.strftime("%Y-%m-%d")
    file_time = datetime.fromtimestamp(time.time())
    file_time_tag = file_time.strftime("%Y-%m-%d %H%M%S")
    # training_data.to_csv(os.path.join(
    #     file_path,f'barriers {date_tag} {file_time_tag}.csv'))
    
    return training_data

