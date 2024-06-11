# metrics_long: LONG TREND FOLLOWING STRATEGY [CONSIDER STOP P/L IF CONTINUOUS OPENING CONDITION IS NOT MET] & PERFORMANCE METRICS PER TRADE (May-13)
# coding="utf-8"
import os
import sys
sys.path.insert(0, os.getcwd())
import talib as ta
import pandas as pd
import numpy as np
import datetime

def process_csv(file_path):
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
    total_trading_cost = 0
    trades = []
    daily = []
    # LONG TREND FOLLWOING STRATEGY [CONSIDER STOP P/L IF CONTINOUS OPENING CONDITION IS NOT MET]
    # USE (ADX, BIAS) = (35, 10) FOR CTZ AS AN EXAMPLE
    for i in range(1, len(df)):
        trading_date = df['trading_date'][i]
        if df['tradeability'][i] == 'tradeable':
            if df['ADX'][i-1] > 35 and \
               df['close'][i-1] > df['EMA10'][i-1] and \
               df['EMA10'][i-1] > df['EMA20'][i-1] and \
               df['EMA10'][i-1] > df['EMA10'][i-2] and \
               df['EMA20'][i-1] > df['EMA20'][i-2] and \
               df['BIAS'][i-1] < 10 and \
               position < 3:
                action = 'BUY'
                price = df['open'][i]
                position += 1
                trading_cost = 0.0005 * price 
                total_trading_cost += trading_cost
                current_cash -= (price + trading_cost)
                current_capital = current_cash + (position * df['open'][i]) 
                trades.append([trading_date, action, price, position, trading_cost, current_capital]) 
            elif position > 0:
                if df['close'][i-1] < df['EMA10'][i-1] or \
                   df['BIAS'][i-1] > 10:
                    action = 'SELL'
                    price = df['open'][i]
                    current_cash += price * position
                    trading_cost = 0.0005 * price * position
                    position = 0
                    total_trading_cost += trading_cost
                    current_cash -= trading_cost
                    current_capital = current_cash
                    trades.append([trading_date, action, price, position, trading_cost, current_capital]) 
                else:
                    action = 'HOLD'
                    price = None
                    trading_cost = 0
                    if df['close'][i] > df['close'][i-1] or \
                       df['close'][i] == df['close'][i-1]:  
                        current_cash += position * (df['close'][i] - df['close'][i-1])
                        current_capital += position * (df['close'][i] - df['close'][i-1])
                    else:
                        current_cash -= position * (df['close'][i-1] - df['close'][i])	
                        current_capital -= position * (df['close'][i-1] - df['close'][i])
                    #trades.append([trading_date, action, price, position, trading_cost, current_capital]) 
            else:
                action = None
                #price = None
                trading_cost = 0
                #current_cash = current_capital
        else:
            action = None
            #price = None
            trading_cost = 0
            #current_cash = current_cash   
    trades_df = pd.DataFrame(trades, columns=['date', 'action', 'price', 'current_share_holding', 'trading_cost', 'current_capital'])
    # CALCULATE PERFORMANCE METRICS
    trades_df['daily_returns'] = trades_df['current_capital'].pct_change()
    final_sharpe_ratio = trades_df['daily_returns'].mean() / trades_df['daily_returns'].std()
    final_max_drawdown = (1 - (trades_df['current_capital'] / trades_df['current_capital'].cummax())).max() # max_dd = MAX(1 - current_capital / high_water_mark)
    daily_returns = trades_df['daily_returns']
    def calculate_gain_to_pain_ratio(daily_returns): #https://jackschwager.com/market-wizards-search-part-2-the-performance-statistics-i-use/
        total_pain = sum([r if r < 0 else 0 for r in daily_returns])
        total_gain = sum([r if r > 0 else 0 for r in daily_returns])
        if total_pain == 0:
            return float('inf')  # return infinity if total pain is zero to avoid division by zero
        else:
            return abs(total_gain / total_pain)
    final_gain_to_pain_ratio = calculate_gain_to_pain_ratio(daily_returns)
    #final_pain_to_gain_ratio = (-final_max_drawdown) / trades_df['current_capital'].cummax().max()
    trades_df['final_sharpe_ratio'] = final_sharpe_ratio
    trades_df['final_max_drawdown'] = final_max_drawdown
    trades_df['final_gain_to_pain_ratio'] = final_gain_to_pain_ratio
    # SAVE RESULTS
    result_folder = "result"
    if not os.path.exists(result_folder):
        os.makedirs(result_folder)
    trades_excel_path = os.path.join(result_folder, os.path.basename(file_path).replace(".csv", "_trades.xlsx"))
    trades_df.to_excel(trades_excel_path, index=False, float_format='%.4f')
    #trades_df.to_csv(os.path.join(result_folder, os.path.basename(file_path).replace(".csv", "_trades.csv")), index=False)
    print(f"Processed {file_path} and saved trade record to {result_folder}")
    print("Final Sharpe Ratio:", final_sharpe_ratio)
    print("Final Max Drawdown:", final_max_drawdown)
    print("Final Gain-to-Pain Ratio:", final_gain_to_pain_ratio)
    print("Total Trading Cost:", total_trading_cost)
    # OUTPUT METRICS TO "metrics.csv"
    metrics_df = pd.DataFrame({
        'Code': [os.path.basename(file_path).replace(".csv", "")],
        'Final_Sharpe_Ratio': [final_sharpe_ratio],
        'Final_Max_Drawdown': [final_max_drawdown],
        'Final_Gain_to_Pain_Ratio': [final_gain_to_pain_ratio]
    })
    metrics_file = os.path.join(output_folder, "metrics.csv")
    if not os.path.exists(metrics_file):
        metrics_df.to_csv(metrics_file, index=False)
    else:
        metrics_df.to_csv(metrics_file, mode='a', header=False, index=False)
    print(f"Saved metrics to {metrics_file}")
if __name__ == "__main__":
    input_folder = "C:/Users/Jiaxu/Desktop/quant/test"
    output_folder = "C:/Users/Jiaxu/Desktop/quant/result"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    for filename in os.listdir(input_folder):
        if filename.endswith(".csv"):
            file_path = os.path.join(input_folder, filename)
            process_csv(file_path)