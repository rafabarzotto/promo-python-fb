@echo off
cd /d "C:\CAMINHO\PARA\SUA\PASTA"
:: Ativa o ambiente virtual se você estiver usando um (opcional)
:: call venv\Scripts\activate
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
pause