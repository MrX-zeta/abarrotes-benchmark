# Esquema de la colección `pedidos`

Un documento por pedido en línea de la tienda de abarrotes (recogida en sucursal). Lo genera `synthetic_data_generator.py`, y el mismo archivo NDJSON se carga en MongoDB (colección `pedidos`) y en PostgreSQL (`pedidos(id UUID PRIMARY KEY, data JSONB)`).

## Ejemplo (documento real del dataset, semilla 20261031)

```json
{
  "pedido_id": "6e89ec17-8db2-4b7a-a23c-2ca6f55e9419",
  "creado_en": "2026-08-22T18:31:52Z",
  "cliente": { "cliente_id": "CLI-045373", "tipo": "nuevo", "segmento": "negocio" },
  "sucursal": {
    "sucursal_id": "SUC-03",
    "nombre": "Sucursal San Cristóbal",
    "ubicacion": {
      "estado": "Chiapas", "ciudad": "San Cristóbal de las Casas", "cp": "29200",
      "coordenadas": { "lat": 16.737, "lng": -92.6376 }
    }
  },
  "lineas": [
    { "codigo_barras": "7509662692397", "nombre": "Dulces 0412", "categoria": "Golosinas",
      "subcategoria": "Dulces", "marca": "Marca 36", "cantidad": 1, "precio_unitario": 72.68, "oferta": null }
  ],
  "pago": { "forma": "en_linea", "metodo": "tarjeta", "estado": "pagado", "referencia": "55c89635-590a-4b79",
            "subtotal": 240.9, "descuento": 0.0, "total_final": 240.9 },
  "estado": "entregado",
  "historial_estados": [ { "estado": "recibido", "fecha": "2026-08-22T18:31:52Z" } ],
  "metadatos": { "canal": "app", "dispositivo": "movil", "sesion_id": "…",
                 "banderas": { "primera_compra": false, "recoger_express": true } }
}
```

*(Arreglos recortados para el ejemplo.)*

## Campos y distribuciones

| Campo | Tipo | Generación |
|---|---|---|
| `pedido_id` | UUID v4 (texto) | Aleatorio con semilla |
| `creado_en` | ISO-8601 UTC `Z` | 2025-01-01 a 2026-10-31; 08:00–16:00 hora local; sábado y domingo con peso ×2 |
| `cliente.cliente_id` / `tipo` / `segmento` | texto | 60 000 clientes; frecuente 45 % · ocasional 40 % · nuevo 15 %; hogar 80 % · negocio 15 % · mayoreo 5 % |
| `sucursal.*` | objeto (3 niveles) | 12 sucursales en 12 ciudades de Chiapas, con pesos según su tamaño (Tuxtla la mayor) |
| `lineas[]` | arreglo | 1 + Poisson(2), acotado a 8 → **promedio 3.0**; productos sin repetir dentro del pedido |
| `lineas.categoria` | texto | 6 categorías de la entrevista (Q22): Alimentos, Bebidas, Limpieza, Aseo personal, Golosinas, Frituras |
| `lineas.precio_unitario` | número (MXN) | Catálogo de 600 productos; log-normal, mediana 38, σ 0.75, acotada a 6–300 → **36.4 % > 50** |
| `lineas.cantidad` | entero | 1–6, sesgado a 1–2 |
| `lineas.oferta` | objeto o `null` | 15 % de las líneas: porcentaje (5–20 %) o precio fijo (−10 %) |
| `pago.total_final` | número | subtotal − descuento; **sin índice** (campo de orden de Q2) |
| `estado` | texto | entregado 70 % · cancelado 10 % · listo_para_recoger 8 % · en_preparacion 6 % · recibido 6 % |
| `historial_estados[]` | arreglo | Recorrido de estados hasta el estado actual |

## Verificación (`scripts/verify_dataset.py`)

| Propiedad (playbook 4) | Resultado |
|---|---|
| Registros | 500 000 |
| Niveles de anidamiento | 3 (`sucursal.ubicacion.coordenadas`) |
| Promedio de elementos por arreglo (`lineas`) | 2.997 |
| Selectividad del filtro de Q1 | 36.38 % (545 122 de 1 498 550 líneas) |
| Grupos de Q1 | 72 (12 ciudades × 6 categorías) |
| Candidatos de Q2 | 159 208 (31.84 %) |
| Tamaño del NDJSON | 736 MB · SHA-256 `43b43458640bdec09312c39f9fbbf5472ada900d12bd8b23a1e919bef681cc9d` |

## Índices

| Motor | Índice | Equivale a (playbook 2) |
|---|---|---|
| MongoDB | `{pedido_id: 1}` único | índice simple en `order_id` |
| MongoDB | `{creado_en: 1}` | índice simple en `timestamp` |
| PostgreSQL | `PRIMARY KEY (id UUID)` | PK en `id` |
| PostgreSQL | B-Tree `((data->>'creado_en'))` | B-Tree sobre `timestamp` extraído del JSONB |
