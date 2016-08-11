""" Unit tests for command_server.py.

    Could have done setUp and tearDown for each test, but kept the socket alive throughout.

    Need to test simlataneous connections to the server.  Need to use separate process, so
    need to add a subprocess that establishes a connection and runs tests.  Could generalize
    and be able to run the tests simultaneously on an arbitary number of connections.  Requires
    more thought...
"""

import os
import sys
import socket
import subprocess
import shlex
import unittest
import time

class TestCommandServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Must have '-u' option or pipe will buffer output.
        cmd = shlex.split('python -u ../command_server.py')
        cls.server = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        expect = "Server running\n"
        line = cls.server.stdout.readline()
        assert line == expect, "Startup message wrong - expected '%s' got '%s'." % (expect, line)

        cls.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cls.socket.settimeout(1)
        cls.socket.connect(("localhost", 5000))

        expect = "Received connection from ('127.0.0.1'"
        line = cls.server.stdout.readline()
        msg = "Connection message wrong - expected '%s' got '%s'." % (expect, line)
        assert line.startswith("Received connection from ('127.0.0.1'"), msg

        # Loopback data.  Make a buffer bigger than the server buffer.  XXX Server fails on writes >512 bytes.
        cls.data = bytearray(1024)
        for b in range(256):
            cls.data[b] = b
            cls.data[511 - b] = b
            cls.data[767 - b] = b
            cls.data[b + 768] = b

    @classmethod
    def tearDownClass(cls):
        cls.server.kill()
        code = cls.server.wait()
        msg = "Server terminated with unexpected code: %i" % code
        assert code == -9, msg

    def test_loopback(self):
        try:
            for test_data in [self.data[:512]]:     # XXX Longer than 512 bytes fails.
                self.socket.send("loopback")
                self.socket.send(test_data)
                looped_data = ''
                while len(looped_data) < len(test_data):
                    looped_data += self.socket.recv(len(test_data) - len(looped_data))
                self.assertEqual(looped_data, test_data, "Loopback data doesn't match - length %i." % len(test_data))
        except socket.timeout:
            self.assertTrue(False, "Timeout on socket - loopback.")

    def test_bogus(self):
        self.socket.send("bogus")
        expect = "Received unsupported command\n"
        response = self.server.stdout.readline()
        self.assertEqual(response, expect, "Did not receive expected unsupported command response.")

    def test_print(self):
        try:
            for test_str in ["Test print function", "foo", "\n"]:    # XXX If "" sent, nothing print'd by server.
                self.socket.send("print")
                self.socket.send(test_str)
                resp = self.server.stdout.read(len(test_str) + 1)
                resp = resp[:-1]    # Get rid of newline from server's print.
                self.assertEqual(test_str, resp, "Print data doesn't match.\nSent: '%s'\nReceived: '%s'" % (test_str, resp))
        except socket.timeout:
            self.assertTrue(False, "Timeout on socket - print.")

    def test_xclose(self):          # Named to run last.  Could order in a suite...
        try:
            self.socket.send("close")
            data = self.socket.recv(1)
            self.assertEqual(len(data), 0, "Socket not closed.")
        except socket.timeout:
            self.assertTrue(False, "Timeout on socket - close.")

if __name__ == '__main__':
    unittest.main()
