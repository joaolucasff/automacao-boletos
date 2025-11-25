Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' Obter pasta do script
PastaBase = FSO.GetParentFolderName(WScript.ScriptFullName)

' Criar atalho
Set Atalho = WshShell.CreateShortcut(PastaBase & "\⭐ Sistema de Boletos.lnk")
Atalho.TargetPath = PastaBase & "\.venv\Scripts\pythonw.exe"
Atalho.Arguments = """" & PastaBase & "\Abrir_Interface.py"""
Atalho.WorkingDirectory = PastaBase
Atalho.IconLocation = PastaBase & "\.venv\Scripts\pythonw.exe,0"
Atalho.Description = "Sistema de Envio de Boletos - Jota Jota"
Atalho.Save

' Mensagem de sucesso
MsgBox "Atalho criado com sucesso!" & vbCrLf & vbCrLf & "Procure por:" & vbCrLf & "⭐ Sistema de Boletos.lnk" & vbCrLf & vbCrLf & "Duplo clique nele para abrir o sistema.", vbInformation, "Sistema de Boletos"

Set Atalho = Nothing
Set FSO = Nothing
Set WshShell = Nothing
