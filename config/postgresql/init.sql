-- Tabla del benchmark: equivalente a orders(id UUID PRIMARY KEY, data JSONB) del playbook (sección 2).
-- La base se inicializa con --locale=C (ver docker-compose.yml): la comparación de texto es binaria,
-- igual que en MongoDB, y el orden alfabético de las fechas ISO-8601 'Z' coincide con el cronológico.
CREATE TABLE IF NOT EXISTS pedidos (
    id   UUID PRIMARY KEY,
    data JSONB NOT NULL
);
