# CTA
This work is a gift for the upcoming fund.<br>
It applies trend following strategy to all relevant contracts and suggests implementation in terms of a dashboard refreshing in a daily basis to human trader.
## author
Yifu Zhu  Jiaxu Meng <br>
## content
* metrics_long: long trend following strategy [if the condition for opening a new position is not met, consider whether the conditions for stopping pervious PnL are met] & performance metrics per trade<br>
* metrics_short: short trend following strategy [if the condition for opening a new position is not met, consider whether the conditions for stopping pervious PnL are met] & performance metrics per trade<br>
* CTA_ver0_long: implement long trend following strategy with optimal (ADX, BIAS) pair for a single contract to generate trade records, daily PnLs, and performance metrics<br>
* CTA_ver0_short: implement short trend following strategy with optimal (ADX, BIAS) pair for a single contract to generate trade records, daily PnLs, and performance metrics<br>
* ergodicity_optimize_long: for long trend following strategy - optimize (ADX, BIAS) pairs based on Gain-to-Pain Ratio, Final Profits<br>
* ergodicity_optimize_short: for short trend following strategy - optimize (ADX, BIAS) pairs based on Gain-to-Pain Ratio, Final Profits<br>
* CTA_ver1: implement uni-directional CTA strategy with optimal (ADX, BIAS) pairs for listed contracts to generate trade records, daily PnLs, and performance metrics<br>
* CTA_ver2: implement CTA strategy with optimal (ADX, BIAS) pairs for all contracts to generate trade records, daily PnLs, and performance metrics<br>
* **CTA_ver3: implement CTA strategy for all contracts in monetary basis [theorectically enough initial capital]<br>**
* __CTA_ver4: allocate initial captial=1000000 to implement CTA strategy for all contracts [iterate through each trading date over all tradeable contracts]<br>__
