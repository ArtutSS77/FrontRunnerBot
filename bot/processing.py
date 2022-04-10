import time

from constants import *
from calculations import *


def decode_tx(tx):
	inp = tx["input"]
	multicall_data = multicall.decode_function_input(inp)
	uniswap_data = uniswap.decode_function_input(multicall_data[1]["data"][0].hex())
	selector = multicall_data[1]["data"][0].hex()[0:8]
	deadline = multicall_data[1]["deadline"]
	gas_price = tx['gasPrice']
	return selector, deadline, uniswap_data, gas_price


def multi_buy_tokens(attacker_amount_out, attacker_amount_in, path, deadline, gas_price, value):
	encoded_bytes = uniswap.encodeABI(fn_name="swapTokensForExactTokens",
		args=[attacker_amount_out, attacker_amount_in, path, attacker_account.address])
	multi_attack = multicall.functions.multicall(deadline, [
		bytes.fromhex((encoded_bytes[2:len(encoded_bytes)]))]).buildTransaction({
		'from': attacker_account.address,
		'nonce': w3.eth.getTransactionCount(attacker_account.address, 'pending'),
		'gas': 300000,
		'gasPrice': gas_price,
		'value': value
	})
	signed_multi_attack = attacker_account.signTransaction(multi_attack)
	tx_hash = w3.eth.sendRawTransaction(signed_multi_attack.rawTransaction)
	print("Buying: ", tx_hash.hex())


def multi_sell_tokens(attacker_amount_out, revenue, path, deadline, gas_price, value):
	time.sleep(20)
	encoded_bytes = uniswap.encodeABI(fn_name="swapExactTokensForTokens",
		args=[attacker_amount_out, revenue, path, attacker_account.address])
	multi_sell = multicall.functions.multicall(deadline,
		[bytes.fromhex((encoded_bytes[2:len(encoded_bytes)]))]).buildTransaction(
		{
			'from': attacker_account.address,
			'nonce': w3.eth.getTransactionCount(attacker_account.address, 'pending'),
			'gas': 300000,
			'gasPrice': gas_price,
			'value': value
		})
	signed_multi_sell = attacker_account.signTransaction(multi_sell)
	tx_hash = w3.eth.sendRawTransaction(signed_multi_sell.rawTransaction)
	print("Selling: ", tx_hash.hex())


def attack_multi_swap_exact_for(deadline, uniswap_data, gas_price):
	print(uniswap_data[1]["path"])
	pair = uniswap_v2_factory.functions.getPair(uniswap_data[1]["path"][0], uniswap_data[1]["path"][1]).call()
	pair_contract = w3.eth.contract(address=pair, abi=uniswap_v2_pair_abi)
	reserves = pair_contract.functions.getReserves().call()
	print("Reserves:", reserves)
	token0 = uniswap_data[1]["path"][0]
	pair_token0 = pair_contract.functions.token0().call()
	token0_in = False
	if token0 == pair_token0:
		token0_in = True
		token1 = uniswap_data[1]["path"][1]
		token0_amount = uniswap_data[1]["amountIn"]
		token1_amount = uniswap_data[1]["amountOutMin"]
	else:
		token0 = uniswap_data[1]["path"][1]
		token1 = uniswap_data[1]["path"][0]
		token0_amount = uniswap_data[1]["amountOutMin"]
		token1_amount = uniswap_data[1]["amountIn"]
	token0_reserve = reserves[0]
	token1_reserve = reserves[1]
	if token0_in:
		amount_out = calc_amount_out(token0_amount, token0_reserve, token1_reserve)
		slippage = 1 - token1_amount / amount_out
		print("Slippage:", slippage)
		if slippage > 0.05:
			attacker_amount_in = calc_attack_amount_in(token0_amount, token1_amount, token0_reserve, token1_reserve)
			attacker_amount_out = int(calc_amount_out(attacker_amount_in, token0_reserve, token1_reserve) * 0.995)
			attacker_amount_in = int(calc_amount_in(attacker_amount_out, token0_reserve, token1_reserve) * 1.005)
			print("Token0 reserve:", token0_reserve)
			print("Token1 reserve:", token1_reserve)
			print("Attacker amount IN:", attacker_amount_in)
			print("Attacker amount OUT:", attacker_amount_out)
			revenue = int(calc_revenue(attacker_amount_in, token0_amount, attacker_amount_out, token1_amount, token0_reserve, token1_reserve) * 0.995)
			print("Revenue:", revenue / 1e18)
			print("PROFIT:", (revenue - attacker_amount_in) / 1e18)
			multi_buy_tokens(attacker_amount_out, attacker_amount_in, [token0, token1], deadline, gas_price * 2, 0)
			multi_sell_tokens(attacker_amount_out, revenue, [token1, token0], deadline, gas_price, attacker_amount_out)
	else:
		amount_out = calc_amount_out(token1_amount, token1_reserve, token0_reserve)
		slippage = 1 - token0_amount / amount_out
		print("Slippage:", slippage)
		if slippage > 0.05:
			attacker_amount_in = calc_attack_amount_in(token1_amount, token0_amount, token1_reserve, token0_reserve)
			attacker_amount_out = int(calc_amount_out(attacker_amount_in, token1_reserve, token0_reserve) * 0.995)
			attacker_amount_in = int(calc_amount_in(attacker_amount_out, token1_reserve, token0_reserve) * 1.005)
			print("Token0 reserve", token0_reserve)
			print("Token1 reserve", token1_reserve)
			print("Attacker amount IN:", attacker_amount_in)
			print("Attacker amount OUT:", attacker_amount_out)
			revenue = int(calc_revenue(attacker_amount_in, token1_amount, attacker_amount_out, token0_amount, token1_reserve, token0_reserve) * 0.995)
			print("Revenue", revenue / 1e18)
			print("PROFIT:", (revenue - attacker_amount_in) / 1e18)
			multi_buy_tokens(attacker_amount_out, attacker_amount_in, [token1, token0], deadline, gas_price * 2, attacker_amount_in)
			multi_sell_tokens(attacker_amount_out, revenue, [token0, token1], deadline, int(gas_price * 0.99), 0)


def process_tx(tx):
	print(tx["input"][0:10])
	print(tx["to"])
	if tx["to"] == "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45":
		if tx["input"][0:10] == MULTICALL_SELECTOR:
			selector, deadline, uniswap_data, gas_price = decode_tx(tx)
			print(selector)
			if selector == SWAP_EXACT_FOR_SELECTOR:
				attack_multi_swap_exact_for(deadline, uniswap_data, gas_price)
