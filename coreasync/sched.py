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

from collections import deque
import select
import time

from .queue import DispatchQueue
from .syscall import SysCall
from .task import Task

def _ishuf(*args):
    """
    Shuffle Elements:
        _ishuf([1, 2, 3, 4], [5, 6, 7], [8, 9])
        output: (1, 5, 8), (2, 6, 9), (3, 7, None), (4, None, None)
    """
    iseq = [iter(s) for s in args]

    while 1:
        has_more_data = False

        data = []
        for s in iseq:
            try:
                data.append(next(s))
                has_more_data = True
            except StopIteration:
                data.append(None)

        if not has_more_data:
            break

        yield tuple(data)

class AsyncScheduler(object):
    def __init__(self):
        self.main_queue = DispatchQueue('_global_main_queue_')
        self._queues = {}

        self._running = False
        self._iotaskid = None

        self._ready = deque([])
        self._tasks = {}

        self._wait_exit = {}
        self._wait_read = {}
        self._wait_write = {}

    def schedule(self, task):
        self._ready.append(task)

    def add_queue(self, queue):
        self._queues[queue.label] = queue

    def clear_queue(self, queue):
        taskid = queue.clear()
        if taskid:
            self.add_block(None, KillTask(taskid))

    def remove_queue(self, queue):
        self.clear_queue(queue)
        del self._queues[queue.label]

    def add_block(self, queue, block):
        return self.add_task(queue, Task(block))

    def add_task(self, queue, task):
        if queue:
            queue.enqueue(task)
            if not queue.running:
                self._schedule_another_queue_task(queue)
        else:
            self._tasks[task.tid] = task
            self.schedule(task)
        return task.tid

    def remove_task(self, task):
        tid = task.tid

        # Remove task from Task List.
        del self._tasks[tid]

        # Remove task from queue and schedule another one
        queue = self._remove_task_from_queue(tid)
        if queue: self._schedule_another_queue_task(queue)

        # Notify other task in 'exit' waiting queue.
        for task in self._wait_exit.pop(tid, []):
            self.schedule(task)

    def _remove_task_from_queue(self, taskid):
        # Remove task from queue
        if self.main_queue.remove_task(taskid):
            return self.main_queue

        for queue in self._queues.itervalues():
            if queue.remove_task(taskid):
                return queue

        return None

    def _schedule_another_queue_task(self, queue):
        task = queue.deque()
        if task:
            self._tasks[task.tid] = task
            self.schedule(task)

    def stop(self):
        self._running = False

    def runloop(self):
        self._running = True

        # Add I/O Task just once.
        if not self._iotaskid:
            self._iotaskid = self.add_block(None, self._io_task)

        # Run Task Scheduling
        while self._running:
            task = self._ready.popleft()
            try:
                result = task.run()
                if isinstance(result, SysCall):
                    result.task = task
                    result.sched = self
                    result.handle()
                    continue
            except KeyboardInterrupt:
                self._running = False
            except StopIteration:
                self.remove_task(task)
                continue

            self.schedule(task)

    def wait_for_exit(self, waittid, task):
        if waittid in self._tasks:
            self._wait_exit.setdefault(waittid, []).append(task)
            return True
        return False

    # I/O
    def wait_for_read(self, fd, task):
        self._wait_read[fd] = task

    def wait_for_write(self, fd, task):
        self._wait_write[fd] = task

    def iopoll(self, timeout):
        if self._wait_read or self._wait_write:
            #_iopoll(rfd, wfd, timeout)
            rfd = self._wait_read.keys()
            wfd = self._wait_write.keys()
            r, w, _ = select.select(rfd, wfd, [], timeout)

            # Mix Read/Write I/O
            for rfd, wfd in _ishuf(r, w):
                if rfd: self.schedule(self._wait_read.pop(rfd))
                if wfd: self.schedule(self._wait_write.pop(wfd))
        else:
            time.sleep(timeout)

    def _io_task(self):
        while 1:
            if self._ready:
                self.iopoll(0.1)
            else:
                self.iopoll(1.1)
            yield

# Sched Global Instance
global_sched = AsyncScheduler()
runloop = global_sched.runloop
stop = global_sched.stop

