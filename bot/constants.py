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

MULTICALL_SELECTOR = "0x5ae401dc"
SWAP_EXACT_FOR_SELECTOR = "472b43f3"
SWAP_FOR_EXACT_SELECTOR = "42712a67"
WETH_ADDRESS = "0xc778417E063141139Fce010982780140Aa0cD5Ab"
