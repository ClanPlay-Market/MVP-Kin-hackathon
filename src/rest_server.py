#!/usr/bin/env python3
import json
import logging
import signal
import sys
import threading
import traceback
from functools import wraps
from json import JSONDecodeError

from flask import Flask, jsonify, request
from mongoengine import connect

import config
import misc.myjson
import transactions
from misc import logs
from misc.exceptions import UserError
from schema import Tourney, TourneyStatus

SESSION_STORAGE = {}

logs.init('rest_server')
app = Flask(__name__)
app.json_encoder = misc.myjson.CustomEncoder


class ArgumentError(Exception):
    pass


def _get_values_source():
    # if request.method == 'POST':
    #     src = request.form
    # else:
    #     src = request.args
    #
    # return src
    return request.values


def get_json(name: str, required=False) -> object:
    s = get_str(name, required=required)
    if not s:
        return None
    try:
        return json.loads(s)
    except JSONDecodeError:
        raise ArgumentError('JSON is corrupted in the parameter %s' % name)


def get_str(name: str, required=False, default=None) -> str:
    s = _get_values_source().get(name)
    if s is None:
        if required:
            raise ArgumentError('The parameter %s must be defined' % name)
        return default
    return s


def get_int(name: str, required=False, default=0) -> int:
    s = get_str(name, required=required)
    if s is None:
        return default
    try:
        return int(s)
    except ValueError:
        raise ArgumentError('The value of parameter %s is not integer (%s)' % (name, s))


def get_bool(name, required=False, default=False):
    s = get_str(name, required=required)
    if s is None:
        return default
    value = s.lower()
    if value == '' or value == 'false' or value == 'f' or value == '0':
        return False
    else:
        return True


def jsonify_with_code(data):
    if 'error' in data:
        if 'errorCode' in data:
            status = 400
        else:
            status = 500
        if 'httpStatus' in data:
            status = int(data.pop('httpStatus'))
    else:
        status = 200

    return jsonify(data), status


def process_exceptions(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ArgumentError as e:
            info = {'status': 'failed', 'error': '%s' % e.args}
            return jsonify_with_code(info)
        except Exception as e:
            traceback.print_exception(e, e, e.__traceback__)
            if isinstance(e, UserError):
                info = {'status': 'failed', 'errorCode': e.__class__.__name__,
                        'error': e.args[0]}
            else:
                info = {'status': 'failed', 'error': 'Exception %s occurred: %s' % (type(e).__name__, e.args)}
            return jsonify_with_code(info)

    return wrap


@app.route('/api/healthz', methods=['GET'])
@process_exceptions
def healthz():
    logging.debug('receive %s', request.full_path)
    return jsonify_with_code({'status': 'ok'})


@app.route('/api/v1/tourneys', methods=['GET'])
@process_exceptions
def get_tourneys():
    logging.debug('receive %s', request.full_path)
    joinable = []
    previous = []
    for t in Tourney.objects():
        if t.status in (TourneyStatus.NOT_PAYED_YET.value, TourneyStatus.PAYED.value):
            joinable.append(t.as_dict())
        else:
            previous.append(t.as_dict())
    return jsonify_with_code(
        {
            "59e5c4d712082e08a857ff64": {
                "joinable": joinable,
                "previous": previous
            }
        }
    )


@app.route('/api/v1/tourneys', methods=['POST'])
@process_exceptions
def create_tourney():
    logging.debug('receive %s', request.full_path)
    Tourney.create(
        name=get_str('name', required=True),
        description=get_str('description', required=False),
        prize=get_str('prize', required=True),
        transaction_id=get_str('transaction_id', required=True),
        user_id=get_str('user_id', required=True),
    )
    return jsonify_with_code({'status': 'ok'})


@app.route('/api/v1/tourneys/<tid>', methods=['GET'])
@process_exceptions
def get_tourney(tid):
    logging.debug('receive %s', request.full_path)
    t = Tourney.objects.get(id=tid)
    return jsonify_with_code(t.as_dict())


@app.route('/api/v1/tourneys/<tid>/join', methods=['POST'])
@process_exceptions
def join_tourney(tid):
    logging.debug('receive %s', request.full_path)
    t = Tourney.objects.get(id=tid)  # type: Tourney
    t.join({
        'user_id': get_str('user_id', required=True),
        'alias_id': get_str('alias_id', required=True),
        'name': get_str('name', required=True),
        'tag': get_str('tag', required=True),
        'wallet_public_key': get_str('wallet_public_key', required=True),
    })
    return jsonify_with_code(t.as_dict())


# noinspection PyBroadException,PyUnusedLocal
def __interrupt(sig, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, __interrupt)

    connect(host=config.MONGODB_URI)

    thread = threading.Thread(target=transactions.main, name='Transactions')
    thread.daemon = True
    thread.start()

    # noinspection SpellCheckingInspection
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
