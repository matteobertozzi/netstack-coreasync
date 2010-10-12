#!/usr/bin/env python
#-*- coding: utf-8 -*-
# ==============================================================================
# Copyright (c) 2010, Matteo Bertozzi
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the author nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL MATTEO BERTOZZI BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ==============================================================================

from time import time

from .queue import DispatchQueue
from .sched import global_sched

def dispatch_get_main_queue():
    return global_sched.main_queue

def dispatch_queue_create(label, attributes=None):
    queue = DispatchQueue(label, attributes)
    global_sched.add_queue(queue)
    return queue

def dispatch_queue_destroy(queue):
    global_sched.remove_queue(queue)

def dispatch_queue_clear(queue):
    global_sched.clear_queue(queue)

def dispatch_async(queue, block):
    global_sched.add_block(queue, block)

def dispatch_apply(iterations, queue, block):
    for i in xrange(iterations):
        dispatch_async(queue, block(i))

def dispatch_repeat(iterations, queue, block):
    for _ in xrange(iterations):
        dispatch_async(queue, block)

def dispatch_concurrent(block):
    dispatch_async(None, block)

def dispatch_concurrent_apply(iterations, block):
    dispatch_apply(iterations, None, block)

def dispatch_concurrent_repeat(iterations, block):
    dispatch_repeat(iterations, block)

def dispatch_timed(block, msec, ntimes=None):
    def yfunc(msec):
        t = time()
        while True:
            if (time() - t) > msec:
                yield block()
                t = time()
            yield

    def yfuncN(msec, ntimes):
        t = time()
        while ntimes > 0:
            if (time() - t) > msec:
                yield block()
                ntimes -= 1
                t = time()
            yield

    if ntimes:
        dispatch_async(None, lambda ms=msec, n=ntimes: yfuncN(ms, n))
    else:
        dispatch_async(None, lambda ms=msec: yfunc(ms))

# CoreAsync Decorators to dispatch work
def asyncmethod(func):
    def yfunc(*args, **kwargs):
        func(*args, **kwargs)
        yield
    return yfunc

def concurrent(func):
    def yfunc(*args, **kwargs):
        dispatch_concurrent(func(*args, **kwargs))
    return yfunc

