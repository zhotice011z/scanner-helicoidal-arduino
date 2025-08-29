import logging
import sys
import os
from datetime import datetime

# Cria instância global
logger = logging.getLogger("app_logger")
logger.setLevel(logging.DEBUG)

# Evita adicionar handlers duplicados ao importar em vários módulos
if not logger.handlers:
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
    console_handler.setFormatter(console_formatter)

    # Arquivo handler
    arquivo_log = f"log/app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler("tests/app.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler.setFormatter(file_formatter)

    # Adiciona ao logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

# Agora o logger pode ser importado em qualquer módulo
