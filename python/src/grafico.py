import pandas as pd
import matplotlib.pyplot as plt

def plotar_dados(nome_arquivo):
    """Lê arquivo CSV e plota os resultados."""
    try:
        df = pd.read_csv(nome_arquivo)
        print(f"\nArquivo '{nome_arquivo}' carregado.")
    except FileNotFoundError:
        print(f"ERRO: Arquivo '{nome_arquivo}' não encontrado.")
        return

    df.dropna(subset=['X_mm', 'Z_mm'], inplace=True)
    if df.empty:
        print("AVISO: Nenhum dado válido para plotar.")
        return

    x, z = df['X_mm'].values, df['Z_mm'].values

    plt.figure(figsize=(8, 8))
    plt.scatter(x, z, color='red', label='Pontos medidos (X,Z)')
    plt.scatter(0, 0, color='black', marker='+', s=100, label='Centro de rotação')
    plt.gca().set_aspect('equal', 'box')
    plt.title('Reconstrução da Camada')
    plt.xlabel('X (mm)')
    plt.ylabel('Z (mm)')
    plt.legend()
    plt.grid(True)
    print("Exibindo gráfico...")
    plt.show()