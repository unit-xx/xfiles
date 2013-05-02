# paired arbitrage between IF futures

import sys
import config
import logging
import threading

import UserApiStruct as ustruct
import UserApiType as utype
from MdApi import MdApi, MdSpi
from TraderApi import TraderApi, TraderSpi  

# start quote server

# start orderman: a naive one

# start accountman: only maintains positions and position limits

# start engine, with trading handler installed

# start pair trading strategy signal

