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

class SysCall(object):
    def handle(self):
        pass

class GetTaskId(SysCall):
    def handle(self):
        self.task.sendval = self.task.tid
        self.sched.schedule(self.task)

class NewTask(SysCall):
    def __init__(self, block):
        self._block = block

    def handle(self):
        tid = self.sched.add_block(self._block)
        self.task.sendval = tid
        self.sched.schedule(self.task)

class KillTask(SysCall):
    def __init__(self, tid):
        self._tid = tid

    def handle(self):
        task = self.sched.tasks.get(self._tid, None)
        if task:
            task.target.close()
            self.task.sendval = True
        else:
            self.task.sendval = False
        self.sched.schedule(self.task)

class WaitTask(SysCall):
    def __init__(self, tid):
        self._tid = tid

    def handle(self):
        result = self.sched.wait_for_exit(self._tid, self.task)
        self.task.sendval = result

        if not result:
            self.sched.schedule(self.task)

class WaitRead(SysCall):
    def __init__(self, fd):
        self._fd = fd

    def handle(self):
        fd = self._fd.fileno()
        self.sched.wait_for_read(fd, self.task)

class WaitWrite(SysCall):
    def __init__(self, fd):
        self._fd = fd

    def handle(self):
        fd = self._fd.fileno()
        self.sched.wait_for_write(fd, self.task)


