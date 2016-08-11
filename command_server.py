import socket
import time

supported_commands = {'loopback', 'print', 'close'}

class CommandServer:

    def __init__(self, ip='localhost', port=5000):
        
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((ip, port))

        print "Server running"
        self.is_running = True

    def start_listening(self, num_connections=2):
        self.server.listen(num_connections)
        self._accept()

    def is_running(self):
        return self.is_running
        
    def _accept(self):
        self.client, self.remote_addr = self.server.accept()
        
        print "Received connection from %s" % (self.remote_addr,)
        self.is_connected = True

    def _get_data(self, bufsize=32):
        try:
            return self.client.recv(bufsize)
        except KeyboardInterrupt:
            self.close()

    def wait_for_commands(self):
        while self.is_connected:
            cmd = self._get_data()
            if cmd:
                if cmd not in supported_commands:
                    print "Received unsupported command"
                    continue

                if cmd in ("loopback", "print"):
                    payload = self._get_data(512)

                if cmd == "loopback":
                    self.client.sendall(payload)

                elif cmd == "print":
                    print payload

                elif cmd == "close":
                    self.close()

    def close(self):
        self.client.close()
        self.server.close()
        self.is_connected = False
        print "Connection closed"

if __name__ == '__main__':
    
    cmd_server = CommandServer(port=5000)    
    cmd_server.start_listening()
    cmd_server.wait_for_commands()
