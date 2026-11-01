SELECT data->>'pedido_id' AS pedido_id,
       data->'cliente'->>'cliente_id' AS cliente_id,
       (data->'pago'->>'total_final')::numeric AS total_final
FROM pedidos
WHERE data->>'estado' = 'entregado'
  AND data->>'creado_en' >= '2026-01-01T00:00:00Z'
ORDER BY (data->'pago'->>'total_final')::numeric DESC
LIMIT 1000;
