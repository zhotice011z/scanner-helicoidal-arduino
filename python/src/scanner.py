import serial
import time
import csv
import numpy as np
import sys
from logger_setup import logger

# ==================================================
# COMUNICAÇÃO COM ARDUINO
# ==================================================

def conectar_serial(porta, baudrate):
    try:
        ser = serial.Serial(porta, baudrate, timeout=2)
        logger.info(f"Conectado em {porta}")
        return ser
    except Exception as e:
        logger.error(f"Não foi possível abrir {porta}: {e}")
        
def iniciar_arduino(ser):
    inicio = time.time()
    while time.time() - inicio < 10:  # timeout 10s
        if ser.in_waiting > 0:
            linha = ser.readline().decode(errors="ignore").strip()
            if "DONE" in linha:
                logger.info("Arduino pronto")
                return
        time.sleep(0.1)
    raise TimeoutError("Timeout: Arduino não respondeu a tempo")
    

def girar_motor(ser, motor_id, passos, timeout=20):
    comando = f"{motor_id}:{passos}\n"
    print(comando)
    ser.write(comando.encode())
    inicio = time.time()

    while True:
        if ser.in_waiting > 0:
            resposta = ser.readline().decode().strip()
            if resposta == f"{motor_id} DONE":
                print(f"Motor [{motor_id}] girado {passos} passos")
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

def ciclo_varredura_camada(ser, camada, arquivo_csv, pontos_por_camada, passos_por_volta, camadas, passos_por_camada):
    with open(arquivo_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Camada', 'Ponto', 'Angulo_rad', 'Distancia_mm'])

        logger.info(f"Camada {camada} iniciada - ({pontos_por_camada} pts).")
        passos_por_ponto = passos_por_volta // pontos_por_camada

        for camada in range(camadas):
            for passo in range(pontos_por_camada):
                girar_motor(ser, 'BASE', passos_por_ponto)
                distancia = medir_distancia(ser)

                angulo = 2 * np.pi * passo / pontos_por_camada
                writer.writerow([camada, passo, angulo, distancia])
            girar_motor(ser, 'ELEV', passos_por_camada)

    logger.info(f"Varredura concluída. CSV: {arquivo_csv}")


# ==================================================
# EXECUÇÃO
# ==================================================

if __name__ == "__main__":
    ser = conectar_serial('COM7', 115200)
    while True:
        linha = ser.readline().decode(errors="ignore").strip()
        if linha:
            print(f"[Arduino] {linha}")
            if "DONE" in linha: break

    try:
        girar_motor(ser, 'ELEV', 4096)

    except Exception as e:
        print(f"[ERRO CRÍTICO]: {e}")

    finally:
        if ser.is_open:
            ser.close()
            print("[INFO] Serial fechada.")