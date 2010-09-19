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

import time

from .syscall import GetTaskId
from .dispatch import concurrent
from .asyncsock import *

# Table mapping response codes to messages; entries have the
# form {code: (shortmessage, longmessage)}.
# See RFC 2616.
httpResponses = {
    100: ('Continue', 'Request received, please continue'),
    101: ('Switching Protocols',
          'Switching to new protocol; obey Upgrade header'),

    200: ('OK', 'Request fulfilled, document follows'),
    201: ('Created', 'Document created, URL follows'),
    202: ('Accepted',
          'Request accepted, processing continues off-line'),
    203: ('Non-Authoritative Information', 'Request fulfilled from cache'),
    204: ('No Content', 'Request fulfilled, nothing follows'),
    205: ('Reset Content', 'Clear input form for further input.'),
    206: ('Partial Content', 'Partial content follows.'),

    300: ('Multiple Choices',
          'Object has several resources -- see URI list'),
    301: ('Moved Permanently', 'Object moved permanently -- see URI list'),
    302: ('Found', 'Object moved temporarily -- see URI list'),
    303: ('See Other', 'Object moved -- see Method and URL list'),
    304: ('Not Modified',
          'Document has not changed since given time'),
    305: ('Use Proxy',
          'You must use proxy specified in Location to access this '
          'resource.'),
    307: ('Temporary Redirect',
          'Object moved temporarily -- see URI list'),

    400: ('Bad Request',
          'Bad request syntax or unsupported method'),
    401: ('Unauthorized',
          'No permission -- see authorization schemes'),
    402: ('Payment Required',
          'No payment -- see charging schemes'),
    403: ('Forbidden',
          'Request forbidden -- authorization will not help'),
    404: ('Not Found', 'Nothing matches the given URI'),
    405: ('Method Not Allowed',
          'Specified method is invalid for this resource.'),
    406: ('Not Acceptable', 'URI not available in preferred format.'),
    407: ('Proxy Authentication Required', 'You must authenticate with '
          'this proxy before proceeding.'),
    408: ('Request Timeout', 'Request timed out; try again later.'),
    409: ('Conflict', 'Request conflict.'),
    410: ('Gone',
          'URI no longer exists and has been permanently removed.'),
    411: ('Length Required', 'Client must specify Content-Length.'),
    412: ('Precondition Failed', 'Precondition in headers is false.'),
    413: ('Request Entity Too Large', 'Entity is too large.'),
    414: ('Request-URI Too Long', 'URI is too long.'),
    415: ('Unsupported Media Type', 'Entity body in unsupported format.'),
    416: ('Requested Range Not Satisfiable',
          'Cannot satisfy request range.'),
    417: ('Expectation Failed',
          'Expect condition could not be satisfied.'),

    500: ('Internal Server Error', 'Server got itself in trouble'),
    501: ('Not Implemented',
          'Server does not support this operation'),
    502: ('Bad Gateway', 'Invalid responses from another server/proxy.'),
    503: ('Service Unavailable',
          'The server cannot process the request due to a high load'),
    504: ('Gateway Timeout',
          'The gateway server did not receive a timely response'),
    505: ('HTTP Version Not Supported', 'Cannot fulfill request.'),
}

def _parseHttpHeader(data):
    req_finished = False
    headers = {}
    reqbuf = []

    old_index = 0
    index = data.find('\r\n')
    while index >= 0:
        name_index = data.find(':', old_index, index)
        head_name = data[old_index:name_index].lower()
        head_value = data[name_index+1:index].strip()

        headers[head_name] = head_value

        old_index = index + 2
        index = data.find('\r\n', old_index)

        if old_index == index:
            old_index += 2
            req_finished = True
            break

    reqbuf.append(data[old_index:])
    return req_finished, reqbuf, headers

def _readHttpRequest(socket):
    request = None
    headers = {}
    reqbuf = []

    # Parse Request Line (GET / HTTP/1.1)
    while 1:
        data = yield socket.recv()
        if not data:
            break

        index = data.find('\r\n')
        if index < 0:
            reqbuf.append(data)
            continue

        reqbuf.append(data[:index])
        request = ''.join(reqbuf).split()

        reqbuf = [data[index+2:]]
        break

    # Parse Http Headers
    req_finished, reqbuf, headers = _parseHttpHeader(''.join(reqbuf))
    while not req_finished:
        data = yield socket.recv()
        if not data:
            break

        reqbuf.append(data)
        req_finished, reqbuf, headers_part = _parseHttpHeader(''.join(reqbuf))
        headers.update(headers_part)

    # Read Body
    body = None
    content_length = int(headers.get('content-length', '0'))
    if content_length > 0:
        data = ''.join(reqbuf)
        data = data[:content_length]
        body = [data]
        content_length -= len(data)

        while content_length > 0:
            data = yield socket.recv()
            if not data:
                break

            data = data[:content_length]
            content_length -= len(data)
            body.append(data)

        body = ''.join(body)

    yield request, headers, body

@concurrent
def _httpHandleClient(socket, addr, handle_response, handle_error):
    print addr, 'New connection'
    st = time.time()

    try:
        request, headers, body = yield _readHttpRequest(socket)
        yield handle_response(socket, addr, request, headers, body)
    except Exception as e:
        yield handle_error(socket, addr, e)
    finally:
        yield socket.close()

    et = time.time()
    print addr, 'Closed Connection', (et - st)

@concurrent
def httpServerLoop(host, port, handle_response, handle_error):
    socket = Socket.tcpServer(host, port)

    while 1:
        try:
            client, addr = yield socket.accept()
            yield _httpHandleClient(client, addr, handle_response, handle_error)
        except Exception as e:
            print 'accept()', type(e), e

    yield socket.close()

