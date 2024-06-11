# CTA_ver1: IMPLEMENT UNI-DIRACTIONAL CTA STRATEGY WITH OPTIMAL (ADX, BIAS) PAIRS FOR LISTED CONTRACTS TO GENERATE TRADE RECORDS, DAILY PNLS, AND PERFORMANCE METRICS
# coding="utf-8"
import os
import sys
sys.path.insert(0, os.getcwd())
import talib as ta
import pandas as pd
import numpy as np
import datetime
# READ STRATEGY FILE
def read_strategy(strategy_file):
    strategy_df = pd.read_csv(strategy_file)
    return strategy_df
# PROCESS HISTROICAL DATA FILES
def process_csv(file_path, strategy_df):
    # EXTRACT CTA STRATEGY INFORMATION FROM quant/CTA_data/instruction/CTA_strategy.csv
    contract_code = os.path.basename(file_path).replace(".csv", "")
    print("Contract Code:", contract_code)
    contract_strategy = strategy_df[strategy_df['CODE'] == contract_code].iloc[0]
    print(contract_strategy)
    if contract_strategy['RUN_OR_NOT'] != 'RUN':
        print(f"Skipping {file_path} as per strategy instruction.")
        return
    adx_optimal = contract_strategy['ADX_OPTIMAL']
    bias_optimal = contract_strategy['BIAS_OPTIMAL']
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
    initial_cash = 10000
    current_cash = initial_cash
    current_capital = initial_cash 
    trading_cost = 0  
    #total_trading_cost = 0
    action = None
    trades = []
    daily = []
    for i in range(1, len(df)):
        trading_date = df['trading_date'][i]
        if df['tradeability'][i] == 'tradeable':
            # LONG TREND FOLLWOING STRATEGY
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
                    #total_trading_cost += trading_cost
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
                        #total_trading_cost += trading_cost
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
                        else:
                            current_cash -= position * (df['close'][i-1] - df['close'][i])
                        current_capital = current_cash + (position * df['open'][i])
                else:
                    action = None
                    #price = None
                    trading_cost = 0
                    #current_cash = current_cash
            # SHORT TREND FOLLWOING STRATEGY
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
                    #total_trading_cost += trading_cost
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
                        #total_trading_cost += trading_cost
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
                        else:
                            current_cash -= position * (df['close'][i-1] - df['close'][i])
                        current_capital = current_cash + (position * df['open'][i])
                else:
                    action = None
                    #price = None
                    trading_cost = 0
                    #current_cash = current_cash
        else:
            action = None
            #price = None
            trading_cost = 0
            #current_cash = current_cash
        daily_capital = current_cash + (position * df['close'][i])
        daily.append([trading_date, df['close'][i], action, df['open'][i], position, trading_cost, current_cash, current_capital, daily_capital]) 
        trades_df = pd.DataFrame(trades, columns=['trading_date', 'action', 'price', 'current_share_holding', 'trading_cost', 'current_cash', 'current_capital'])
        daily_df = pd.DataFrame(daily, columns=['date', 'close', 'action', 'open', 'current_share_holding', 'trading_cost', 'current_cash', 'current_capital', 'daily_capital'])
    # PERFORMANCE METRICS PER TRADE AND PERFORMANCE METRICS DAILY
    trades_df['per_trade_returns'] = trades_df['current_capital'].pct_change()
    daily_df['daily_returns'] = daily_df['daily_capital'].pct_change()
    sharpe_ratio_per_trade = trades_df['per_trade_returns'].mean() / trades_df['per_trade_returns'].std()
    sharpe_ratio_daily = daily_df['daily_returns'].mean() / daily_df['daily_returns'].std()
    max_drawdown_per_trade = (1 - (trades_df['current_capital'] / trades_df['current_capital'].cummax())).max()
    max_drawdown_daily = (1 - (daily_df['daily_capital'] / daily_df['daily_capital'].cummax())).max()
    per_trade_returns = trades_df['per_trade_returns']
    def calculate_gain_to_pain_ratio_per_trade(per_trade_returns):
        total_pain_per_trade = sum([r if r < 0 else 0 for r in per_trade_returns])
        total_gain_per_trade = sum([r if r > 0 else 0 for r in per_trade_returns])
        if total_pain_per_trade == 0:
            return float('inf')  
        else:
            return abs(total_gain_per_trade / total_pain_per_trade)
    gain_to_pain_ratio_per_trade = calculate_gain_to_pain_ratio_per_trade(per_trade_returns)
    daily_returns = daily_df['daily_returns']
    def calculate_gain_to_pain_ratio_daily(daily_returns): 
        total_pain_daily = sum([r if r < 0 else 0 for r in daily_returns])
        total_gain_daily = sum([r if r > 0 else 0 for r in daily_returns])
        if total_pain_daily == 0:
            return float('inf') 
        else:
            return abs(total_gain_daily / total_pain_daily)
    gain_to_pain_ratio_daily = calculate_gain_to_pain_ratio_daily(daily_returns)
    trades_df['sharpe_ratio_per_trade'] = sharpe_ratio_per_trade
    trades_df['max_drawdown_per_trade'] = max_drawdown_per_trade
    trades_df['gain_to_pain_ratio_per_trade'] = gain_to_pain_ratio_per_trade
    daily_df['sharpe_ratio_daily'] = sharpe_ratio_daily
    daily_df['max_drawdown_daily'] = max_drawdown_daily
    daily_df['gain_to_pain_ratio_daily'] = gain_to_pain_ratio_daily
    # OUTPUT TRADE RECORDS AND DAILY PNLS ALONG WITH PERFORMANCE METRICS to "_trades.xlsx" and "_daily.xlsx"
    result_folder = "CTA_result"
    if not os.path.exists(result_folder):
        os.makedirs(result_folder)
    trades_excel_path = os.path.join(result_folder, os.path.basename(file_path).replace(".csv", "_trades.xlsx"))
    trades_df.to_excel(trades_excel_path, index=False, float_format='%.4f')
    daily_excel_path = os.path.join(result_folder, os.path.basename(file_path).replace(".csv", "_daily.xlsx"))
    daily_df.to_excel(daily_excel_path, index=False, float_format='%.4f')
    print(f"Processed {file_path} and saved trade record to {result_folder}")
    print("Sharpe Ratio Per Trade:", sharpe_ratio_per_trade)
    print("Max Drawdown Per Trade:", max_drawdown_per_trade)
    print("Gain-to-Pain Ratio Per Trade:", gain_to_pain_ratio_per_trade)
    print(f"Processed {file_path} and saved daily record to {result_folder}")
    print("Sharpe Ratio Daily:", sharpe_ratio_daily)
    print("Max Drawdown Daily:", max_drawdown_daily)
    print("Gain-to-Pain Ratio Daily:", gain_to_pain_ratio_daily)
    # OUTPUT PERFORMANCE METRICS PER TRADE FOR ALL CONTRACTS TO "performance_metrics_per_trade.csv"
    performance_metrics_per_trade_df = pd.DataFrame({
        'Code': [os.path.basename(file_path).replace(".csv", "")],
        'Sharpe_Ratio_Per_Trade': [sharpe_ratio_per_trade],
        'Max_Drawdown_Per_Trade': [max_drawdown_per_trade],
        'Gain_to_Pain_Ratio_Per_Trade': [gain_to_pain_ratio_per_trade]
    })
    performance_metrics_per_trade_file = os.path.join(result_folder, "performance_metrics_per_trade.csv")
    if not os.path.exists(performance_metrics_per_trade_file):
        performance_metrics_per_trade_df.to_csv(performance_metrics_per_trade_file, index=False)
    else:
        performance_metrics_per_trade_df.to_csv(performance_metrics_per_trade_file, mode='a', header=False, index=False)
    print(f"Saved performance metrics per trade to {performance_metrics_per_trade_file}")
    # OUTPUT PERFORMANCE METRICS DAILY FOR ALL CONTRACTS TO "performance_metrics_daily.csv"
    performance_metrics_daily_df = pd.DataFrame({
        'Code': [os.path.basename(file_path).replace(".csv", "")],
        'Sharpe_Ratio_Daily': [sharpe_ratio_daily],
        'Max_Drawdown_Daily': [max_drawdown_daily],
        'Gain_to_Pain_Ratio_Daily': [gain_to_pain_ratio_daily]
    })
    performance_metrics_daily_file = os.path.join(result_folder, "performance_metrics_daily.csv")
    if not os.path.exists(performance_metrics_daily_file):
        performance_metrics_daily_df.to_csv(performance_metrics_daily_file, index=False)
    else:
        performance_metrics_daily_df.to_csv(performance_metrics_daily_file, mode='a', header=False, index=False)
    print(f"Saved performance metrics daily to {performance_metrics_daily_file}")
if __name__ == "__main__":
    input_folder = "C:/Users/Jiaxu/Desktop/quant/CTA_data"
    result_folder = "C:/Users/Jiaxu/Desktop/quant/CTA_result"
    strategy_file = "C:/Users/Jiaxu/Desktop/quant/CTA_data/instruction/CTA_strategy.csv"
    if not os.path.exists(result_folder):
        os.makedirs(result_folder)
    strategy_df = read_strategy(strategy_file)
    for filename in os.listdir(input_folder):
        if filename.endswith(".csv"):
            file_path = os.path.join(input_folder, filename)
            process_csv(file_path, strategy_df)







