# Agua de llave: cortes de 2026 en Guadalupe, San Nicolás, Apodaca y Escobedo (fuera de García)

Fecha de consulta: **2026-10-02**. Solo páginas públicas sin login; no se contactó a nadie. Complementa `docs/SADM_AGUA_CONFIABILIDAD.md` (que no se modificó). VERIFICADO = visto en la página citada; SUPUESTO = inferencia. **No altera ningún score.** Script: `scripts/analisis_agua_otro_municipio.py` (sin red; listas transcritas de las páginas). Tablas: `v2/data/agua_otro_municipio_eventos.csv` (7 filas) y `v2/data/agua_otro_municipio_match.csv` (8 colonias).

## 1. Resultado

- **VERIFICADO: no encontré tandeo por calendario fuera de García.** Las notas de 2026 sobre Guadalupe, San Nicolás, Apodaca, Escobedo y Santa Catarina son cortes programados o por falla, de horas. Una búsqueda sin resultados no prueba que no exista; la fuente primaria son las redes de AyD, que no consulté (piden sesión).
- **Fuente nueva más completa: aviso de AyD del 5 de marzo de 2026, con lista por municipio.** Corte de 16:00 del jueves 5 a 00:00 del viernes 6 de marzo (8 h) por cambio de válvulas en Guadalupe. N+ cuenta 226 colonias en Guadalupe, Apodaca y San Nicolás. Milenio (publicada 2026-03-04 20:16, autora Gabriela Tovar) trae las tres listas completas: https://www.milenio.com/estados/anuncian-cortes-agua-apodaca-guadalupe-san-nicolas-colonias-afectadas · N+ (conteo y horario): https://www.nmas.com.mx/nuevo-leon/sociedad/cuando-inician-cortes-agua-nuevo-leon-lista-200-colonias-afectadas-apodaca-guadalupe-san-nicolas/ . El doc previo anotaba «sin coincidencias en Guadalupe ni San Nicolás» y no traía este aviso.
- **VERIFICADO: Apodaca, 2026-09-02, lista completa.** AyD cortó ~12 h (16:00 del 2 a ~04:00 del 3 de septiembre) por mantenimiento de una tubería de 24" en el límite con Escobedo. N+ lista 54 colonias: https://www.nmas.com.mx/nuevo-leon/sociedad/corte-de-agua-apodaca-hoy-54-colonias-municipio-de-nuevo-leon-no-tendran-suministro/ (el doc previo, evento E16, solo extrajo 6 nombres). Confirmación del horario por MVS y Círculo Rojo.
- **VERIFICADO: Escobedo, Santa Catarina y Guadalupe, 2026-04-07**, reparación de tubería general, normalización estimada entre 14:00 y 17:00 (MVS Noticias): https://mvsnoticias.com/nuevo-leon/2026/4/7/estas-son-las-colonias-sin-agua-hoy-de-abril-en-escobedo-guadalupe-santa-catarina-728538.html
- **Sitio oficial:** https://www.sadm.gob.mx/index.jsp responde HTTP 200. Anuncia notificaciones de fallas por servicio en línea y atención 24 h por el 073; no publica una lista de cortes en esa página. Las fechas y listas de este doc son **secundarias**: un medio que cita a AyD.
- Sin nada nuevo para Juárez, Monterrey ni San Pedro en septiembre-octubre de 2026 (no encontré avisos). La nota de Guadalupe más reciente es del 2026-09-26 (Gamavisión): vecinos de Riveras de Guadalupe reportan una fuga de agua potable sin atender desde hace un mes; no es corte de zona.

## 2. Colonias de las 167 con coincidencia (mismo municipio)

Regla: la de `SADM_AGUA_CONFIABILIDAD.md` (nombre normalizado igual = «exacto»; contenido y ≥6 caracteres = «parcial»). Homonimia posible: confirmar contra polígono o dirección.

| Rank base | Colonia | Municipio | Nivel | Nombre en el aviso | Evento | Fecha |
|--:|---|---|---|---|---|---|
| 74 | Prados de La Cieneguita | Apodaca | MEDIO (corte puntual de horas) | Prados De La Cieneguita (exacto) | A02 | 2026-03-05 |
| 79 | Pedregal del Topo Chico [19021_0183] | General Escobedo | MEDIO (corte puntual de horas) | Pedregal del Topo Chico (exacto) | A05 | 2026-04-07 |
| 84 | Pedregal del Topo Chico [19021_0184] | General Escobedo | MEDIO (corte puntual de horas) | Pedregal del Topo Chico (exacto) | A05 | 2026-04-07 |
| 116 | Nuevo San Rafael | Guadalupe | MEDIO (corte puntual de horas) | Nuevo San Rafael (exacto) | San Rafael (parcial) | A01 | 2026-03-05 |
| 167 | Los Fresnos 1Er Sector | Apodaca | MEDIO (corte puntual de horas) | Los Fresnos (exacto) | A02;A04 | 2026-03-05;2026-09-02 |
| 55 | Vicente Guerrero 3 Sector | San Nicolás de los Garza | MEDIO-BAJO | Vicente Guerrero (parcial) | A03 | 2026-03-05 |
| 71 | Eulalio Villarreal | General Escobedo | MEDIO-BAJO | Eulalio Villarreal Ayala (parcial) | A05 | 2026-04-07 |
| 112 | Serranias | General Escobedo | MEDIO-BAJO | Serranía (parcial) | A05 | 2026-04-07 |

- «Vicente Guerrero» (San Nicolás) del aviso del 5 de marzo es un nombre común; la coincidencia con «Vicente Guerrero 3 Sector» (#55) es SUPUESTO. Lo mismo «Eulalio Villarreal Ayala» con #71 y «Serranía» con «Serranias» #112 (probablemente la misma, falta confirmar).
- Dos polígonos «Pedregal del Topo Chico» (19021_0183 y _0184, ranks 79 y 84) entran por el mismo nombre; el aviso no dice cuál sector.
- «Nuevo San Rafael» (Guadalupe, #116) coincide en el corte del 5 de marzo. Es una de las colonias de `docs/SCOUT_TOP30_RETAIL.md` (celda `8848a20191fffff`).
- Solo 8 de las 167 coinciden con 62 + 97 + 70 + 53 nombres de aviso: la mayoría de las colonias de las 167 (marginación media-alta, no fraccionamientos nuevos) no aparece en esos cortes. Es una muestra de eventos, no un registro de continuidad del servicio.

## 3. Cómo leerlo

- Un corte de 8 a 14 h una vez no cambia hábitos de compra de garrafón. La señal de «agua de llave poco confiable» sigue siendo el tandeo de García. SUPUESTO: no hay dato de ventas que lo cuantifique, y no se propone sumar puntos.
- Para la estación importa el riesgo operativo: una colonia con cortes largos necesita cisterna del anfitrión. Las 8 colonias de la tabla quedan como pregunta de campo («¿hay cisterna?»), no como filtro.
- Si Nicolás quiere cerrar el hueco: revisar las páginas de AyD en redes con sesión (no se hizo desde aquí).

## 4. Límites

- Listas transcritas a mano de dos páginas de prensa; omití 5 puntos del aviso de Apodaca que no son colonias (calles, plazas comerciales y una privada numerada).
- El texto de N+ del 2 de septiembre repite «Cosmópolis» y trae un «Jardines» suelto; transcribí 53 nombres de los 54 anunciados.
- No se consultó Facebook, X ni Instagram de AyD.
