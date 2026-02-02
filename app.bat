@echo off
cd /d "C:\PromoSystem\promo-python-fb-master\promo-python-fb-master"
:: Ativa o ambiente virtual se você estiver usando um (opcional)
call venv\Scripts\activate
:: pip install streamlit pandas fdb
python -m streamlit run app.py --server.port 8501 --server.address 127.0.0.1
pause