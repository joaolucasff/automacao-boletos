#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Launcher do Sistema de Envio de Boletos - Jota Jota
Este arquivo inicia a interface gráfica
"""

import sys
import os

# Garantir que o diretório base está no path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

if __name__ == "__main__":
    # Importar e iniciar a interface (versão atualizada em src/)
    from src.InterfaceBoletos import InterfaceBoletos
    import tkinter as tk

    root = tk.Tk()
    app = InterfaceBoletos(root)
    root.mainloop()
