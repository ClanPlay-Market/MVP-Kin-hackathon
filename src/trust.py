from kin.stellar.builder import Builder
from stellar_base.network import NETWORKS

from config import TEST_USER_SK

NETWORKS['CUSTOM'] = 'private testnet'

builder = Builder(secret=TEST_USER_SK,
                  horizon_uri='https://horizon-kik.kininfrastructure.com', network='CUSTOM')
# noinspection SpellCheckingInspection
builder.append_trust_op("GBQ3DQOA7NF52FVV7ES3CR3ZMHUEY4LTHDAQKDTO6S546JCLFPEQGCPK", 'KIN')

builder.sign()
builder.submit()
