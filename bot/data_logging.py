def log_sandwich(mode, path, token0_reserve, token1_reserve, attacker_amount_in, attacker_amount_out, revenue, profit, slippage):
	if mode == 0:
		print("SwapExactTokensForTokens Attack")
		print("-------------------------------")
	elif mode == 1:
		print("SwapTokensForExactTokens Attack")
		print("-------------------------------")
	print("Slippage:", slippage)
	print("Token0 reserve", token0_reserve)
	print("Token1 reserve", token1_reserve)
	print("Attacker amount IN:", attacker_amount_in)
	print("Attacker amount OUT:", attacker_amount_out)
	print("Revenue:", revenue / 1e18)
	print("PROFIT:", profit)