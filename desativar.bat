@echo off
cd /d "C:\Program Files (x86)\Firebird\Firebird_2_5\bin"
(echo execute procedure SP_ROTINA_DESATIVAR_PROMO; commit; exit;) | isql.exe -u SYSDBA -p masterkey "C:\Windows\en-BR\ESTOQUE.FDB"