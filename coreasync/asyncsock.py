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

import socket

from .syscall import WaitRead, WaitWrite

class Socket(object):
    def __init__(self, sock):
        self.sock = sock

    def connect(self, host, port):
        self.sock.connect_ex((host, port))

    def accept(self):
        yield WaitRead(self.sock)

        client, addr = self.sock.accept()
        yield Socket(client), addr

    def send(self, buf):
        while buf:
            yield WaitWrite(self.sock)
            n = self.sock.send(buf)
            buf = buf[n:]

    def recv(self, nbytes=1024):
        yield WaitRead(self.sock)
        yield self.sock.recv(nbytes)

    def close(self):
        yield self.sock.shutdown(socket.SHUT_RDWR)
        yield self.sock.close()

    @staticmethod
    def tcpServer(host, port):
        rawsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        rawsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        rawsock.bind((host, port))
        rawsock.listen(128)
        return Socket(rawsock)

    @staticmethod
    def tcpClient(host, port):
        rawsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock = Socket(rawsock)
        sock.connect(host, port)
        return sock

