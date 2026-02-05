-- 1. Tabela Pai (Cabeçalho da Promoção)
CREATE TABLE IF NOT EXISTS regras_promocao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mercado_id INT NOT NULL,
    cod_secao INT DEFAULT 0,       -- Com Default 0 para evitar erros
    descricao VARCHAR(150) NOT NULL,
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    dias_semana VARCHAR(50),       -- Ex: "0,1,5" (Dom, Seg, Sex)
    status VARCHAR(20) DEFAULT 'NORMAL', -- 'NORMAL' (aguardando) ou 'PROMO' (aplicado no PDV)
    ativo CHAR(1) DEFAULT 'S',     -- 'S' ou 'N'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    processed_at DATETIME NULL
);

-- 2. Tabela Filha (Itens - Atualizada para Código de Barras)
CREATE TABLE IF NOT EXISTS regras_promocao_itens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_regra INT NOT NULL,
    codigo_barras VARCHAR(20) NOT NULL, -- Importante ser VARCHAR para o EAN
    preco_promo DECIMAL(10,2),
    
    -- Chave Estrangeira com Delete Cascade 
    -- (se apagar a regra, apaga os itens automaticamente)
    FOREIGN KEY (id_regra) REFERENCES regras_promocao(id) ON DELETE CASCADE
);

-- 3. Índices para performance (Opcional, mas recomendado)
CREATE INDEX idx_promo_mercado ON regras_promocao(mercado_id);
CREATE INDEX idx_promo_datas ON regras_promocao(data_inicio, data_fim);
CREATE INDEX idx_itens_gtin ON regras_promocao_itens(codigo_barras);


CREATE TABLE IF NOT EXISTS produtos_cloud (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mercado_id INT NOT NULL,
    codigo_externo VARCHAR(30),
    codigo_barras VARCHAR(20) NOT NULL,
    descricao VARCHAR(100),
    preco_varejo DECIMAL(10,2),
    preco_promocao DECIMAL(10,2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Garante que não duplica o mesmo produto DENTRO do mesmo mercado
    UNIQUE KEY uk_prod_mercado_ean (mercado_id, codigo_barras)
);

-- Índice para busca rápida
CREATE INDEX idx_busca_cloud ON produtos_cloud(descricao);

select * from regras_promocao;
select * from regras_promocao_itens;
SELECT * FROM produtos_cloud;
