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

from types import FunctionType, MethodType, GeneratorType

from .syscall import SysCall

class Task(object):
    _TASK_ID = 0

    def __init__(self, block):
        Task._TASK_ID += 1
        self.tid = Task._TASK_ID

        if isinstance(block, FunctionType) or isinstance(block, MethodType):
            block = block()

        self.target = block
        self.sendval = None
        self.stack = []

    def run(self):
        while 1:
            try:
                result = self.target.send(self.sendval)
                ret, value = self._processResult(result)
                if ret: return value
            except StopIteration:
                if not self.stack:
                    raise
                self.sendval = None
                self.target = self.stack.pop()
            except Exception as e:
                if not self.stack:
                    raise e

                self.target = self.stack.pop()
                result = self.target.throw(type(e), e)
                ret, value = self._processResult(result)
                if ret: return value

    def _processResult(self, result):
        if isinstance(result, SysCall):
            return True, result

        if isinstance(result, GeneratorType):
            self.stack.append(self.target)
            self.sendval = None
            self.target = result
        elif not self.stack:
            return True, None
        else:
            self.sendval = result
            self.target = self.stack.pop()

        return False, None

