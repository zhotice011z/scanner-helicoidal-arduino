import numpy as np
from stl import mesh
import pandas as pd
from logger_setup import logger

def dataframe_para_stl(df, nome_arquivo_saida):
    """
    Converte pontos cartesianos de um DataFrame em uma malha STL.

    Parâmetros:
    -----------
    df : pandas.DataFrame
        Deve conter colunas ['Camada', 'X_mm', 'Y_mm', 'Z_mm']
    nome_arquivo_saida : str
        Nome do arquivo STL de saída (ex: 'saida.stl')
    """

    # Ordena para garantir consistência
    df = df.sort_values(by=['Camada'])

    faces = []

    # Itera camada por camada
    camadas = df['Camada'].unique()
    for i in range(len(camadas)-1):
        camada_atual = df[df['Camada'] == camadas[i]][['X_mm', 'Y_mm', 'Z_mm']].to_numpy()
        camada_prox = df[df['Camada'] == camadas[i+1]][['X_mm', 'Y_mm', 'Z_mm']].to_numpy()

        # Garante mesma quantidade de pontos
        n = min(len(camada_atual), len(camada_prox))
        camada_atual = camada_atual[:n]
        camada_prox = camada_prox[:n]

        # Conecta os pontos entre as camadas
        for j in range(n):
            p1 = camada_atual[j]
            p2 = camada_prox[j]
            p3 = camada_prox[(j+1) % n]
            p4 = camada_atual[(j+1) % n]

            # Duas faces por quadrilátero
            faces.append([p1, p2, p3])
            faces.append([p1, p3, p4])

    # Concatena em um único array
    faces_np = np.array(faces)

    # Cria malha STL
    stl_mesh = mesh.Mesh(np.zeros(faces_np.shape[0], dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces_np):
        stl_mesh.vectors[i] = f

    # Salva
    stl_mesh.save(nome_arquivo_saida)

if __name__ == "__main__":
    arquivo_csv = "tests/ampulheta/ampulheta_sim_cart.csv"
    
    df = pd.read_csv(arquivo_csv)

    # Gerar STL
    arquivo_saida = arquivo_csv.replace(".csv", ".stl")
    dataframe_para_stl(df, arquivo_saida)