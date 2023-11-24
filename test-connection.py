import argparse

from ib_insync import IB

parser = argparse.ArgumentParser(description="Just an example",
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--host", default="127.0.0.1")
parser.add_argument("-p", "--port", default=4002)
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
print(results)
ibkr.disconnect()