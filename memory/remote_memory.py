import collections
import socket
import struct
import threading
import queue


OP_READ = b'\x01'
OP_WRITE = b'\x02'

MSGTYPE_GET_RESPONSE = b'\x0A'


Page = collections.namedtuple('Page', ['pageno', 'data'])


def parse_message(bs):
    # one byte message type (only one for now)
    # one byte page number
    # 256 bytes page
    _optype, pageno, bs = struct.unpack('cc256s', bs)
    return Page(int.from_bytes(pageno, 'little', signed=False), bytearray(bs))


def monitor_responses(sock, queue):
    while True:
        data, _addr = sock.recvfrom(512)
        msg = parse_message(data)
        queue.put(msg, block=True)


def send_get_page_request(sock, remote_addr, pageno):
    # one byte for either read or write
    # one byte for the page number
    message = OP_READ + bytes([pageno])
    sock.sendto(message, remote_addr)

def send_set_val_request(sock, remote_addr, page, index, val):
    message = OP_WRITE + bytes([page, index, val])
    sock.sendto(message, remote_addr)


class RemoteMemory:
    def __init__(self, config):
        self.config = config
        # store the zeropage locally
        self.zeropage = Page(0, bytearray(256))
        self.current_page = None

        self.sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.sock.bind((config['listen_host'], config['listen_port']))

        # we will spawn a thread for the listener that writes all incoming messages to a queue
        self.queue = queue.Queue(maxsize=64)
        threading.Thread(target=monitor_responses, args=(self.sock, self.queue), daemon=True).start()


    def get_page(self, pageno):
        # fire off the get_page_request then block until we recieve a message with the correct page
        send_get_page_request(self.sock, (self.config['remote_host'], self.config['remote_port']), pageno)

        # TODO: timeout to retry the request
        while True:
            page = self.queue.get(block=True)
            if page.pageno == pageno:
                return page
            else:
                # it was the wrong page, requeue it
                self.queue.put(page, block=True)


    def get_addr(self, addr):
        hi, lo = divmod(addr, 256)
        if hi == 0:
            return self.zeropage[lo]

        if self.current_page and hi == self.current_page.pageno:
            return self.current_page.data[lo]

        self.current_page = self.get_page(hi)
        return self.current_page.data[lo]


    # TODO: instead of writing every value back individually, maybe we should just do the write locally
    # and store the whole page when the current_page changes
    def set_addr(self, addr, val):
        hi, lo = divmod(addr, 256)
        if hi == 0:
            self.zeropage[lo] = val

        send_set_val_request(self.sock, (self.config['remote_host'], self.config['remote_port']), hi, lo, val)


    def __getitem__(self, key):
        if isinstance(key, int):
            if key >= 65536:
                raise KeyError
            return self.get_addr(key)

        if isinstance(key, slice):
            r = range(*key.indices(65536))
            return [self.get_addr(addr) for addr in r]

        raise TypeError

    def __setitem__(self, key, val):
        return self.set_addr(key, val)
