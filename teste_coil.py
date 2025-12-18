from pymodbus.client.sync import ModbusTcpClient

HOST = "127.0.0.1"
PORT = 502
UNIT = 2

client = ModbusTcpClient(host=HOST, port=PORT, timeout=3)
ok = client.connect()
print("connect:", ok)
if not ok:
    client.close()
    raise SystemExit("Não foi possível conectar ao servidor Modbus")

try:
    # pyModSlave foi configurado com Start Addr = 1100 e No of Coils = 2
    rr = client.read_coils(1100, 1, unit=UNIT)
    print("read_coils(1100) raw:", rr)
    if hasattr(rr, 'isError') and rr.isError():
        print("Erro Modbus:", rr)
    else:
        print("Bits:", getattr(rr, 'bits', None))

    rr2 = client.read_coils(1101, 1, unit=UNIT)
    print("read_coils(1101) raw:", rr2)
    if hasattr(rr2, 'isError') and rr2.isError():
        print("Erro Modbus:", rr2)
    else:
        print("Bits:", getattr(rr2, 'bits', None))
finally:
    client.close()

