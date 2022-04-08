import json

from web3 import Web3

w3 = Web3(Web3.HTTPProvider("http://62.113.114.85/4f5d85e2-99cd-4bd7-8f38-6a438ea18d79"))

TestUserPK = "6eed74c128feceeb5dfc23ae63728679f2008a1eb41825744f10b49999295b43"

uniswap_ABI = json.loads(open("../artifacts/contracts/IUniswapV2Router02.sol/IUniswapV2Router02.json").read())["abi"]

uniswap = w3.eth.contract(address="0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D", abi=uniswap_ABI)

uni

