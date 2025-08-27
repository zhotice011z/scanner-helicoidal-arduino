import pandas as pd
import numpy as np
from scipy.ndimage import uniform_filter1d

def reconstruir_pontos(arquivo_csv: str,
                       altura_inicial: float,
                       altura_camada: float,
                       dist_sensor: float,
                       alin_horizontal: float,
                       escala: float) -> pd.DataFrame:
    """
    Reconstrói pontos 3D a partir de medições polares armazenadas em CSV.
    Itera por todas as camadas registradas.

    Args:
        arquivo_csv (str): Caminho para o arquivo de medições.
        altura_inicial (float): Posição Z da primeira camada.
        altura_camada (float): Incremento de altura entre camadas.

    Returns:
        dict: {camada: (xs, ys, zs)} com arrays numpy de pontos para cada camada
    """
    df = pd.read_csv(arquivo_csv)
    
    def calibracao(dist):
        if dist is None or np.isnan(dist): return np.nan
        # invert a medição e corrige o deslocamento horizontal do sensor
        return np.sqrt((dist_sensor - dist)**2 + alin_horizontal**2) * escala

    df['Distancia_calibrada'] = df['Distancia_mm'].apply(
        lambda d: calibracao(d)
    )
    
    camadas, xs, ys, zs = [], [], [], []
    for camada in sorted(df['Camada'].unique()):
        linhas = df[df['Camada'] == camada]

        for _, linha in linhas.iterrows():
            dist = linha['Distancia_calibrada']
            if pd.isna(dist): continue
            
            ang = linha['Angulo_rad']

            # Conversão polar para cartesiana (plano XY)
            x = dist * np.cos(ang)
            y = dist * np.sin(ang)

            # Altura da camada no eixo Z
            z = altura_camada * (camada - 1) + altura_inicial

            camadas.append(camada)
            xs.append(x)
            ys.append(y)
            zs.append(z)

    # cria DataFrame direto
    pontos = pd.DataFrame({
        "Camada": camadas,
        "X_mm": xs,
        "Y_mm": ys,
        "Z_mm": zs
    })

    # Salvar CSV consolidado
    nome_saida = arquivo_csv.replace(".csv", "_cart.csv")
    pontos.to_csv(nome_saida, index=False)

    return pontos


def suavizar_pontos(pontos: pd.DataFrame, janela: int = 3) -> pd.DataFrame:
    """
    Suaviza todos os pontos de todas as camadas de uma reconstrução 3D
    usando média móvel circular (modo wrap).

    Args:
        pontos (pd.DataFrame): colunas ['Camada', 'X_mm', 'Y_mm', 'Z_mm']
        janela (int): tamanho da janela (ímpar, >=1)

    Returns:
        pd.DataFrame: X e Y suavizados, Z inalterado
    """
    if janela <= 1: return pontos.copy()
    if janela % 2 == 0: janela += 1

    camadas_suavizadas = []

    for camada_val, grupo in pontos.groupby('Camada', sort=True):
        xs = uniform_filter1d(grupo['X_mm'].values, size=janela, mode='wrap')
        ys = uniform_filter1d(grupo['Y_mm'].values, size=janela, mode='wrap')
        zs = grupo['Z_mm'].values  # Z não é suavizado

        df_camada = pd.DataFrame({
            'Camada': camada_val,
            'X_mm': xs,
            'Y_mm': ys,
            'Z_mm': zs
        })
        camadas_suavizadas.append(df_camada)

    # Concatena todas as camadas
    df_suavizado = pd.concat(camadas_suavizadas, ignore_index=True)
    return df_suavizado
