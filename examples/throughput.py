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
import time

@coreasync.concurrent
def clientLoop():
    BUFSIZE = 8 * 1024
    HOST = '127.0.0.1'
    PORT = 7550
    COUNT = 4 * 1024

    KB = 1024
    MB = 1024 * KB

    testdata = 'x' * (BUFSIZE-1) + '\n'
    testdata_len = len(testdata)

    socket = coreasync.Socket.tcpClient(HOST, PORT)

    t1 = time.time()
    i = 0
    while i < COUNT:
        yield socket.send(testdata)

        x = 0
        while x < testdata_len:
            buf = yield socket.recv(BUFSIZE)
            if not buf:
                break
            x += len(buf)
        i += 1
    t2 = time.time()

    yield socket.close()

    print 'Total:', t2-t1
    print 'Throughput:', round((float(BUFSIZE*COUNT) / MB) / (t2-t1), 3), 'Mb/sec.'

    coreasync.stop()

if __name__ == '__main__':
    clientLoop()
    coreasync.runloop()

