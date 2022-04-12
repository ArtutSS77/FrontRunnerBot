from sandwich import Sandwich

w3_rpc = "http://62.113.114.85/4f5d85e2-99cd-4bd7-8f38-6a438ea18d79"
attacker_pk = "e23362bbe82c915e22c83d520d95eb57c92b3a78f0ad373dedada5cdcf88273f"
multi_call_address = "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45"
v2_router_address = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
v2_factory_address = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"

sandwich_bot = Sandwich(w3_rpc, multi_call_address, v2_router_address, v2_factory_address, attacker_pk)
sandwich_bot.start()
