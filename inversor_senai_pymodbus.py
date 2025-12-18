"""
PRÁTICA 1 – PROGRAMAÇÃO DE DISPOSITIVOS DE AUTOMAÇÃO (MODBUS TCP)
Aluno(a): Marciana Agostinho   Turma: Internet das coisas   Data: _18/12/2025

Objetivo:
Implementar um software em Python (cliente Modbus TCP) para controlar e monitorar um drive/inversor,
enviando comandos (liga/desliga, sentido e setpoint de velocidade) e lendo grandezas (velocidade,
corrente, tensão e temperatura), além do estado do motor.

Características do código:
- Menu interativo (CLI)
- Validação de entrada (não aceita valores inválidos)
- Tratamento robusto de exceções (anti-quebra)
- Tentativas automáticas (retries) em falhas de conexão
- Log em arquivo (registro de ações e erros)




Dependência:
pip install umodbus
"""

import socket
import sys
import time
import logging
from datetime import datetime

from umodbus import conf
from umodbus.client import tcp
import traceback

# -----------------------------
# CONFIGURAÇÕES GERAIS
# -----------------------------
conf.SIGNED_VALUES = False

SERVER_IP = "172.20.108.28"     # <<< TROQUE pelo IP do professor / drive
SERVER_PORT = 502              # Modbus TCP padrão
SLAVE_ID = 2                   # conforme atividade

TIMEOUT_S = 3.0
RETRIES = 2

# -----------------------------
# MAPA DE REGISTRADORES (conforme manual da prática)
# -----------------------------
# COILS (Saídas Digitais -> comando no drive)
REG_COIL_MOTOR_ONOFF = 1100    # 1 liga / 0 desliga
REG_COIL_DIR         = 1101    # 0 horário / 1 anti-horário

# DISCRETE INPUTS (Entradas Digitais -> status)
REG_DI_MOTOR_STATE   = 100     # 1 girando / 0 parado

# INPUT REGISTERS (Entradas Analógicas -> leitura)
REG_IR_SPEED    = 30400        # velocidade atual (Hz)
REG_IR_CURRENT  = 30401        # corrente (A)
REG_IR_VOLTAGE  = 30402        # tensão (V)
REG_IR_TEMP     = 30403        # temperatura (°C)

# HOLDING REGISTERS (Saídas Analógicas -> setpoint)
REG_HR_SPEED_SET = 41400       # setpoint de velocidade (Hz)

# Limites pedidos na atividade
SPEED_MIN_HZ = 1
SPEED_MAX_HZ = 60

# -----------------------------
# LOG
# -----------------------------
logging.basicConfig(
    filename="pratica1_modbus.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
def log_info(msg: str):
    print(msg)
    logging.info(msg)

def log_error(msg: str):
    print(msg)
    logging.error(msg)


# -----------------------------
# UTILITÁRIOS (ANTI-QUEBRA)
# -----------------------------
def safe_int(prompt: str, min_val=None, max_val=None) -> int:
    while True:
        try:
            raw = input(prompt).strip()
            val = int(raw)
            if min_val is not None and val < min_val:
                print(f"⚠️ Valor inválido. Mínimo: {min_val}")
                continue
            if max_val is not None and val > max_val:
                print(f"⚠️ Valor inválido. Máximo: {max_val}")
                continue
            return val
        except ValueError:
            print("⚠️ Digite um número inteiro válido.")
        except (KeyboardInterrupt, EOFError):
            print("\nSaindo com segurança...")
            sys.exit(0)

def safe_choice(prompt: str, choices: set[str]) -> str:
    while True:
        try:
            val = input(prompt).strip()
            if val in choices:
                return val
            print(f"⚠️ Opção inválida. Escolha: {', '.join(sorted(choices))}")
        except (KeyboardInterrupt, EOFError):
            print("\nSaindo com segurança...")
            sys.exit(0)

def with_modbus_socket(fn):
    """
    Abre conexão TCP, executa a função e fecha SEMPRE.
    Em caso de falha, tenta novamente algumas vezes (RETRIES).
    """
    def wrapper(*args, **kwargs):
        last_err = None
        for attempt in range(RETRIES + 1):
            sock = None
            try:
                sock = socket.create_connection((SERVER_IP, SERVER_PORT), timeout=TIMEOUT_S)
                sock.settimeout(TIMEOUT_S)
                return fn(sock, *args, **kwargs)
            except (socket.timeout, ConnectionRefusedError, OSError) as e:
                last_err = e
                log_error(f"❌ Conexão Modbus falhou ({attempt+1}/{RETRIES+1}): {repr(e)}")
                time.sleep(0.4)
            except Exception as e:
                last_err = e
                log_error(f"❌ Erro inesperado (anti-quebra): {repr(e)}")
                log_error(traceback.format_exc())
                time.sleep(0.4)
            finally:
                try:
                    if sock:
                        sock.close()
                except Exception:
                    pass

        log_error("❌ Operação cancelada: não foi possível comunicar após tentativas.")
        if last_err:
            log_error(f"Detalhe final: {repr(last_err)}")
        return None

    return wrapper


# -----------------------------
# FUNÇÕES MODBUS (baixo nível)
# -----------------------------
@with_modbus_socket
def mb_write_coil(sock, address: int, value: bool) -> bool:
    msg = tcp.write_single_coil(SLAVE_ID, address, value)
    tcp.send_message(msg, sock)
    return True

@with_modbus_socket
def mb_read_discrete_input(sock, address: int) -> bool:
    msg = tcp.read_discrete_inputs(SLAVE_ID, address, 1)
    res = tcp.send_message(msg, sock)
    return bool(res[0])

@with_modbus_socket
def mb_write_holding_register(sock, address: int, value: int) -> bool:
    msg = tcp.write_single_register(SLAVE_ID, address, value)
    tcp.send_message(msg, sock)
    return True

@with_modbus_socket
def mb_read_input_register(sock, address: int) -> int:
    msg = tcp.read_input_registers(SLAVE_ID, address, 1)
    res = tcp.send_message(msg, sock)
    return int(res[0])


# -----------------------------
# FUNÇÕES (alto nível) – menu
# -----------------------------
def ligar_motor():
    ok = mb_write_coil(REG_COIL_MOTOR_ONOFF, True)
    if ok:
        log_info("✅ Motor LIGADO (coil 1100 = 1).")

def parar_motor():
    ok = mb_write_coil(REG_COIL_MOTOR_ONOFF, False)
    if ok:
        log_info("✅ Motor PARADO (coil 1100 = 0).")

def definir_velocidade():
    hz = safe_int(f"Digite a velocidade ({SPEED_MIN_HZ}..{SPEED_MAX_HZ} Hz): ",
                  min_val=SPEED_MIN_HZ, max_val=SPEED_MAX_HZ)
    ok = mb_write_holding_register(REG_HR_SPEED_SET, hz)
    if ok:
        log_info(f"✅ Setpoint de velocidade enviado: {hz} Hz (HR 41400).")

def definir_sentido():
    print("Sentido de giro:")
    print("  0 - Horário")
    print("  1 - Anti-horário")
    op = safe_choice("Escolha (0/1): ", {"0", "1"})
    value = (op == "1")
    ok = mb_write_coil(REG_COIL_DIR, value)
    if ok:
        log_info(f"✅ Sentido definido: {'Anti-horário' if value else 'Horário'} (coil 1101).")

def ler_estado_motor():
    state = mb_read_discrete_input(REG_DI_MOTOR_STATE)
    if state is None:
        return
    log_info(f"📌 Estado do motor (DI 100): {'GIRANDO' if state else 'PARADO'}")

def ler_velocidade_atual():
    hz = mb_read_input_register(REG_IR_SPEED)
    if hz is None:
        return
    log_info(f"🏎️ Velocidade atual (IR 30400): {hz} Hz")

def ler_corrente():
    a = mb_read_input_register(REG_IR_CURRENT)
    if a is None:
        return
    log_info(f"⚡ Corrente (IR 30401): {a} A")

def ler_tensao():
    v = mb_read_input_register(REG_IR_VOLTAGE)
    if v is None:
        return
    log_info(f"🔌 Tensão (IR 30402): {v} V")

def ler_temperatura():
    t = mb_read_input_register(REG_IR_TEMP)
    if t is None:
        return
    log_info(f"🌡️ Temperatura (IR 30403): {t} °C")

def iniciar_padrao():
    # padrão solicitado: 30 Hz + sentido horário + ligar
    ok1 = mb_write_holding_register(REG_HR_SPEED_SET, 30)
    ok2 = mb_write_coil(REG_COIL_DIR, False)            # 0 = horário
    ok3 = mb_write_coil(REG_COIL_MOTOR_ONOFF, True)     # liga
    if ok1 and ok2 and ok3:
        log_info("✅ Padrão aplicado: 30 Hz + horário + motor ligado.")


# -----------------------------
# MENU PRINCIPAL
# -----------------------------
def print_menu():
    print("\n==============================")
    print(" PRÁTICA 1 - MODBUS TCP (Python)")
    print("==============================")
    print(f"Destino: {SERVER_IP}:{SERVER_PORT} | Slave ID: {SLAVE_ID}")
    print("------------------------------")
    print("1) Ligar motor")
    print("2) Parar motor")
    print("3) Definir velocidade (1..60 Hz)")
    print("4) Ler temperatura")
    print("5) Ler corrente")
    print("6) Ler tensão")
    print("7) Definir sentido")
    print("8) Ler estado do motor")
    print("9) Ler velocidade atual")
    print("10) Iniciar padrão (30 Hz + horário)")
    print("0) Sair")

def main():
    log_info(f"== Início da execução: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} ==")
    while True:
        print_menu()
        op = safe_choice("Escolha: ", {str(i) for i in range(0, 11)})

        if op == "1":
            ligar_motor()
        elif op == "2":
            parar_motor()
        elif op == "3":
            definir_velocidade()
        elif op == "4":
            ler_temperatura()
        elif op == "5":
            ler_corrente()
        elif op == "6":
            ler_tensao()
        elif op == "7":
            definir_sentido()
        elif op == "8":
            ler_estado_motor()
        elif op == "9":
            ler_velocidade_atual()
        elif op == "10":
            iniciar_padrao()
        elif op == "0":
            log_info("Saindo... ✅")
            break

if __name__ == "__main__":
    main()



