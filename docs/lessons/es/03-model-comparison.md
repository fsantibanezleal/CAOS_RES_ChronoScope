# Comparar adaptadores ejecutados con trayectorias archivadas

**Nivel:** 3. **Requisitos previos:** Las lecciones anteriores de este tema; arrays NumPy y evaluación temporal. **Tiempo de lectura:** 50 minutos.

**Pregunta:** ¿Cómo se comparan cuatro adaptadores estadísticos y de árboles ajustados ahora, siete referencias neuronales o preentrenadas recién ejecutadas y trayectorias archivadas separadas sobre el mismo bloque sintético de 12 objetivos?

## Objetivos

Compararemos métodos sin borrar cómo se obtuvieron sus predicciones. La lección ejecuta tres fuentes distintas de evidencia sobre la misma historia sintética y 12 objetivos reservados. Primero ajusta los adaptadores instalados AutoETS, AutoTheta, AutoARIMA acotado y LightGBM. Después el entorno de referencia fijado ajusta realmente NLinear, DLinear y NHITS de NeuralForecast y ejecuta los checkpoints fijados de Chronos-Bolt, Chronos-2, TimesFM-2.5 y TiRex-2. Por separado vuelve a puntuar trayectorias conservadas, incluidas adaptaciones directas en torch. Puntuar una predicción archivada produce un cálculo nuevo, no un ajuste nuevo ni una inferencia del checkpoint.

Examinaremos por separado error puntual y amplitud, conservaremos los nombres originales e identificaremos limitaciones que una clasificación no resuelve. El experimento no demuestra rendimiento poblacional, independencia respecto de datos de preentrenamiento ni precisión de una política productiva. Su propósito más acotado resulta útil: los competidores comparten serie disponible, horizonte, objetivos finales y escala. Así, una diferencia de error no puede atribuirse a bloques de evaluación diferentes.

## Preparación

Las dependencias directas exactas identifican el entorno del notebook y sus proveedores estadísticos y de árboles. El entorno Linux de referencia declarado por separado aporta las siete implementaciones neuronales o preentrenadas; sus versiones comprobadas y revisiones de checkpoints se imprimen junto con las trayectorias nuevas. Prepare ese entorno y sus pesos mediante el flujo documentado antes de ejecutar. Ninguna celda instala paquetes ni sustituye modelos menores.

```text
{{PINS}}
```

<!-- code: setup -->

## Datos

El experimento común de adaptadores utiliza el control sintético TRND_seasonal con tendencia y ciclo, desde `data/derived/TRND_seasonal/trace.json`. ChronoScope es su propietario, bajo MIT; el generador con semilla 42 está en `data-pipeline/engine/cases/forecast_cases.py`. History contiene el prefijo disponible, actual el bloque final consecutivo reservado, seasonality vale 12 observaciones y horizon vale 12 predicciones. Las unidades son generadas. Se distinguen las trayectorias conservadas de las llamadas ejecutadas aquí. Referencias identifica paquetes y modelos; este ejemplo no descarta exposición de los modelos preentrenados a datos semejantes.

<!-- code: data -->

## Método

AutoETS selecciona una especificación de suavizamiento exponencial mediante statsforecast instalado. El adaptador recibe el período estacional de la traza y convierte las columnas de intervalos analíticos en los cuantiles solicitados. Ejecutar el adaptador real importa: una curva manual con el mismo nombre no reproduciría la selección ni la estimación de parámetros de la biblioteca. La medida obtenida corresponde a esta versión y esta historia, en lugar de una implementación ideal no especificada de la familia ETS.

<!-- code: ets -->

AutoTheta también delega el ajuste a la biblioteca de referencia. Es distinto de la función Theta local de historia finita presentada antes. El tratamiento estacional y la selección automáticos pueden modificar el resultado; combinar ambos nombres ocultaría una decisión de implementación. El código imprime la primera predicción para mostrar una salida ejecutada y conserva el origen y horizonte de ETS. Sus parámetros no se eligen después de observar el bloque futuro reservado.

<!-- code: auto_theta -->

AutoARIMA emplea la configuración acotada publicada: búsqueda por pasos, ajuste aproximado y contexto máximo de trescientas sesenta observaciones. Estas decisiones hacen viable el cálculo y forman parte del método evaluado. No representan una búsqueda exhaustiva de órdenes estacionales. Una alternativa más lenta constituiría otro experimento, con tiempo y procedencia propios. Los avisos numéricos, incluidos problemas de convergencia, se capturan e imprimen sin rutas de máquina. Una predicción con ese aviso no demuestra un óptimo exitoso. Cualquier excepción o salida no finita impide completar limpiamente el notebook.

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

### Sensibilidad al paso de pronóstico

Sea $y_1,\ldots,y_n$ la historia de ajuste y sea $m$ el rezago estacional declarado. La escala de referencia usa diferencias calculadas íntegramente dentro de esa historia.

$$
s_m=\frac{1}{n-m}\sum_{i=m+1}^{n}|y_i-y_{i-m}|.
$$

Con una escala común para todos los métodos, el error absoluto escalado de un conjunto $G$ de pasos es

$$
E_G(f)=\frac{1}{|G|s_m}\sum_{j\in G}|y_{n+j}-\widehat y_{n+j}^{(f)}|.
$$

El conjunto completo da el MASE del bloque reservado. Divida los pasos en dos grupos iguales después de generar las trayectorias originales para el horizonte fijo. La celda aplica esa operación a cada trayectoria puntual recién ejecutada y a la referencia estacional. Conserva el ajuste, el origen, el horizonte y la escala. Un cambio de orden relativo refleja qué observaciones y posiciones entran en la puntuación. Reajustar en un origen posterior incorporaría información nueva y respondería otra pregunta. Cambiar el horizonte también podría modificar el ajuste del adaptador o la forma de construir su trayectoria.

<!-- code: lead_sensitivity -->

Lea juntas las dos barras de cada método. Las diferencias al final pueden reflejar la recursión, un desacuerdo de tendencia que se acumula o la posición de un máximo difícil. La figura por sí sola no identifica cuál de esas explicaciones corresponde. Revise los pasos exactos en el gráfico anterior de trayectorias antes de atribuirles una causa. Los dos puntajes son dependientes porque las predicciones se emitieron juntas y los objetivos provienen de una serie. Repetir el ejercicio en orígenes con bloques futuros disjuntos aportaría evidencia más sólida. Conserve ambos resultados para cada método, incluso cuando cambie el que obtiene el menor error. Una decisión que actúa solo durante seis pasos puede dar más peso al primer grupo. Declare esa prioridad antes de examinar los puntajes.

### Adapta el análisis a tus propios datos

Elija una serie regularmente espaciada y conserve las marcas temporales, las unidades y los indicadores de valores faltantes. Determine el horizonte a partir de la acción que utilizará el pronóstico. Use la frecuencia de medición para fijar un rezago estacional o declare una escala de un paso cuando falte evidencia de periodicidad. Elija la última fecha de ajuste antes de leer los valores reservados. Guarde la historia contigua completa, los objetivos en orden cronológico y el origen. Compruebe que todos los métodos reciban esa historia y devuelvan el mismo número de pasos en las unidades originales de la variable.

Inspeccione el denominador antes de calcular el MASE. Una recurrencia estacional constante puede dar escala cero. En ese caso informe error absoluto en unidades originales y declare indefinido el error escalado. Omitir esos casos para un solo candidato puede producir una ventaja aparente al cambiar la muestra. Registre las excepciones, los avisos de convergencia y las revisiones de pesos junto a las trayectorias. Si se desconoce el solapamiento con el entrenamiento de un modelo preentrenado, consérvelo como incertidumbre asociada a sus puntajes. Aplique las mismas decisiones a los próximos bloques reservados antes de cambiar el conjunto de métodos. Con ese registro, otro lector puede determinar si una mejora aparente corresponde al método, al diseño de evaluación o a la información disponible en su momento.

Si la variable representa energía por intervalo, sume pronósticos de un bloque de decisión solo después de comprobar la regla de agregación. Sumar cuantiles inferiores marginales generalmente produce un valor distinto al cuantil inferior del total. Para una compra agregada, evalúe la distribución pronosticada del total en bloques históricos definidos para esa decisión.

## Resultados

**Respuesta:** Sobre el mismo bloque sintético de 12 objetivos, AutoARIMA recién ajustado obtiene MASE 0.526274 y Chronos-2 recién ejecutado obtiene 0.532694. AutoARIMA informa un aviso de convergencia, por lo que su puntuación no demuestra haber alcanzado un óptimo. La cobertura nueva de TimesFM-2.5 es 0.833333 en este bloque; no establece cobertura poblacional calibrada. La trayectoria conservada de DLinear directo en torch obtiene MASE 0.378737, mientras la referencia DLinear de NeuralForecast recién ajustada obtiene 2.951097. Estas implementaciones distintas deben mantener identidades separadas. Cuatro adaptadores instalados, siete ajustes o inferencias reales de referencia y trayectorias archivadas puntuadas por separado comparten objetivos y escala, pero tienen distinta procedencia. Este único caso generado no sostiene superioridad general.

La cantidad de métodos no equivale a repeticiones experimentales independientes. Sus errores comparten objetivos y, con frecuencia, supuestos. Una comparación general requiere datos declarados, varios orígenes, incertidumbre que considere la dependencia y presupuestos computacionales. Para extractos reales también debe investigarse el posible solapamiento con preentrenamiento. Conservamos esas obligaciones visibles, sin sustituirlas por un promedio favorable obtenido de una colección seleccionada.

## Resumen

Declare qué se ejecutó, qué se leyó, qué configuración produjo cada trayectoria y qué observaciones definen cada medida. Mantenga separadas adaptaciones y bibliotecas de referencia. Compare calidad puntual, amplitud y cobertura, conservando los resultados negativos. La próxima lección evalúa una combinación contextual fija frente a dos ablaciones con los mismos expertos y un criterio declarado antes de examinar los bloques reservados.

## Referencias

- Escalamiento: https://doi.org/10.1016/j.ijforecast.2006.03.001
- Identidad de Theta: https://robjhyndman.com/papers/Theta.pdf
- Suavizamiento y continuación: https://otexts.com/fpp3/holt-winters.html
- Combinaciones por características: https://doi.org/10.1016/j.ijforecast.2019.02.011
- Ensambles dinámicos: https://doi.org/10.1007/s10994-018-05774-y
