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
from itertools import product
from tqdm import tqdm
from pricing import noisyfier
from settings import model_settings
from routine_calibration_global import calibrate_heston
ms = model_settings()
import numpy as np


def generate_train_features(K,T,s,flag):
    features = pd.DataFrame(
        product(
            [s],
            K,
            T,
            flag
            ),
        columns=[
            "spot_price", 
            "strike_price",
            "days_to_maturity",
            "w"
                  ])
    return features



s = ms.s

call_K = ms.call_K
put_K = ms.put_K



n= 10
n_strikes = int(n)
n_maturities = int(n)

T = np.linspace(1,7,n_maturities).astype(int)

n_contracts = int(n_maturities*n_strikes*2)

print(f"\n\npricing {n_contracts} contracts...")



pricing_spread = 0.002
call_K_interp = np.linspace(s, s*(1+pricing_spread),int(n_strikes))
put_K_interp = np.linspace(s*(1-pricing_spread),s,int(n_strikes))


print(f"\ntrain s: {s}")
print(f"strikes between {int(min(put_K_interp))} and {int(max(call_K_interp))}")
print(f"maturities between {int(min(T))} and {int(max(T))} days")
progress_bar = tqdm(total=2, desc="generating", leave=False,
                    bar_format='{l_bar}{bar} | {n_fmt}/{total_fmt}')

call_features = generate_train_features(call_K_interp, T, s, ['call'])
put_features = generate_train_features(put_K_interp, T, s, ['put'])

train_K = np.sort(np.array([put_K_interp,call_K_interp],dtype=int).flatten())

features = pd.concat(
    [call_features,put_features],ignore_index=True).reset_index(drop=True)

def compute_moneyness_row(row):
    s = row['spot_price']
    k = row['strike_price']
    
    if row['w'] == 'call':
        call_moneyness = s-k
        row['moneyness'] = call_moneyness
        return row
    elif row['w'] == 'put':
        put_moneyness = k-s
        row['moneyness'] = put_moneyness
        return row
    else:
        raise ValueError('\n\n\nflag error')


features = features.apply(compute_moneyness_row,axis = 1)


features['dividend_rate'] = 0.02
features['risk_free_rate'] = 0.04

heston_parameters = calibrate_heston(features,s)
features['sigma'] = heston_parameters['sigma'].iloc[0]
features['theta'] = heston_parameters['theta'].iloc[0]
features['kappa'] = heston_parameters['kappa'].iloc[0]
features['rho'] = heston_parameters['rho'].iloc[0]
features['v0'] = heston_parameters['v0'].iloc[0]

progress_bar.set_description('pricing')
progress_bar.update(1)


heston_features = features.apply(ms.heston_price_vanilla_row,axis=1)
ml_data = noisyfier(heston_features)
progress_bar.update(1)
progress_bar.close()



# pd.set_option('display.max_rows',None)
pd.set_option('display.max_columns',None)
print(f"\n\ntraining dataset:\n{ml_data}")
print(f"\n\ndescriptive statistics:\n{ml_data.describe()}")
pd.reset_option('display.max_columns')
# pd.reset_option('display.max_rows')
