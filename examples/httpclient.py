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

import sys

from coreasync import Socket
import coreasync

@coreasync.concurrent
def _httpClient():
    HOST = '127.0.0.1'
    PORT = 8080

    try:
        sock = Socket.tcpClient(HOST, PORT)
    except Exception as e:
        print 'Connection Failure', e
        yield
        return

    try:
        yield sock.send('GET / 1.1\r\n')
        yield sock.send('Host: %s\r\n' % HOST)
        yield sock.send('\r\n\r\n')

        while 1:
            buf = yield sock.recv()
            if not buf:
                break

            sys.stdout.write(buf)
    except Exception as e:
        print 'Client Failure', e

    sys.stdout.write('\n')
    yield sock.close()

    coreasync.stop()

if __name__ == '__main__':
    _httpClient()
    coreasync.runloop()

