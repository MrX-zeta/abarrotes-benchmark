# Correcciones y contradicciones del proyecto ficticio

Contradicciones encontradas entre la entrevista (`entrevista_original.md`), la tabla de operaciones (`tabla_operaciones.csv`) y el Excel de patrones de acceso (`patrones_acceso.xlsx`), y cómo se resolvió cada una. **Los originales no se editan.**

| # | Contradicción | Fuentes | Resolución |
|---|---|---|---|
| 1 | La entrevista tiene respuestas solo hasta Q27 (faltan Q23 y Q25) y las tablas de resumen están vacías. | Entrevista | Se completaron las preguntas que justifican el dataset en `entrevista_complementada.md`, marcando su origen. |
| 2 | Q4: el entrevistado dice que "no sabe" qué hace cada empleado. | Entrevista | Se conserva tal cual; no afecta al benchmark. |
| 3 | Q11 dice que el sistema lo usan el dueño y el personal de inventario; Q17 dice que los cajeros consultan ventas. | Entrevista Q11 vs Q17 | Se interpreta que los cajeros son usuarios de consulta de ventas. No afecta al benchmark. |
| 4 | Q3: "de 5 a 20 personas" es un rango demasiado amplio para dimensionar. | Entrevista | No se usa para dimensionar; el volumen se fija con Q119 (complementada). |
| 5 | El CSV tiene 24 operaciones y el Excel 37; 12 están marcadas "(propuesta)", entre ellas **registrar venta**. | CSV vs Excel | Para el benchmark solo se usan los pedidos en línea (Q8, "Registrar pedido en línea" / "Consultar pedidos en línea"), presentes en ambas fuentes. |
| 6 | Los tipos de operación difieren ("Lectura / actualización" en el CSV, "Lectura" en el Excel). | CSV vs Excel | Sin efecto en el benchmark; prevalece el Excel por ser más detallado. |
| 7 | Q18 dice que **no** hace falta saber qué empleado hizo cada operación, pero el Excel guarda `registrado_por`. | Entrevista vs Excel | Prevalece la entrevista: el dataset del benchmark no incluye `registrado_por`. |
| 8 | Q13 dice que solo inventario tiene permisos; OP-013 deja que cajeros y compras actualicen su ubicación. | Entrevista vs Excel | Sin efecto en el benchmark. |
| 9 | El Excel crea `historial_precios` (Q28), pero Q28 está sin responder. | Entrevista vs Excel | Sin efecto en el benchmark. |
| 10 | Los estantes del Excel se llaman `"OP-001-E1"` y `"OP-004-E2"`, el mismo formato que los IDs de operación (probable error de buscar y reemplazar). | Excel | Debería ser un código de estante (p. ej. `P01-E1`). Sin efecto en el benchmark. |
| 11 | El modelo del Excel no tiene los campos ni los 3 niveles que exige el playbook (geo, tier, brand, totals…). | Excel vs playbook | Se diseñó la colección `pedidos` con las propiedades estructurales del playbook (ADR-002). |
| 12 | El ejemplo de pedido del Excel usa fechas con offset `-06:00`. | Excel vs ADR-003 | El dataset guarda las fechas en **UTC con `Z`** para que la comparación de texto sea cronológica en ambos motores (ADR-003, decisión 6). |
