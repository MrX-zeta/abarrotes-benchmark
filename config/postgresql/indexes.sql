-- Se ejecuta después de la carga (scripts/load_postgresql.py).
-- B-Tree sobre la fecha extraída del JSONB (playbook sección 2). Se indexa la expresión de texto
-- porque el cast a timestamptz no es IMMUTABLE; Q2 compara contra texto ISO-8601 (ADR-003, decisión 6).
CREATE INDEX IF NOT EXISTS idx_pedidos_creado_en ON pedidos ((data->>'creado_en'));
VACUUM (ANALYZE) pedidos;
