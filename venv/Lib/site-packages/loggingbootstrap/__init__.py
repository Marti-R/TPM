# !/usr/bin/python3
# -*- coding: utf-8 -*-

""" loggingbootstrap

"""

__version__ = "1.0.0"
__author__ = "Carlos Mão de Ferro"
__credits__ = ["Carlos Mão de Ferro", "Ricardo Ribeiro"]
__license__ = "Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>"
__maintainer__ = ["Carlos Mão de Ferro", "Ricardo Ribeiro"]
__email__ = ["cajomferro@gmail.com", "ricardojvr@gmail.com"]
__status__ = "Development"

import logging


def create_console_logger(log_name, console_handler_level):
    """
    Create logger with console handler
    :param log_name: Name of the logger to be used when logger is invoked
    :param console_handler_level: logger level for console handler
    """
    loggers_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(process)d | %(name)s | %(funcName)s | %(message)s',
        datefmt='%d/%m/%Y %I:%M:%S')

    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(console_handler_level)
    ch.setFormatter(loggers_formatter)
    logger.addHandler(ch)


def create_file_logger(log_name, log_filename, file_handler_level):
    """
    Create simple logger with console and file handlers
    :param log_name: Name of the logger to be used when logger is invoked
    :param log_filename: name of the filename where file handler will output
    :param file_handler_level: logger level for file handler
    """
    loggers_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(funcName)s | %(message)s',
        datefmt='%d/%m/%Y %I:%M:%S')

    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(log_filename)
    fh.setLevel(file_handler_level)
    fh.setFormatter(loggers_formatter)
    logger.addHandler(fh)


def create_double_logger(log_name, console_handler_level, log_filename, file_handler_level):
    """
    Create simple logger with console and file handlers
    :param log_name: Name of the logger to be used when logger is invoked
    :param log_filename: name of the filename where file handler will output
    :param file_handler_level: logger level for file handler
    :param console_handler_level: logger level for console handler
    """

    create_console_logger(log_name, console_handler_level)
    create_file_logger(log_name, log_filename, file_handler_level)
