import kin
from stellar_base.network import NETWORKS

from config import NETWORK, HORIZON_URL, KIN_ASSET, TEST_USER_SK, PUBLIC_KEY

NETWORKS['CUSTOM'] = 'private testnet'

sdk = kin.SDK(network=NETWORK,
              horizon_endpoint_uri=HORIZON_URL,
              secret_key=TEST_USER_SK,
              kin_asset=KIN_ASSET)

# Get the address of my wallet account. The address is derived from the secret key the SDK was inited with.
my_addr = sdk.get_address()
print('Address: %s' % my_addr)

native_balance = sdk.get_native_balance()

# Get KIN balance of the SDK wallet
kin_balance = sdk.get_kin_balance()

print('Native balance: %r, KIN balance: %r' % (native_balance, kin_balance))

data = sdk.get_account_data(my_addr)

tx_hash = sdk.send_kin(PUBLIC_KEY, 1, memo_text='for_tournament')

print('tx_hash=%r' % tx_hash)


def process_payment(address, tx_data):
    print("address: %r, tx_data: %r" % (address, tx_data))


sdk.monitor_kin_payments(callback_fn=process_payment)
