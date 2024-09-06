#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 11:54:40 2024

@author: doomd
"""
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
import QuantLib as ql


class calibrate_heston_vanilla:
    def __init__(self):
        return
        # self.strikes = None
        # self.implied_vols_matrix = None
        # self.black_var_surface = None
        # self.data = None
    def calibrate_heston(vanilla_prices, 
                         dividend_rate, 
                         risk_free_rate,
                         implied_vols,
                         data,
                         counter_spot,
                         of_total_spots,n_strikes, nspots, n_maturities
                         ):
        day_count = ql.Actual365Fixed()
        calendar = ql.UnitedStates(m=1)
        
        calculation_date = vanilla_prices['calculation_date'][0]
        spot = vanilla_prices['spot_price'][0]
        ql.Settings.instance().evaluationDate = calculation_date
        
        
        dividend_yield = ql.QuoteHandle(ql.SimpleQuote(dividend_rate))
        dividend_rate = dividend_yield
        flat_ts = ql.YieldTermStructureHandle(ql.FlatForward(calculation_date, risk_free_rate, day_count))
        dividend_ts = ql.YieldTermStructureHandle(ql.FlatForward(calculation_date, dividend_rate, day_count))
        
        
        expiration_dates = vanilla_prices['maturity_date'].unique()
        
        strikes = vanilla_prices['strike_price'].unique()
        
    
        implied_vols = ql.Matrix(len(strikes), len(expiration_dates))
        
        
        for i in range(implied_vols.rows()):
            for j in range(implied_vols.columns()):
                implied_vols[i][j] = data[j][i]
        black_var_surface = ql.BlackVarianceSurface(
            calculation_date, calendar,
            expiration_dates, strikes,
            implied_vols, day_count)
        
        implied_vols_matrix = ql.Matrix(len(strikes), len(expiration_dates))
        for i in range(implied_vols_matrix.rows()):
            for j in range(implied_vols_matrix.columns()):
                implied_vols_matrix[i][j] = data[j][i]  
    
        # dummy parameters
        v0 = 0.01; kappa = 0.2; theta = 0.02; rho = -0.75; sigma = 0.5;
        
        process = ql.HestonProcess(flat_ts, dividend_ts,
                                   ql.QuoteHandle(ql.SimpleQuote(spot)),
                                   v0, kappa, theta, sigma, rho)
        model = ql.HestonModel(process)
        engine = ql.AnalyticHestonEngine(model)
        heston_helpers = []
        
        # Loop through all maturities and perform calibration for each one
        for current_index, date in enumerate(expiration_dates):
            print(f"\nCurrently calibrating for maturity: {date}")
            black_var_surface.setInterpolation("bicubic")
            for j, s in enumerate(strikes):
               t = day_count.yearFraction(calculation_date, date)
               sigma = black_var_surface.blackVol(t, s)  
               
               helper = ql.HestonModelHelper(
                   ql.Period(int(t * 365), ql.Days),
                   calendar, spot, s,
                   ql.QuoteHandle(ql.SimpleQuote(sigma)),
                   flat_ts, dividend_ts
               )
               helper.setPricingEngine(engine)
               heston_helpers.append(helper)
                
                
            lm = ql.LevenbergMarquardt(1e-8, 1e-8, 1e-8)
            model.calibrate(heston_helpers, lm,
                             ql.EndCriteria(500, 50, 1.0e-8,1.0e-8, 1.0e-8))
            theta, kappa, sigma, rho, v0 = model.params()
            
            print (
                "\ntheta = %f, kappa = %f, "
                "sigma = %f, rho = %f, v0 = %f" % (theta, kappa, 
                                                   sigma, rho, v0))
            avg = 0.0
            
            print ("%15s %15s %15s %20s" % (
                "Strikes", "Market Value",
                 "Model Value", "Relative Error (%)"))
            print ("="*70)
                
            for i in range(min(len(heston_helpers), len(strikes))):
                opt = heston_helpers[i]
                err = (opt.modelValue() / opt.marketValue() - 1.0)
            
                # Print the results in the formatted output
                print(f"{strikes[i]:15.2f} {opt.marketValue():14.5f} "
                      f"{opt.modelValue():15.5f} {100.0 * err:20.7f}")
                
                avg += abs(err)  # Accumulate the absolute error
            
            avg = avg*100.0/len(heston_helpers)
            print(f"{int(current_index * n_strikes + i + 1)}/"
                  f"{int(n_maturities * n_strikes * nspots)} "
                  f"prices computed")
            print(f"Set for spot {counter_spot}/{of_total_spots}")
            print("-"*70)
            print("Total Average Abs Error (%%) : %5.3f" % (avg))
    
        vanilla_prices['dividend_rate'] = dividend_rate.value()
        vanilla_prices['v0'] = v0
        vanilla_prices['kappa'] = kappa
        vanilla_prices['theta'] = theta
        vanilla_prices['sigma'] = sigma
        vanilla_prices['rho'] = rho
        
        vanilla_prices
        return vanilla_prices
    
    
    
# =============================================================================
# =============================================================================
# =============================================================================
# =============================================================================
# =============================================================================
# # # # # import numpy as np
# # # # # import matplotlib.pyplot as plt
# # # # # plt.rcParams['figure.figsize']=(15,7)
# # # # # plt.style.use("dark_background")
# # # # # from matplotlib import cm
# # # # # from mpl_toolkits.mplot3d import Axes3D
# # # # # import math
# # # # # 
# # # # # # First plot: 2D line plot of strikes vs vols
# # # # # fig, ax = plt.subplots()  # Just a single plot
# # # # # ax.plot(self.strikes, [self.implied_vols_matrix[i][0] for i in range(len(self.strikes))], label="Black Surface")
# # # # # ax.plot(self.strikes, self.data[0], "o", label="Actual")
# # # # # ax.set_xlabel("Strikes", size=12)
# # # # # ax.set_ylabel("Vols", size=12)
# # # # # legend = ax.legend(loc="upper right")
# # # # # plt.show()
# # # # # plt.close(fig)
# # # # # 
# # # # # 
# # # # # # Second plot: 3D surface plot of strikes and years vs implied vols
# # # # # plot_years = np.arange(0, 2, 0.1)
# # # # # plot_strikes = np.arange(min(self.strikes), max(self.strikes), 1.0)
# # # # # plt.show()
# # # # # ax = fig.add_subplot(projection='3d')
# # # # # X, Y = np.meshgrid(plot_strikes, plot_years)
# # # # # 
# # # # # # Calculate Z as implied volatilities over the strikes and years
# # # # # Z = np.array([self.black_var_surface.blackVol(y, x) for xr, yr in zip(X, Y)
# # # # #               for x, y in zip(xr, yr)]).reshape(len(X), len(X[0]))
# # # # # 
# # # # # surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.coolwarm, linewidth=0.1)
# # # # # fig.colorbar(surf, shrink=0.5, aspect=5)
# # # # # 
# # # # # plt.show()
# # # # # plt.close(fig)
# # # # # =============================================================================
# =============================================================================
# =============================================================================
# =============================================================================
# 
# =============================================================================
