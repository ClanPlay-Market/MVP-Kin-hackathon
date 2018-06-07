import logging
import logging.handlers
import os.path

import config

skip_modules = [
    'decoder',
    'multi_queue',
    'connectionpool',  # boto3
    'rmq'
]
skip_names = [
    'pika.adapters.blocking_connection',
    'pika.adapters.select_connection',
    'pika.callback',
    'pika.adapters.base_connection',
    'pika.connection',
    'pika.channel'
]


def init(log_file_prefix,
         log_file_enable=False, debug_file_enable=False,
         debug_level=config.LOG_LEVEL_DEFAULT, log_format=config.LOG_FORMAT):
    logging.getLogger().setLevel(logging.DEBUG)

    default_logger = logging.StreamHandler()
    default_logger.setFormatter(logging.Formatter(log_format))
    default_logger.setLevel(debug_level)
    default_logger.addFilter(debug_filter)
    logging.getLogger().addHandler(default_logger)

    if log_file_enable:
        rotating_handler = logging.handlers.TimedRotatingFileHandler(
            os.path.join(config.SERVER_LOG_PATH, '%s.log' % log_file_prefix), 'D'
        )
        rotating_handler.setFormatter(logging.Formatter(log_format))
        rotating_handler.setLevel(debug_level)
        rotating_handler.addFilter(debug_filter)
        logging.getLogger().addHandler(rotating_handler)

    if debug_file_enable:
        rotating_handler_debug = logging.handlers.TimedRotatingFileHandler(
            os.path.join(config.SERVER_LOG_PATH, '%s_debug.log' % log_file_prefix), 'D'
        )
        rotating_handler_debug.setFormatter(logging.Formatter(log_format))
        rotating_handler_debug.setLevel(logging.DEBUG)
        rotating_handler_debug.addFilter(debug_filter)
        logging.getLogger().addHandler(rotating_handler_debug)


def debug_filter(record):
    if record.levelno > logging.INFO:
        return 1
    if record.name in skip_names:
        return 0
    if record.module in skip_modules:
        return 0
    return 1
