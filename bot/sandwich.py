import json
import time
from web3 import Web3
from calculations import *
from data_logging import *


class Sandwich:

	MULTI_CALL_SELECTOR = "0x5ae401dc"
	MULTI_SWAP_EXACT_FOR_SELECTOR = "472b43f3"
	MULTI_SWAP_FOR_EXACT_SELECTOR = "42712a67"
	SWAP_EXACT_FOR_SELECTOR = "0x38ed1739"
	SWAP_EXACT_ETH_FOR_SELECTOR = "0x7ff36ab5"
	SWAP_ETH_FOR_EXACT_SELECTOR = "0xfb3bdb41"

	WETH_ADDRESS = "0xc778417E063141139Fce010982780140Aa0cD5Ab"

	def __init__(self, w3_rpc, multi_call_address, v2_router_address, v2_factory_address, attacker_pk):
		self.w3 = Web3(Web3.HTTPProvider(w3_rpc))
		self.pending_filter = self.w3.eth.filter('pending')
		self.multi_call_address = multi_call_address
		self.v2_router_address = v2_router_address
		self.v2_factory_address = v2_factory_address
		multi_v2_router_abi = json.loads(open("../artifacts/contracts/IV2SwapRouter.sol/IV2SwapRouter.json").read())["abi"]
		self.multi_v2_router = self.w3.eth.contract(abi=multi_v2_router_abi)
		self.attacker_account = self.w3.eth.account.privateKeyToAccount(attacker_pk)
		multi_call_abi = json.loads(open("../artifacts/contracts/IMulticall.sol/IMulticall.json").read())["abi"]
		self.multi_call = self.w3.eth.contract(address=multi_call_address, abi=multi_call_abi)
		v2_router_abi = json.loads(open("../artifacts/contracts/IUniswapV2Router02.sol/IUniswapV2Router02.json").read())["abi"]
		self.v2_router = self.w3.eth.contract(address=v2_router_address, abi=v2_router_abi)
		v2_factory_abi = json.loads(open("../artifacts/contracts/IUniswapV2Factory.sol/IUniswapV2Factory.json").read())["abi"]
		self.v2_factory = self.w3.eth.contract(address=v2_factory_address, abi=v2_factory_abi)
		self.v2_pair_abi = json.loads(open("../artifacts/contracts/IUniswapV2Pair.sol/IUniswapV2Pair.json").read())["abi"]

	def start(self):
		while True:
			for event in self.pending_filter.get_new_entries():
				tx = self.w3.eth.get_transaction(event.hex())
				if tx["from"] == "0x6408bD404C9Ba5E1021C0f863CCEaEadcB1Defb7":
					self.process_tx(tx)

	def process_tx(self, tx):
		print(tx)
		if tx["to"] == self.multi_call_address or tx["to"] == self.v2_router_address:
			tx_selector = tx["input"][0:10]
			if tx_selector == self.MULTI_CALL_SELECTOR:
				selector, deadline, decoded_data, gas_price, max_fee, max_priority_fee = self.decode_multi_call_tx(tx, )
				if selector == self.MULTI_SWAP_EXACT_FOR_SELECTOR:
					self.attack_swap_exact_for(deadline, decoded_data, max_fee, max_priority_fee, 0, True)
				elif selector == self.MULTI_SWAP_FOR_EXACT_SELECTOR:
					self.attack_swap_for_exact(deadline, decoded_data, max_fee, max_priority_fee, 0, True)
			elif tx_selector == self.SWAP_EXACT_FOR_SELECTOR or tx_selector == self.SWAP_EXACT_ETH_FOR_SELECTOR:
				decoded_data, deadline, gas_price, max_fee, max_priority_fee, value = self.decode_tx(tx)
				self.attack_swap_exact_for(deadline, decoded_data, max_fee, max_priority_fee, value, False)
			elif tx_selector == self.SWAP_ETH_FOR_EXACT_SELECTOR:
				decoded_data, deadline, gas_price, max_fee, max_priority_fee, value = self.decode_tx(tx)
				self.attack_swap_for_exact(deadline, decoded_data, max_fee, max_priority_fee, value, False)

	def decode_tx(self, tx):
		inp = tx["input"]
		decoded_data = self.v2_router.decode_function_input(inp)
		value = tx["value"]
		gas_price = tx["gasPrice"]
		max_fee = tx['maxFeePerGas']
		max_priority_fee = tx['maxPriorityFeePerGas']
		deadline = decoded_data[1]["deadline"]
		return decoded_data, deadline, gas_price, max_fee, max_priority_fee, value

	def decode_multi_call_tx(self, tx):
		inp = tx["input"]
		decoded_multi_call_data = self.multi_call.decode_function_input(inp)
		decoded_data = self.multi_v2_router.decode_function_input(decoded_multi_call_data[1]["data"][0].hex())
		selector = decoded_multi_call_data[1]["data"][0].hex()[0:8]
		deadline = decoded_multi_call_data[1]["deadline"]
		gas_price = tx['gasPrice']
		max_fee = tx['maxFeePerGas']
		max_priority_fee = tx['maxPriorityFeePerGas']
		return selector, deadline, decoded_data, gas_price, max_fee, max_priority_fee

	def get_pair_info(self, decoded_data):
		print(decoded_data[1]["path"])
		pair = self.v2_factory.functions.getPair(decoded_data[1]["path"][0], decoded_data[1]["path"][1]).call()
		pair_contract = self.w3.eth.contract(address=pair, abi=self.v2_pair_abi)
		reserves = pair_contract.functions.getReserves().call()
		print("Reserves:", reserves)
		pair_token0 = pair_contract.functions.token0().call()
		return reserves, pair_token0

	def multi_buy_tokens(self, attacker_amount_out, attacker_amount_in, path, deadline, max_fee, max_priority_fee, value):
		encoded_bytes = self.multi_v2_router.encodeABI(fn_name="swapTokensForExactTokens", args=[attacker_amount_out, attacker_amount_in, path, self.attacker_account.address])
		tx_hash = self.multi_call_send_tx(encoded_bytes, deadline, max_fee, max_priority_fee, value)
		print("Buying: ", tx_hash.hex())

	def multi_sell_tokens(self, attacker_amount_out, revenue, path, deadline, max_fee, max_priority_fee, value):
		encoded_bytes = self.multi_v2_router.encodeABI(fn_name="swapExactTokensForTokens", args=[attacker_amount_out, revenue, path, self.attacker_account.address])
		tx_hash = self.multi_call_send_tx(encoded_bytes, deadline, max_fee, max_priority_fee, value)
		print("Selling:", tx_hash.hex())

	def multi_call_send_tx(self, encoded_bytes, deadline, max_fee, max_priority_fee, value):
		multi_attack = self.multi_call.functions.multicall(deadline, [
			bytes.fromhex((encoded_bytes[2:len(encoded_bytes)]))]).buildTransaction(
			{
				'from': self.attacker_account.address,
				'nonce': self.w3.eth.getTransactionCount(self.attacker_account.address, 'pending'),
				'maxFeePerGas': max_fee,
				'maxPriorityFeePerGas': max_priority_fee,
				'value': value,
				'gas': 200000
			})
		signed_multi_sell = self.attacker_account.signTransaction(multi_attack)
		tx_hash = self.w3.eth.sendRawTransaction(signed_multi_sell.rawTransaction)
		return tx_hash

	def buy_tokens(self, attacker_amount_out, attacker_amount_in, path, deadline, max_fee, max_priority_fee, value):
		print(deadline)
		buy_tx = self.v2_router.functions.swapTokensForExactTokens(attacker_amount_out, attacker_amount_in, path, self.attacker_account.address, deadline).buildTransaction(
			{
				'from': self.attacker_account.address,
				'nonce': self.w3.eth.getTransactionCount(self.attacker_account.address, 'pending'),
				'maxFeePerGas': max_fee,
				'maxPriorityFeePerGas': max_priority_fee,
				'value': value
			}
		)
		signed_buy = self.attacker_account.signTransaction(buy_tx)
		tx_hash = self.w3.eth.sendRawTransaction(signed_buy.rawTransaction)
		print("Buying:", tx_hash.hex())

	def sell_tokens(self, attacker_amount_out, revenue, path, deadline, max_fee, max_priority_fee, value):
		sell_tx = self.v2_router.functions.swapExactTokensForTokens(attacker_amount_out, revenue, path, self.attacker_account.address, deadline).buildTransaction(
			{
				'from': self.attacker_account.address,
				'nonce': self.w3.eth.getTransactionCount(self.attacker_account.address, 'pending'),
				'maxFeePerGas': max_fee,
				'maxPriorityFeePerGas': max_priority_fee,
				'value': value,
				'gas': 200000
			}
		)
		signed_sell = self.attacker_account.signTransaction(sell_tx)
		tx_hash = self.w3.eth.sendRawTransaction(signed_sell.rawTransaction)
		print("Selling:", tx_hash.hex())

	def attack_swap_exact_for(self, deadline, decoded_data, max_fee, max_priority_fee, value, multi):
		print(decoded_data)
		reserves, pair_token0 = self.get_pair_info(decoded_data)
		if len(decoded_data[1]["path"]) == 2 and decoded_data[1]["path"][0] == self.WETH_ADDRESS:
			if pair_token0 == self.WETH_ADDRESS:
				weth_reserve = reserves[0]
				token_reserve = reserves[1]
			else:
				weth_reserve = reserves[1]
				token_reserve = reserves[0]
			token_address = decoded_data[1]["path"][1]
			weth_amount = decoded_data[1]["amountIn"] if value == 0 else value
			token_amount = decoded_data[1]["amountOutMin"]
			amount_out = calc_amount_out(weth_amount, weth_reserve, token_reserve)
			slippage = 1 - token_amount / amount_out
			print(slippage)
			if slippage > 0.05:
				attacker_amount_in = calc_attack_amount_in(weth_amount, token_amount, weth_reserve, token_reserve)
				attacker_amount_out = int(calc_amount_out(attacker_amount_in, weth_reserve, token_reserve) * 0.995)
				attacker_amount_in = int(calc_amount_in(attacker_amount_out, weth_reserve, token_reserve) * 1.005)
				revenue = int(calc_revenue(attacker_amount_in, weth_amount, attacker_amount_out, token_amount, weth_reserve, token_reserve) * 0.995)
				profit = (revenue - attacker_amount_in) / 1e18
				log_sandwich(0, decoded_data[1]["path"], weth_reserve, token_reserve, attacker_amount_in, attacker_amount_out, revenue, profit, slippage)
				if profit > 0.01:
					if multi:
						self.multi_buy_tokens(attacker_amount_out, attacker_amount_in, [self.WETH_ADDRESS, token_address], deadline, max_fee * 2, max_priority_fee * 2, attacker_amount_in)
						self.multi_sell_tokens(attacker_amount_out, revenue, [token_address, self.WETH_ADDRESS], deadline, max_fee, max_priority_fee, 0)
					else:
						self.buy_tokens(attacker_amount_out, attacker_amount_in, [self.WETH_ADDRESS, token_address], deadline, max_fee * 2, max_priority_fee * 2, 0)
						self.sell_tokens(attacker_amount_out, revenue, [token_address, self.WETH_ADDRESS], deadline, max_fee, max_priority_fee, 0)

	def attack_swap_for_exact(self, deadline, decoded_data, max_fee, max_priority_fee, value, multi):
		print(decoded_data)
		reserves, pair_token0 = self.get_pair_info(decoded_data)
		if len(decoded_data[1]["path"]) == 2 and decoded_data[1]["path"][0] == self.WETH_ADDRESS:
			if pair_token0 == self.WETH_ADDRESS:
				weth_reserve = reserves[0]
				token_reserve = reserves[1]
			else:
				weth_reserve = reserves[1]
				token_reserve = reserves[0]
			token_address = decoded_data[1]["path"][1]
			token_amount = decoded_data[1]["amountOut"]
			weth_amount = decoded_data[1]["amountInMax"] if value == 0 else value
			amount_in = calc_amount_in(token_amount, weth_reserve, token_reserve)
			slippage = 1 - amount_in / weth_amount
			if slippage > 0.05:
				attacker_amount_out = calc_attack_amount_out(weth_amount, token_amount, weth_reserve, token_reserve)
				attacker_amount_in = calc_amount_in(attacker_amount_out, weth_reserve, token_reserve)
				attacker_amount_out = int(attacker_amount_out * 0.995)
				revenue = int(calc_revenue(attacker_amount_in, weth_amount, attacker_amount_out, token_amount, weth_reserve, token_reserve) * 0.995)
				profit = (revenue - attacker_amount_in) / 1e18
				log_sandwich(0, [token_address, self.WETH_ADDRESS], weth_reserve, token_reserve, attacker_amount_in, attacker_amount_out, revenue, profit, slippage)
				if profit > 0.01:
					if multi:
						self.multi_buy_tokens(attacker_amount_out, attacker_amount_in, [self.WETH_ADDRESS, token_address], deadline, max_fee * 2, max_priority_fee * 2, attacker_amount_in)
						self.multi_sell_tokens(attacker_amount_out, revenue, [token_address, self.WETH_ADDRESS], deadline, max_fee, max_priority_fee, 0)
					else:
						self.buy_tokens(attacker_amount_out, attacker_amount_in, [self.WETH_ADDRESS, token_address], deadline, max_fee * 2, max_priority_fee * 2, 0)
						self.sell_tokens(attacker_amount_out, revenue, [token_address,self.WETH_ADDRESS], deadline, max_fee, max_priority_fee, 0)




