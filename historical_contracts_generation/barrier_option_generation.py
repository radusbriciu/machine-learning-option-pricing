# -*- coding: utf-8 -*-
"""
Created on Sat Sep 21 13:54:06 2024

@author: boomelage
"""
import os
import pandas as pd
import numpy as np
from joblib import Parallel, delayed
from pathlib import Path
from tqdm import tqdm
from itertools import product
from datetime import datetime
from model_settings import ms
from quantlib_pricers import barrier_option_pricer
barp = barrier_option_pricer()
pd.set_option('display.max_columns',None)
def generate_barrier_features(s, K, T, barriers, updown, OUTIN, W):
    barrier_features = pd.DataFrame(
        product([s], K, barriers, T, [updown], OUTIN, W),
        columns=[
            'spot_price', 'strike_price', 'barrier', 'days_to_maturity',
            'updown', 'outin', 'w'
        ]
    )
    
    barrier_features['barrier_type_name'] = \
        barrier_features['updown'] + barrier_features['outin']
    
    return barrier_features

ms.find_root(Path(__file__).resolve())
ms.collect_spx_calibrations()
underlying_product = ms.cboe_spx_barriers
df = ms.spx_calibrations

root_dir = Path(__file__).resolve().parent.parent.parent.parent.absolute()
datadir =  os.path.join(root_dir,underlying_product['calibrations_dir'])
file = [f for f in os.listdir(datadir) if f.find(underlying_product['calibrations_filetag'])!=-1][0]
filepath = os.path.join(datadir,file)
output_dir = os.path.join(root_dir,underlying_product['dump'])

if not os.path.exists(output_dir):
    os.mkdir(output_dir)
computed_outputs = len([f for f in os.listdir(output_dir) if f.endswith('.csv')])
print(computed_outputs)
df['calculation_date'] = pd.to_datetime(df['calculation_date'],format='mixed')
df = df.sort_values(by='calculation_date',ascending=False).reset_index(drop=True)
df = df.iloc[computed_outputs:].copy()


print(f"\n{df}")

bar = tqdm(total=df.shape[0])
def row_generate_barrier_features(row):
    s = row['spot_price']
    calculation_date = row['calculation_date'] 
    date_print = datetime(
        calculation_date.year,
        calculation_date.month,
        calculation_date.day
        ).strftime('%A, %Y-%m-%d')

    rebate = 0.
    step = 1
    K = np.linspace(
        s*0.9,
        s*1.1,
        9
    )
    T = [
        60,
        90,
        180,
        360,
        540,
        720
        ]
    OUTIN = ['Out','In']
    W = ['call','put']
        
    
    barriers = np.linspace(
        s*0.5,s*0.99,
        5
        ).astype(float).tolist()
    down_features = generate_barrier_features(
        s, K, T, barriers, 'Down', OUTIN, W)
    
    
    barriers = np.linspace(
        s*1.01,s*1.5,
        5
        ).astype(float).tolist()
    up_features = generate_barrier_features(
        s, K, T, barriers, 'Up', OUTIN, W)

    
    features = pd.concat(
        [down_features,up_features],
        ignore_index = True
        )
    features['rebate'] = rebate
    features['dividend_rate'] = row['dividend_rate']
    features['risk_free_rate'] = row['risk_free_rate']
    heston_parameters = pd.Series(row[['theta', 'kappa', 'rho', 'eta', 'v0']]).astype(float)
    features[heston_parameters.index] = np.tile(heston_parameters,(features.shape[0],1))
    features['calculation_date'] = calculation_date
    features['date'] = calculation_date.floor('D')
    features['barrier_price'] = barp.df_barrier_price(features)
    features.to_csv(os.path.join(output_dir,f'{calculation_date.strftime('%Y-%m-%d_%H%M%S%f')}_{(str(int(s*100))).replace('_','')} SPX barrier options.csv'))
    bar.update(1)

import time
start = time.time()
df.apply(row_generate_barrier_features,axis=1)
bar.close()
end = time.time()
runtime = end-start
print(f"\ncpu: {runtime}\n")


