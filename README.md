# Trading-Analytics
Repository to house all trading related data and analytics

Steps:
1. Build database to house all relevant trading data that is available in an easily accessible format for everyone on team.
2. Build predictive analytics utilizing data in warehouse. Predictions for flat price, calendar spreads, and intermarket spreads for kw, mw, w, matif, corn, soybeans, soybean meal, and soybean oil. Predictions for new crop acreage for each commodity on each continent.
3. Create dashboard showing the predictions and their past performance. 

Steps for predictive model algo.
1. Adjust target variable for long term trend and seasonality. Check for stationarity.
2. Adjust x variables for long term trend and seasonality. Check for stationarity.
3. Find top n predictive variables. Best way to do this... Find top n 'kendall' correlations? Use XGBoost to find them using 'feature importance' method?

Main Tools/Dashboards:
1. Price predictions mentioned above.
2. New crop planted acreage prediction. What drives it, what are those variables looking like, etc. For US, South America, Europe and Black Sea.
3. Yield sensitivity. How much less rain than normal will it take to hurt yields? Understand volatility of rainfall/temps to illustrate risk to production.
4. World supply/demand stack along with FOB prices. For any importing country, how much demand do they have left in crop year? What are delivered prices from various potential origins? Estimate how much from each country they will import. For each exporting country, estimate how much supply they have to export and where it will go based on prices.


Data:
1. See excel workbook.
