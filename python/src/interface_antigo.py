# interface.py
import pandas as pd
import matplotlib.pyplot as plt
from ipywidgets import IntSlider, interactive_output, HBox, VBox
from scipy.ndimage import uniform_filter1d
from IPython.display import display
from reconstrucao import reconstruir_pontos  # sua função que gera DataFrame

def suavizar_camada(camada_df: pd.DataFrame, janela: int) -> pd.DataFrame:
    """
    Aplica suavização circular (média móvel) nos pontos X e Y de uma camada.
    Z não é alterado.
    """
    if janela <= 1:
        return camada_df.copy()

    if janela % 2 == 0:
        janela += 1

    camada_suave = camada_df.copy()
    camada_suave['X_mm'] = uniform_filter1d(camada_df['X_mm'].values, size=janela, mode='wrap')
    camada_suave['Y_mm'] = uniform_filter1d(camada_df['Y_mm'].values, size=janela, mode='wrap')

    return camada_suave

def plotar_reconstrucao(pontos: pd.DataFrame, arquivo_csv: str, janela_max: int = 15):
    """
    Visualização interativa de reconstrução 3D com controle de suavização em tempo real.
    """
    camadas_ordenadas = sorted(pontos['Camada'].unique())

    # sliders
    slider_camada = IntSlider(min=0, max=len(camadas_ordenadas)-1, step=1, value=0, description='Camada')
    slider_suavizacao = IntSlider(min=1, max=janela_max, step=1, value=1, description='Janela Suavização')

    def atualizar(n_camada_idx, janela_suavizacao):
        camada_valor = camadas_ordenadas[n_camada_idx]
        camada_df = pontos[pontos['Camada'] == camada_valor]

        camada_suave = suavizar_camada(camada_df, janela_suavizacao)

        xs = camada_suave['X_mm'].values
        ys = camada_suave['Y_mm'].values
        zs = camada_suave['Z_mm'].values

        plt.figure(figsize=(8, 8))
        plt.scatter(xs, ys, s=10, c='blue')
        plt.gca().set_aspect('equal', adjustable='box')
        plt.title(f"Reconstrução - Camada {n_camada_idx+1} de {len(camadas_ordenadas)} - Z={zs[0]:.1f} mm")
        plt.suptitle(f"Arquivo: {arquivo_csv}")
        plt.xlabel("X (mm)")
        plt.ylabel("Y (mm)")
        plt.grid(True)
        plt.show()

    out = interactive_output(atualizar, {'n_camada_idx': slider_camada, 'janela_suavizacao': slider_suavizacao})
    display(VBox([HBox([slider_camada, slider_suavizacao]), out]))
