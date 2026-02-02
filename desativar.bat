@echo off
"C:\Program Files (x86)\Firebird\Firebird_2_5\bin\isql.exe" -u SYSDBA -p masterkey -d "C:\CAMINHO\SEU_BANCO.FDB" -i "execute procedure SP_ROTINA_DESATIVAR_PROMO; commit;"
exit