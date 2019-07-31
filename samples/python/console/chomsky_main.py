#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

import speech_sample
import intent_sample
import translation_sample

from collections import OrderedDict
import platform

eofkey = 'Ctrl-Z' if "Windows" == platform.system() else 'Ctrl-D'

intent_samples = [
        intent_sample.recognize_intent_once_from_mic,
        intent_sample.recognize_intent_once_async_from_mic,
        intent_sample.recognize_intent_continuous
]


def select():
    print('select sample module, {} to abort'.format(eofkey))
    modules = intent_samples
    for i, module in enumerate(modules):
        print(i, module.__name__)

    try:
        num = int(input())
        selected_module = modules[num]
    except EOFError:
        raise
    except Exception as e:
        print(e)
        return

    print('select sample function, {} to abort'.format(eofkey))
    for i, fun in enumerate(intent_samples):
        print(i, fun.__name__)

    try:
        num = int(input())
        selected_function = intent_samples[num]
    except EOFError:
        raise
    except Exception as e:
        print(e)
        return

    print('You selected: {}'.format(selected_function))
    try:
        selected_function()
    except Exception as e:
        print('Error running sample: {}'.format(e))

    print()


while True:
    try:
        select()
    except EOFError:
        break
