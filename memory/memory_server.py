import argparse
import collections
import socket


OP_READ = b'\x01'
OP_WRITE = b'\x02'

MSGTYPE_GET_RESPONSE = b'\x0A'

ReadPage = collections.namedtuple('ReadPage', ['pageno'])
WritePage = collections.namedtuple('WritePage', ['pageno', 'index', 'val'])


def parse_message(bs):
    if bs[0] == OP_READ:
        return ReadPage(pageno=int.from_bytes(bs[1], 'little', signed=False))
    if bs[0] == OP_WRITE:
        return WritePage(
            pageno=int.from_bytes(bs[1], 'little', signed=False),
            index=int.from_bytes(bs[2], 'little', signed=False),
            val=int.from_bytes(bs[3], 'little', signed=False)
        )
    raise ValueError


def page_response(pageno, bs):
    return MSGTYPE_GET_RESPONSE + bytes([pageno]) + bs


def memory_server(sock, start_page, stop_page):
    pages = {i: bytearray(256) for i in range(start_page, stop_page+1)}
    while True:
        bs, addr = sock.recvfrom(512)
        msg = parse_message(bs)
        match msg:
            case ReadPage(pageno=pageno) if start_page <= pageno <= stop_page:
                sock.sendto(addr, page_response(pageno, pages[pageno]))
            case Write(pageno=pageno, index=index, val=val) if start_page <= pageno <= stop_page:
                pages[pageno][index] = val
            case _:
                pass




if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', default='127.0.0.1')
    parser.add_argument('--port', type=int default=6503)
    parser.add_argument('--start_page', type=int, default=1)
    parser.add_argument('--stop_page', type=int, default=255)

    args = parser.parse_args()

    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    sock.bind((args.ip, args.port))

    memory_server(sock, args.start_page, args.stop_page)
