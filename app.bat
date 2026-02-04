@echo off
cd /d "D:\MERCADO\promo-python-fb"
:: Ativa o ambiente virtual se você estiver usando um (opcional)
call venv\Scripts\activate
:: pip install streamlit pandas fdb
python -m streamlit run app.py --server.port 8501 --server.address 127.0.0.1
pause