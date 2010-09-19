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

import coreasync

def foo():
    for i in xrange(10):
        print 'Foo Function', i
        yield

@coreasync.asyncmethod
def work(n, value):
    print 'work(%d): %s' % (n, value)

@coreasync.asyncmethod
def repeat_func():
    print 'Repeat'

def concurrent_func(text):
    for i in range(5):
        print text
        yield

if __name__ == '__main__':
    if 1:
        main_queue = coreasync.dispatch_get_main_queue()
        queue2 = coreasync.dispatch_queue_create('queue2')
        queue3 = coreasync.dispatch_queue_create('queue3')

        coreasync.dispatch_async(main_queue, foo())

        data = ['Test 1', 'Test 2', 'Test 3']
        coreasync.dispatch_apply(len(data), queue2, lambda n: work(n, data[n]))

        coreasync.dispatch_repeat(10, queue3, repeat_func)
    else:
        coreasync.dispatch_concurrent(lambda: concurrent_func("Concurrent 1"))
        coreasync.dispatch_concurrent(lambda: concurrent_func("Concurrent 2"))
        coreasync.dispatch_concurrent(lambda: concurrent_func("Concurrent 3"))
        coreasync.dispatch_concurrent(lambda: concurrent_func("Concurrent 4"))
        coreasync.dispatch_concurrent(lambda: concurrent_func("Concurrent 5"))


    coreasync.runloop()
