## PRÁTICA 1 – Cliente Modbus TCP em 
## Turma Internet das coisas

Este projeto implementa o cliente Modbus TCP da prática de **Programação de Dispositivos de Automação (Inversor)** usando a biblioteca `umodbus`.

### 1. Requisitos

- Python 3 instalado  
- Biblioteca `umodbus`

Instalação:

```bash
pip install umodbus
```

### 2. Arquivos principais

- **`inversor_senai_pymodbus.py`**  
  Programa principal da prática.  
  Funções:
  - Conecta ao servidor Modbus TCP (drive ou simulador / pyModSlave).  
  - Envia comandos para o inversor:  
    - Ligar / desligar o motor (coil 1100).  
    - Trocar o sentido de giro (coil 1101).  
    - Ajustar o setpoint de velocidade (HR 41400).  
  - Lê variáveis de processo:  
    - Velocidade (IR 30400).  
    - Corrente (IR 30401).  
    - Tensão (IR 30402).  
    - Temperatura (IR 30403).  
    - Estado do motor (DI 100 – girando/parado).  
  - Possui:
    - **Menu interativo (CLI)**.  
    - **Validação de entrada** (ex.: faixa de 1 a 60 Hz).  
    - **Tratamento de exceções e retries** na conexão Modbus.  
    - **Log em arquivo** `pratica1_modbus.log` com ações e erros.

- **`test_umod.py`**  
  Script simples para teste da comunicação Modbus TCP.  
  - Abre uma conexão com o servidor (`SERVER`, `SLAVE`).  
  - Lê a coil 1100 e imprime o resultado.

### 3. Como executar

1. **Configurar o servidor Modbus (inversor ou simulador)**  
   - Definir IP e porta (ex.: `127.0.0.1:502`).  
   - Definir **Unit ID (Slave ID)** (ex.: `1` ou `2`).  
   - Garantir que as coils e registradores usados na prática existam:
     - Coils **1100** (liga/desliga) e **1101** (sentido).  
     - Discrete Input **100**.  
     - Input Registers **30400–30403**.  
     - Holding Register **41400**.

2. **Ajustar IP / porta / Slave ID no código**

No início de `inversor_senai_pymodbus.py`:

```python
SERVER_IP   = "127.0.0.1"   # IP do servidor Modbus (drive ou pyModSlave)
SERVER_PORT = 502           # Porta TCP do servidor Modbus
SLAVE_ID    = 2             # Unit ID / Slave Address
```

Em `test_umod.py`:

```python
SERVER = ('127.0.0.1', 502)
SLAVE  = 2
```

Certifique-se de que **IP, porta e Slave ID** sejam os mesmos no simulador/inversor e no código.

3. **Rodar o teste rápido**

```bash
python test_umod.py
```

Se a comunicação estiver correta, você verá:

```text
connected
sending ...
response: [0]  # ou [1], valor da coil 1100
```

4. **Rodar o programa da prática (menu)**

```bash
python inversor_senai_pymodbus.py
```

Exemplos de opções do menu:

- `1` – Ligar motor (escreve 1 na coil 1100).  
- `2` – Parar motor (escreve 0 na coil 1100).  
- `3` – Definir velocidade (1..60 Hz) no HR 41400.  
- `4–6` – Ler temperatura, corrente e tensão (IR 30403, 30401, 30402).  
- `7` – Definir sentido (coil 1101).  
- `8` – Ler estado do motor (DI 100).  
- `9` – Ler velocidade atual (IR 30400).  
- `10` – Iniciar padrão: 30 Hz + horário + ligar motor.  
- `0` – Sair do programa.

Todos os eventos e erros são registrados em `pratica1_modbus.log`.


# inversor-senai
