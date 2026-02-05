Set WshShell = CreateObject("WScript.Shell")
ruta = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run chr(34) & ruta & "\iniciar_app.bat" & chr(34), 0
Set WshShell = Nothing
