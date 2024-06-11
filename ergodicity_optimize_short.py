# ergodicity_optimize_short: SHORT - OPTIMIZE (ADX, BIAS) PAIRS BASED ON GAIN-TO-PAIN-RATIO, FINAL-PROFITS (May-17)
# coding="utf-8"
import os
import sys
sys.path.insert(0, os.getcwd())
import talib as ta
import pandas as pd
import numpy as np
import datetime

def process_csv(file_path, output_folder):
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
    # LONG TREND FOLLWOING STRATEGY
    df['expire_date'] = expire_dates
    df['EMA20'] = ta.EMA(df['close'], timeperiod=20)
    df['EMA10'] = ta.EMA(df['close'], timeperiod=10)
    df['EMA5'] = ta.EMA(df['close'], timeperiod=5)
    df['ADX'] = ta.ADX(df['high'], df['low'], df['close'], timeperiod=14)
    df['BIAS'] = (df['close'] - df['close'].rolling(window=20).mean()) / df['close'].rolling(window=20).mean() * 100
    adx_values = [10, 15, 20, 25, 30, 35, 40, 45]
    #bias_values = [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]
    bias_values = [-3, -4, -5, -6, -7, -8, -9, -10, -12, -14, -16, -18, -20, -22, -24, -26, -28, -30]
    gain_to_pain_matrix = []
    final_profits_matrix = []
    number_of_trades_matrix = []
    for adx in adx_values:
        for bias in bias_values:
            trades = []
            position = 0  
            initial_cash = 10000
            current_cash = initial_cash
            current_capital = initial_cash
            trading_cost = 0
            total_trading_cost = 0
            for i in range(1, len(df)):
                trading_date = df['trading_date'][i]
                if df['tradeability'][i] == 'tradeable':
                    if df['ADX'][i-1] > adx and \
                       df['close'][i-1] < df['EMA10'][i-1] and \
                       df['EMA10'][i-1] < df['EMA20'][i-1] and \
                       df['EMA10'][i-1] < df['EMA10'][i-2] and \
                       df['EMA20'][i-1] < df['EMA20'][i-2] and \
                       df['BIAS'][i-1] > bias and \
                       position < 1:
                        action = 'SELL'
                        price = df['open'][i]
                        position += 1
                        trading_cost = 0.0005 * price 
                        total_trading_cost += trading_cost
                        current_cash -= (price + trading_cost)
                        current_capital = current_cash + (position * df['open'][i]) 
                        trades.append([trading_date, action, price, position, trading_cost, current_capital]) 
                    elif position > 0:
                        if df['close'][i-1] > df['EMA10'][i-1] or \
                           df['BIAS'][i-1] < bias:
                           action = 'BUY'
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
                            if df['close'][i] < df['close'][i-1] or \
                               df['close'][i] == df['close'][i-1]:  
                                current_cash += position * (df['close'][i-1] - df['close'][i])
                                current_capital += position * (df['close'][i-1] - df['close'][i])
                            else:
                                current_cash -= position * (df['close'][i] - df['close'][i-1])	
                                current_capital -= position * (df['close'][i] - df['close'][i-1])
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
            columns = ['trading_date', 'action', 'price', 'current_share_holding', 'trading_cost', 'current_capital']
            trades_df = pd.DataFrame(trades, columns=columns)
            trades_df['daily_returns'] = trades_df['current_capital'].pct_change()
            daily_returns = trades_df['daily_returns']   
            def calculate_gain_to_pain_ratio(daily_returns):
                total_pain = sum([r if r < 0 else 0 for r in daily_returns])
                total_gain = sum([r if r > 0 else 0 for r in daily_returns])
                if total_pain == 0:
                    return float('inf')
                else:
                    return abs(total_gain / total_pain)
            gain_to_pain_ratio = calculate_gain_to_pain_ratio(daily_returns)
            gain_to_pain_matrix.append([adx, bias, gain_to_pain_ratio])
            #final_profits_matrix.append([adx, bias, (trades_df['current_capital'].iloc[len(trades_df) - 1] - initial_cash) / df['close'].mean()])
            # Check if trades_df is not empty before accessing its elements
            if not trades_df.empty:
                final_profit = (trades_df['current_capital'].iloc[-1] - initial_cash) / df['close'].mean()
            else:
                final_profit = 0.0  # or any default value you prefer
            final_profits_matrix.append([adx, bias, final_profit])
            #print("被除数：", trades_df['current_capital'].iloc[-1] - initial_cash)
            #print("除数：", df['close'].mean())
            #print("final profit:", final_profit)
            number_of_trades_matrix.append([adx, bias, len(trades_df) - 1])
    matrix_df_gain_to_pain = pd.DataFrame(gain_to_pain_matrix, columns=['ADX', 'BIAS', 'Gain-to-Pain Ratio'])
    pivot_gain_to_pain_matrix = matrix_df_gain_to_pain.pivot(index='BIAS', columns='ADX', values='Gain-to-Pain Ratio')
    matrix_df_final_profits = pd.DataFrame(final_profits_matrix, columns=['ADX', 'BIAS', 'Final Profits'])
    pivot_final_profits_matrix = matrix_df_final_profits.pivot(index='BIAS', columns='ADX', values='Final Profits')
    matrix_df_number_of_trades = pd.DataFrame(number_of_trades_matrix, columns=['ADX', 'BIAS', 'Number of Trades'])
    pivot_number_of_trades_matrix = matrix_df_number_of_trades.pivot(index='BIAS', columns='ADX', values='Number of Trades')
    # Reset index to convert pivot tables into DataFrames
    pivot_gain_to_pain_matrix_reset = pivot_gain_to_pain_matrix.reset_index()
    pivot_final_profits_matrix_reset = pivot_final_profits_matrix.reset_index()
    pivot_number_of_trades_matrix_reset = pivot_number_of_trades_matrix.reset_index()
    empty_row = pd.DataFrame([[""] * len(pivot_gain_to_pain_matrix_reset.columns)], columns=pivot_gain_to_pain_matrix_reset.columns)
    second_row = pd.DataFrame([["Final Profits"] + list(pivot_gain_to_pain_matrix_reset.columns[1:])], columns=pivot_gain_to_pain_matrix_reset.columns)
    third_row = pd.DataFrame([["Number of Trades"] + list(pivot_gain_to_pain_matrix_reset.columns[1:])], columns=pivot_gain_to_pain_matrix_reset.columns)
    combined_df = pd.concat([pivot_gain_to_pain_matrix_reset, empty_row, second_row, pivot_final_profits_matrix_reset, empty_row, third_row, pivot_number_of_trades_matrix_reset])
    combined_df.reset_index(drop=True, inplace=True)
    combined_df.columns = ['Gain to Pain'] + list(combined_df.columns[1:])
    ##########combined_df.to_csv('combined_matrix.csv', index=False, float_format='%.2f')
    # look for top 5 optimal (ADX, BIAS) pairs
    #matrix_df_gain_to_pain = pd.DataFrame(gain_to_pain_matrix, columns=['ADX', 'BIAS', 'Gain-to-Pain Ratio'])
    #matrix_df_final_profits = pd.DataFrame(final_profits_matrix, columns=['ADX', 'BIAS', 'Final Profits'])
    ranked_df = pd.merge(matrix_df_gain_to_pain, matrix_df_final_profits, on=['ADX', 'BIAS'])
    ranked_df['Gain_to_Pain_Rank'] = ranked_df['Gain-to-Pain Ratio'].rank(ascending=False)
    ranked_df['Final_Profits_Rank'] = ranked_df['Final Profits'].rank(ascending=False)
    ranked_df['Weighted_Average_Rank'] = (0.5 * ranked_df['Gain_to_Pain_Rank']) + (0.5 * ranked_df['Final_Profits_Rank'])
    sorted_df = ranked_df.sort_values(by='Weighted_Average_Rank', ascending=True)
    top_five_pairs = sorted_df.head(3)
    print(top_five_pairs[['ADX', 'BIAS', 'Gain-to-Pain Ratio', 'Final Profits']])
    # SAVE RESULTS
    optimization_folder = "optimization"
    if not os.path.exists(optimization_folder):
        os.makedirs(optimization_folder)
    combined_excel_path = os.path.join(optimization_folder, os.path.basename(file_path).replace(".csv", "_combined_matrix.xlsx"))
    combined_df.to_excel(combined_excel_path, index=False, float_format='%.4f')
    #combined_df.to_csv(os.path.join(optimization_folder, os.path.basename(file_path).replace(".csv", "_combined_matrix.csv")), index=False, float_format='%.2f')
    print(f"Processed {file_path} and saved combined matrix to {combined_excel_path}")
    # OUTPUT top 5 optimal (ADX, BIAS) pairs TO "optimization.csv"
    # Extract the optimal (ADX, BIAS) pairs from top_five_pairs DataFrame
    optimal_row = top_five_pairs.iloc[0]
    optimal_adx = optimal_row['ADX']
    optimal_bias = optimal_row['BIAS']
    gain_to_pain_optimal = optimal_row['Gain-to-Pain Ratio']
    final_profits_optimal = optimal_row['Final Profits']
    ADXBIAS_df = pd.DataFrame({
        'Code': [os.path.basename(file_path).replace(".csv", "")],
        'ADX_optimal': [optimal_adx],
        'BIAS_optimal': [optimal_bias],
        'GAIN_TO_PAIN_optimal': [gain_to_pain_optimal],
        'FINAL_PROFITS_optimal': [final_profits_optimal]
    })
    ADXBIAS_file = os.path.join(output_folder, "ADXBIAS.csv")
    if not os.path.exists(ADXBIAS_file):
        ADXBIAS_df.to_csv(ADXBIAS_file, index=False)
    else:
        ADXBIAS_df.to_csv(ADXBIAS_file, mode='a', header=False, index=False)
    print(f"Saved ADXBIAS to {ADXBIAS_file}")
if __name__ == "__main__":
    input_folder = "C:/Users/Jiaxu/Desktop/quant/data"
    output_folder = "C:/Users/Jiaxu/Desktop/quant/optimization"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    for filename in os.listdir(input_folder):
        if filename.endswith(".csv"):
            file_path = os.path.join(input_folder, filename)
            process_csv(file_path, output_folder)
