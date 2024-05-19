#!/usr/bin/env python3

import  logging
from   logging import FileHandler, StreamHandler
import sys

def setlogging():
    global logger
    FormatString='%(asctime)s %(levelname)s %(funcName)s %(lineno)s %(message)s'
#    logging.basicConfig(level = logging.DEBUG, format=FormatString)
    
    logger = logging.getLogger('logtest')
    logger.setLevel(logging.DEBUG)
    fileHandler = FileHandler(filename = 'logtest.log')
    fileHandler.setFormatter(logging.Formatter(fmt=FormatString))
    fileHandler.setLevel(logging.DEBUG)
    logger.addHandler(fileHandler)

    stdioHandler = StreamHandler(sys.stdout)
    stdioHandler.setFormatter(logging.Formatter(fmt=FormatString))
    stdioHandler.setLevel(logging.WARNING)
    logger.addHandler(stdioHandler)

setlogging()
logger.debug('DEBUG')
logger.info('INFO')
logger.warning('WARN')
logger.error('ERROR')
