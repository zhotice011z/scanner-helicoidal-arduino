import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize

# ====================================================================
# CONFIGURAÇÕES
# ====================================================================

# Tamanho do objeto de calibração em mm.
# Mantenha este valor consistente com o objeto real que você está usando.
TAMANHO_QUADRADO = 80.0  # mm

# O desvio horizontal do sensor em relação ao eixo de rotação.
# Este parâmetro é fixo e não faz parte da otimização. Ajuste manualmente se necessário.
ALINHAMENTO_HORIZONTAL_FIXO = 0.0 # mm

# ====================================================================
# FUNÇÕES DE PROCESSAMENTO DE DADOS
# ====================================================================

def reduzir_ruido(distancias, janela=5):
    """
    Aplica um filtro de mediana para reduzir picos de ruído nos dados de distância.
    A mediana é eficaz para remover ruído impulsivo sem distorcer as bordas.
    
    Args:
        distancias (np.array): Array de distâncias com ruído.
        janela (int): O tamanho da janela do filtro de mediana.
    
    Returns:
        np.array: Array de distâncias com o ruído reduzido.
    """
    dist_limpa = []
    # Itera sobre cada ponto para aplicar o filtro
    for i in range(len(distancias)):
        # Define a janela de vizinhos para o filtro de mediana
        inicio = max(0, i - janela // 2)
        fim = min(len(distancias), i + janela // 2 + 1)
        vizinhos = [d for d in distancias[inicio:fim] if not pd.isna(d)]
        
        if len(vizinhos) > 0:
            dist_limpa.append(np.median(vizinhos))
        else:
            dist_limpa.append(distancias[i])
            
    return np.array(dist_limpa)

def reconstruir_pontos(angulos, distancias, dist_sensor, fator_escala):
    """
    Reconstrói as coordenadas cartesianas (X, Z) a partir dos dados polares
    (ângulo, distância) e dos parâmetros de calibração.
    
    Args:
        angulos (np.array): Ângulos de varredura em radianos.
        distancias (np.array): Distâncias medidas pelo sensor em mm.
        dist_sensor (float): Distância calibrada do sensor ao eixo de rotação.
        fator_escala (float): Fator de escala de medição do sensor.
    
    Returns:
        tuple: Arrays numpy de coordenadas X e Z.
    """
    xs, zs = [], []
    for ang, dist in zip(angulos, distancias):
        # Apenas processa se a distância for um valor válido
        if not pd.isna(dist):
            # Aplica o fator de escala à distância medida
            dist_calibrada = dist * fator_escala
            
            # A distância real do ponto ao centro é a distância do sensor ao eixo
            # menos a distância medida pelo sensor (lembrando que a medida do sensor
            # diminui à medida que o objeto se aproxima dele)
            dist_real_centro = dist_sensor - dist_calibrada
            
            # Converte de coordenadas polares para cartesianas
            x = (dist_real_centro * np.cos(ang)) + ALINHAMENTO_HORIZONTAL_FIXO
            z = dist_real_centro * np.sin(ang)
            
            xs.append(x)
            zs.append(z)
            
    return np.array(xs), np.array(zs)

def calcular_dimensoes(xs, zs):
    """
    Calcula a largura e a altura da forma reconstruída.
    
    Args:
        xs (np.array): Array de coordenadas X.
        zs (np.array): Array de coordenadas Z.
    
    Returns:
        tuple: Largura e altura da forma em mm.
    """
    if len(xs) == 0:
        return 0, 0
    largura = np.max(xs) - np.min(xs)
    altura = np.max(zs) - np.min(zs)
    return largura, altura

def plotar_resultado(angulos_orig, distancias_orig, parametros_otim, tamanho_quadrado, arquivo_csv, arquivo_saida='calibracao_plot.png'):
    """
    Plota os pontos reconstruídos e o quadrado de referência para visualização.
    
    Args:
        angulos_orig (np.array): Ângulos originais da medição.
        distancias_orig (np.array): Distâncias originais da medição.
        parametros_otim (list): Parâmetros de calibração otimizados.
        tamanho_quadrado (float): Tamanho esperado do lado do quadrado.
        arquivo_csv (str): Nome do arquivo CSV de entrada.
        arquivo_saida (str): Nome do arquivo de imagem para salvar o plot.
    """
    dist_sensor, fator_escala = parametros_otim
    xs, zs = reconstruir_pontos(angulos_orig, distancias_orig, dist_sensor, fator_escala)

    plt.figure(figsize=(8, 8))
    plt.title(f"Resultados da Calibração ({arquivo_csv})")
    plt.xlabel("X (mm)")
    plt.ylabel("Z (mm)")
    plt.gca().set_aspect('equal', adjustable='box')
    plt.grid(True)
    
    # Plotar o quadrado de referência
    meio_quadrado = tamanho_quadrado / 2
    x_quad = [-meio_quadrado + ALINHAMENTO_HORIZONTAL_FIXO, meio_quadrado + ALINHAMENTO_HORIZONTAL_FIXO, 
              meio_quadrado + ALINHAMENTO_HORIZONTAL_FIXO, -meio_quadrado + ALINHAMENTO_HORIZONTAL_FIXO, 
              -meio_quadrado + ALINHAMENTO_HORIZONTAL_FIXO]
    z_quad = [meio_quadrado, meio_quadrado, -meio_quadrado, -meio_quadrado, meio_quadrado]
    plt.plot(x_quad, z_quad, 'r--', label=f'Quadrado Ideal ({tamanho_quadrado}x{tamanho_quadrado} mm)')
    
    # Plotar os pontos reconstruídos com os parâmetros otimizados
    plt.plot(xs, zs, 'b.', label='Pontos Reconstruídos')
    
    plt.legend()
    plt.tight_layout()
    plt.savefig(arquivo_saida)
    plt.show()

def erro_objetivo(parametros, angulos, distancias, tamanho_quadrado):
    """
    Função de erro para otimização.
    Minimiza a diferença entre as dimensões reconstruídas e o tamanho ideal.
    
    Args:
        parametros (list): Lista de parâmetros a serem otimizados
                          [dist_sensor, fator_escala].
        angulos (np.array): Ângulos de varredura.
        distancias (np.array): Distâncias medidas.
        tamanho_quadrado (float): Tamanho esperado do lado do quadrado.
    
    Returns:
        float: O valor do erro total.
    """
    dist_sensor, fator_escala = parametros
    
    # Reconstruir os pontos com os parâmetros atuais
    xs, zs = reconstruir_pontos(angulos, distancias, dist_sensor, fator_escala)
    
    # Se a reconstrução falhar, retorne um erro alto
    if len(xs) == 0:
        return 1e10
    
    # Calcular as dimensões da forma reconstruída
    largura, altura = calcular_dimensoes(xs, zs)
    
    # Calcular o erro quadrático
    erro_largura = (largura - tamanho_quadrado)**2
    erro_altura = (altura - tamanho_quadrado)**2
    
    # O valor a ser minimizado é a soma dos erros
    return erro_largura + erro_altura

# ====================================================================
# FUNÇÃO PRINCIPAL
# ====================================================================

def calibrar_scanner(arquivo_csv):
    """
    Carrega os dados de medição e executa a otimização para encontrar
    os parâmetros de calibração ideais.
    
    Args:
        arquivo_csv (str): O caminho para o arquivo CSV com os dados de medição.
    
    Returns:
        dict: Um dicionário com os resultados da calibração ou None se falhar.
    """
    try:
        # Carregar os dados
        df = pd.read_csv(arquivo_csv)
        angulos_originais = df['Angulo_rad'].values
        distancias_brutas = df['Distancia_mm'].values
        
        # Filtrar o ruído dos dados de distância
        distancias_limpas = reduzir_ruido(distancias_brutas)

    except FileNotFoundError:
        print(f"[ERRO] O arquivo '{arquivo_csv}' não foi encontrado.")
        return None
    
    # Valores iniciais para a otimização.
    # dist_sensor: estimativa inicial da distância do sensor ao eixo.
    # fator_escala: estimativa inicial do fator de escala (idealmente 1.0).
    x0 = [150.0, 1.0]
    
    print(f"[INFO] Iniciando otimização com dados do arquivo: '{arquivo_csv}'")
    print(f"[INFO] Parâmetros iniciais: dist_sensor={x0[0]}, fator_escala={x0[1]}")
    
    # Executa a otimização
    resultado = minimize(
        fun=erro_objetivo,
        x0=x0,
        args=(angulos_originais, distancias_limpas, TAMANHO_QUADRADO),
        method='Nelder-Mead'
    )
    
    if resultado.success:
        dist_sensor, fator_escala = resultado.x
        
        print("\n============================================")
        print("RESULTADOS DA CALIBRAÇÃO")
        print("============================================")
        print(f"DIST_SENSOR_EIXO = {dist_sensor:.3f} mm")
        print(f"FATOR_ESCALA = {fator_escala:.3f}")
        print(f"ALINHAMENTO_HORIZONTAL = {ALINHAMENTO_HORIZONTAL_FIXO:.3f} mm (fixo)")
        print(f"Erro de otimização = {resultado.fun:.3f}")
        
        # Teste com os resultados otimizados
        xs, zs = reconstruir_pontos(angulos_originais, distancias_limpas, dist_sensor, fator_escala)
        largura, altura = calcular_dimensoes(xs, zs)
        
        print("\n--- Validação ---")
        print(f"Dimensões reconstruídas: Largura={largura:.1f} mm, Altura={altura:.1f} mm")
        print(f"Dimensões esperadas: {TAMANHO_QUADRADO:.1f} x {TAMANHO_QUADRADO:.1f} mm")
        
        # Plota o resultado para visualização
        plotar_resultado(angulos_originais, distancias_brutas, resultado.x, TAMANHO_QUADRADO, arquivo_csv)
        
        return {
            'dist_sensor': dist_sensor,
            'fator_escala': fator_escala,
            'offset_x': ALINHAMENTO_HORIZONTAL_FIXO,
            'erro': resultado.fun,
            'dimensoes': (largura, altura)
        }
    else:
        print("\n[ERRO] Falha na calibração. Mensagem: " + resultado.message)
        return None

# ====================================================================
# EXECUÇÃO DO SCRIPT
# ====================================================================

if __name__ == "__main__":
    # Nome do arquivo CSV gerado pelo scanner.py
    # Certifique-se de que este arquivo está na mesma pasta.
    ARQUIVO_DADOS = "medicoes_motor copy.csv"
    
    # Inicia o processo de calibração
    resultado = calibrar_scanner(ARQUIVO_DADOS)
