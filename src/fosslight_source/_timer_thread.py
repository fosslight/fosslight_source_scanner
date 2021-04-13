#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import threading
import time
from progress.spinner import Spinner

class TimerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self, name=' Thread')

    def run(self):
        spinner = Spinner('')
        while True:
            time.sleep(1)
            spinner.next()