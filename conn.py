#!/usr/bin/env python3
"""
    Load testing for HTTP and HTTPS.
    Author: João Bernardo Oliveira <jboliveira@netfilter.com.br>
    Netfilter
"""

import argparse
import itertools
import multiprocessing
import random
import ssl
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib import request


VERSION = '1.6.1'
VERBOSE = True


def display(*args, **kw):
    if VERBOSE:
        print(*args, **kw)


class ConnectError(Exception):
    pass


class ConnectionTest(object):
    threads = 1
    timeout = 100
    sleep = 0
    shuffle = False
    base_offset = 0
    dry_run = False

    def __init__(self, url=None, urlfile=None, skip=0):
        if not urlfile:
            self._urls = [url]
        else:
            with open(url) as f:
                self._urls = f.read().splitlines()
        self.set_cycle(skip)

    def url(self, skip=None):
        return next(self._urls_cycle)

    def set_cycle(self, offset):
        position = offset
        position = position % len(self._urls)
        self._urls = self._urls[position:] + self._urls[:position]
        self._urls_cycle = itertools.cycle(self._urls)

    def connect(self, pos_offset):
        if self.shuffle:
            random.shuffle(self._urls)

        self.set_cycle(pos_offset * self.base_offset)

        def target():
            url = self.url()
            try:
                time.sleep(self.sleep)

                if self.dry_run:
                    display(url)
                    return 0

                ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
                with request.urlopen(url, context=ssl_context, timeout=self.timeout) as conn:
                    return len(conn.read())
            except Exception as e:
                raise ConnectError(url, e)

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = [executor.submit(target) for _ in range(self.threads)]
            total = 0
            errors = []
            
            for fut in as_completed(futures):
                try:
                    total += fut.result()
                except ConnectError as ce:
                    display(*ce.args)
                    errors.append(ce)
                except Exception as e:
                    display(e)
                    errors.append(e)
                finally:
                     pass
            return total, errors


def main():
    parser = argparse.ArgumentParser(prog='Conn', description='HTTP and HTTPS load test')
    parser.add_argument('-i', dest='url', default=None, required=True, help='Input URL (or file) to test. See -f option.')
    parser.add_argument('-f', dest='urlfile', default=False, action='store_true', help='Treat input as a file containing one URL per line.')
    parser.add_argument('-p', dest='procs', default=1, type=int, help='Number of simultaneous processes to start.')
    parser.add_argument('-t', dest='threads', default=ConnectionTest.threads, type=int, help='Number of threads per process. Each thread open an URL.')
    parser.add_argument('-r', dest='repeat', default=None, type=int, help='Total number of processes to open.')
    parser.add_argument('-q', dest='quiet', default=False, action="store_true", help="Do not print errors and URLs.")
    parser.add_argument('--version', action='version', version='%(prog)s ' + VERSION)
    parser.add_argument('--timeout', default=ConnectionTest.timeout, type=int, help='Timeout for HTTP(S) connection.')
    parser.add_argument('--sleep', default=ConnectionTest.sleep, type=float, help='Time to sleep prior to each request.')
    parser.add_argument('--shuffle', default=ConnectionTest.shuffle, action='store_true', help='Shuffle the list of URLs at the start of each process.')
    parser.add_argument('--offset', default=ConnectionTest.base_offset, type=int, help='Offset the input list by OFFSET*k elements on each repetition.')
    parser.add_argument('--skip', default=0, type=int, help='Skip the first N elements on the list. Note the list is a clycle.')
    parser.add_argument('--dry_run', default=False, action='store_true', help='Print URLs instead of opening them.')
    args = parser.parse_args()

    global VERBOSE
    VERBOSE = not args.quiet

    ctest = ConnectionTest(args.url, args.urlfile, args.skip)
    ctest.threads = args.threads
    ctest.timeout = args.timeout
    ctest.shuffle = args.shuffle
    ctest.sleep = args.sleep
    ctest.base_offset = args.offset
    ctest.dry_run = args.dry_run

    repeat = args.repeat if args.repeat is not None else args.procs

    t = time.time()
    with multiprocessing.Pool(args.procs) as pool:
        data = pool.map(ctest.connect, range(repeat))
    t = time.time() - t

    size, errors = zip(*data)
    size = sum(size)
    errors = sum(errors, [])

    output = '''
        Time: {:.3f}s
        Bytes: {:.2f} MB
        Rate: {:.2f} mbps

        Requests: {}
        Max Simultaneous Requests: {}
        Connection Errors: {}
    '''.format(t, size/1024**2, size/1024**2*8/t, repeat * args.threads,
               min(repeat, args.procs) * args.threads, len(errors))
    
    print('\n'.join(x.strip() for x in output.strip().splitlines()))


if __name__ == '__main__':
    main()
