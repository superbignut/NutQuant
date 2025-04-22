.PHONY: data backtest dry strategy test ui iu 


data:
	docker compose run --rm freqtrade download-data --timeframes 15m

backtest:
	docker compose down

	docker compose run --rm freqtrade backtesting	\
	--strategy BigStrategy	\
	--dry-run-wallet 10000	\
	--timerange=20250301-20250401	\
	--cache none	\
	--breakdown day week

# docker compose -f docker-compose-bt.yml up -d

dry:
	docker compose up

strategy:
	docker compose run --rm freqtrade trade --strategy SBN_MACD_Strategy

test:
# docker compose run --rm freqtrade test-pairlist

down:
	docker compose down

ai:
	docker compose -f docker-compose-ai.yml run	\
	 --rm freqtrade trade \
	--config config_examples/config_freqai.example.json \
	--strategy FreqaiExampleStrategy \
	--freqaimodel LightGBMRegressor \
	--strategy-path freqtrade/templates
