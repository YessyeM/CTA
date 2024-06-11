# CTA_ver33: IMPLEMENT CTA STRATEGY FOR ALL CONTRACTS IN MONETARY BASIS (THEORETICALLY ENOUGH INITIAL CAPITAL)
# coding="utf-8"
import os
import sys
sys.path.insert(0, os.getcwd())
import talib as ta
import pandas as pd
import numpy as np
import datetime
import openpyxl
import csv  

# READ STRATEGY FILE
def read_strategy(strategy_file):
    strategy_df = pd.read_csv(strategy_file)
    return strategy_df

# PROCESS HISTORICAL DATA FILES
def process_csv(file_path, strategy_df):
    # EXTRACT CTA STRATEGY INFORMATION FROM quant/CTA_data/instruction/CTA_strategy.csv
    contract_code = os.path.basename(file_path).replace(".csv", "")
    print("Contract Code:", contract_code)
    contract_strategies = strategy_df[strategy_df['CODE'] == contract_code]
    for index, contract_strategy in contract_strategies.iterrows():
        print(contract_strategy)
        if contract_strategy['RUN_OR_NOT'] != 'RUN':
            print(f"Skipping {file_path} as per strategy instruction.")
            continue
        adx_optimal = contract_strategy['ADX_OPTIMAL']
        bias_optimal = contract_strategy['BIAS_OPTIMAL']
        multiplier = contract_strategy['MULTIPLIER']
        # LOAD DATA AND DECIDE TRADEABILITY
        df = pd.read_csv(file_path, engine='python')
        df.columns = df.columns.str.replace(' ', '')
        df.fillna(value={'open': df['close']}, inplace=True)
        df.interpolate(method='nearest', inplace=True)
        df = df.dropna(axis=1, how='all')
        df = df.iloc[::-1]
        df = df.reset_index(drop=True)
        df['trading_date'] = pd.to_datetime(df['trading_date'], format='%m/%d/%Y')
        df['contract_year'] = df['contract_year'].apply(lambda x: int('20' + x.split('^')[1] + x.split('^')[0]))
        if 'N' in df['contract_month'].values:
            month_code = 'N'
        elif 'V' in df['contract_month'].values:
            month_code = 'V'
        elif 'X' in df['contract_month'].values:
            month_code = 'X'
        elif 'Z' in df['contract_month'].values:
            month_code = 'Z'
        else:
            month_code = input("Enter the month code of the contract (N, V, X, Z): ")
        expire_dates = []
        for i in range(len(df)):
            contract_year = df['contract_year'][i]
            if month_code == 'N':
                expire_date = pd.Timestamp(str(contract_year) + '-07-01')
            elif month_code == 'V':
                expire_date = pd.Timestamp(str(contract_year) + '-10-01')
            elif month_code == 'X':
                expire_date = pd.Timestamp(str(contract_year) + '-11-01')
            elif month_code == 'Z':
                expire_date = pd.Timestamp(str(contract_year) + '-12-01')
            else:
                print("Invalid month code!")
                break
            expire_dates.append(expire_date)
            if df['trading_date'][i].year == contract_year:
                if df['trading_date'][i] > expire_date:
                    df.loc[i, 'tradeability'] = 'nontradeable'
                else:
                    df.loc[i, 'tradeability'] = 'tradeable'
            elif df['trading_date'][i].year != contract_year and df['trading_date'][i].month < expire_date.month:
                df.loc[i, 'tradeability'] = 'not to trade'
            else:
                df.loc[i, 'tradeability'] = 'tradeable'
        # INITIALIZE VARIABLES
        df['expire_date'] = expire_dates
        df['EMA20'] = ta.EMA(df['close'], timeperiod=20)
        df['EMA10'] = ta.EMA(df['close'], timeperiod=10)
        df['EMA5'] = ta.EMA(df['close'], timeperiod=5)
        df['ADX'] = ta.ADX(df['high'], df['low'], df['close'], timeperiod=14)
        df['BIAS'] = (df['close'] - df['close'].rolling(window=20).mean()) / df['close'].rolling(window=20).mean() * 100
        position = 0  
        initial_cash = 10000 # not exactly initial cash, but enough points to cover the margin (transform to monetary basis later)
        current_cash = initial_cash
        current_capital = initial_cash 
        trading_cost = 0  
        total_trading_cost = 0
        action = None
        trades = []
        daily = []
        for i in range(1, len(df)):
            trading_date = df['trading_date'][i]
            if df['tradeability'][i] == 'tradeable':
                # LONG TREND FOLLOWING STRATEGY
                if contract_strategy['LONG/SHORT'] == 'LONG':
                    if df['ADX'][i-1] > adx_optimal and \
                       df['close'][i-1] > df['EMA10'][i-1] and \
                       df['EMA10'][i-1] > df['EMA20'][i-1] and \
                       df['EMA10'][i-1] > df['EMA10'][i-2] and \
                       df['EMA20'][i-1] > df['EMA20'][i-2] and \
                       df['BIAS'][i-1] < bias_optimal and \
                       position < 3:
                        action = 'BUY'
                        price = df['open'][i]
                        position += 1
                        trading_cost = 0.0005 * price 
                        total_trading_cost += trading_cost
                        current_cash -= (price + trading_cost)
                        current_capital = current_cash + (position * df['open'][i])
                        trades.append([trading_date, action, price, position, trading_cost, current_cash, current_capital]) 
                    elif position > 0:
                        if df['close'][i-1] < df['EMA10'][i-1] or \
                           df['BIAS'][i-1] > bias_optimal:
                            action = 'SELL'
                            price = df['open'][i]
                            current_cash += price * position
                            trading_cost = 0.0005 * price * position
                            position = 0
                            total_trading_cost += trading_cost
                            current_cash -= trading_cost
                            current_capital = current_cash
                            trades.append([trading_date, action, price, position, trading_cost, current_cash, current_capital]) 
                        else:
                            action = 'HOLD'
                            price = None
                            trading_cost = 0
                            if df['close'][i] > df['close'][i-1] or \
                               df['close'][i] == df['close'][i-1]:
                                current_cash += position * (df['close'][i] - df['close'][i-1])
                                current_capital += position  * (df['close'][i] - df['close'][i-1])
                            else:
                                current_cash -= position * (df['close'][i-1] - df['close'][i])
                                current_capital -= position * (df['close'][i-1] - df['close'][i])
                    else:
                        action = None
                        trading_cost = 0
                # SHORT TREND FOLLOWING STRATEGY
                if contract_strategy['LONG/SHORT'] == 'SHORT':
                    if df['ADX'][i-1] > adx_optimal and \
                       df['close'][i-1] < df['EMA10'][i-1] and \
                       df['EMA10'][i-1] < df['EMA20'][i-1] and \
                       df['EMA10'][i-1] < df['EMA10'][i-2] and \
                       df['EMA20'][i-1] < df['EMA20'][i-2] and \
                       df['BIAS'][i-1] > bias_optimal and \
                       position < 1:
                        action = 'SELL'
                        price = df['open'][i]
                        position += 1
                        trading_cost = 0.0005 * price 
                        total_trading_cost += trading_cost
                        current_cash -= (price + trading_cost)
                        current_capital = current_cash + (position * df['open'][i])
                        trades.append([trading_date, action, price, position, trading_cost, current_cash, current_capital]) 
                    elif position > 0:
                        if df['close'][i-1] > df['EMA10'][i-1] or \
                           df['BIAS'][i-1] < bias_optimal:
                            action = 'BUY'
                            price = df['open'][i]
                            current_cash += price * position
                            trading_cost = 0.0005 * price * position
                            position = 0
                            total_trading_cost += trading_cost
                            current_cash -= trading_cost
                            current_capital = current_cash
                            trades.append([trading_date, action, price, position, trading_cost, current_cash, current_capital]) 
                        else:
                            action = 'HOLD'
                            price = None
                            trading_cost = 0
                            if df['close'][i] < df['close'][i-1] or \
                               df['close'][i] == df['close'][i-1]:
                                current_cash += position * (df['close'][i-1] - df['close'][i])
                                current_capital += position * (df['close'][i-1] - df['close'][i])
                            else:
                                current_cash -= position * (df['close'][i] - df['close'][i-1])
                                current_capital -= position * (df['close'][i] - df['close'][i-1])
                    else:
                        action = None
                        trading_cost = 0
            else:
                action = None
                trading_cost = 0
            daily_capital = current_cash + (position * df['close'][i])
            daily.append([trading_date, df['close'][i], action, df['open'][i], position, trading_cost, current_cash, current_capital, daily_capital]) 
            #check indent position!!!
            trades_df = pd.DataFrame(trades, columns=['trading_date', 'action', 'price', 'current_share_holding', 'trading_cost', 'current_cash', 'current_capital'])
            daily_df = pd.DataFrame(daily, columns=['date', 'close', 'action', 'open', 'current_share_holding', 'trading_cost', 'current_cash', 'current_capital', 'daily_capital'])
        
        # PERFORMANCE METRICS PER TRADE AND PERFORMANCE METRICS DAILY
        
        # transform to monetary basis
        daily_df['daily_returns_diff'] = daily_df['daily_capital'] - daily_df['daily_capital'].shift(1)
        daily_df['daily_point'] = daily_df['daily_capital'] - 10000 
        daily_point = daily_df['daily_point']
        monetary_daily_profit = daily_point * multiplier
        daily_df['monetary_daily_profit'] = monetary_daily_profit
        
        trades_df['per_trade_returns_pct_change'] = trades_df['current_capital'].pct_change()
        daily_df['daily_returns_pct_change'] = daily_df['daily_capital'].pct_change()
        sharpe_ratio_per_trade = trades_df['per_trade_returns_pct_change'].mean() / trades_df['per_trade_returns_pct_change'].std()
        sharpe_ratio_daily = daily_df['daily_returns_pct_change'].mean() / daily_df['daily_returns_pct_change'].std()

        max_drawdown_per_trade = (1 - (trades_df['current_capital'] / trades_df['current_capital'].cummax())).max()
        max_drawdown_daily = (1 - (daily_df['daily_capital'] / daily_df['daily_capital'].cummax())).max()

        per_trade_returns_pct_change = trades_df['current_capital'].pct_change()
        def calculate_gain_to_pain_ratio_per_trade(per_trade_returns_pct_change):
            total_pain_per_trade = sum([r if r < 0 else 0 for r in per_trade_returns_pct_change])
            total_gain_per_trade = sum([r if r > 0 else 0 for r in per_trade_returns_pct_change])
            if total_pain_per_trade == 0:
                return float('inf')  
            else:
                return abs(total_gain_per_trade / total_pain_per_trade)
        gain_to_pain_ratio_per_trade = calculate_gain_to_pain_ratio_per_trade(per_trade_returns_pct_change)
       
        daily_returns_pct_change = daily_df['daily_capital'].pct_change()
        def calculate_gain_to_pain_ratio_daily(daily_returns_pct_change): 
            total_pain_daily = sum([r if r < 0 else 0 for r in daily_returns_pct_change])
            total_gain_daily = sum([r if r > 0 else 0 for r in daily_returns_pct_change])
            if total_pain_daily == 0:
                return float('inf') 
            else:
                return abs(total_gain_daily / total_pain_daily)
        gain_to_pain_ratio_daily = calculate_gain_to_pain_ratio_daily(daily_returns_pct_change)

        final_profit = (daily_df['daily_capital'].iloc[-1] - initial_cash) / df['close'].mean()

        trades_df['sharpe_ratio_per_trade'] = sharpe_ratio_per_trade
        trades_df['max_drawdown_per_trade'] = max_drawdown_per_trade
        trades_df['gain_to_pain_ratio_per_trade'] = gain_to_pain_ratio_per_trade
        
        daily_df['sharpe_ratio_daily'] = sharpe_ratio_daily
        daily_df['max_drawdown_daily'] = max_drawdown_daily
        daily_df['gain_to_pain_ratio_daily'] = gain_to_pain_ratio_daily
        daily_df['final_profit'] = final_profit
        
        # OUTPUT TRADE RECORDS AND DAILY PNLS ALONG WITH PERFORMANCE METRICS to "_trades.xlsx" and "_daily.xlsx"
        result_folder = "CTA_result"
        if not os.path.exists(result_folder):
            os.makedirs(result_folder)
        # OUTPUT FILE PATHS WITH SUFFIX DENOTING LONG OR SHORT STRATEGY
        output_suffix = '_long' if contract_strategy['LONG/SHORT'] == 'LONG' else '_short'
        trades_excel_path = os.path.join(result_folder, f"{os.path.basename(file_path).replace('.csv', '')}{output_suffix}_trades.xlsx")
        daily_excel_path = os.path.join(result_folder, f"{os.path.basename(file_path).replace('.csv', '')}{output_suffix}_daily.xlsx")
        trades_df.to_excel(trades_excel_path, index=False, float_format='%.4f')
        daily_df.to_excel(daily_excel_path, index=False, float_format='%.4f')
        print(f"Processed {file_path} and saved trade record to {trades_excel_path}")
        print("Sharpe Ratio Per Trade:", sharpe_ratio_per_trade)
        print("Max Drawdown Per Trade:", max_drawdown_per_trade)
        print("Gain-to-Pain Ratio Per Trade:", gain_to_pain_ratio_per_trade)
        
        print(f"Processed {file_path} and saved daily record to {daily_excel_path}")
        print("Sharpe Ratio Daily:", sharpe_ratio_daily)
        print("Max Drawdown Daily:", max_drawdown_daily)
        print("Gain-to-Pain Ratio Daily:", gain_to_pain_ratio_daily)
        print("Final Profit:", final_profit)

        # AGGREGATE PROFITS AND LOSSES FROM ALL CONTRACTS FOR TOTAL DAILY PNL
        aggregated_profits = {}
        previous_profit = 0
        # ITERATE OVER ALL FILES IN THE CTA_result FOLDER
        for filename in os.listdir(result_folder):
            if filename.endswith("_daily.xlsx"): 
                file_path = os.path.join(result_folder, filename)
                contract_code = filename.split("_")[0] 
                daily_df = pd.read_excel(file_path, header=None, skiprows=1)
                dates = daily_df.iloc[:, 0] 
                profits = daily_df.iloc[:, 11] # extract monetary daily profit
                actions = daily_df.iloc[:, 2]
                # ITERATE OVER EACH DATE, ACTION, AND PROFIT
                for date, action, profit in zip(dates, actions, profits):
                    if pd.notna(date):
                        if date in aggregated_profits:
                            existing_profit, contract_codes = aggregated_profits[date]
                            # Aggregate profits for multiple contracts
                            #aggregated_profits[date] = (existing_profit + profit, contract_codes + [contract_code])
                        else:
                            existing_profit, contract_codes = previous_profit, []
                        if action == 'BUY' or action == 'SELL':
                            new_profit = profit
                            contract_codes.append(contract_code)
                        elif action == 'HOLD':
                            new_profit = profit
                            contract_codes.append(contract_code)
                        elif pd.isna(action):
                            new_profit = existing_profit # Use the same profit as the previous day for NaN actions
                        aggregated_profits[date] = (new_profit, contract_codes) # Update the aggregated_profits dictionary     
                        previous_profit = new_profit # Update the previous profit to the current date's total profit
        aggregated_df = pd.DataFrame(list(aggregated_profits.items()), columns=['Date', 'Total Profit']) # Convert the aggregated_profits dictionary to a DataFrame
        aggregated_df[['Total Profit', 'Contract Codes']] = pd.DataFrame(aggregated_df['Total Profit'].tolist(), index=aggregated_df.index) # Extract the total profit and contract codes to separate columns

        # Sort the DataFrame by date
        aggregated_df['Date'] = pd.to_datetime(aggregated_df['Date'], format='%Y-%m-%d') 
        aggregated_df = aggregated_df.dropna(subset=['Date'])  # Drop rows with invalid dates
        # Check if the list of contract codes is empty and assign an empty string to the 'contract code' column if it is
        aggregated_df['Contract Code'] = aggregated_df['Date'].apply(lambda x: '' if len(aggregated_profits[x][1]) == 0 else ', '.join(aggregated_profits[x][1]))
        csv_file_path = os.path.join(result_folder, "monetary_daily_profit.csv")
        aggregated_df.to_csv(csv_file_path, index=False)
        print("Aggregated profits saved to:", csv_file_path)


if __name__ == "__main__":
    input_folder = "C:/Users/meng/Desktop/quant/CTA_data"
    result_folder = "C:/Users/meng/Desktop/quant/CTA_result"
    strategy_file = "C:/Users/meng/Desktop/quant/CTA_data/instruction/CTA_strategy.csv"
    if not os.path.exists(result_folder):
        os.makedirs(result_folder)
    strategy_df = read_strategy(strategy_file)
    for filename in os.listdir(input_folder):
        if filename.endswith(".csv"):
            file_path = os.path.join(input_folder, filename)
            process_csv(file_path, strategy_df)