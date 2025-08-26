import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==================================================
# PARÂMETROS GEOMÉTRICOS
# ==================================================
# Estes parâmetros devem ser obtidos do script de calibração (calibracao.py)
# e atualizados aqui após cada calibração.
DIST_SENSOR_EIXO = 157   # mm
ALINHAMENTO_HORIZONTAL = -5  # mm
FATOR_ESCALA = 0.98

# Calibração simples
def calibracao(dist):
    """
    Aplica o fator de escala de calibração à distância bruta medida.
    
    Args:
        dist (float): Distância medida pelo sensor em mm.
        
    Returns:
        float: Distância calibrada.
    """
    if dist is None or np.isnan(dist):
        return None
    return dist * FATOR_ESCALA

# ==================================================
# FUNÇÃO DE RECONSTRUÇÃO E EXPORTAÇÃO
# ==================================================
def reconstruir_pontos(arquivo_csv, salvar_csv=True):
    """
    Lê os dados de um arquivo CSV, converte coordenadas polares
    para cartesianas e, opcionalmente, salva os resultados em um novo CSV.
    
    Args:
        arquivo_csv (str): Caminho para o arquivo de medições.
        salvar_csv (bool): Se True, salva um novo arquivo com as coordenadas cartesianas.
    
    Returns:
        tuple: Arrays numpy de coordenadas X, Z e distâncias calibradas.
    """
    df = pd.read_csv(arquivo_csv)

    xs, zs = [], []
    dists_calibradas = []

    for _, row in df.iterrows():
        dist = row['Distancia_mm']
        if pd.isna(dist):
            continue

        dist_c = calibracao(dist)
        ang = row['Angulo_rad']
        
        # CORREÇÃO: Inverte a distância usando DIST_SENSOR_EIXO como referência
        # Distância curta do sensor = ponto longe do centro
        dist_real = DIST_SENSOR_EIXO - dist_c

        # Cálculo das coordenadas cartesianas
        x = dist_real * np.cos(ang) + ALINHAMENTO_HORIZONTAL
        z = dist_real * np.sin(ang)

        xs.append(x)
        zs.append(z)
        dists_calibradas.append(dist_c)

    xs = np.array(xs)
    zs = np.array(zs)
    dists_calibradas = np.array(dists_calibradas)

    if salvar_csv:
        df_cart = pd.DataFrame({
            'X_mm': xs,
            'Z_mm': zs,
            'Distancia_calibrada_mm': dists_calibradas,
            'Distancia_real_centro_mm': DIST_SENSOR_EIXO - dists_calibradas
        })
        nome_saida = str.replace(arquivo_csv, ".csv", "_cart.csv")
        df_cart.to_csv(nome_saida, index=False)
        print(f"[INFO] CSV com pontos cartesianos salvo: {nome_saida}")

    return xs, zs, dists_calibradas

# ==================================================
# FUNÇÃO DE SUAVIZAÇÃO
# ==================================================
def suavizar_pontos(xs, zs, janela=3):
    """
    Suaviza os pontos de uma reconstrução usando uma média móvel circular.
    A suavização 'circular' garante que a forma se feche em 360 graus sem
    perder pontos nas extremidades.
    
    Args:
        xs (np.array): Array de coordenadas X.
        zs (np.array): Array de coordenadas Z.
        janela (int): O número de pontos na janela de suavização.
                      Deve ser ímpar para garantir um centro simétrico.
                      Se a janela for 1, os pontos originais são retornados.
    
    Returns:
        tuple: Arrays numpy de coordenadas X e Z suavizadas.
    """
    if janela <= 1:
        return xs, zs
    
    # Certifica-se de que a janela seja ímpar para um 'padding' simétrico
    if janela % 2 == 0:
        janela += 1
    
    # Define a metade da janela para o padding
    padding = janela // 2
    
    # Cria o "padding circular" nos arrays
    xs_padded = np.concatenate((xs[-padding:], xs, xs[:padding]))
    zs_padded = np.concatenate((zs[-padding:], zs, zs[:padding]))
    
    # Aplica o filtro de média móvel
    xs_suavizados = np.convolve(xs_padded, np.ones(janela)/janela, mode='valid')
    zs_suavizados = np.convolve(zs_padded, np.ones(janela)/janela, mode='valid')
    
    # Remove as partes do padding do resultado final
    return xs_suavizados, zs_suavizados

# ==================================================
# PLOT E ANÁLISE
# ==================================================
def plotar_reconstrucao(xs, zs, arquivo_csv, titulo="Reconstrução em Coordenadas Cartesianas"):
    """
    Plota os pontos reconstruídos.
    
    Args:
        xs (np.array): Array de coordenadas X.
        zs (np.array): Array de coordenadas Z.
        arquivo_csv (str): Nome do arquivo CSV de entrada.
        titulo (str): Título do gráfico.
    """
    arquivo_saida = str.replace(arquivo_csv, ".csv", ".png")
    
    plt.figure(figsize=(8, 8))
    plt.scatter(xs, zs, s=10, c='blue')
    plt.gca().set_aspect('equal', adjustable='box')
    plt.title(titulo)
    plt.xlabel("X (mm)")
    plt.ylabel("Z (mm)")
    plt.grid(True)
    
    # Adiciona círculo de referência mostrando a posição do sensor
    circle = plt.Circle((ALINHAMENTO_HORIZONTAL, 0), DIST_SENSOR_EIXO, 
                        fill=False, color='red', linestyle='--', alpha=0.5)
    plt.gca().add_patch(circle)
    plt.text(DIST_SENSOR_EIXO + ALINHAMENTO_HORIZONTAL + 5, 5, 
             'Posição do Sensor', color='red', fontsize=8)
    
    plt.savefig(arquivo_saida, dpi=150, bbox_inches='tight')
    plt.show()

# ==================================================
# EXECUÇÃO
# ==================================================
if __name__ == "__main__":
    # Nome do arquivo CSV a ser processado
    ARQUIVO_DADOS = "medicoes_motor 22_08.csv"
    
    # Ajuste este valor para controlar a suavização dos pontos
    # 1 = sem suavização
    # 3-5 = suavização leve
    # >5 = suavização mais forte
    JANELA_SUAVIZACAO = 9
    
    # 1. Reconstruir os pontos brutos a partir do arquivo CSV
    xs_brutos, zs_brutos, dists = reconstruir_pontos(ARQUIVO_DADOS)
    
    # 2. Suavizar os pontos reconstruídos
    xs_suavizados, zs_suavizados = suavizar_pontos(xs_brutos, zs_brutos, JANELA_SUAVIZACAO)
    
    # 3. Plotar os pontos suavizados
    plotar_reconstrucao(xs_suavizados, zs_suavizados, ARQUIVO_DADOS, 
                        titulo=f"Reconstrução Suavizada (Janela={JANELA_SUAVIZACAO})")
