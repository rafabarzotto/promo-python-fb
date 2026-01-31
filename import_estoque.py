import pandas as pd
import unicodedata

def limpar_string_para_latin1(texto):
    if not isinstance(texto, str):
        return ""
    # Remove acentos e caracteres especiais incompatíveis com Latin-1
    nfkd_form = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).encode('ascii', 'ignore').decode('ascii').upper().strip()

def gerar_sql_firebird(arquivo_csv, arquivo_saida):
    # Lendo o CSV
    df = pd.read_csv(arquivo_csv, sep=';', encoding='latin-1', dtype=str)
    
    # Identifica as colunas pela posição para evitar erro com caracteres corrompidos no cabeçalho
    # 0: CODIGO, 1: GTIN, 2: DESCRICAO, 4: PRECO_ATUAL
    cols = df.columns
    comandos_sql = []

    for _, row in df.iterrows():
        # --- TRATAMENTO DOS CAMPOS DO CSV ---
        
        # GTIN com 13 dígitos (completando com zeros)
        gtin_raw = str(row[cols[1]]).strip() if pd.notna(row[cols[1]]) else ""
        if gtin_raw.lower() == 'nan' or gtin_raw == "":
            # Caso o GTIN esteja vazio, usa o código do produto para não ficar nulo
            gtin_final = str(row[cols[0]]).strip().zfill(13)
        else:
            gtin_final = gtin_raw.zfill(13)

        # Descrição (Sem acentos, Maiúscula, Limite de 80 caracteres)
        desc_limpa = limpar_string_para_latin1(row[cols[2]])[:80]
        
        # Preço (Garante ponto decimal)
        preco_raw = str(row[cols[4]]).replace(',', '.') if pd.notna(row[cols[4]]) else "0.00"

        # --- MAPEAMENTO DE DADOS (VALORES FIXOS E VARIÁVEIS) ---
        dados = {
            "COD_PRO":               row[cols[0]],
            "CODIGO_BARRA_PRO":      gtin_final,
            "TP_PRODUTO":            'GERAL',
            "TP_PRODUCAO":           'GERAL',
            "ESTOQUE_MINIMO":        99,
            "NOME_PRO":              desc_limpa,
            "DESC_CUPOM":            desc_limpa,
            "COD_MARC":              1,
            "COD_SEC":               1,
            "COD_GRUP":              1,
            "COD_SGRUP":             1,
            "COD_UNI_ENT":           2,
            "COD_UNI_SAI":           2,
            "PRECO_VAREJO":          preco_raw,
            "PRECO_PROMOCAO":        preco_raw,
            "PRECO_PRAZO":           preco_raw,
            "MARGEM_LUCRO":          0,
            "QUANT_ESTOQ":           9999,
            "DATA_VALIDADE":         '2099-01-01',
            "DIAS_VALIDADE_PRO":     0,
            "CONTROLA_ESTOQUE_PRO":  'N',
            "ATIVO_PRO":             'S'
        }

        # --- MONTAGEM DA QUERY SQL ---
        sql = f"""UPDATE OR INSERT INTO PRODUTO (
    COD_PRO, CODIGO_BARRA_PRO, TP_PRODUTO, TP_PRODUCAO, ESTOQUE_MINIMO, 
    NOME_PRO, DESC_CUPOM, COD_MARC, COD_SEC, COD_GRUP, COD_SGRUP, 
    COD_UNI_ENT, COD_UNI_SAI, PRECO_VAREJO, PRECO_PROMOCAO, PRECO_PRAZO, 
    MARGEM_LUCRO, QUANT_ESTOQ, DATA_VALIDADE, DIAS_VALIDADE_PRO, 
    CONTROLA_ESTOQUE_PRO, ATIVO_PRO
) VALUES (
    {dados['COD_PRO']}, '{dados['CODIGO_BARRA_PRO']}', '{dados['TP_PRODUTO']}', '{dados['TP_PRODUCAO']}', {dados['ESTOQUE_MINIMO']},
    '{dados['NOME_PRO']}', '{dados['DESC_CUPOM']}', {dados['COD_MARC']}, {dados['COD_SEC']}, {dados['COD_GRUP']}, {dados['COD_SGRUP']},
    {dados['COD_UNI_ENT']}, {dados['COD_UNI_SAI']}, {dados['PRECO_VAREJO']}, {dados['PRECO_PROMOCAO']}, {dados['PRECO_PRAZO']},
    {dados['MARGEM_LUCRO']}, {dados['QUANT_ESTOQ']}, '{dados['DATA_VALIDADE']}', {dados['DIAS_VALIDADE_PRO']},
    '{dados['CONTROLA_ESTOQUE_PRO']}', '{dados['ATIVO_PRO']}'
) MATCHING (CODIGO_BARRA_PRO);"""
        
        comandos_sql.append(sql)

    # --- GRAVAÇÃO DO ARQUIVO ---
    with open(arquivo_saida, 'w', encoding='latin-1', errors='replace') as f:
        for comando in comandos_sql:
            f.write(comando + "\n")

    print(f"Sucesso! Arquivo '{arquivo_saida}' gerado com {len(comandos_sql)} linhas.")

# Chamada do script
gerar_sql_firebird('produtos.csv', 'importacao_firebase.sql')