# ¿Qué formas locales se repiten en el caso con quiebres?

**Pregunta:** ¿Podemos identificar ventanas repetidas sin confundir sus posiciones originales con un eje visual reducido? Esta lección sigue el caso de quiebres estructurales desde sus observaciones completas hasta un perfil matricial, un par de motivos y límites candidatos. La pregunta trata sobre similitud de formas locales. No pregunta si un valor extraño es peligroso, si un límite demuestra un cambio del generador ni si un detector en línea habría podido emitir una alarma en esa posición.

## Objetivos

Conserve el inicio de ventana sobre el eje original, distinga distancia de forma y amplitud, y examine un perfil independiente. Explique por qué solicitar una cantidad de regímenes no equivale a descubrir cambios verdaderos.

## Preparación

Cree un entorno aislado e instale las dependencias exactas que aparecen a continuación. Estas versiones identifican el entorno numérico de las salidas comprometidas. La lección lee el pequeño artefacto admitido y ejecuta sus propios diagnósticos; no descarga el corpus completo ni requiere un checkpoint. Mantenga juntas la secuencia original y sus posiciones al comparar las ventanas calculadas con los datos del gráfico.

{{PINS}}

<!-- code: setup -->

## Datos

El artefacto admitido conserva la identidad y las observaciones utilizadas a continuación.

<!-- code: data -->

## Método

El caso contiene trescientas observaciones originales. Una ventana de veinticuatro observaciones avanza de una en una y produce 277 inicios. Cada ventana se centra y divide por su propia desviación poblacional antes de medir la distancia. Por ello, dos ventanas pueden compartir una forma normalizada aunque sus niveles absolutos sean distintos. Un cambio de nivel no constituye automáticamente una discordancia de forma; aplicar un umbral de amplitud respondería otra pregunta.

<!-- code: profile -->

La comparación excluye coincidencias triviales dentro de un radio de seis inicios. Sin esa exclusión, una ventana podría elegirse a sí misma o escoger una copia desplazada con gran superposición, produciendo una distancia engañosamente pequeña. El par de motivos exige además ventanas separadas. Las discordancias candidatas corresponden a grandes distancias al vecino más cercano, con sus ventanas de consulta separadas entre sí. Este ordenamiento es descriptivo: la distancia no lleva asociada una probabilidad calibrada de falsa alarma.

<!-- code: profile_reference -->

La llamada independiente a la biblioteca expone el mismo perfil exacto de distancias. La concordancia comprueba la extracción del adaptador sobre un caso real del producto; la prueba exhaustiva pequeña del repositorio aporta otro oráculo numérico. La lección no sustituye esa prueba por una afirmación sobre una imagen atractiva. Examine el vector de distancias y los índices enteros cuando evalúe si dos intervalos destacados corresponden realmente a las observaciones esperadas.

<!-- code: sequence -->

FLUSS lee los arcos entre vecinos y construye una curva corregida. El producto solicita tres regímenes candidatos y comunica sus límites internos. Recibe una cantidad, no los puntos de quiebre conocidos del generador. Esta diferencia importa: la cantidad solicitada no debe presentarse como una estimación del número de cambios verdaderos. Los límites usan la secuencia completa, por lo que describen un análisis retrospectivo y no información disponible en un origen anterior de predicción.

Una ventana de doce observaciones permite examinar sensibilidad a la escala local declarada. Es una comparación diagnóstica, no una búsqueda de anotaciones favorables.

<!-- code: sensitivity -->

## Resultados

**Respuesta:** Las ventanas del par de motivos comienzan en 112 y 232 sobre el eje original. FLUSS propone límites en 104 y 239 para los tres regímenes solicitados. Los candidatos describen formas observadas; sus posiciones no establecen rupturas conocidas del generador ni una alarma prospectiva.

<!-- code: pattern_plot -->

El panel superior conserva el eje original y muestra los intervalos de motivos sobre los valores brutos. El panel inferior asigna una distancia a cada inicio de ventana; su último índice es menor que el último índice de la secuencia. Lea el ancho del intervalo antes de asociar una característica del perfil con un punto superior. Un mínimo identifica un vecino elegible cercano; un máximo señala una ventana cuyo mejor vecino disponible resulta relativamente distante bajo la normalización declarada.

Respuesta: las ventanas de veinticuatro observaciones generan 277 posiciones del perfil a partir de 300 observaciones originales. Los registros impresos de motivos y discordancias indican las ubicaciones candidatas de esta ejecución, y la diferencia respecto a la biblioteca comprueba su fuente numérica. Esto permite describir formas repetidas de manera reproducible. No establece que una discordancia haya causado un error de pronóstico ni que FLUSS encuentre todos los cambios de nivel. Otra longitud definiría otros patrones locales y exigiría una comparación descrita por separado.

### Limitaciones

La normalización elimina deliberadamente información de media y escala. Un valor absoluto infrecuente puede tener una coincidencia de forma ordinaria, mientras que un patrón frecuente puede aparecer en un nivel importante para una decisión. Las ventanas casi constantes requieren la convención declarada por la biblioteca. Una secuencia totalmente constante se presenta como no disponible porque no discrimina formas. Las anotaciones y tablas de ventanas de la app conservan esas diferencias sin transformar las posiciones en una precisión aparente.

## Resumen

Una ventana es un intervalo con normalización y exclusión declaradas. Posiciones originales, distancias de referencia y límites retrospectivos permiten examinar la afirmación sobre patrones.

### Reproducir

Ejecute el cuaderno completo en el entorno fijado. Compare los inicios impresos con el artefacto admitido y revise las pruebas de distancias exhaustivas y transición plantada. No sustituya las observaciones originales por una trayectoria diezmada: hacerlo cambiaría las formas locales y las unidades de la longitud de ventana.

## Referencias

Yeh y colaboradores, Matrix Profile I, DOI 10.1109/ICDM.2016.0179. Gharghabi y colaboradores, Matrix Profile VIII, DOI 10.1109/ICDM.2017.21. Los tutoriales STUMPY documentan normalización, exclusión y segmentación candidata.
