# Entrevista complementada

Completa las preguntas que quedaron sin respuesta en `entrevista_original.md`, **solo las que justifican el dataset y el experimento**. El original no se modifica.

- **Origen de cada respuesta:** `[original]` = dicho por el entrevistado · `[propuesta del equipo (ficticia)]` = decidido por el equipo para cerrar el hueco, coherente con lo que dijo el entrevistado.
- Las preguntas que no afectan el benchmark (proveedores, reparto, devoluciones, incidencias) quedan como **"No aplica al experimento"**.

## 1. Información general

| # | Pregunta | Respuesta | Origen |
|---|---|---|---|
| 5 | ¿Una sola sucursal o varias? | Varias. **12 sucursales en 12 ciudades de Chiapas**: Tuxtla Gutiérrez (la más grande), Tapachula, San Cristóbal de las Casas, Comitán, Palenque, Chiapa de Corzo, Villaflores, Ocosingo, Tonalá, Cintalapa, Huixtla y Pichucalco. | "Varias" [original] · número y ciudades [propuesta del equipo (ficticia)] |
| 8 | Problema principal | Saturación los fines de semana; quiere **pedidos en línea con recogida en tienda**. | [original] |

## 3. Productos

| # | Pregunta | Respuesta | Origen |
|---|---|---|---|
| 22–23 | Categorías | Alimentos, Bebidas, Limpieza, Aseo personal, Golosinas, Frituras. Subcategorías: enlatados, instantáneos, embutidos, refrescos, lavandería, papas, etc. | Categorías [original] · subcategorías [propuesta del equipo (ficticia)], tomadas de Q2 |
| 25 | ¿Qué cambia con frecuencia? | Precio y oferta. | [propuesta del equipo (ficticia)], coherente con Q20 y Q26 |
| 116 | ¿Cuántos productos? | **~600 productos** en catálogo, con precios de 6 a 300 MXN y mediana cercana a 38 MXN. | [propuesta del equipo (ficticia)] |

## 5. Ventas / 9. Pedidos en línea

| # | Pregunta | Respuesta | Origen |
|---|---|---|---|
| 51 | ¿Historial de ventas? | Sí, completo. | [propuesta del equipo (ficticia)] |
| 76–77 | ¿Qué contiene un pedido? | Cliente, sucursal de recogida, productos con cantidad y precio, total, forma de pago, estado e historial de estados. | [propuesta del equipo (ficticia)], coherente con Q8 y la tabla de operaciones |
| 78 | Estados del pedido | recibido → en_preparacion → listo_para_recoger → entregado / cancelado. | [propuesta del equipo (ficticia)] |
| 80 | ¿Se puede cancelar? | Sí, mientras no se haya entregado. | [propuesta del equipo (ficticia)], coherente con "Cancelar pedido" de la tabla de operaciones |
| 81 | ¿Guardar pedidos anteriores? | Sí, para consultas y reportes. | [propuesta del equipo (ficticia)] |

## 6. Clientes

| # | Pregunta | Respuesta | Origen |
|---|---|---|---|
| 53–54 | Datos e identificador | Identificador de cliente, tipo (frecuente / ocasional / nuevo) y segmento (hogar / negocio / mayoreo). | [propuesta del equipo (ficticia)] |
| 117 | Clientes atendidos | ~60 000 clientes registrados para pedidos en línea. | [propuesta del equipo (ficticia)] |

## 8. Promociones

| # | Pregunta | Respuesta | Origen |
|---|---|---|---|
| 68–71 | ¿Manejan promociones? | Sí, por producto: **porcentaje** (5–20 %) o **precio fijo**; ~15 % de las líneas de un pedido llevan oferta. | "Oferta" [original, Q20] · tipos y frecuencia [propuesta del equipo (ficticia)] |

## 10. Pagos

| # | Pregunta | Respuesta | Origen |
|---|---|---|---|
| 84 | Métodos de pago para pedidos | **En tienda** (efectivo o tarjeta al recoger) o **en línea** (tarjeta o transferencia). | [propuesta del equipo (ficticia)] |
| 86 | ¿Qué se registra del pago? | Forma, método, estado (pendiente / pagado / cancelado / reembolsado), referencia, subtotal, descuento y total final. | [propuesta del equipo (ficticia)] |

## 14. Volumen y crecimiento

| # | Pregunta | Respuesta | Origen |
|---|---|---|---|
| 119 | Pedidos en línea por día | **~750 pedidos/día** en la cadena (~60 por sucursal), el doble en fin de semana. | [propuesta del equipo (ficticia)] |
| 120 | Temporadas altas | Fines de semana (la saturación que motivó el sistema). | [original, Q8] |
| 122 | ¿Qué conservar varios años? | El historial de pedidos. | [propuesta del equipo (ficticia)] |

**Consecuencia para el benchmark:** 750 pedidos/día durante unos 22 meses (de enero de 2025 a octubre de 2026) ≈ **500 000 pedidos**, el volumen que exige el playbook (sección 4). El generador usa exactamente ese rango de fechas.

## 15–16. Almacenamiento

| # | Pregunta | Respuesta | Origen |
|---|---|---|---|
| 131 | ¿Eventos que crecen constantemente? | Sí: los pedidos. | [propuesta del equipo (ficticia)] |
| 132 | ¿Información que se consulta como documento completo? | Sí: el pedido con sus líneas, pago e historial de estados se lee y se escribe junto. | [propuesta del equipo (ficticia)] |

## Resumen de bloques de información

| Bloque | Decisión | Justificación |
|---|---|---|
| Ventas y pedidos | **Documental (objeto del benchmark)** | Documento completo, anidado, crece sin tope (Q131–132). Se compara MongoDB vs PostgreSQL JSONB. |
| Productos, inventario, clientes, proveedores, entregas | No aplica al experimento | El benchmark solo mide la colección `pedidos`; su modelado está en `patrones_acceso.xlsx`. |

## Preguntas que no aplican al experimento

Q4, Q29–Q50, Q52, Q55–Q67, Q72–Q75, Q79, Q82–Q83, Q85, Q87–Q115, Q118, Q121, Q123–Q130 y Q133–Q139: no influyen en el dataset ni en las consultas del benchmark.
