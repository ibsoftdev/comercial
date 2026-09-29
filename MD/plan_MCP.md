# Plan de construcción del MCP para Formas Configurables

Documento de trabajo: cómo construir un MCP (*Model Context Protocol*) que automatice el ciclo de creación y evolución de aplicaciones basadas en **Formas Configurables**, partiendo del patrimonio ya existente (módulos construidos + gestión de operaciones de usuario).

**Relacionado:** presentación comercial `portal/` (punto *Hacia dónde ir*), skill Formas Configurables, `docs/MD/cursor_mpc_for_configurable_apps.md` (ibForms).

---

## 1. Objetivo

Disponer de un MCP que permita a agentes de IA (Cursor u otros clientes) operar de forma **determinística** sobre el ciclo:

```text
documento / cambio de negocio
        → Project JSON (Formas Configurables)
        → validar / minimizar
        → registrar / publicar (entorno test)
        → scaffold mínimo (si aplica)
        → pruebas (config + API + E2E) + evidencia
        → informe + gaps de dominio
```

**No es el objetivo** “inventar una app enterprise 100% desde un PDF”. El MCP industrializa lo declarativo (formas, flujos, consultas) y deja explícito lo que requiere dominio (BD, APIs, UI custom).

---

## 2. Principios

| Principio | Implicación |
|-----------|-------------|
| El JSON `Project` es el artefacto central | Toda tool entra o sale de ahí |
| Separar **generar** (LLM) de **operar** (MCP) | El agente razona; el MCP valida, persiste, scaffold, prueba |
| No regenerar pantallas en React | Reutilizar runtime ibForms / DynamicForm; solo shell y gaps |
| Medir éxito por ciclo cerrado | Spec → JSON válido (§13) → registrado → renderiza → pruebas con evidencia |
| Skill = semántica; MCP = ejecución | Una sola fuente de verdad documental; no duplicar reglas solo en el server |

### Por qué este enfoque encaja con un MCP

Con Formas Configurables, cada funcionalidad nueva es principalmente **configuración JSON** interpretada por el mismo motor. Eso implica un solo modelo de ejecución, menos superficie de error del agente, evolución sin redeploy de cada pieza, integración natural al Portal, pruebas sobre un contrato estable y orquestación por tools fijas — frente al modelo tradicional asistido por agente que artesanaliza cada funcionalidad.

---

## 3. Patrimonio de partida (activo del piloto)

Ya existe material suficiente para no construir el MCP sobre un ejemplo inventado:

| Activo | Uso en el plan |
|--------|----------------|
| Skill **Formas Configurables** + `definicion_estructura_project` (§1–13) | Contrato semántico y canónico del `Project` |
| **ibQuoter.React** (cotización / emisión) | Módulo real con formas; candidato a golden files / E2E |
| **ibAPS.React** (órdenes médicas) | Segundo dominio de regresión / cobertura |
| **ibProfile.React** (usuarios, roles, menús) | Piloto recomendado de flujo corto |
| **Gestión de operaciones / admin-trx** (traza) | Evidencia y auditoría tras E2E; gobierno del ciclo |
| Docs HTML por módulo (`docs/html/...`) | Entrada para Fase 2 (spec → JSON) y escenarios de prueba |
| Presentación `portal/` | Narrativa comercial alineada al mismo camino por fases |

### Módulo piloto (decidido)

- **Piloto:** despliegue de un **nuevo producto** en `ibQuoter.React`.
- **Repo MCP:** `/home/ibsoft/trabajo/desarrollo/ibSuiteWEB/forms-mcp` (`https://github.com/ibsoftdev/forms-mcp`), transporte **stdio** (sin Docker en el arranque).

Criterio: JSON/`Project` del producto nuevo, app desplegable en **test**, usuario/rol de prueba con menú del flujo. La gestión de operaciones (admin-trx) sigue como acelerador de evidencia.

---

## 4. Qué se necesita para construirlo

### 4.1 Contrato y modelo

- [ ] Reglas ejecutables (JSON Schema o validador) derivadas de §1–13 — el MCP debe validar **sin** LLM.
- [ ] Convención §13 (`minimize_project`) como paso obligatorio del pipeline.
- [ ] Golden files: al menos un `project_*.json` real del piloto (válido y documentado).

### 4.2 Plataforma MCP

- [ ] Runtime del servidor MCP (Node o Python), empaquetable.
- [ ] Registro de tools con schemas claros de input/output.
- [ ] Uso desde Cursor; diseño compatible con otros clientes MCP.
- [ ] Autenticación hacia API ibForms / BD solo en **dev/test** al inicio.

### 4.3 Entorno de ejecución

- [ ] Entorno test: API que sirve la config, app React del módulo piloto.
- [ ] Credenciales de prueba (usuario, rol, menú).
- [ ] Datos fixture para caminos felices y validaciones negativas.
- [ ] Política explícita: **no producción** hasta que validate + tests sean estables.

### 4.4 Pruebas E2E y evidencia

- [ ] Convenio de selectores estables en DynamicForm (`name` / `data-testid` o mapa attribute → selector).
- [ ] Playwright (recomendado) u equivalente.
- [ ] Almacén de evidencia (carpeta versionada o artefacto CI): informe HTML/Markdown + capturas.
- [ ] (Opcional) Integración con admin-trx / traza para enriquecer la evidencia.

### 4.5 Personas y gobierno

- [ ] Checklist humano de revisión de cobertura (pantallas/campos) antes de registrar en test (Fase 2 → Fase 3).
- [ ] Definición de “gaps de dominio” como salida normal del pipeline (no como fallo oculto).

---

## 5. Mapa de fases

```text
F0 Fundación
 → F1 Configuración
 → F2 Desde documentos
 → F3 Persistencia
 → F4 Scaffold
 → F5 Pruebas y evidencia
 → F6 Orquestación completa
```

Cada fase entrega valor usable y prepara la siguiente. **No** esperar el MCP “completo” para empezar.

---

## 6. Desglose de fases

### Fase 0 — Fundación (1–2 semanas)

**Objetivo:** saber exactamente qué automatizar y con qué contratos.

**Actividades**

- Inventariar entradas/salidas del piloto: specs HTML, `project_*.json`, scripts/API de registro, rutas React, endpoints, docs.
- Documentar el **flujo manual actual** (pasos humanos → resultado en sistema).
- Fijar stack del servidor MCP y accesos a entornos test.
- Elegir módulo piloto y BeanTypes de referencia.
- Alinear con el modelo canónico (`definicion_estructura_project`).

**Criterio de salida**

- Un `Project` de referencia del piloto está descrito de punta a punta: cargar config → renderiza → (opcional) operación visible en gestión de trx.

**Entregables**

- Inventario + diagrama del flujo manual.
- Decisión de stack / auth / entornos.
- Lista de golden files.

---

### Fase 1 — Configuración (MVP útil)

**Lema del esquema:** *Validar y gestionar proyectos.*

**Objetivo:** que cualquier agente pueda auditar y limpiar JSON **sin** inventar reglas en el prompt.

| Tool | Función |
|------|---------|
| `validate_project` | JSON válido vs modelo `Project` |
| `minimize_project` | Aplicar simplificaciones §13 |
| `summarize_project` | Pantallas, attrs, steps, botones, gaps detectables |
| `diff_project` | Comparar versiones / entornos |
| `export_beantype_html` | Plantilla de completado desde JSON |

**Entrada típica:** JSON real de `ibProfile` o `ibQuoter`.

**Criterio de salida**

- Validar / minimizar / resumir / diff sobre golden files del piloto de forma repetible.

**Valor**

- Alto ROI, bajo riesgo; base de todas las fases siguientes.

---

### Fase 2 — Desde documentos

**Lema:** *Spec → configuración.*

**Objetivo:** generar la parte declarativa desde material funcional y listar lo que el JSON no puede inventar.

| Tool | Función |
|------|---------|
| `spec_to_project` | Orquesta el skill Formas Configurables (HTML/PDF/imagen → JSON) |
| `list_backend_gaps` | `FN:`, datasources, `IncludeRouteType`, scripts, endpoints de dominio |

**Piloto sugerido**

- Tomar un HTML de `docs/html` ya existente, generar/completar BeanType y comparar con el JSON productivo vía `diff_project`.

**Criterio de salida**

- De un documento sale: JSON + checklist de gaps + (recomendado) revisión humana de cobertura pantallas/campos antes de registrar.

**Valor**

- Acelerar construcción sin ocultar pendientes de negocio/backend.

---

### Fase 3 — Persistencia

**Lema:** *Registrar y publicar.*

**Objetivo:** cerrar `JSON → tablas / API → el runtime sirve la misma config`, sin pasos manuales opacos.

| Tool | Función |
|------|---------|
| `register_project` | Escribir config (API ibForms o scripts SQL versionados) |
| `export_project` | Leer desde BD/API → JSON |
| `publish_environment` | Sync controlado dev → test (no prod al inicio) |

**Criterio de salida**

- Round-trip: registrar → exportar → `diff_project` sin diferencias semánticas inesperadas.
- La app test renderiza las formas desde la config publicada.

**Valor**

- Lo diseñado en JSON es exactamente lo que el Portal puede ejecutar.

---

### Fase 4 — Scaffold

**Lema:** *Módulo listo para arrancar.*

**Objetivo:** plantilla delgada para el *siguiente* módulo; no reescribir Quoter/APS/Profile.

| Tool | Función |
|------|---------|
| `scaffold_module` | Shell React (rutas, consumo ibForms, enganche a menú) |
| `scaffold_domain_stubs` | Stubs Spring / contratos PL/SQL para gaps |
| `wire_routes` | Mapear BeanTypes / botones a rutas |

**Regla:** no duplicar DynamicForm; reutilizar el motor compartido.

**Criterio de salida**

- Módulo nuevo (o plantilla) arranca, muestra formas desde config registrada e integra al Portal con el mismo patrón que lo disponible.

**Valor**

- Tiempo de puesta en marcha corto y consistencia visual/operativa.

**Nota:** con módulos ya construidos, esta fase puede ir **después** de un primer E2E (Fase 5 parcial) si se prioriza evidencia sobre nuevos módulos.

---

### Fase 5 — Pruebas y evidencia

**Lema:** *Automatizar y documentar.*

**Objetivo:** demostrar que lo generado funciona y dejar evidencia auditable por entrega.

| Tool | Función |
|------|---------|
| `generate_tests` | Casos desde el JSON (campos, cascadas, validaciones, navegación) |
| `run_tests` | Unit de config + contrato API + E2E (Playwright) contra test |
| `export_test_evidence` | Informe (casos, resultado, capturas) ligado a funcionalidades |

#### Capas de prueba

| Capa | Qué cubre |
|------|-----------|
| Unitarias de config | BeanTypes, steps, botones, filtros, §13 |
| Contrato / API | `/loadBean`, `/fireFilter`, paginación, etc. (mock o test) |
| **E2E funcionales** | Navegador: camino de usuario sobre shell + DynamicForm + APIs |
| Evidencia | Informe + capturas; opcionalmente traza vía gestión de operaciones |

#### Escenarios E2E mínimos del piloto

- Smoke por pantalla (render + campos esperados).
- Camino feliz entre steps.
- Validación negativa (obligatorios / formatos).
- Cascadas y filtros.
- Regresión tras un cambio menor de configuración.

#### Rol de la gestión de operaciones (admin-trx)

No es una fase del MCP; es un **acelerador de evidencia y gobierno**:

- Tras E2E, consultar trx/traza del usuario de prueba.
- Tool futura opcional: `fetch_operation_trace` para enriquecer el informe.

**Criterio de salida**

- Cada entrega del piloto deja suite ejecutable + evidencia; la app se comportó como el JSON define.

**Valor**

- Aceptación más rápida, menos riesgo al evolucionar, gobierno del ciclo de vida.

---

### Fase 6 — Orquestación completa

**Lema:** *Documento → aplicación.*

**Objetivo:** componer un flujo de alto nivel solo cuando F1–F5 existan como tools estables.

| Tool (ejemplo) | Función |
|----------------|---------|
| `create_app_from_spec` / `evolve_capability` | Orquesta el pipeline completo |

**Secuencia orquestada**

1. Spec → Project  
2. Validate + minimize  
3. Register (test)  
4. Scaffold (si aplica)  
5. Generate + run tests  
6. Devolver informe + gaps pendientes  

**Criterio de salida**

- Un agente puede invocar una sola tool (o un playbook corto) y obtener aplicación operable en test + evidencia + gaps.

---

## 7. Orden de trabajo recomendado (sprints)

| Sprint | Foco | Módulo ancla |
|--------|------|----------------|
| 1–2 | F0 + F1 (`validate` / `minimize` / `summarize` / `diff`) | JSON real Profile o Quoter |
| 3 | F2 `spec_to_project` sobre HTML documentado | Diff vs JSON actual (130 / 131) |
| 4 | F3 `register` / `export` en test | JSON generado o existente |
| 5 | F5 smoke E2E + evidencia (aunque sea parcial) | Flujo corto + admin-trx |
| 6+ | F4 scaffold plantilla + F6 orquestador | Extensión o dominio chico |

**Evitar:** empezar por el orquestador o por “app completa desde PDF”.

---

## 8. Definición de “MCP útil” (primer hito de negocio)

Un agente, sobre el módulo piloto, puede:

1. Validar y minimizar el `Project`.  
2. Registrarlo en entorno test.  
3. Abrir / ejercer el flujo en la aplicación.  
4. Correr al menos smoke E2E.  
5. Entregar informe de evidencia (+ traza de operación si aplica).

Sin ese ciclo cerrado, hay piezas sueltas; aún no hay MCP de producto.

---

## 9. Riesgos a acotar desde el día 1

| Riesgo | Mitigación |
|--------|------------|
| Expectativa de “100% app desde documento” | Gaps de dominio como salida normal y visible |
| JSON verboso / inconsistente | §13 obligatorio en el MCP, no solo en el skill |
| Publicar a prod demasiado pronto | Solo dev/test hasta validate + tests estables |
| Duplicar lógica del skill en el server | Skill = reglas; MCP = ejecución; una fuente documental |
| Suites E2E frágiles | Convenio de selectores + casos derivados del JSON |

---

## 10. Relación con la presentación comercial (`portal/`)

El punto **Hacia dónde ir** describe el mismo camino:

1. Configuración  
2. Desde documentos  
3. Persistencia  
4. Scaffold  
5. Pruebas y evidencia  
6. Orquestación completa  

Este plan es la **versión de implementación**: tools, criterios, piloto y orden de sprints.

---

## 11. Siguientes pasos inmediatos

1. Revisión humana de cobertura **128 / 127** vs HTML `ap-prototipo` + IncludeRoute Resumen/Resultado AP (front).
2. Actualizar MCP de Cursor a **forms-mcp 0.3.0** (hoy la sesión IDE aún reporta 0.2.1 / solo F1).
3. Implementar validators custom de cupos Parentesco en Cot 127 (1 Padre, 1 Madre, ≤3 hijos ≤18) — **reglas y códigos ya confirmados**; falta cablear validators AP (los de Funerario no aplican tal cual).
4. Más adelante (F3): BD destino, Maven y eventual `export` en `GenerateProjects` (b47).
5. Convenio de selectores E2E sobre DynamicForm (F5; no bloquea F2).

---

## 12. Referencias

- Skill Formas Configurables: `ibForms/.../.cursor/skills/FormasConfigurables/`
- Modelo Project: `definicion_estructura_project.md` (§1–13)
- Conversación / visión MCP: `ibForms/.../docs/MD/cursor_mpc_for_configurable_apps.md`
- Presentación Portal: `comercial/portal/index.html` (sección *Hacia dónde ir*)
- Módulos: `ibQuoter.React`, `ibAPS.React`, `ibProfile.React` (incl. admin-trx / traza)
- Repo MCP: `https://github.com/ibsoftdev/forms-mcp` (local: `ibSuiteWEB/forms-mcp`)

---

## 13. Bitácora

Registro **resumido** de avances por sesión de trabajo. Al arrancar la siguiente, leer el **punto más reciente**.

**Convención:** cada sesión es un **punto** identificado por su **fecha**. Los puntos nuevos se agregan **arriba** (más reciente primero), con fase, avances, pendiente inmediato y commits/refs si aplica.

### Índice de puntos

| Punto | Fecha | Título |
|-------|-------|--------|
| 6 | 2026-09-28 (lunes) | Cot 127 mapeado desde HTML + flujo MCP documentado |
| 5 | 2026-09-28 (lunes) | Emisión 128 completada + `cod_product` 80500 |
| 4 | 2026-09-27 (domingo) | Arranque F2 — Desde documentos |
| 3 | 2026-09-27 (domingo) | Prototipo AP listo como entrada de F2 |
| 2 | 2026-09-26 (sábado) | Cierre de F1: `minimize`, `diff`, `export_beantype_html` |
| 1 | 2026-09-20 (domingo) | Arranque F0/F1 + bootstrap `forms-mcp` |

---

### Flujo resumido: HTML `ap-prototipo` → Project JSON (vía MCP)

Cómo se lleva a cabo el mapeo de la especificación en
`ibQuoter.React/docs/html/ap-prototipo` hacia el JSON de Formas Configurables:

1. **Entrada** — El HTML (pantallas, tablas de campos y secciones `#mapeo-*`) es la especificación.
2. **MCP F2 (`spec_to_project`)** — Lee el HTML y genera un **borrador** de Project JSON (BeanTypes / atributos / estructura). **No** completa solo transformers, filters ni behaviours.
3. **Agente + skill Formas Configurables** — Con el mapeo del HTML y Projects de referencia (Auto 130/131, AP 122, Funerario 125, legacy 123), completa catálogos, validators, behaviours, resumen, botones, etc.
4. **MCP F1** — `validate_project` (JSON válido) → `minimize_project` (§13) → opcional `list_backend_gaps` / `diff_project`.
5. **Salida** — `project_AP_Cot_127.json` / `project_AP_Emi_128.json` en `ibQuoter.React/.../data/`.

En una frase: **el HTML dice qué configurar; el MCP arma y valida el JSON; el agente aplica el mapeo fino que el HTML documenta.**

**Observaciones**

- Hoy el paso 3 **depende de Projects de referencia** (Auto/AP/Funerario) como catálogo *de facto*: el HTML indica qué copiar y el agente fusila bloques reales. Es pragmático en F2, pero acopla el pipeline y es frágil si esos JSON cambian o mezclan producto.
- **Mejora deseada:** biblioteca de **bloques canónicos** genéricos y bien documentados (TipoID, persona + `personExist`, select JDBC, DetailType, IncludeRoute, botones, etc.). El HTML/`spec_to_project` referencia el bloque y solo declara deltas (filtercondition, labels, producto).
- Así docs → JSON se resuelve **sin** abrir 130/122/125 en cada generación; los Projects vivos quedarían como origen histórico para extraer patrones una vez, no como dependencia operativa.

---

### Punto 6 — 2026-09-28 (lunes)

**Título:** Cot 127 mapeado desde HTML + flujo MCP documentado

| | |
|--|--|
| **Fase del plan** | **F2 en curso** (127 completado a nivel catálogos; gaps de negocio puntuales) |
| **Contexto previo** | Punto 5: Emisión 128 lista + `cod_product` 80500; Cot 127 aún con gaps de transformers/behaviours. |

**Decisiones**

- Cot 127 se completa desde `01-cotizacion-ap/index.html` (`#mapeo-titular`, `#mapeo-adicionales`, `#mapeo-resumen`), **sin** editar el JSON “a mano” como sustituto del flujo: fuentes Auto 130 (ID/nombres), AP 122 (fecha/sexo/resumen), Auto Emi 131 (profesión/ocupación/ingreso), Funerario 125 (Parentesco).
- TipoID solo **V/E**; sin behaviours de persona jurídica.
- `ResumenCotAP` se sustituye por **`ResumenCotPersonas`** (`RoutePath=resumen`; sin `FrecuenciaPago` en el Project).
- Parentesco: `CRTB_CD_TABLA = 80032 AND CRTB_DATO1 IN (3,4,5,6)` — **confirmado con negocio (2026-09-28)** (Padre / Madre / Hijo / Hija; máx. 1 Padre, 1 Madre, ≤3 hijos ≤18). Queda pendiente cablear validators custom AP (no reutilizar tal cual Funerario).
- HTML emisión: domiciliación y recaudos pasan a capturas **copiadas** de Auto (no “ref”); título AP en 07a y 08.

**Avances**

- **`project_AP_Cot_127.json` completado** (transformers / filters / behaviours / botones / resumen):
  - F1 local (forms-mcp **0.3.0**): **0 errores / 0 warnings**; minimize −125 claves.
  - Artefactos: `forms-mcp/out/ap-cot-127/` + `data/project_AP_Cot_127.json`.
- Prototipo HTML: domiciliación (`07a/b/c`) y recaudos (`08-recaudos.png`, solo cédula + RIF) alineados a Auto + título AP.
- Documentado en esta bitácora el **flujo resumido HTML → MCP → JSON** (sección arriba).
- Nota operativa: el MCP conectado en Cursor aún reportaba **v0.2.1** (solo F1); validate/minimize de 127 se corrieron con el paquete local **0.3.0**.

**Estado al cerrar**

```text
F0 Fundación     ██ parcial
F1 Configuración ████ completada
F2 Desde docs    ▓▓▓▓▓ 127 + 128 con catálogos; gaps negocio/front  ← AQUÍ
F3…F6            ░░ no iniciado
```

**Pendiente inmediato**

1. Revisión humana 127/128 vs HTML; IncludeRoute Resumen/Resultado emisión (front).
2. Cablear validators de límites Parentesco (reglas ya confirmadas).
3. Alinear MCP IDE a forms-mcp 0.3.0.
4. F3 más adelante.

---

### Punto 5 — 2026-09-28 (lunes)

**Título:** Emisión 128 completada + `cod_product` 80500

| | |
|--|--|
| **Fase del plan** | **F2 en curso** (completar Projects desde docs + catálogos) |
| **Contexto previo** | Punto 4: tools F2 OK; borradores `project_AP_Cot_127` / `project_AP_Emi_128` generados (esqueleto sin transformers). |

**Decisiones**

- Emisión AP se basa en Auto (`project_Auto_Emi_131.json`) para tablas/behaviours; el HTML documenta el mapeo (`#mapeo-auto`).
- Declaración de salud y beneficiarios se toman de legacy `project_AP_Emi_123.json` (sin COVID/fondos/docs mezclados en declaración).
- **`cod_product` / `cd_producto` = `80500`** para Cot 127 y Emi 128 (sustituye 50100).
- No editar a mano como sustituto del flujo: el JSON se completa a partir del HTML + Projects de referencia (Auto/legacy); F1 valida/minimiza.

**Avances**

- HTML `02-emision-ap` enriquecido: sección **Mapeo desde Emisión Auto (131)** (BeanTypes, transformers JDBC, rows static, behaviours, domiciliación/recaudos). Sincronizado staging ↔ `ibQuoter.React/docs/html/`.
- **`project_AP_Emi_128.json` completado** (ya no es borrador vacío):
  - Titular / Pagador / Domiciliación (sin tarjetas) / Documentos Recaudos ← Auto 131
  - Declaración Salud + Beneficiarios ← legacy 123
  - Navegación adaptada al wizard AP; `cd_producto` docs = 80500
  - F1: **0 errores / 1 warning** (`BUTTON_SPARSE`)
  - Artefactos: `forms-mcp/out/ap-emi-128/` + `ibQuoter.React/.../data/project_AP_Emi_128.json`
- **`cod_product` 80500** aplicado en 127 y 128 (JSON + minimized + checklist + prototipo HTML + bitácora). Referencias Auto `250100` intactas.

**Estado al cerrar**

```text
F0 Fundación     ██ parcial
F1 Configuración ████ completada
F2 Desde docs    ▓▓▓▓ 128 con catálogos; 127 gaps pendientes  ← AQUÍ
F3…F6            ░░ no iniciado
```

**Pendiente inmediato**

1. Completar transformers/behaviours de **`project_AP_Cot_127.json`** (mismo enfoque).
2. Revisión humana 128 vs HTML; IncludeRoute Resumen/Resultado AP (front).
3. F3 más adelante.

---

### Punto 4 — 2026-09-27 (domingo)

**Título:** Arranque F2 — Desde documentos

| | |
|--|--|
| **Fase del plan** | **F2 iniciada** (`spec_to_project`, `list_backend_gaps`) |
| **Contexto previo** | Punto 3: prototipo AP documentado; F1 operativa (v0.2.1). Decisión: **avanzar F2 aunque queden preguntas abiertas en Emisión** — van como gaps, no bloquean. |

**Decisiones**

- Entrada de F2: `ibQuoter.React/docs/html/ap-prototipo/` (01 Cotización + 02 Emisión).
- Preguntas abiertas remanentes (persona no registrada, «NA», autocompletado beneficiarios, recaudos que bloquean, carga de archivos, datos inconsistentes entre capturas, HIJA/HIJOS, tomador vs titular) → salida de `list_backend_gaps` / checklist; no detienen el arranque.
- `spec_to_project` produce un **borrador** de Project JSON + gaps a partir del HTML (tablas de campos, notas Formas Configurables, preguntas abiertas). El agente completa con el skill Formas Configurables; F1 valida/minimiza/diff.
- Comparación de referencia: target **`project_AP_Cot_127.json` / `project_AP_Emi_128.json`**; legacy 122/123 solo como patrón.

**Avances (sesión)**

- Bitácora y §11 actualizados: F2 es el trabajo activo.
- Tools F2 en `forms-mcp` v0.3.0: `spec_to_project`, `list_backend_gaps`; smoke OK.
- **`project_AP_Cot_127.json` borrador** (id 127): BeanTypes `APCotTitular`, `APCotAseguradoAdicional`, `ResumenCotAP`. Validate 0 errores. Artefactos en `forms-mcp/out/ap-cot-127/`.
- **`project_AP_Emi_128.json` borrador** (id 128): esqueleto de BeanTypes de emisión. Validate 0 errores. Artefactos en `forms-mcp/out/ap-emi-128/`.
- Continuación (mapeo HTML, completar 128, `cod_product` 80500): ver **Punto 5**.

**Estado al cerrar (fin del arranque)**

```text
F0 Fundación     ██ parcial
F1 Configuración ████ completada
F2 Desde docs    ▓▓▓ borradores 127 + 128  ← AQUÍ (luego Punto 5)
F3…F6            ░░ no iniciado
```

**Pendiente inmediato (al cerrar el arranque)**

1. Completar transformers/behaviours de 127 y 128.
2. Diff/revisión humana vs legacy 122/123 y cobertura HTML.
3. F3 más adelante.

---

### Punto 3 — 2026-09-27 (domingo)

**Título:** Prototipo AP listo como entrada de F2

| | |
|--|--|
| **Fase del plan** | **F1 cerrada**; entrada documental de **F2** en curso (aún sin tools `spec_to_project` / `list_backend_gaps`) |
| **Contexto previo** | Punto 2: F1 completa (v0.2.1), fases reordenadas (F2 = Desde documentos), decisión de documentar un producto nuevo (AP) en lugar de usar Auto como fuente de F2. |

**Decisiones de producto (prototipo AP)**

- Ubicación: `ibQuoter.React/docs/html/ap-prototipo/` (fuente de verdad del prototipo AP para F2).
- **Cotización (01):** paso 0 Selección producto/plan (varios planes a la vez) → titular (sin “Plan a Contratar”) → adicionales opcionales → resultado estilo Resumen Funerario (titular + asegurados arriba; varias tarjetas de plan).
- **Emisión (02):** wizard de 6 pasos. Paso 1 Cliente = mismos campos que Auto `Datos del Titular`. Paso 4 Domiciliación = mismo formulario Auto (Moneda / Instrumento / Banco / Número de cuenta).
- Navegación de cotización alineada a Funerario (`INICIO` / `CONTINUAR`, `ATRÁS` / `GUARDAR COTIZACIÓN`).
- Referencias de diseño tomadas de `docs/html/auto/04-emision-auto` y `docs/html/funerario/05-cotizacion-funerario` donde aplica.

**Avances**

- Documentación HTML referencial completa para Cotización y Emisión AP (tablas de campos, notas Formas Configurables, preguntas abiertas / resueltas).
- Decisiones ya cerradas en cotización: multi-plan, botones tipo Funerario, adicionales opcionales, resultado multi-plan.
- Alineación Emisión paso 1 y 4 con Auto (imágenes de referencia Auto en el doc).
- `forms-mcp` sin cambios de código en esta ventana: sigue en **v0.2.1** (`764d6c3`), tools F1 operativas.

**Estado al cerrar**

```text
F0 Fundación     ██ parcial
F1 Configuración ████ completada
F2 Desde docs    ▓░ entrada documental lista  ← SIGUIENTE (tools)
F3…F6            ░░ no iniciado
```

**Pendiente inmediato (próxima sesión)**

1. Resolver preguntas abiertas que bloquean un JSON limpio (prioridad sugerida):
   - Cotización: planes reales AP; texto del botón del paso 0.
   - Emisión: ¿pagador si titular ≠ pagador?; vigencia/sentido del bloque COVID; pantalla final post-emisión; unificar caso de capturas (10.000/155,34 vs 2.000/194,18).
2. Arrancar **F2** en `forms-mcp`: tool `spec_to_project` (orquesta skill → JSON) y `list_backend_gaps`; generar desde `ap-prototipo`, validar/minimizar con F1, `diff_project` vs `project_AP_Cot_122` / `project_AP_Emi_123`.
3. F3 (después): BD destino, Maven, eventual `export` BD→JSON en b47.

---

### Punto 2 — 2026-09-26 (sábado)

**Título:** Cierre de F1: `minimize`, `diff`, `export_beantype_html`

| | |
|--|--|
| **Fase del plan** | **F1 completada** (criterio de salida cumplido sobre el golden) |
| **Contexto previo** | Punto 1: `ping`, `summarize_project` y `validate_project` operativos (v0.1.1). |

**Decisiones**

- `minimize_project` aplica solo reglas documentadas en §13 de `definicion_estructura_project.md`. El `order` automático (§13.4) se omite únicamente cuando todos los hermanos son 1..n (desactivable con `omitAutoOrder: false`).
- `diff_project` compara por defecto **normalizado** (ambos lados pasan por §13), para que las diferencias de solo defaults no cuenten como cambio.
- Las tools que escriben archivos no sobrescriben salvo `overwrite: true`.
- `ATTR_MINIMAL` en `validate_project` se redefinió: ya no penaliza omisiones §13; solo avisa de un input texto visible sin labels (ni en el attribute ni en su attrGroup).
- Se agrega un **segundo proyecto de verificación**: `project_Auto_Emi_131.json` (Emisión Auto RCV, id 131, 7 BeanTypes, 144 attributes), junto al golden de Cotización 130.
- **Reordenamiento de fases:** ahora **F2 = Desde documentos** (generar el JSON) y **F3 = Persistencia** (registrarlo en dev/test). Sigue el orden natural del producto: primero se construye el JSON y después se carga. Actualizado en §5, §6, §7 y §10 de este plan, en las tarjetas de “Hacia dónde ir” de `docs/portal/index.html` y en la imagen `camino-mcp-fases.png` (respaldo: `camino-mcp-fases.before-reorden.png`). En el Punto 1, “F2/F3” se refiere a la numeración anterior.

**Hallazgos para F3 (Persistencia)** — relevados hoy, para no repetir la investigación:

- ibQuoter **no lee** los `project_*.json`: se importan a Oracle con `ibForms/git/b47/generateProject.sh [<application.yml>] create <json>` (`GenerateProjects`: borra el `id` y lo recrea en tablas `IBCONF_*`). También existe `delete <id>`.
- ibQuoter recarga desde la BD al arrancar y cada **45 s** (Quartz, filtro `appName = ibQuoter-React`); `/reloadProduct` exige JWT.
- **No hay export BD → JSON** (habría que agregarlo a `GenerateProjects`).
- `cod_product` es `@Transient` en `Project.java`: **no se persiste**.
- `project_AutoCasco_Cot_131.json` tiene en realidad `id` 134 (riesgo de pisar el proyecto equivocado).
- `deleteTablesFromProjectId.sql` tiene un `UPDATE IBCONF_ATTRIBUTES SET TRANSFORMER_ID = NULL` **sin `WHERE`**.
- `ibQuoter.React/src/main/resources/application.yml` tiene una API key de OpenRouter en texto plano (rotar y sacar del repo).
- Al momento: Oracle local (`localhost:32118`) apagado y `mvn` fuera del PATH.

**Avances**

- `minimize_project`: sobre el golden quita 72 claves (59 274 → 57 048 bytes): 56 `order` automáticos, 6 `typevisual: "texto"`, 4 `use: "input"`, 3 `filterbyInput: true`, 3 `obligatory: false`. El resultado sigue validando sin errores.
- `diff_project`: reporta BeanTypes, attrRows, attrGroups y attributes agregados / eliminados / movidos / modificados, más cambios de propiedades con valores antes/después.
- `export_beantype_html`: genera la plantilla de completado (formato `plantilla_BeanType.html`) de uno o de todos los BeanTypes; en el golden: AutoCobAmpliaContratante (19 attrs), AutoCobAmpliaAsegurado (20), ResumenAuto (5).
- `validate_project` sobre el golden: 0 errores, **0 warnings** (los 8 `ATTR_MINIMAL` previos eran falsos positivos).
- Proyecto 131: valida sin errores; `minimize_project` quita 146 claves (228 547 → 223 866 bytes), 109 de ellas `order` automáticos. Los 6 `ATTR_MINIMAL` iniciales eran falsos positivos (label definido en el attrGroup); corregido → 0 warnings. Observación: el 131 **no tiene `cod_product`**.
- Prueba de humo repetible `npm run smoke`: levanta el servidor por stdio con el cliente MCP y recorre **ambos proyectos** (summarize, validate, minimize, re-validate, diff normalizado/sin normalizar, diff con cambios inducidos, export HTML), más un diff cruzado 130 vs 131. Todas las verificaciones OK. Las salidas quedan en `forms-mcp/out/<proyecto>/` (ignorado en git).
- Versión **0.2.1**; `ping` lista las 6 tools y los proyectos de verificación.

**Commits en `forms-mcp` (trunk)**

- `5e45e70` — F1 completa: `minimize_project`, `diff_project`, `export_beantype_html`, ajuste de `ATTR_MINIMAL`, smoke test, v0.2.0.
- `764d6c3` — proyecto de verificación 131, `ATTR_MINIMAL` considera labels del attrGroup, smoke multi-proyecto, v0.2.1.

**Estado al cerrar**

```text
F0 Fundación     ██ parcial
F1 Configuración ████ completada
F2 Desde docs    ░░ no iniciado  ← SIGUIENTE
F3…F6            ░░ no iniciado
```

**Pendiente inmediato (próxima sesión)**

1. ~~Commit + `git push` y reiniciar el MCP~~ — hecho: ambos commits en GitHub; `ping` responde v0.2.1 con 6 tools.
2. Arrancar **F2 — Desde documentos** (`spec_to_project`, `list_backend_gaps`) con el **prototipo de Accidentes Personales** creado en esta sesión: `ibQuoter.React/docs/html/ap-prototipo/` (01 Cotización: 3 pantallas; 02 Emisión: wizard de 6 pasos). Cada página trae tablas de campos, notas para Formas Configurables y preguntas abiertas. Al generar: validar/minimizar con F1, revisar gaps y comparar con `project_AP_Cot_122` / `project_AP_Emi_123`.
   - Antes de generar conviene resolver las preguntas abiertas clave: botones de la cotización, pantalla final tras emitir y los datos inconsistentes entre capturas (suma asegurada 10.000 vs 2.000, prima 155,34 vs 194,18).
3. Para F3 (más adelante): elegir BD destino (Oracle local o 192.168.229.137 SEGU), ubicar Maven y decidir si se agrega `export` a `GenerateProjects` en b47.

---

### Punto 1 — 2026-09-20 (domingo)

**Título:** Arranque F0/F1 + bootstrap `forms-mcp`

| | |
|--|--|
| **Fase del plan** | F0 (parcial) + **F1 en curso** |
| **Contexto previo** | Plan escrito en este MD; presentación Portal ya con “Hacia dónde ir” y énfasis en pruebas E2E (sesiones anteriores, fuera del repo MCP). |

**Decisiones**

- Transporte: **stdio** (sin Docker en esta etapa).
- Runtime: **TypeScript / Node**.
- Repo propio: `forms-mcp` en GitHub (`ibsoftdev/forms-mcp`), clone en `ibSuiteWEB/forms-mcp`.
- Piloto: despliegue de producto en **ibQuoter.React**.
- Golden file: `ibQuoter.React/.../data/project_AutoRCV_Cot_130.json` (Cotización Auto RCV, id 130).

**Avances**

- Repo vacío clonado; bootstrap MCP (`ping`, `summarize_project`).
- Cableado Cursor: `~/.cursor/mcp.json` y `forms-mcp/.cursor/mcp.json`.
- `summarize_project` adaptado a formato ibQuoter (`beanTypes` mapa + `attrRows` → `attrGroups` → `attributes`).
- `validate_project` implementado (validación estructural §1–2); corrido sobre el golden → `ok: true`, 0 errors, 8 warnings `ATTR_MINIMAL`.
- `ping` en v0.1.1 reporta tools: `ping`, `summarize_project`, `validate_project`.
- Nota: el catálogo de tools de Cursor a veces no listaba `validate_project` hasta reiniciar el proceso MCP (`pkill` + Reload Window / re-auth).

**Commits en `forms-mcp` (trunk)**

- `9fdc6b6` — bootstrap (stdio, ping, summarize_project).
- `c51bccb` — `validate_project` + fix summarize + lockfile + `.cursor/mcp.json` + docs fixtures.

**Estado al cerrar**

```text
F0 Fundación     ██ parcial
F1 Configuración ██ en curso  ← AQUÍ
F2…F6            ░░ no iniciado
```

**Pendiente inmediato (próxima sesión)**

1. Completar F1: `minimize_project` (§13) y/o `diff_project`.
2. Estabilizar descubrimiento de `validate_project` en Cursor (si vuelve a fallar el catálogo).
3. Más adelante: F2 persistencia o F3 `spec_to_project` (generar JSON desde documentos).

**No hecho aún:** generar JSON desde specs, register en BD/API, scaffold, E2E.

