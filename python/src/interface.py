# interface.py
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QSpinBox, QPushButton, QLineEdit, QProgressBar, QSlider,
    QFrame, QPlainTextEdit
)
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from logger_setup import logger
import logging
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

class QtSignalHandler(logging.Handler, QObject):
    log_signal = pyqtSignal(str)

    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        self.log_signal.emit(msg)

class LogViewer(QPlainTextEdit):
    """QPlainTextEdit que recebe mensagens de log."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)

    def connect_logger(self, logger):
        handler = QtSignalHandler()
        handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        handler.log_signal.connect(self.appendPlainText)
        logger.addHandler(handler)

class Input_SpinBox(QSpinBox):
        """SpinBox que arredonda o valor ao step mais próximo ao perder foco."""
        def __init__(self, min_value=0, max_value=100, step=1, start_value=0, prefix="", suffix="", parent = None):
            super().__init__(parent)
            self.setKeyboardTracking(False)  # evita múltiplos sinais ao digitar
            self.setRange(min_value, max_value)
            self.setSingleStep(step)
            self.setValue(start_value)
            self.setPrefix(prefix)
            self.setSuffix(suffix)
        
        def focusOutEvent(self, event):
            super().focusOutEvent(event)
            step = self.singleStep()
            valor = self.value()
            minimo = self.minimum()
            maximo = self.maximum()

            # arredonda para múltiplo mais próximo do step e garante que não saia dos limites
            arredondado = max(minimo, min(maximo, round((valor - minimo) / step) * step + minimo))

            self.setValue(arredondado)

class Interface(QMainWindow):
    def __init__(self, parametros_padrao):
        super().__init__()
        # self.showMaximized()
        self.parametros_padrao = parametros_padrao
        self.setWindowTitle("Scanner Helicoidal")
        self.setMinimumSize(800, 600)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.vis_2d = False  # começa em 3D

        # Layout principal: Config | Visualização | Log
        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        self.init_config_panel()
        self.init_visual_panel()
        self.init_log_panel()

    # ============================
    # Funções de interface
    # ===========================
    def resumir_caminho(caminho, max_chars=40):
        """
        Retorna o caminho encurtado para exibição em QLabel,
        cortando do início até caber no limite, garantindo que
        a divisão de pastas seja respeitada.
        """
        if len(caminho) <= max_chars: return caminho
        
        # pega os últimos caracteres que cabem dentro do limite
        final = caminho[-(max_chars+4):]
        
        # encontra o primeiro "/" dentro dessa substring
        slash_index = final.find('/')
        
        if slash_index != -1:
            # corta tudo antes desse "/"
            return "…/" + final[slash_index+1:]
        else:
            # se não tiver "/", mostra apenas os últimos max_chars
            return "…/" + final

    def lim_plot(self):
        if hasattr(self, "pontos_reconst"):
            max_xy = self.pontos_reconst[["X_mm", "Y_mm"]].abs().max().max()
            self.lim_xy = np.ceil(max_xy / 10) * 10 + 10
            self.lim_z = np.ceil(self.pontos_reconst["Z_mm"].max() / 10) * 10 + 10
        else:
            self.lim_xy = -self.parametros_padrao["dist_max"]//2
            self.lim_xy = self.parametros_padrao["dist_max"]//2
            self.lim_z = self.parametros_padrao["altura_max"] + 10

    def base_plot_2D(self, title):
        self.ax_2D.set_aspect('equal', 'box')
        self.ax_2D.set_title(title)
        self.ax_2D.set_xlabel("X (mm)")
        self.ax_2D.set_ylabel("Y (mm)")
        
        self.lim_plot()
        self.ax_2D.set_xlim([-self.lim_xy, self.lim_xy])
        self.ax_2D.set_ylim([-self.lim_xy, self.lim_xy])
        self.ax_2D.grid(True)
        
    def base_plot_3D(self, title):
        self.ax_3D.set_title(title)
        self.ax_3D.set_xlabel("X (mm)")
        self.ax_3D.set_ylabel("Y (mm)")
        self.ax_3D.set_zlabel("Z (mm)")
        
        self.lim_plot()
        self.ax_3D.set_xlim([-self.lim_xy, self.lim_xy])
        self.ax_3D.set_ylim([-self.lim_xy, self.lim_xy])
        self.ax_3D.set_zlim([0, self.lim_z])
        self.ax_3D.grid(True)
    
    def alternar_2d_3d(self):
        self.canvas_2D.setVisible(not self.vis_2d)
        self.canvas_3D.setVisible(self.vis_2d)
        self.vis_2d = not self.vis_2d
    
    # ===========================
    # Painel de Configurações
    # ===========================
    def init_config_panel(self):
        self.config_frame = QFrame()
        self.config_frame.setFixedWidth(300)
        self.config_layout = QVBoxLayout()
        self.config_frame.setLayout(self.config_layout)

        # ---------- varredura ----------
        self.varredura_frame = QFrame()
        self.varredura_layout = QVBoxLayout()
        self.varredura_frame.setLayout(self.varredura_layout)

        self.varredura_layout.addWidget(QLabel("<b>Varredura do objeto</b>"))

        form_varredura = QFormLayout()

        # Conectar arduino
        self.layout_porta = QHBoxLayout()
        self.btn_conectar_arduino = QPushButton("Conectar Arduino")
        self.layout_porta.addWidget(self.btn_conectar_arduino)
        self.input_porta = Input_SpinBox(
            min_value=1,
            max_value=10,
            step=1,
            start_value=self.parametros_padrao["porta_serial"],
            prefix="COM"
        )
        self.layout_porta.addWidget(self.input_porta)
        self.varredura_layout.addLayout(self.layout_porta)
        
        # Pontos por camada
        self.input_pts_camada = Input_SpinBox(
            min_value=8,
            max_value=256,
            step=8,
            start_value=self.parametros_padrao["pts_camada"],
        )
        form_varredura.addRow("Pontos por camada", self.input_pts_camada)

        # Altura da camada
        self.input_alt_camada_varredura = Input_SpinBox(
            min_value=self.parametros_padrao["altura_camada"],
            max_value=self.parametros_padrao["altura_camada"]*4,
            step=self.parametros_padrao["altura_camada"],
            start_value=self.parametros_padrao["altura_camada"],
            suffix=" mm"
        )
        form_varredura.addRow("Altura da camada", self.input_alt_camada_varredura)

        # Altura máxima
        self.input_alt_max = Input_SpinBox(
            min_value=20,
            max_value=90,
            step=10,
            start_value=self.parametros_padrao["altura_max"],
            suffix=" mm"
        )
        form_varredura.addRow("Altura máxima", self.input_alt_max)

        # Nome do projeto / pasta
        self.input_nome_projeto = QLineEdit()
        form_varredura.addRow("Nome do projeto", self.input_nome_projeto)

        # Botão selecionar pasta
        self.btn_select_pasta = QPushButton("Selecionar pasta")
        form_varredura.addRow("Pasta de salvamento", self.btn_select_pasta)

        self.varredura_layout.addLayout(form_varredura)

        # Botões iniciar / parar
        self.btn_iniciar_varredura = QPushButton("Iniciar varredura")
        self.btn_parar_varredura = QPushButton("Parar varredura")
        self.btn_iniciar_varredura.setEnabled(False)
        self.btn_parar_varredura.setEnabled(False)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_iniciar_varredura)
        btn_layout.addWidget(self.btn_parar_varredura)
        self.varredura_layout.addLayout(btn_layout)

        # Barras de progresso
        self.progress_pts = QProgressBar()
        self.progress_pts.setFormat("Pontos: %v/%m")
        self.varredura_layout.addWidget(self.progress_pts)

         # Barra de progresso camadas
        self.progress_camadas = QProgressBar()
        self.progress_camadas.setFormat("Camadas: %v/%m")
        self.varredura_layout.addWidget(self.progress_camadas)

        self.config_layout.addWidget(self.varredura_frame)

        # ---------- Reconstrução ----------
        self.reconst_frame = QFrame()
        self.reconst_layout = QVBoxLayout()
        self.reconst_frame.setLayout(self.reconst_layout)

        self.reconst_layout.addWidget(QLabel("<b>Reconstrução</b>"))
        form_reconst = QFormLayout()

        # Seletor CSV
        self.btn_select_csv = QPushButton("Selecionar CSV")
        self.reconst_layout.addWidget(self.btn_select_csv)
        
        self.label_reconst_csv = QLabel("Nenhum arquivo selecionado")
        self.reconst_layout.addWidget(self.label_reconst_csv)

        # Distância sensor
        self.input_dist_sens = Input_SpinBox(
            min_value=100,
            max_value=200,
            step=1,
            start_value=self.parametros_padrao["dist_sensor"],
            suffix=" mm"
        )
        form_reconst.addRow("Distância do sensor", self.input_dist_sens)

        # Alinhamento horizontal
        self.input_alin_hor = Input_SpinBox(
            min_value=0,
            max_value=10,
            step=1,
            start_value=self.parametros_padrao["alin_hor"],
            suffix=" mm"
        )
        form_reconst.addRow("Alinhamento horizontal", self.input_alin_hor)

        # Escala
        self.input_escala = Input_SpinBox(
            min_value=80,
            max_value=200,
            step=1,
            start_value=int(self.parametros_padrao["escala"]*100),
            suffix=" %"
        )
        form_reconst.addRow("Escala", self.input_escala)
        
        self.input_alt_camada_reconst = Input_SpinBox(
            min_value=5,
            max_value=20,
            step=5,
            start_value=self.parametros_padrao["altura_camada"],
            suffix=" mm"
        )
        form_reconst.addRow("Altura da camada", self.input_alt_camada_reconst)
        
        # Janela de suavização
        self.input_suav = Input_SpinBox(
            min_value=1,
            max_value=11,
            step=2,
            start_value=self.parametros_padrao["suavizacao"],
            suffix=" pts"
        )
        form_reconst.addRow("Janela suavização", self.input_suav)
        self.reconst_layout.addLayout(form_reconst)

        # Botão export STL
        self.btn_export_stl = QPushButton("Exportar STL")
        self.btn_export_stl.setEnabled(False)
        self.reconst_layout.addWidget(self.btn_export_stl)
        
        self.config_layout.addWidget(self.reconst_frame)

        self.main_layout.addWidget(self.config_frame)

    # ===========================
    # Painel de Visualização
    # ===========================
    def init_visual_panel(self):
        self.visu_frame = QFrame()
        self.visu_frame.setFrameShape(QFrame.StyledPanel)
        self.visu_layout = QVBoxLayout()
        self.visu_frame.setLayout(self.visu_layout)

        self.slider_camada = QSlider(Qt.Horizontal)
        self.slider_camada.setMinimum(1)
        self.slider_camada.setMaximum(1)
        self.slider_camada.setValue(1)
        self.slider_camada.setTickInterval(1)
        self.visu_layout.addWidget(self.slider_camada)
        
        self.btn_2d3d = QPushButton("Alternar 2D/3D")
        self.btn_2d3d.clicked.connect(self.alternar_2d_3d)
        self.visu_layout.addWidget(self.btn_2d3d)
        
        self.figura_2D = Figure(figsize=(5,5))
        self.canvas_2D = FigureCanvas(self.figura_2D)
        self.canvas_2D.setMinimumSize(400, 400)
        self.canvas_2D.setVisible(self.vis_2d)
        self.ax_2D = self.figura_2D.add_subplot(111)
        self.ax_2D.set_aspect('equal', adjustable='box')
        self.base_plot_2D("Nenhum dado carregado")
        self.visu_layout.addWidget(self.canvas_2D)
        
        self.figura_3D = Figure(figsize=(5,5))
        self.canvas_3D = FigureCanvas(self.figura_3D)
        self.canvas_3D.setMinimumSize(400, 400)
        self.canvas_3D.setVisible(not self.vis_2d)
        self.ax_3D = self.figura_3D.add_subplot(111, projection='3d')
        self.ax_3D.set_aspect('equal', adjustable='box')
        self.base_plot_3D("Nenhum dado carregado")
        self.visu_layout.addWidget(self.canvas_3D)
        
        # Aqui será adicionado o matplotlib canvas ou similar
        self.main_layout.addWidget(self.visu_frame, stretch=2)

    # ===========================
    # Painel de Log
    # ===========================
    def init_log_panel(self):
        self.log_frame = QFrame()
        self.log_frame.setFrameShape(QFrame.StyledPanel)
        self.log_frame.setMinimumWidth(150)
        self.log_layout = QVBoxLayout()
        self.log_frame.setLayout(self.log_layout)

        self.log_layout.addWidget(QLabel("Log:"))
        self.log_viewer = LogViewer()
        self.log_layout.addWidget(self.log_viewer)
        self.log_viewer.connect_logger(logger)

        self.main_layout.addWidget(self.log_frame, stretch=1)
