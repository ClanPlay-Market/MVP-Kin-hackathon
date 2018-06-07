# !/usr/bin/env python3
import logging
import threading
import time
from datetime import datetime

import kin
from mongoengine import connect
from stellar_base.network import NETWORKS

from config import NETWORK, HORIZON_URL, KIN_ASSET, SECRET_KEY, MONGODB_URI, PUBLIC_KEY, TOURNEY_PAY_TIMEOUT
from misc import logs
from schema import Tourney, TourneyStatus, TourneyMemberED

NETWORKS['CUSTOM'] = 'private testnet'

sdk = kin.SDK(network=NETWORK,
              horizon_endpoint_uri=HORIZON_URL,
              secret_key=SECRET_KEY,
              kin_asset=KIN_ASSET)


# TX_HASH = 'e3f4b6167243118d60284cd18c7d9e16be776a4cec0713516239d49c680928c7'
#
# tx_dat = sdk.get_transaction_data(TX_HASH)
#
# print(tx_dat)
#

def store_tourney_err(tourney, err_msg, status):
    logging.info(err_msg)
    tourney.status = status
    tourney.ended = datetime.utcnow()
    tourney.error_message = err_msg
    tourney.save()


def try_start_tourney(tourney: Tourney):
    try:
        tx_data = sdk.get_transaction_data(tourney.transaction_id)
    except kin.errors.ResourceNotFoundError:
        if (datetime.utcnow() - tourney.startAt).total_seconds() < TOURNEY_PAY_TIMEOUT:
            logging.info('Transaction %s isn\'t exist yet' % tourney.transaction_id)
        else:
            store_tourney_err(
                tourney=tourney,
                err_msg='Transaction %s isn\'t exist, stop tournament as not payed' % tourney.transaction_id,
                status=TourneyStatus.NOT_PAYED_ERROR.value
            )
        return
    total_amount = 0
    from_addresses = set()
    for op in tx_data.operations:
        if op.type != 'payment':
            continue
        if op.asset_code != KIN_ASSET.code or op.asset_issuer != KIN_ASSET.issuer:
            continue
        if op.to_address != PUBLIC_KEY:
            continue
        total_amount += op.amount
        from_addresses.add(op.from_address)
    if total_amount == 0:
        store_tourney_err(
            tourney=tourney,
            err_msg='Receive a transaction without money (%d ops)' % len(tx_data.operations),
            status=TourneyStatus.PAYMENT_ERROR.value
        )
        return
    logging.info(
        'Tournament %s (%s) started with prize %f (when created was %f)' % (
            tourney.id, tourney.name, total_amount, tourney.prize
        )
    )
    tourney.prize = float(total_amount)
    tourney.payed = datetime.utcnow()
    tourney.status = TourneyStatus.PAYED.value
    tourney.save()


def monitor_new_tourneys():
    while True:
        for tourney in Tourney.objects(status=TourneyStatus.NOT_PAYED_YET.value):
            try_start_tourney(tourney)
        time.sleep(10)


def end_tourney(tourney: Tourney):
    prize_sending_log = []
    total_sent = 0
    sorted_members = sorted(tourney.members, key=lambda m: m.currentTrophies, reverse=True)
    for i, percent in [(0, 40), (1, 25), (2, 15)]:
        if i >= len(sorted_members):
            err = 'Member #%d does not exist, don\'t send %d%% of prize %f KIN' % (i + 1, percent, tourney.prize)
            prize_sending_log.append(err)
            logging.error(err)
            continue
        member = sorted_members[i]  # type:TourneyMemberED
        try:
            prize_amount = tourney.prize * percent / 100
            sdk.send_kin(member.wallet_public_key, prize_amount, memo_text='Your prize for #%d place' % (i + 1))
            total_sent += prize_amount
            msg = 'Prize for #%d place %f KIN (%d %%) was sent to %s (wallet %s)' % (
                i + 1, prize_amount, percent, member.user_id, member.wallet_public_key
            )
            prize_sending_log.append(msg)
            logging.info(msg)
        except BaseException as e:
            err = 'Can\'t send prize to user_id=%s (wallet %s): %r' % (member.user_id, member.wallet_public_key, e)
            prize_sending_log.append(err)
            logging.error(err)
    tourney.prize_sent = total_sent
    tourney.prize_sending_log = '\n'.join(prize_sending_log)
    tourney.ended = datetime.utcnow()
    tourney.status = TourneyStatus.ENDED.value
    tourney.save()
    logging.info(
        'Tournament %s (%s) ended. Total tournament amount was %f, sent %f of prize' % (
            tourney.id, tourney.name, tourney.prize, total_sent
        )
    )


def control_run_tourneys():
    while True:
        next_start = None  # type:datetime
        for tourney in Tourney.objects(status=TourneyStatus.PAYED.value):  # type:Tourney
            if datetime.utcnow() >= tourney.endAt:
                end_tourney(tourney)
            else:
                if next_start is None or tourney.endAt < next_start:
                    next_start = tourney.endAt
        if next_start is None:
            time.sleep(10)
        else:
            time.sleep((next_start - datetime.utcnow()).total_seconds())


def main():
    available_commands = {
        'monitor_new_tourneys': monitor_new_tourneys,
        'control_run_tourneys': control_run_tourneys,
    }

    threads = []
    for name, proc in available_commands.items():
        thread = threading.Thread(target=proc, name=name)
        thread.daemon = True
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()


if __name__ == '__main__':
    logs.init('transactions')

    connect(host=MONGODB_URI)
    main()
