# a simple dual momentum strategy
# long a stock/index when 1) it is top N by return of previous k months 
# 2) its return of previous k months is better than cash account

# input: 
# pmat, price series matrix order by column
# N, top N in momentum
# k1, k2, lookback from k1 to k2 days 
# step, rebalance every step days
# r, rate of cash account

