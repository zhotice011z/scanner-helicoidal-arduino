import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize

# ============================================
# CONFIGURAÇÕES
# ============================================

TAMANHO_QUADRADO = 80.0  # mm - altere conforme seu objeto

# ============================================
# PROCESSAMENTO DOS DADOS
# ============================================

def calibracao_sensor(dist):
    """Calibração básica do sensor"""
    if dist is None or np.isnan(dist):
        return None
    return dist * 1.02 - 3

def reduzir_ruido(distancias, janela=3):
    """Aplica filtro de mediana para reduzir ruído"""
    dist_limpa = []
    for i, d in enumerate(distancias):
        if pd.isna(d):
            dist_limpa.append(d)
            continue
            
        inicio = max(0, i - janela//2)
        fim = min(len(distancias), i + janela//2 + 1)
        vizinhos = [distancias[j] for j in range(inicio, fim) if not pd.isna(distancias[j])]
        
        if len(vizinhos) > 0:
            dist_limpa.append(np.median(vizinhos))
        else:
            dist_limpa.append(d)
            
    return np.array(dist_limpa)

def reconstruir_pontos(angulos, distancias, dist_sensor, fator_escala, offset_x):
    """Reconstrói pontos 3D a partir das medições"""
    xs, zs = [], []
    
    for ang, dist in zip(angulos, distancias):
        if pd.isna(dist):
            continue
            
        dist_cal = calibracao_sensor(dist) * fator_escala
        dist_real = dist_sensor - dist_cal
        
        x = dist_real * np.cos(ang) + offset_x
        z = dist_real * np.sin(ang)
        
        xs.append(x)
        zs.append(z)
        
    return np.array(xs), np.array(zs)

def calcular_dimensoes(xs, zs):
    """Calcula largura e altura do objeto"""
    if len(xs) == 0:
        return 0, 0
    return np.max(xs) - np.min(xs), np.max(zs) - np.min(zs)

# ============================================
# OTIMIZAÇÃO
# ============================================

def funcao_custo(params, angulos, distancias, tamanho_esperado):
    """Função de custo para otimização dos parâmetros"""
    dist_sensor, fator_escala, offset_x = params
    
    try:
        xs, zs = reconstruir_pontos(angulos, distancias, dist_sensor, fator_escala, offset_x)
        
        if len(xs) < 20:
            return 1e6
        
        largura, altura = calcular_dimensoes(xs, zs)
        
        erro_largura = abs(largura - tamanho_esperado)
        erro_altura = abs(altura - tamanho_esperado)
        
        return erro_largura + erro_altura
        
    except:
        return 1e6

# ============================================
# VISUALIZAÇÃO
# ============================================

def plotar_resultado(angulos, distancias, params, tamanho_quadrado, arquivo_csv):
    """Plota o resultado da calibração"""
    xs, zs = reconstruir_pontos(angulos, distancias, *params)
    
    plt.figure(figsize=(8, 8))
    plt.scatter(xs, zs, s=8, alpha=0.7)
    plt.gca().set_aspect('equal')
    plt.title('Resultado da Calibração')
    plt.xlabel('X (mm)')
    plt.ylabel('Z (mm)')
    plt.grid(True, alpha=0.3)
    
    # Quadrado de referência
    meio = tamanho_quadrado / 2
    quadrado = plt.Rectangle((-meio, -meio), tamanho_quadrado, tamanho_quadrado, 
                           fill=False, color='red', linestyle='--', linewidth=2)
    plt.gca().add_patch(quadrado)
    
    plt.plot(0, 0, 'k+', markersize=8)
    
    nome_saida = arquivo_csv.replace('.csv', '_calibrado.png')
    plt.savefig(nome_saida, dpi=150, bbox_inches='tight')
    plt.show()
    print(f"Gráfico salvo: {nome_saida}")

# ============================================
# FUNÇÃO PRINCIPAL
# ============================================

def calibrar_scanner(arquivo_csv, tamanho_quadrado=TAMANHO_QUADRADO):
    """Executa a calibração automática do scanner"""
    print("Carregando dados...")
    df = pd.read_csv(arquivo_csv)
    angulos = df['Angulo_rad'].values
    distancias = df['Distancia_mm'].values
    
    print("Reduzindo ruído...")
    distancias = reduzir_ruido(distancias)
    
    # Parâmetros iniciais e limites
    params_inicial = [155.0, 1.0, -7.0]
    bounds = [(100.0, 250.0), (0.5, 2.0), (-50.0, 50.0)]
    
    print("Otimizando parâmetros...")
    resultado = minimize(
        funcao_custo,
        params_inicial,
        args=(angulos, distancias, tamanho_quadrado),
        method='L-BFGS-B',
        bounds=bounds,
        options={'maxiter': 100}
    )
    
    if resultado.success:
        dist_sensor, fator_escala, offset_x = resultado.x
        
        print(f"\nCalibração concluída. Erro: {resultado.fun:.1f} mm")
        print(f"\nDIST_SENSOR_EIXO = {dist_sensor:.1f}")
        print(f"FATOR_ESCALA = {fator_escala:.3f}")
        print(f"ALINHAMENTO_HORIZONTAL = {offset_x:.1f}")
        
        # Teste dos resultados
        xs, zs = reconstruir_pontos(angulos, distancias, dist_sensor, fator_escala, offset_x)
        largura, altura = calcular_dimensoes(xs, zs)
        
        print(f"\nDimensões obtidas: {largura:.1f} x {altura:.1f} mm")
        print(f"Dimensão esperada: {tamanho_quadrado:.1f} x {tamanho_quadrado:.1f} mm")
        
        plotar_resultado(angulos, distancias, resultado.x, tamanho_quadrado, arquivo_csv)
        
        return {
            'dist_sensor': dist_sensor,
            'fator_escala': fator_escala,
            'offset_x': offset_x,
            'erro': resultado.fun,
            'dimensoes': (largura, altura)
        }
    else:
        print("Falha na calibração")
        return None

# ============================================
# EXECUÇÃO
# ============================================

if __name__ == "__main__":
    resultado = calibrar_scanner("medicoes_motor 22_08.csv")
    
    if resultado:
        print("\n" + "="*40)
        print("Valores para usar no código:")
        print("="*40)
        print(f"DIST_SENSOR_EIXO = {resultado['dist_sensor']:.1f}")
        print(f"FATOR_ESCALA = {resultado['fator_escala']:.3f}  # na função calibracao()")
        print(f"ALINHAMENTO_HORIZONTAL = {resultado['offset_x']:.1f}")
