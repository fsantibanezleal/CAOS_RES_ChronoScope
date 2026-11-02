# Comparar adaptadores ejecutados con trayectorias archivadas

**Pregunta:** ¿Qué permite concluir un bloque final compartido cuando los adaptadores estadísticos y de árboles se ejecutan ahora, mientras los pronósticos neuronales y preentrenados provienen de artefactos publicados identificables?

## Objetivos

Compararemos métodos sin borrar cómo se obtuvieron sus predicciones. Esta lección ejecuta AutoETS, AutoTheta, AutoARIMA acotado y LightGBM instalados sobre una historia comprometida. También recalcula las medidas de trayectorias neuronales y preentrenadas publicadas utilizando exactamente los mismos objetivos futuros. Son dos fuentes de evidencia diferentes. Ejecutar una medida sobre una predicción archivada produce un cálculo nuevo, pero no constituye un ajuste del modelo ni una inferencia con su checkpoint actual.

Examinaremos por separado error puntual y amplitud, conservaremos los nombres originales e identificaremos limitaciones que una clasificación no resuelve. El experimento no demuestra rendimiento poblacional, independencia respecto de datos de preentrenamiento ni precisión de una política productiva. Su propósito más acotado resulta útil: los competidores comparten serie disponible, horizonte, objetivos finales y escala. Así, una diferencia de error no puede atribuirse a bloques de evaluación diferentes.

## Preparación

Las dependencias directas exactas incluyen las bibliotecas estadísticas y de árboles ejecutadas aquí. Los adaptadores del producto especifican sus configuraciones. Las bibliotecas neuronales y preentrenadas no se instalan silenciosamente ni se sustituyen por modelos menores mientras se ejecuta el cuaderno.

```text
{{PINS}}
```

<!-- code: setup -->

## Datos

Utilizaremos el caso generado con tendencia y estacionalidad para vincular la interpretación con un mecanismo visible. El artefacto comparativo completo contiene quince casos seleccionados, incluidos cuatro extractos reales. Aquí nos concentramos en un prefijo y su bloque final para que cada adaptador recién ejecutado reciba la misma información. Los pronósticos archivados mantienen su procedencia. Los experimentos móviles originales utilizaron diferentes cantidades de orígenes por método: sus agregados no deben sustituirse en esta comparación de bloque común.

<!-- code: data -->

## Método

AutoETS selecciona una especificación de suavizamiento exponencial mediante statsforecast instalado. El adaptador recibe el período estacional de la traza y convierte las columnas de intervalos analíticos en los cuantiles solicitados. Ejecutar el adaptador real importa: una curva manual con el mismo nombre no reproduciría la selección ni la estimación de parámetros de la biblioteca. La medida obtenida corresponde a esta versión y esta historia, en lugar de una implementación ideal no especificada de la familia ETS.

<!-- code: ets -->

AutoTheta también delega el ajuste a la biblioteca de referencia. Es distinto de la función Theta local de historia finita presentada antes. El tratamiento estacional y la selección automáticos pueden modificar el resultado; combinar ambos nombres ocultaría una decisión de implementación. El código imprime la primera predicción para mostrar una salida ejecutada y conserva el origen y horizonte de ETS. Sus parámetros no se eligen después de observar el bloque futuro reservado.

<!-- code: auto_theta -->

AutoARIMA emplea la configuración acotada publicada: búsqueda por pasos, ajuste aproximado y contexto máximo de trescientas sesenta observaciones. Estas decisiones hacen viable el cálculo y forman parte del método evaluado. No representan una búsqueda exhaustiva de órdenes estacionales. Una alternativa más lenta constituiría otro experimento, con tiempo y procedencia propios. Los avisos numéricos, incluidos problemas de convergencia, se capturan e imprimen sin rutas de máquina. Una predicción con ese aviso no demuestra un óptimo exitoso. Cualquier excepción o salida no finita impide completar limpiamente el cuaderno.

<!-- code: arima -->

LightGBM convierte valores pasados en variables de rezago y predice recursivamente mediante MLForecast. La configuración utiliza cien árboles, treinta y una hojas y tasa de aprendizaje de cinco centésimas. Su objetivo puntual no es regresión de cuantiles. El adaptador estima una desviación residual y construye intervalos gaussianos: la incertidumbre añade un supuesto, en lugar de representar una distribución condicional aprendida. Reutilizar predicciones recursivamente puede amplificar errores lejanos incluso cuando el primer paso parece convincente.

<!-- code: tree -->

## Comparación

La primera figura compara trayectorias recién ejecutadas con el mismo bloque observado y una referencia SeasonalNaive recalculada. Todas las líneas comparten escala. Identifique si los modelos discrepan principalmente en tendencia, forma recurrente o amplitud. Un método puede mejorar el promedio y perder precisamente el máximo que importa en planificación. El gráfico ayuda al diagnóstico; las medidas impresas definen una comparación del bloque completo sin inventar una función de costo operativo.

<!-- code: reference_plot -->

La figura hace visible el desacuerdo, pero no identifica una causa única. La diferencia entre un árbol y un modelo estadístico puede depender de rezagos, recursión, longitud del contexto, objetivo de ajuste o selección de parámetros. No debe atribuirse automáticamente a mayor capacidad. El corte temporal compartido elimina un factor de confusión, manteniendo diferencias reales entre métodos. Para aislar cada explicación propuesta se requieren ablaciones controladas y criterios declarados antes de evaluar.

La celda siguiente utiliza trayectorias neuronales y preentrenadas congeladas de la traza publicada. Las adaptaciones directas de NLinear, DLinear y NHITS mantienen nombres distintos de las variantes neuralforecast. Chronos-Bolt, Chronos-2, TimesFM y TiRex conservan la procedencia de sus checkpoints. La función de medidas vuelve a ejecutarse sobre esas predicciones con la misma escala y objetivos finales de los adaptadores actuales. Esta celda no entrena redes, descarga checkpoints ni ejecuta inferencia de modelos fundacionales.

<!-- code: frozen_scores -->

Precisión puntual y amplitud responden preguntas diferentes. La segunda figura enfrenta MASE con amplitud media para los modelos archivados. La tabla conserva cobertura para evitar valorar intervalos estrechos sin revisar sus fallos. La amplitud se expresa en unidades de la serie y no debe agregarse directamente entre conjuntos sin relación. Un punto bajo describe este bloque; no demuestra dominancia a través de múltiples orígenes o funciones de costo.

<!-- code: frozen_plot -->

La dispersión revela intercambios que desaparecen en una clasificación única. Dos métodos con errores puntuales semejantes pueden expresar incertidumbres muy diferentes. Un intervalo amplio puede aumentar la cobertura y resultar poco preciso para decidir. Además, tres cuantiles ofrecen una descripción limitada de la distribución. La pérdida ponderada del artefacto promedia esas tres medidas; no integra una distribución completa ni demuestra que todas las probabilidades de las colas sean confiables.

## Resultados

**Respuesta:** Las trayectorias actuales y archivadas se evalúan contra las mismas 12 observaciones futuras, lo que permite comparar sus medidas en este caso. Aquí se ejecutan cuatro adaptadores estadísticos y de árboles. Las entradas neuronales y preentrenadas son rutas congeladas reevaluadas: la lección no aporta un ajuste nuevo ni evidencia de checkpoints actuales. Sus errores y coberturas siguen siendo útiles si se interpretan junto con esa procedencia.

La cantidad de métodos no equivale a repeticiones experimentales independientes. Sus errores comparten objetivos y, con frecuencia, supuestos. Una comparación general requiere datos declarados, varios orígenes, incertidumbre que considere la dependencia y presupuestos computacionales. Para extractos reales también debe investigarse el posible solapamiento con preentrenamiento. Conservamos esas obligaciones visibles, sin sustituirlas por un promedio favorable obtenido de una colección seleccionada.

## Resumen

Declare qué se ejecutó, qué se leyó, qué configuración produjo cada trayectoria y qué observaciones definen cada medida. Mantenga separadas adaptaciones y bibliotecas de referencia. Compare calidad puntual, amplitud y cobertura, conservando los resultados negativos. La próxima lección evalúa una combinación contextual fija frente a dos ablaciones con los mismos expertos y un criterio declarado antes de examinar los bloques reservados.

## Referencias

- Escalamiento: https://doi.org/10.1016/j.ijforecast.2006.03.001
- Identidad de Theta: https://robjhyndman.com/papers/Theta.pdf
- Suavizamiento y continuación: https://otexts.com/fpp3/holt-winters.html
- Combinaciones por características: https://doi.org/10.1016/j.ijforecast.2019.02.011
- Ensambles dinámicos: https://doi.org/10.1007/s10994-018-05774-y
