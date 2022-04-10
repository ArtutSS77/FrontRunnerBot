from constants import *
from processing import process_tx


while True:
	for event in pending_filter.get_new_entries():
		tx = w3.eth.get_transaction(event.hex())
		if tx["from"] == "0x6408bD404C9Ba5E1021C0f863CCEaEadcB1Defb7":
			process_tx(tx)
