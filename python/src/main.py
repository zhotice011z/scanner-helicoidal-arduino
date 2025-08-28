from PyQt5.QtWidgets import QApplication, QFileDialog
from mpl_toolkits.mplot3d import Axes3D
from interface import Interface
from reconstrucao import reconstruir_pontos, suavizar_pontos
from logger_setup import logger
from exportar_stl import dataframe_para_stl
from scanner import (
    conectar_serial, iniciar_arduino, girar_motor, medir_distancia)
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os
import csv

# ----- Parâmetros padrões -----
parametros_padrao = {
    "pts_camada": 128,
    "altura_camada": 5,
    "altura_max": 150,
    "dist_sensor": 157,
    "alin_hor": 5,
    "escala": 1.10,
    "dist_min": 20,
    "dist_max": 300,
    "suavizacao": 3,
    "passos_por_volta": 2048*2,  # passos por volta
    "altura_volta": 70, # mm por volta elevação
    "baudrate": 115200,
    "porta_serial": "COM7"
}

# elev: uma volta = 70 mm
# base: uma volta = 360 graus

class App(Interface):
    def __init__(self, parametros_padrao):
        super().__init__(parametros_padrao)
        self.pontos_reconst = None
        
        self.btn_select_csv.clicked.connect(self.carregar_csv_reconst)
        self.btn_iniciar_coleta.clicked.connect(self.coletar_dados)
        
        self.input_dist_sens.valueChanged.connect(self.plotar_dados)
        self.input_alin_hor.valueChanged.connect(self.plotar_dados)
        self.input_escala.valueChanged.connect(self.plotar_dados)
        self.input_suav.valueChanged.connect(self.plotar_dados)
        self.input_alt_camada_reconst.valueChanged.connect(self.plotar_dados)
        self.slider_camada.valueChanged.connect(self.plotar_dados)
        
        self.btn_export_stl.clicked.connect(self.exportar_stl)
    
    def iniciar_arduino(self):
        self.ser = conectar_serial(parametros_padrao["porta_serial"], parametros_padrao["baudrate"])
        iniciar_arduino(self.ser)
    
    
    def coletar_dados(self):
        pts_por_camada = self.input_pts_camada.value()
        altura_camada = self.input_alt_camada_coleta.value()
        altura_max = self.input_alt_max.value()
        camadas = altura_max // altura_camada
        passos_por_volta = parametros_padrao["passos_por_volta"]
        altura_volta = parametros_padrao["altura_volta"]
        passos_por_altura = int(passos_por_volta * (altura_camada / altura_volta))
    
        nome_projeto = self.input_nome_projeto.text().strip()
        if not nome_projeto:
            nome_projeto = "projeto_sem_nome"

        pasta_base = "tests"
        pasta_destino = os.path.join(pasta_base, nome_projeto)
        os.makedirs(pasta_destino, exist_ok=True)
        arquivo_csv = os.path.join(pasta_destino, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

        logger.info(f"Iniciando varredura: {arquivo_csv}")
        
        with open(arquivo_csv, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Camada', 'Passo', 'Angulo_rad', 'Distancia_mm'])

            logger.info(f"Camada {camada} iniciada - ({pts_por_camada} pts).")
            passos_por_ponto = passos_por_volta // pts_por_camada

            for camada in range(camadas):
                for passo in range(pts_por_camada):
                    girar_motor(self.ser, 'BASE', passos_por_ponto)
                    distancia = medir_distancia(self.ser)

                    angulo = 2 * np.pi * passo / pts_por_camada
                    writer.writerow([camada, passo, angulo, distancia])
                girar_motor(self.ser, 'ELEV', passos_por_altura)

        logger.info(f"Varredura concluída. CSV: {arquivo_csv}")
    
    def carregar_csv_reconst(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self,
            "Selecione um arquivo CSV",
            "",
            "Arquivos CSV (*.csv)"
        )
        if caminho:
            logger.info(f"Arquivo escolhido: {caminho}")
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
        altura_camada = self.input_alt_camada_reconst.value()
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
            logger.error(f"Erro na reconstrução: {e}")
            return
        
        try:
            self.pontos_reconst = suavizar_pontos(
                pontos,
                self.input_suav.value()
            )
        except Exception as e:
            logger.error(f"Erro na suavização: {e}")
            self.pontos_reconst = pontos.copy()
            return

    def plotar_dados(self):
        """
        Plota a reconstrução no canvas usando os parâmetros atuais.
        """
        
        self.reconstruir()
        
        xs_todos = self.pontos_reconst['X_mm'].values
        ys_todos = self.pontos_reconst['Y_mm'].values
        zs_todos = self.pontos_reconst['Z_mm'].values
        
        camada_idx = self.slider_camada.value()  # se tiver slider de camada
        camada = self.pontos_reconst[self.pontos_reconst['Camada'] == camada_idx]
        
        xs_camada = camada['X_mm'].values
        ys_camada = camada['Y_mm'].values
        zs_camada = camada['Z_mm'].values
        mask_outros = self.pontos_reconst['Camada'] != camada_idx

        # limpa eixo e plota
        self.ax_2D.clear()
        self.ax_2D.scatter(xs_camada, ys_camada, c='blue', s=10)
        self.base_plot_2D(f"Camada {camada_idx} - Z={zs_todos[camada_idx]:.1f} mm")
        self.canvas_2D.draw()
        
        self.ax_3D.clear()
        self.ax_3D.scatter(xs_todos[mask_outros], ys_todos[mask_outros], zs_todos[mask_outros], c='blue', s=1)
        self.ax_3D.scatter(xs_camada, ys_camada, zs_camada, c='red', s=5)
        self.base_plot_3D(f"Camada {camada_idx} - Z={zs_camada[0]:.1f} mm")
        self.canvas_3D.draw()


    def exportar_stl(self):
        if self.pontos_reconst is None:
            logger.warning("Nenhum ponto reconstruído para exportar.")
            return
        
        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar arquivo STL",
            "",
            "Arquivos STL (*.stl)"
        )
        if caminho:
            if not caminho.lower().endswith('.stl'):
                caminho += '.stl'
            try:
                dataframe_para_stl(self.pontos_reconst, caminho)
            except Exception as e:
                logger.error(f"Erro ao exportar STL: {e}")
            else:
                logger.info(f"STL salvo em: {caminho}")

def main():
    app = QApplication(sys.argv)
    janela = App(parametros_padrao)
    janela.show()
    logger.info(f"Aplicação iniciada: {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}")
    
    janela.iniciar_arduino()
    logger.info("Arduino iniciado e pronto para varredura.")
    
    return sys.exit(app.exec_())

if __name__ == "__main__":
    main()
