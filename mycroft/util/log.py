# Copyright 2017 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


"""
Mycroft Logging module.

This module provides the LOG pseudo function quickly creating a logger instance
for use.

The default log level of the logger created here can ONLY be set in
/etc/mycroft/mycroft.conf or ~/.config/mycroft/mycroft.conf

The default log level can also be programatically be changed by setting the
LOG.level parameter.
"""

import inspect
import logging
import sys

import mycroft


def getLogger(name="MYCROFT"):
    """Depreciated. Use LOG instead"""
    return logging.getLogger(name)


def _make_log_method(fn):
    @classmethod
    def method(cls, *args, **kwargs):
        cls._log(fn, *args, **kwargs)

    method.__func__.__doc__ = fn.__doc__
    return method


class LOG:
    """
    Custom logger class that acts like logging.Logger
    The logger name is automatically generated by the module of the caller

    Usage:
        >>> LOG.debug('My message: %s', debug_str)
        13:12:43.673 - :<module>:1 - DEBUG - My message: hi
        >>> LOG('custom_name').debug('Another message')
        13:13:10.462 - custom_name - DEBUG - Another message
    """

    _custom_name = None
    level = logging.getLevelName('INFO')
    log_message_format = (
        '{asctime} | {levelname:8} | {process:5} | {name} | {message}'
    )
    formatter = logging.Formatter(log_message_format, style='{')
    formatter.default_msec_format = '%s.%03d'
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Copy actual logging methods from logging.Logger
    # Usage: LOG.debug(message)
    debug = _make_log_method(logging.Logger.debug)
    info = _make_log_method(logging.Logger.info)
    warning = _make_log_method(logging.Logger.warning)
    error = _make_log_method(logging.Logger.error)
    exception = _make_log_method(logging.Logger.exception)

    @classmethod
    def init(cls):
        """ Initializes the class, sets the default log level and creates
        the required handlers.
        """
        config = mycroft.configuration.Configuration.get()
        cls.level = logging.getLevelName(config.get('log_level', 'INFO') or 'INFO')
        # Enable logging in external modules
        cls.create_logger('').setLevel(cls.level)

    @classmethod
    def create_logger(cls, name):
        logger = logging.getLogger(name)
        logger.propagate = False
        logger.addHandler(cls.handler)
        return logger

    def __init__(self, name):
        LOG._custom_name = name

    @classmethod
    def _log(cls, func, *args, **kwargs):
        if cls._custom_name is not None:
            name = cls._custom_name
            cls._custom_name = None
        else:
            # Stack:
            # [0] - _log()
            # [1] - debug(), info(), warning(), or error()
            # [2] - caller
            try:
                stack = inspect.stack()

                # Record:
                # [0] - frame object
                # [1] - filename
                # [2] - line number
                # [3] - function
                # ...
                record = stack[2]
                mod = inspect.getmodule(record[0])
                module_name = mod.__name__ if mod else ''
                name = module_name + ':' + record[3] + ':' + str(record[2])
            except Exception:
                # The location couldn't be determined
                name = 'HolmesV'

        func(cls.create_logger(name), *args, **kwargs)
