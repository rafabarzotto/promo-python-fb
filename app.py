import streamlit as st
import pandas as pd
import unicodedata
import fdb
import datetime
import platform
import os

def inicializar_firebird_client():
    sistema = platform.system()
    caminho_lib = None

    if sistema == 'Windows':
        # Caminhos comuns no Windows (ajuste conforme sua versão do Firebird)
        possiveis_caminhos = [
            r'C:\Program Files\Firebird\Firebird_3_0\fbclient.dll',
            r'C:\Program Files\Firebird\Firebird_2_5\bin\fbclient.dll',
            r'C:\Windows\System32\fbclient.dll',
            os.path.join(os.getcwd(), 'fbclient.dll') # Procura na pasta do script
        ]
    else:
        # Caminhos comuns no Manjaro / Linux
        possiveis_caminhos = [
            '/usr/lib/libfbclient.so',
            '/usr/lib64/libfbclient.so',
            '/usr/lib/libfbclient.so.2',
            '/opt/firebird/lib/libfbclient.so'
        ]

    # Tenta encontrar a primeira biblioteca válida
    for caminho in possiveis_caminhos:
        if os.path.exists(caminho):
            caminho_lib = caminho
            break

    if caminho_lib:
        try:
            fdb.load_api(caminho_lib)
            # st.sidebar.success(f"Driver carregado: {sistema}") # Opcional: feedback na barra lateral
            return True
        except Exception as e:
            st.error(f"Erro ao carregar a biblioteca {caminho_lib}: {e}")
            return False
    else:
        st.error(f"Cliente Firebird não encontrado para o sistema {sistema}.")
        st.info("No Windows: Instale o Firebird ou coloque a fbclient.dll na pasta do script.")
        st.info("No Linux: Execute 'pamac build firebird-client' ou 'sudo pacman -S libfbclient'.")
        return False

# Executa a inicialização
if not inicializar_firebird_client():
    st.stop() # Interrompe o app se não carregar o driver

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Integrador Firebird", layout="wide")

# --- FUNÇÕES DE PROCESSAMENTO ---
def limpar_string_para_latin1(texto):
    if not isinstance(texto, str): return ""
    nfkd_form = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).encode('ascii', 'ignore').decode('ascii').upper().strip()

def processar_e_enviar(df, db_config):
    try:
        # Conexão com o Firebird
        conn = fdb.connect(
            host=db_config['host'],
            database=db_config['path'],
            user=db_config['user'],
            password=db_config['password'],
            charset='WIN1252'
        )
        cur = conn.cursor()
        
        cols = df.columns
        count = 0
        
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, row in df.iterrows():
            # Tratamento de dados
            gtin_raw = str(row[cols[1]]).strip() if pd.notna(row[cols[1]]) else ""
            gtin_final = gtin_raw.zfill(13) if gtin_raw and gtin_raw.lower() != 'nan' else str(row[cols[0]]).strip().zfill(13)
            desc_limpa = limpar_string_para_latin1(row[cols[2]])[:80]
            preco_raw = float(str(row[cols[4]]).replace(',', '.')) if pd.notna(row[cols[4]]) else 0.0

            # Ajuste 1 e 2: EXECUTE BLOCK para lógica condicional
            # Se não existir pelo GTIN, INSERT (com COD_SEC = 1)
            # Se existir, UPDATE (apenas campos necessários, ignorando COD_SEC)
            sql = """
            EXECUTE BLOCK (
                gtin VARCHAR(14) = ?, nome VARCHAR(80) = ?, preco NUMERIC(18,2) = ?
            ) AS BEGIN
            /* 1. Tenta inserir se não existir */
            IF (NOT EXISTS (SELECT 1 FROM PRODUTO WHERE CODIGO_BARRA_PRO = :gtin)) THEN
            BEGIN
                INSERT INTO PRODUTO (
                    CODIGO_BARRA_PRO, TP_PRODUTO, TP_PRODUCAO, ESTOQUE_MINIMO, 
                    NOME_PRO, DESC_CUPOM, COD_MARC, COD_SEC, COD_GRUP, COD_SGRUP, 
                    COD_UNI_ENT, COD_UNI_SAI, PRECO_VAREJO, PRECO_PROMOCAO, PRECO_PRAZO, 
                    MARGEM_LUCRO, QUANT_ESTOQ, DATA_VALIDADE, DIAS_VALIDADE_PRO, 
                    CONTROLA_ESTOQUE_PRO, ATIVO_PRO
                ) VALUES (
                    :gtin, 'GERAL', 'GERAL', 99, 
                    :nome, :nome, 1, 1, 1, 1, 
                    2, 2, :preco, 0, 0, 
                    0, 9999, '2099-01-01', 0, 
                    'N', 'S'
                );
            END
            ELSE
            BEGIN
                /* 2. Se existir, verifica se NÃO é o código 99 antes de atualizar */
                /* Usamos 13 dígitos pois é o padrão que você definiu no preenchimento (zfill) */
                IF (:gtin <> '0000000000099') THEN
                BEGIN
                    UPDATE PRODUTO SET 
                        NOME_PRO = :nome, 
                        DESC_CUPOM = :nome,
                        PRECO_VAREJO = :preco
                    WHERE CODIGO_BARRA_PRO = :gtin;
                END
            END
            END
            """
            
            # Passamos apenas 4 parâmetros agora, pois o bloco reutiliza as variáveis :gtin, :nome, etc.
            cur.execute(sql, (gtin_final, desc_limpa, preco_raw))
            
            count += 1
            progress_bar.progress(count / len(df))
            status_text.text(f"Processando: {count} / {len(df)}")

        conn.commit()
        cur.close()
        conn.close()
        return True, count
    except Exception as e:
        return False, str(e)

# --- INTERFACE WEB ---
st.title("🚀 Sistema de Integração de Produtos")

# Criação das Abas
tab1, tab2, tab3, tab4 = st.tabs(["📥 Importar CSV", "⚙️ Configurações DB", "🏷️ Gestão de Promoções", "📊 Log"])

with tab2:
    st.header("Configuração do Banco de Dados Firebird")
    col1, col2 = st.columns(2)
    with col1:
        db_host = st.text_input("IP do Servidor", value="localhost")
        db_user = st.text_input("Usuário", value="SYSDBA")
    with col2:
        db_path = st.text_input("Caminho do Banco (ex: D:\\MERCADO\\1.FDB)", value="C:\\Windows\\en-BR\\ESTOQUE.FDB")
        db_pw = st.text_input("Senha", type="password", value="masterkey")

with tab1:
    st.header("Upload de Arquivo")
    arquivo = st.file_uploader("Selecione o arquivo CSV", type=['csv'])

    if arquivo is not None:
        # Preview dos dados
        df_preview = pd.read_csv(arquivo, sep=';', encoding='latin-1', dtype=str)
        st.subheader("Pré-visualização dos dados")
        st.dataframe(df_preview.head(20))

        if st.button("Iniciar Importação Direta"):
            if not db_path or not db_pw:
                st.error("Por favor, preencha as configurações do banco na aba Configurações.")
            else:
                config = {
                    'host': db_host,
                    'path': db_path,
                    'user': db_user,
                    'password': db_pw
                }
                
                with st.spinner('Integrando com Firebird...'):
                    sucesso, resultado = processar_e_enviar(df_preview, config)
                
                if sucesso:
                    st.success(f"Sucesso! {resultado} produtos processados no banco.")
                else:
                    st.error(f"Erro na conexão ou processamento: {resultado}")

with tab3:
    st.header("📅 Gestão de Promoções por Seção")
    
    # --- 1. CARREGAMENTO DAS SEÇÕES (Sempre executado) ---
    try:
        conn = fdb.connect(host=db_host, database=db_path, user=db_user, password=db_pw, charset='WIN1252')
        cur = conn.cursor()
        cur.execute("SELECT COD_SEC, NOME_SEC FROM SECAO WHERE COD_SEC <> 1 ORDER BY NOME_SEC")
        secoes_db = cur.fetchall()
        dict_secoes = {f"{r[0]} - {r[1]}": r[0] for r in secoes_db}
    except Exception as e:
        st.error(f"Erro ao conectar ao banco para carregar seções: {e}")
        dict_secoes = {}

    # --- 2. INTERFACE DE CADASTRO ---
    if dict_secoes:
        secao_nome = st.selectbox("Selecione a Seção para Nova Regra", options=list(dict_secoes.keys()))
        cod_sec_selecionado = dict_secoes[secao_nome]
        
        tipo_promo = st.radio("Tipo de Promoção", ["Recorrente (Dias da Semana)", "Data Fixa (Calendário)"], horizontal=True)

        with st.form("confirmar_cadastro"):
            dias_string = ""
            data_fixa = None
            
            if tipo_promo == "Recorrente (Dias da Semana)":
                dias_labels = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
                escolhidos = st.multiselect("Dias da Semana", dias_labels)
                mapa_firebird = {"Domingo":"0","Segunda":"1","Terça":"2","Quarta":"3","Quinta":"4","Sexta":"5","Sábado":"6"}
                dias_string = ",".join([mapa_firebird[d] for d in escolhidos])
            else:
                data_fixa = st.date_input("Data do Calendário", value=datetime.date.today())

            if st.form_submit_button("💾 Salvar Regra de Promoção"):
                if tipo_promo == "Recorrente (Dias da Semana)" and not dias_string:
                    st.error("Selecione pelo menos um dia da semana.")
                else:
                    try:
                        cur.execute("""
                            INSERT INTO REGRAS_PROMOCAO (COD_SEC, DIAS_SEMANA, DATA_FIXA, STATUS) 
                            VALUES (?, ?, ?, 'NORMAL')
                        """, (cod_sec_selecionado, dias_string if dias_string else None, data_fixa))
                        conn.commit()
                        st.success("Regra salva com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar regra: {e}")
    else:
        st.warning("Nenhuma seção encontrada no banco de dados.")

    st.divider()

    # --- 3. LISTAGEM E AÇÕES ---
    try:
        cur.execute("""
            SELECT R.ID, S.NOME_SEC, R.DIAS_SEMANA, R.DATA_FIXA, R.STATUS, R.COD_SEC 
            FROM REGRAS_PROMOCAO R
            JOIN SECAO S ON S.COD_SEC = R.COD_SEC
            ORDER BY R.ID DESC
        """)
        regras = cur.fetchall()

        # CORREÇÃO AQUI: de 'colegas' para 'regras'
        if regras:
            st.subheader("📋 Promoções Ativas e Agendadas")
            
            for r in regras:
                id_regra, nome_sec, dias, data, status, cod_sec = r
                
                with st.expander(f"{'🚀' if status == 'PROMO' else '⏳'} {nome_sec} (ID: {id_regra})"):
                    col_info, col_grid_btn, col_actions = st.columns([2, 1, 1])
                    
                    with col_info:
                        if data:
                            st.write(f"📅 **Data Fixa:** {data.strftime('%d/%m/%Y')}")
                        else:
                            # Tradução visual dos dias para o usuário
                            mapa_nomes = {"0":"Dom","1":"Seg","2":"Ter","3":"Qua","4":"Qui","5":"Sex","6":"Sab"}
                            dias_formatados = ", ".join([mapa_nomes.get(d, d) for d in dias.split(",")])
                            st.write(f"🔁 **Dias:** {dias_formatados}")
                        st.write(f"**Status Atual:** `{status}`")

                    with col_grid_btn:
                        if st.button(f"🔍 Ver Produtos", key=f"grid_{id_regra}"):
                            cur.execute("""
                                SELECT 
                                    CODIGO_BARRA_PRO as "Cód. Barras",
                                    NOME_PRO as "Produto",
                                    PRECO_VAREJO as "Preço Varejo",
                                    PRECO_PROMOCAO as "Preço Promo",
                                    PROMO_ATIVA as "Ativa"
                                FROM PRODUTO 
                                WHERE COD_SEC = ?
                                ORDER BY NOME_PRO
                            """, (cod_sec,))
                            
                            # Criando o DataFrame
                            df_produtos = pd.DataFrame(cur.fetchall(), 
                                                    columns=["Cód. Barras", "Produto", "Preço Varejo", "Preço Promo", "Ativa"])
                            
                            st.write(f"### Itens da Seção: {nome_sec}")
                            
                            # Exibindo o Grid com ajuste de largura de colunas
                            st.dataframe(
                                df_produtos, 
                                use_container_width=True, 
                                hide_index=True,
                                column_config={
                                    "Cód. Barras": st.column_config.TextColumn("Cód. Barras"),
                                    "Produto": st.column_config.TextColumn("Descrição do Produto"),
                                    "Preço Varejo": st.column_config.NumberColumn("Varejo (R$)", format="%.2f"),
                                    "Preço Promo": st.column_config.NumberColumn("Promo (R$)", format="%.2f"),
                                    "Ativa": st.column_config.TextColumn("Status")
                                }
                            )

                    with col_actions:
                        # Botão Ativar/Desativar conforme status atual
                        if status == 'NORMAL':
                            if st.button("🚀 Ativar", key=f"at_{id_regra}", use_container_width=True):
                                cur.execute("EXECUTE PROCEDURE SP_ATIVAR_PROMO_SECAO(?)", (cod_sec,))
                                cur.execute("UPDATE REGRAS_PROMOCAO SET STATUS = 'PROMO' WHERE ID = ?", (id_regra,))
                                conn.commit()
                                st.rerun()
                        else:
                            if st.button("🛑 Desativar", key=f"de_{id_regra}", use_container_width=True, type="primary"):
                                cur.execute("EXECUTE PROCEDURE SP_DESATIVAR_PROMO_SECAO(?)", (cod_sec,))
                                cur.execute("UPDATE REGRAS_PROMOCAO SET STATUS = 'NORMAL' WHERE ID = ?", (id_regra,))
                                conn.commit()
                                st.rerun()
                        
                        # Botão Excluir
                        if st.button("🗑️ Excluir", key=f"del_{id_regra}", use_container_width=True):
                            # Sempre desativa os produtos antes de apagar a regra
                            cur.execute("EXECUTE PROCEDURE SP_DESATIVAR_PROMO_SECAO(?)", (cod_sec,))
                            cur.execute("DELETE FROM REGRAS_PROMOCAO WHERE ID = ?", (id_regra,))
                            conn.commit()
                            st.rerun()

        else:
            st.info("Nenhuma promoção agendada.")
            
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Erro ao carregar promoções: {e}")