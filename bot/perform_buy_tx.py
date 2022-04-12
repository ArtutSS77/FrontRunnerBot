from web3 import Web3
import json

w3_rpc = "http://62.113.114.85/4f5d85e2-99cd-4bd7-8f38-6a438ea18d79"
w3 = Web3(Web3.HTTPProvider(w3_rpc))

buyer_pk = "69f50fab28ad9c8cf440769e49a56ff922602bb303b843b40b7b1bd1b0e97341"
buyer_account = w3.eth.account.privateKeyToAccount(buyer_pk)

v2_router_address = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
v2_router_abi = json.loads(open("../artifacts/contracts/IUniswapV2Router02.sol/IUniswapV2Router02.json").read())["abi"]
v2_router = w3.eth.contract(address=v2_router_address, abi=v2_router_abi)