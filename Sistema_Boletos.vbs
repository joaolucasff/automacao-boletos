Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' Obter pasta do script
PastaBase = FSO.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = PastaBase

' Executar sem mostrar janela
WshShell.Run """" & PastaBase & "\.venv\Scripts\pythonw.exe"" """ & PastaBase & "\Abrir_Interface.py""", 0, False

Set FSO = Nothing
Set WshShell = Nothing
