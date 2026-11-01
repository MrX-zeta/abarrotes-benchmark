SELECT data->'sucursal'->'ubicacion'->>'ciudad' AS ciudad,
       linea->>'categoria' AS categoria,
       SUM((linea->>'cantidad')::numeric * (linea->>'precio_unitario')::numeric) AS total_revenue,
       AVG((linea->>'cantidad')::numeric * (linea->>'precio_unitario')::numeric) AS avg_revenue,
       COUNT(*) AS count
FROM pedidos, jsonb_array_elements(data->'lineas') AS linea
WHERE (linea->>'precio_unitario')::numeric > 50
GROUP BY 1, 2;
