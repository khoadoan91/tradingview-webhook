import argparse

from ib_insync import IB, Contract, Future

# TWS uses 7496 (live) and 7497 (paper), while IB gateway uses 4001 (live) and 4002 (paper).
parser = argparse.ArgumentParser(description="Just an example",
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--host", default="127.0.0.1")
parser.add_argument("-p", "--port", default=8888)
args = parser.parse_args()
config = vars(args)

host = config["host"]
port = config["port"]
ibkr = IB()
ibkr.connect(
    host=host,
    port=port,
    clientId = 2,
    timeout = 15,
    readonly = True)

results = ibkr.client.connectionStats()
# print(f"connectionStats: {results}")
# print(f"Positions: {ibkr.positions()}")

es_future=Future(symbol="ES", currency="USD")
contract_details = ibkr.reqContractDetails(es_future)
print("contractDetails", contract_details)
qualify_contracts = ibkr.qualifyContracts(contract_details[0].contract)
print("qualify_contracts", qualify_contracts)
marketDetails=ibkr.reqMktData(contract_details[0].contract)
print("marketDetails", marketDetails)

ibkr.disconnect()