import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from python.src.interface_antigo import plotar_reconstrucao
from reconstrucao import reconstruir_pontos, suavizar_pontos

# ===== Configurações do experimento =====
ARQUIVO_DADOS = r"C:\Users\igor_\Desktop\ufabc\scanner-helicoidal-arduino\tests\22_08_2025\medicoes_motor.csv"

DIST_SENSOR_EIXO = 157         # mm
ALINHAMENTO_HORIZONTAL = -5    # mm
ALTURA_CAMADA = 7              # mm
ALTURA_INICIAL = 10            # mm
FATOR_ESCALA = 1.10            # fator de correção de escala

JANELA_SUAVIZACAO = 1          # tamanho da janela do filtro
# ========================================

def main():
    # 1. Reconstruir os pontos brutos a partir do CSV
    camadas = reconstruir_pontos(
        ARQUIVO_DADOS,
        altura_inicial=ALTURA_INICIAL,
        altura_camada=ALTURA_CAMADA,
        dist_sensor=DIST_SENSOR_EIXO,
        alin_horizontal=ALINHAMENTO_HORIZONTAL,
        escala=FATOR_ESCALA
    )

    # 2. Suavizar pontos (opcional)
    camadas_suave = suavizar_pontos(
        camadas,
        janela=JANELA_SUAVIZACAO
    )

    # 3. Plotar reconstrução
    plotar_reconstrucao(
        camadas_suave,
        arquivo_csv=ARQUIVO_DADOS
    )

if __name__ == "__main__":
    main()
