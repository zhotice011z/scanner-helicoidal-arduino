import serial
import time
import csv
import numpy as np
import sys

# ==================================================
# CONFIGURAÇÕES DO SCANNER
# ==================================================

PORTA_SERIAL = 'COM6'
BAUDRATE = 115200

PASSOS_POR_VOLTA_COMPLETA = 2048*2
PONTOS_POR_CAMADA = 2**4
PASSOS_ENTRE_MEDICOES = PASSOS_POR_VOLTA_COMPLETA // PONTOS_POR_CAMADA

NOME_ARQUIVO_SAIDA = 'medicoes_motor 22_08.csv'


# ==================================================
# COMUNICAÇÃO COM ARDUINO
# ==================================================

def conectar_serial(porta, baudrate):
    try:
        ser = serial.Serial(porta, baudrate, timeout=2)
        print(f"[OK] Conectado em {porta}")
        time.sleep(2)  # tempo para inicializar
        return ser
    except Exception as e:
        print(f"[ERRO] Não foi possível abrir {porta}: {e}")
        sys.exit(1)


def girar_motor(ser, motor_id, passos=PASSOS_ENTRE_MEDICOES, timeout=20):
    comando = f"{motor_id}:{passos}\n"
    ser.write(comando.encode())
    inicio = time.time()

    while True:
        if ser.in_waiting > 0:
            resposta = ser.readline().decode().strip()
            if resposta == f"{motor_id} DONE":
                print(f"Moto [{motor_id}] girado {passos} passos")
                return True
            elif resposta.startswith("ERRO"):
                raise Exception(resposta)
        if time.time() - inicio > timeout:
            raise TimeoutError(f"[ERRO] Timeout no motor '{motor_id}'")


def medir_distancia(ser, timeout=5):
    ser.write(b"SENS\n")
    inicio = time.time()

    while True:
        if ser.in_waiting > 0:
            linha = ser.readline().decode().strip()
            if linha.startswith("DIST:"):
                valor = linha.split(":")[1].strip()
                if valor != "TIMEOUT":
                    try:
                        return int(valor)
                    except ValueError:
                        return None
                else:
                    return None
        if time.time() - inicio > timeout:
            raise TimeoutError("Timeout na leitura do sensor")


# ==================================================
# CICLO DE VARREDURA
# ==================================================

def ciclo_varredura_camada(ser, camada, arquivo_csv, pontos=PONTOS_POR_CAMADA):
    with open(arquivo_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Camada', 'Passo', 'Angulo_rad', 'Distancia_mm'])

        print(f"\n[INFO] Camada {camada} iniciada ({pontos} pontos).")

        for passo in range(pontos):
            print(f"\n--- Ponto {passo + 1}/{pontos} ---")
            girar_motor(ser, 'BASE', PASSOS_ENTRE_MEDICOES)
            distancia = medir_distancia(ser)

            angulo = 2 * np.pi * passo / pontos
            writer.writerow([camada, passo, angulo, distancia])

            print(f"Salvo → passo={passo}, dist={distancia}")

    print(f"\n[FIM] Varredura concluída. CSV: {arquivo_csv}")


# ==================================================
# EXECUÇÃO
# ==================================================

if __name__ == "__main__":
    ser = conectar_serial(PORTA_SERIAL, BAUDRATE)

    try:
        girar_motor(ser, 'BASE', 256)
        #ciclo_varredura_camada(ser, camada=1, arquivo_csv=NOME_ARQUIVO_SAIDA)
    except Exception as e:
        print(f"[ERRO CRÍTICO]: {e}")
    finally:
        if ser.is_open:
            ser.close()
            print("[INFO] Serial fechada.")
