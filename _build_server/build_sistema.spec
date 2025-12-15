# -*- mode: python ; coding: utf-8 -*-
# build_sistema.spec - Configuração PyInstaller para Sistema de Boletos
# Gerado em: 15/12/2025
# Validado por: Claude + ChatGPT

from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Coletar todos os dados do unidecode
unidecode_datas, unidecode_binaries, unidecode_hiddenimports = collect_all('unidecode')

a = Analysis(
    ['InterfaceBoletos.py'],
    pathex=['.'],
    binaries=unidecode_binaries,
    datas=[
        ('config_server.py', '.'),
        ('EnvioBoleto.py', '.'),
        ('RenomeaçãoBoletos.py', '.'),
        ('auditoria.py', '.'),
        ('xml_nfe_reader.py', '.'),
        ('COMO_USAR.txt', '.'),
        ('extractors/*.py', 'extractors'),
    ] + unidecode_datas,
    hiddenimports=[
        'win32com.client',
        'pdfplumber',
        'openpyxl',
        'PIL',
        'PIL.Image',
        'decimal',
        'difflib',
        'xml.etree.ElementTree',
        'tkinter',
        'tkinter.ttk',
        'tkinter.scrolledtext',
        'tkinter.messagebox',
        'tkinter.simpledialog',
        'unidecode',
    ] + unidecode_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'pytest',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SistemaBoletosJotaJota',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # DESABILITADO para evitar problemas com antivírus
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Sem janela de console (GUI)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Adicionar ícone se tiver: icon='icone.ico'
)
