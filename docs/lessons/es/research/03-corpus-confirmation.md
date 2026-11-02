# ¿Se conservan las asociaciones en otra partición de series?

**Pregunta:** ¿Qué asociaciones diagnósticas sobreviven al separar descubrimiento y confirmación, y reduce el error un selector basado en características? Examinamos el estudio completo M4 Daily bajo su protocolo fijo. La lección distingue tres evidencias: pruebas de asociación, una regla aprendida de selección y un oráculo que conoce los resultados futuros. Una respuesta fuerte en una de ellas no resuelve automáticamente las otras; un selector desfavorable debe permanecer visible aunque varias pruebas rechacen sus hipótesis nulas.

## Objetivos

Siga las características de prefijos entre particiones separadas, repita la corrección de pruebas dependientes y vuelva a entrenar el selector. Distinga una asociación del error reservado de una regla de selección utilizable.

## Preparación

Instale el entorno fijado y lea el artefacto compacto del corpus ejecutado. Contiene características por serie, medidas de modelos, índices de origen e identidades de partición, no todas las observaciones descargadas. La auditoría externa del productor repuntuó independientemente cada método y origen antes de exportar estas filas. Aquí podemos repetir el análisis estadístico y entrenar el selector con la tabla admitida, sin descargar el corpus bruto ni presentar predicciones almacenadas como ajustes nuevos.

{{PINS}}

<!-- code: setup -->

## Datos

El artefacto admitido conserva la identidad y las observaciones utilizadas a continuación.

<!-- code: corpus -->

## Método

La fuente contiene 4.227 series diarias. Cada secuencia admitida aporta tres bloques separados de catorce pasos; cada ajuste utiliza hasta 1.024 observaciones contiguas anteriores. Las características se calculan una sola vez en el primer origen, de modo que ninguno de esos bloques futuros entra en su cálculo. La estacionalidad diaria del pronóstico es uno. Un diagnóstico semanal separado no cambia ese ajuste. Los duplicados exactos conservan una identidad para inferencia y las exclusiones mantienen sus razones.

<!-- code: prefix -->

La llamada de prefijo muestra el mismo límite informativo sobre un caso comprometido cuyas observaciones originales están disponibles. Sus cuarenta características combinan resúmenes estadísticos con diagnósticos de orden. El ejemplo no reemplaza una fila M4 ni pretende reconstruir el corpus bruto desde la salida compacta. En el estudio, cada vector M4 procede del primer prefijo de su propia serie y su identidad queda vinculada al archivo externo de origen.

El objetivo es log(1 + mejor MASE medio dentro de los ocho métodos fijados). El error de cada método se promedia entre los tres orígenes antes de escoger el mínimo por serie. Es un objetivo optimista porque los resultados futuros identifican al ganador. Describe el error alcanzable entre esas configuraciones, no una predictibilidad inherente. Una característica también puede relacionarse con la construcción del denominador MASE sin revelar un mecanismo físico útil para pronosticar.

<!-- code: associations -->

Las series de descubrimiento y confirmación son distintas por identidad exacta de secuencia. Su asignación es determinista e independiente de las etiquetas de error. Contrastamos todas las características registradas en cada partición y conservamos tamaños de muestra, efectos Kendall y probabilidades. La unidad es una serie; cada origen no se trata como réplica independiente. Promediar orígenes evita ese riesgo inmediato de pseudorreplicación, pero no demuestra independencia entre sectores u orígenes subyacentes de diferentes series.

## Comparación

<!-- code: kendall_reference -->

El cálculo directo de SciPy comprueba una característica escogida explícitamente frente a la implementación Kendall de referencia. Usa filas de confirmación con valores disponibles y el mismo objetivo transformado. El coeficiente mide asociación monótona, no una respuesta causal ajustada. La biblioteca trata los empates. Una probabilidad pequeña debe leerse dentro de toda la familia, en vez de informarse aisladamente porque una característica haya resultado interesante.

<!-- code: correction -->

La corrección BY emplea la cantidad de pruebas y su factor armónico para tratar la dependencia entre hipótesis de características. Comparamos el resultado del producto con la referencia sobre toda la familia de confirmación. Confirmar exige rechazo corregido en ambas particiones y la misma dirección. Escoger primero únicamente probabilidades pequeñas y después corregir definiría un procedimiento diferente y engañoso. Ninguna corrección elimina dependencias no medidas entre fuentes relacionadas del benchmark.

<!-- code: reference_join -->

La comparación exacta del perfil usa un prefijo que termina antes de los tres bloques finales del caso trabajado. Comprueba que el adaptador puede operar dentro del límite temporal sin requerir la secuencia futura completa. El perfil retrospectivo de la app y este cálculo de prefijo cumplen, por tanto, funciones diferentes. Sus coordenadas conservan las unidades originales, pero los vecinos elegibles y las distancias pueden cambiar porque las observaciones disponibles son distintas.

<!-- code: association_plot -->

La figura presenta las primeras doce características en el orden fijo del esquema, no una selección por probabilidades mínimas. Las cuarenta pruebas permanecen en el artefacto y en la tabla corregida de la app. Compare magnitud y dirección entre particiones antes de leer el indicador de rechazo. Coeficientes parecidos aportan evidencia condicional; cambios de signo o efectos que desaparecen deben conservarse como hallazgos y no retirarse de la presentación.

<!-- code: refit_selector -->

El selector se vuelve a entrenar con las filas compactas de descubrimiento. Usa el bosque fijo y medianas calculadas solo allí para valores ausentes. Las etiquetas de confirmación no eligen hiperparámetros, umbrales ni el método constante. Comparamos las medidas reproducidas con las exportadas; la siguiente figura procede de un entrenamiento ejecutado sobre la tabla pública. Repetir esta capa de selección es diferente de reajustar los ocho métodos de pronóstico sobre todo el corpus externo.

## Resultados

**Respuesta:** El selector obtiene MASE medio {{SELECTED}} frente a {{CONSTANT}} de la constante de descubrimiento. Los conteos admitidos, decisiones corregidas y errores de selección confirmatoria responden la pregunta fija del corpus. Reproducir la puntuación verifica el cálculo de la tabla; no convierte el oráculo retrospectivo en una política ni establece superioridad poblacional.

<!-- code: selection_plot -->

La barra del oráculo usa medidas futuras para elegir un ganador distinto en cada serie de confirmación. Es una referencia inferior dentro del conjunto, no una regla desplegable. El método constante se eligió solo en descubrimiento y el bosque decide usando características de prefijos disponibles. Lea ambas reglas sobre las mismas filas y unidades. Un error bajo del oráculo puede coexistir con un selector desfavorable porque las características no identifican fiablemente a los ganadores individuales.

Respuesta: el selector reproducido tiene MASE medio de confirmación {{SELECTED}}, frente a {{CONSTANT}} del método constante elegido en descubrimiento. {{CONFIRMED}} características cumplen la regla declarada de confirmación en dos particiones. Son conclusiones diferentes: una asociación no garantiza mejorar la selección discreta de métodos, y una diferencia observada tampoco establece superioridad poblacional. La fuente tiene 4.227 series y se usan tres orígenes; la muestra estadística corresponde a las series distintas admitidas.

### Limitaciones

El corpus representa una frecuencia de benchmark con identidades de fuente anonimizadas. La deduplicación exacta no reconoce todos los sectores relacionados ni factores latentes compartidos. El conjunto excluye modelos profundos y preentrenados y no puede ordenarlos por implicación. El contexto limitado, los ajustes fijos y el oráculo de error escalado acotan el significado del objetivo. Ningún resultado modifica las características o parámetros del bosque. El otro experimento de veintidós variantes permanece disponible con sus propias identidades y procedencia.

## Resumen

La partición de confirmación evalúa reglas e hipótesis fijadas previamente. Conserve familia corregida completa, exclusiones y resultados negativos junto a cualquier coeficiente favorable.

### Reproducir

<!-- code: checks -->

Ejecute las celdas y compare correcciones de referencia, medidas reproducidas del selector y comprobaciones de partición. Reproducir los pronósticos completos requiere además el TSF licenciado y el evaluador externo; el repositorio documenta su suma de verificación, caché y puntuación independiente de trayectorias. Este cuaderno reproduce la capa inferencial y de selección y declara expresamente ese límite.

## Referencias

Monash M4 Daily, DOI 10.5281/zenodo.4656548. La documentación tsfresh explica la corrección BY para pruebas dependientes. Hyndman y Koehler, DOI 10.1016/j.ijforecast.2006.03.001, examinan el error escalado. STUMPY documenta el perfil exacto de prefijo usado como comparación numérica.

[Dependent-test feature filtering](https://tsfresh.readthedocs.io/en/v0.21.0/text/feature_filtering.html); [Matrix Profile reference](https://doi.org/10.1109/ICDM.2016.0179).
