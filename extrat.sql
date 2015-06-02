SELECT
	U.Symbol,
	SUM(U.count_orders) count_orders,
	SUM(U.count_orders_algo) count_orders_algo,
	SUM(U.count_orders_algo_market) count_orders_algo_market,
	SUM(U.count_orders_algo_limit) count_orders_algo_limit,
        SUM(U.count_order_algo_market_stop) count_order_algo_market_stop,
	SUM(U.count_order_algo_market_regular) count_order_algo_market_regular,
	SUM(U.count_order_algo_limit_stop) count_order_algo_limit_stop,
	SUM(U.count_order_algo_limit_regular) count_order_algo_limit_regular
FROM (
	SELECT
		co1.Symbol,                                 	-- COL 1
		COUNT(co1.Record_Indicator) `count_orders`, 	-- COL 2
		NULL `count_orders_algo`,                 	-- COL 3
		NULL `count_orders_algo_market`,        	-- COL 4
		NULL `count_orders_algo_limit`,          	-- COL 5
		NULL `count_order_algo_market_stop`,   		-- COL 6
		NULL `count_order_algo_market_regular`,		-- COL 7
		NULL `count_order_algo_limit_stop`,		-- COL 8
		NULL `count_order_algo_limit_regular`		-- COL 9
	FROM
		cash_order01 co1
	GROUP BY
		co1.Symbol

	UNION

	SELECT
		co2.Symbol,                             -- COL 1
		NULL , 					-- COL 2
		COUNT(co2.Record_Indicator) ,        	-- COL 3
		NULL ,        				-- COL 4
		NULL ,          			-- COL 5
		NULL ,   				-- COL 6
		NULL ,					-- COL 7
		NULL ,					-- COL 8
		NULL 					-- COL 9
	FROM
		cash_order01 co2
	WHERE
		co2.Algo_Indicator = 0
	GROUP BY
		co2.Symbol

	UNION

	SELECT
		co3.Symbol,                          	-- COL 1
		NULL , 					-- COL 2
		NULL ,                 			-- COL 3
		COUNT(co3.Record_Indicator) ,        	-- COL 4
		NULL ,          			-- COL 5
		NULL ,   				-- COL 6
		NULL ,					-- COL 7
		NULL ,					-- COL 8
		NULL 					-- COL 9
	FROM
		cash_order01 co3
	WHERE
		co3.Algo_Indicator = 0
		AND co3.Market_Order_Flag = 'Y'
	GROUP BY
		co3.Symbol

	UNION

	SELECT
		co4.Symbol,                             -- COL 1
		NULL , 					-- COL 2
		NULL ,                 			-- COL 3
		NULL ,        				-- COL 4
		COUNT(co4.Record_Indicator) ,          	-- COL 5
		NULL ,   				-- COL 6
		NULL ,					-- COL 7
		NULL ,					-- COL 8
		NULL 					-- COL 9
	FROM
		cash_order01 co4
	WHERE
		co4.Algo_Indicator = 0
		AND co4.Market_Order_Flag = 'N'
	GROUP BY
		co4.Symbol
	UNION

	SELECT
		co5.Symbol,                             -- COL 1
		NULL , 					-- COL 2
		NULL ,                 			-- COL 3
		NULL ,        				-- COL 4
		NULL ,          			-- COL 5
		COUNT(co5.Record_Indicator)  ,   	-- COL 6
		NULL ,					-- COL 7
		NULL ,					-- COL 8
		NULL 					-- COL 9
	FROM
		cash_order01 co5
	WHERE
		co5.Algo_Indicator = 0
		AND co5.Market_Order_Flag = 'Y'
		AND co5.Stop_Loss_Flag= 'Y'
	GROUP BY
		co5.Symbol
	UNION

	SELECT
		co6.Symbol,                             -- COL 1
		NULL , 					-- COL 2
		NULL ,                 			-- COL 3
		NULL ,        				-- COL 4
		NULL ,          			-- COL 5
		NULL ,   				-- COL 6
		COUNT(co6.Record_Indicator) ,		-- COL 7
		NULL ,					-- COL 8
		NULL 					-- COL 9
	FROM
		cash_order01 co6
	WHERE
		co6.Algo_Indicator = 0
		AND co6.Market_Order_Flag = 'Y'
		AND co6.Stop_Loss_Flag= 'N'
	GROUP BY
		co6.Symbol
	UNION

	SELECT
		co7.Symbol,                             -- COL 1
		NULL , 					-- COL 2
		NULL ,                 			-- COL 3
		NULL ,        				-- COL 4
		NULL ,          			-- COL 5
		NULL ,   				-- COL 6
		NULL ,					-- COL 7
		COUNT(co7.Record_Indicator) ,		-- COL 8
		NULL 					-- COL 9
	FROM
		cash_order01 co7
	WHERE
		co7.Algo_Indicator = 0
		AND co7.Market_Order_Flag = 'N'
		AND co7.Stop_Loss_Flag= 'Y'
	GROUP BY
		co7.Symbol
	UNION

	SELECT
		co8.Symbol,                             -- COL 1
		NULL , 					-- COL 2
		NULL ,                 			-- COL 3
		NULL ,        				-- COL 4
		NULL ,          			-- COL 5
		NULL ,   				-- COL 6
		NULL ,					-- COL 7
		NULL ,					-- COL 8
		COUNT(co8.Record_Indicator)		-- COL 9
	FROM
		cash_order01 co8
	WHERE
		co8.Algo_Indicator = 0
		AND co8.Market_Order_Flag = 'N'
		AND co8.Stop_Loss_Flag= 'N'
	GROUP BY
		co8.Symbol
) U
GROUP BY
	U.Symbol into outfile '/tmp/finex1.csv';
