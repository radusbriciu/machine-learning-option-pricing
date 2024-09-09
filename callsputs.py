#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep  8 14:59:04 2024

A function that collects option data given there is an even number of columns
equally split between for calls and puts repsectively

"""
import os
pwd = str(os.path.dirname(os.path.abspath(__file__)))
os.chdir(pwd)
import pandas as pd
from datapwd import dirdata
import QuantLib as ql
import warnings
warnings.simplefilter(action='ignore')
import numpy as np

# pd.set_option('display.max_rows', None)  # Display all rows
# pd.set_option('display.max_columns', None)  # Display all columns

pd.reset_option('display.max_rows')
pd.reset_option('display.max_columns')

dividend_rate = 0.005
risk_free_rate = 0.05


# Pricing Settings
calculation_date = ql.Date.todaysDate()

# =============================================================================
                                                                # fetching data
data_files = dirdata()                                                            
calls = pd.DataFrame()
# puts = pd.DataFrame()
for file in data_files:
    octo = pd.read_excel(file)
    octo = octo.dropna()
    octo.columns = octo.iloc[0]
    octo = octo.drop(index = 0).reset_index().drop(
        columns = 'index')
    splitter = int(octo.shape[1]/2)
    # octoputs = octo.iloc[:,:-splitter]
    octocalls = octo.iloc[:,:splitter]
    
    octocalls.loc[:,'w'] = 1
    calls = pd.concat([calls, octocalls], ignore_index=True)

calls = calls.sort_values(by='DyEx')
calls['DyEx'] = calls['DyEx'].astype(int)
calls['IVM'] = calls['IVM']/100
calls['maturity_date'] = calls.apply(
    lambda row: calculation_date + ql.Period(
        int(row['DyEx']/365), ql.Days), axis=1)
og_calls = calls.copy()

# =============================================================================
                                                        # ivol table generation
                                                        
maturities_days = calls['DyEx'].unique()
expiration_dates = np.empty(len(maturities_days),dtype=object)
for i in range(len(expiration_dates)):
    expiration_dates[i] = calculation_date + \
        ql.Period(int(maturities_days[i]), ql.Days)


ivols = calls.copy().reset_index().drop(columns = ['index','w'])
ivols
def group_by_maturity(ivols):
    grouped = ivols.groupby('DyEx')
    group_arrays = []
    for _, group in grouped:
        group_array = group.values
        group_arrays.append(group_array)
    ivol_table = np.array(group_arrays, dtype=object)
    return ivol_table
ivol_table = group_by_maturity(ivols)
n_maturities = len(ivol_table)
n_strikes = len(ivol_table[0])
implied_vols_matrix = ql.Matrix(n_strikes,n_maturities,float(0))
for i in range(n_maturities):
    for j in range(n_strikes):
        implied_vols_matrix[j][i] = ivol_table[i][j][1]

ivolnump = np.empty(n_maturities,dtype=object)
for i in range(n_maturities):
    volmat = np.zeros(n_strikes)
    for j in range(n_strikes):
        volmat[j] = ivol_table[i][j][1]
        ivolnump[i] = volmat

