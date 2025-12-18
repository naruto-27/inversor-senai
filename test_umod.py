import socket
from umodbus.client import tcp

SERVER = ('127.0.0.1', 502)
SLAVE = 2

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    try:
        s.connect(SERVER)
        print('connected')
        msg = tcp.read_coils(SLAVE, 1100, 1)
        print('sending', msg)
        res = tcp.send_message(msg, s)
        print('response:', res)
    except Exception as e:
        import traceback
        print('error:', repr(e))
        traceback.print_exc()
    finally:
        s.close()

if __name__ == '__main__':
    main()
