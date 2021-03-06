# -*- coding: utf-8 -*-
import datetime, time, logging
import os
from pybpodapi.protocol import Bpod

PYBPOD_API_LOG_LEVEL = logging.CRITICAL


os.makedirs("./sessions",exist_ok=True)

PYBPOD_SESSION_PATH = './sessions'

PYBPOD_SESSION 		= "TPM_Session_"+time.strftime("%Y_%m_%d_%H_%M_%S")
PYBPOD_SERIAL_PORT 	= 'COM5'

PYBPOD_API_ACCEPT_STDIN = False
PYBPOD_API_STREAM2STDOUT = False

BPOD_BNC_PORTS_ENABLED 		= [False, False]
BPOD_WIRED_PORTS_ENABLED 	= [False, False]
BPOD_BEHAVIOR_PORTS_ENABLED = [False, False, False, False, False, False, False, False]
