Set WshShell = CreateObject("WScript.Shell")
' O número 0 no final indica que a janela deve ser oculta
WshShell.Run chr(34) & "D:\MERCADO\promo-python-fb\desativar.bat" & chr(34), 0
Set WshShell = Nothing