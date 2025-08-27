from PyQt5.QtWidgets import QApplication, QFileDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from interface import Interface
from reconstrucao import reconstruir_pontos, suavizar_pontos
from logger_setup import logger
import pandas as pd
import numpy as np
import sys

# ----- Parâmetros padrões -----
parametros_padrao = {
    "pts_camada": 128,
    "altura_camada": 10,
    "altura_max": 150,
    "dist_sensor": 157,
    "alin_hor": 5,
    "escala": 1.10,
    "dist_min": 20,
    "dist_max": 300,
    "suavizacao": 3
}

class App(Interface):
    def __init__(self, parametros_padrao):
        super().__init__(parametros_padrao)
        self.pontos_reconst = None
        
        self.btn_select_csv.clicked.connect(self.carregar_csv_reconst)
        self.input_dist_sens.valueChanged.connect(self.plotar_dados)
        self.input_alin_hor.valueChanged.connect(self.plotar_dados)
        self.input_escala.valueChanged.connect(self.plotar_dados)
        self.input_suav.valueChanged.connect(self.plotar_dados)
        self.input_alt_camada.valueChanged.connect(self.plotar_dados)
        self.slider_camada.valueChanged.connect(self.plotar_dados)
        
    def carregar_csv_reconst(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self,
            "Selecione um arquivo CSV",
            "",
            "Arquivos CSV (*.csv)"
        )
        if caminho:
            logger.info("Arquivo escolhido:", caminho)
            self.csv_reconst_path = caminho
            self.label_reconst_csv.setText(caminho)
            
            try:
                self.dados_reconst = pd.read_csv(self.csv_reconst_path)
                if not {"Camada","Passo","Angulo_rad","Distancia_mm"}.issubset(self.dados_reconst.columns):
                    raise ValueError("CSV não possui colunas corretas")
                self.dados_reconst = self.dados_reconst.sort_values(by='Camada', ascending=True, inplace=False)
                self.slider_camada.setMaximum(self.dados_reconst['Camada'].max())
                self.plotar_dados()
            except Exception as e:
                msg = f"Erro ao carregar CSV"
                self.label_reconst_csv.setText(msg)
                logger.error(f"{msg}: {e}")

    def reconstruir(self):
        # pega valores dos spinboxes atuais
        altura_inicial = 0  # pode ser um input se quiser depois
        altura_camada = self.input_alt_camada.value()
        dist_sensor   = self.input_dist_sens.value()
        alin_hor      = self.input_alin_hor.value()
        escala        = self.input_escala.value()/100.0  # converte de % para fator

        # chama função de reconstrução
        try:
            pontos = reconstruir_pontos(
                arquivo_csv=self.csv_reconst_path,
                altura_inicial=altura_inicial,
                altura_camada=altura_camada,
                dist_sensor=dist_sensor,
                alin_horizontal=alin_hor,
                escala=escala
            )
        except Exception as e:
            logger.error("Erro na reconstrução:", e)
            return
        
        try:
            self.pontos_reconst = suavizar_pontos(
                pontos,
                self.input_suav.value()
            )
        except Exception as e:
            logger.error("Erro na suavização:", e)
            self.pontos_reconst = pontos.copy()
            return

    def plotar_dados(self):
        """
        Plota a reconstrução no canvas usando os parâmetros atuais.
        """
        
        self.reconstruir()
        
        if True:
            camada_idx = self.slider_camada.value()  # se tiver slider de camada
            camada = self.pontos_reconst[self.pontos_reconst['Camada'] == camada_idx]

            xs = camada['X_mm'].values
            ys = camada['Y_mm'].values
            zs = camada['Z_mm'].values

            # limpa eixo e plota
            self.ax_2D.clear()
            self.ax_2D.scatter(xs, ys, c='blue', s=10)
            self.base_plot_2D(f"Camada {camada_idx} - Z={zs[camada_idx]:.1f} mm")

            self.canvas_2D.draw()

def main():
    app = QApplication(sys.argv)
    janela = App(parametros_padrao)
    janela.show()

    logger.info("Aplicação iniciada")
    return app.exec_()
    

if __name__ == "__main__":
    main()
