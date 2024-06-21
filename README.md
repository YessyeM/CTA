# CTA
This work is a gift for the upcoming fund.<br>
It applies trend following strategy to all relevant contracts and suggests implementation in terms of a dashboard refreshing in a daily basis to a human trader.
## author
Yifu Zhu  Jiaxu Meng <br>
## content
* <code>metrics_long</code>: long trend following strategy [if the condition for opening a new position is not met, consider whether the conditions for stopping pervious PnL are met] & performance metrics per trade<br>
* <code>metrics_short</code>: short trend following strategy [if the condition for opening a new position is not met, consider whether the conditions for stopping pervious PnL are met] & performance metrics per trade<br>
* <code>ergodicity_optimize_long</code>: for long trend following strategy - optimize (ADX, BIAS) pairs based on Gain-to-Pain Ratio, Final Profits<br>
* <code>ergodicity_optimize_short</code>: for short trend following strategy - optimize (ADX, BIAS) pairs based on Gain-to-Pain Ratio, Final Profits<br>
* <code>CTA_ver0_long</code>: implement long trend following strategy with optimal (ADX, BIAS) pair for a single contract to generate trade records, daily PnLs, and performance metrics<br>
* <code>CTA_ver0_short</code>: implement short trend following strategy with optimal (ADX, BIAS) pair for a single contract to generate trade records, daily PnLs, and performance metrics<br>
* <code>CTA_ver1</code>: implement uni-directional CTA strategy with optimal (ADX, BIAS) pairs for listed contracts to generate trade records, daily PnLs, and performance metrics<br>
* <code>CTA_ver2</code>: implement CTA strategy with optimal (ADX, BIAS) pairs for all contracts to generate trade records, daily PnLs, and performance metrics<br>
* **<code>CTA_ver3</code>: implement CTA strategy for all contracts in monetary basis [theoretically enough initial capital]<br>**
* <code>CTA_ver4</code>: allocate initial captial=1000000 to implement CTA strategy for all contracts [iterate through each trading date over all tradeable contracts]<br>
## install
create a python environment using <code>conda</code> and clone my repository<br>
## implement
* collect historical data for all contracts in <code>data</code> folder in default format<br>
* process csv files and decide tradeability: each date should only correspond to one contract
* for one single contract, apply your designated strategy to <code>metrics_long</code> or <code>metrics_short</code> for <code>_trades.xlsx</code> trade records (in terms of point variation on initial=10000) and <code>metrics.csv</code> performance metrics (per trade statistics)<br>
* investigate optimal (ADX, BIAS) pair for each contract
* have a look at trading record based on trend following strategy by implementing CTA_ver0_long 
* investigate optimcal (ADX, BIAS) pair for each contract by exploring ergodicity_optimize_short matrixs, where you can 
