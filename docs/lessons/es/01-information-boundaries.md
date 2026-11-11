# ¿Qué información corresponde a un pronóstico al momento de emitirlo?

**Pregunta:** ¿Por qué el mismo extracto eléctrico puede dar una elección histórica, una clasificación del bloque final y una trayectoria de cobertura diferentes?

## Objetivos

Un tablero puede mostrar un método preferido, una trayectoria para un origen concreto y una estimación de cobertura reciente en la misma pantalla. Las tres cantidades usan observaciones distintas y responden preguntas diferentes. Las reproduciremos siguiendo la información disponible en cada cálculo. El experimento también permite distinguir una exportación didáctica pequeña de una entrega completa del producto.

El caso usa un extracto cronológico del medidor MT_010 de la colección eléctrica de UCI. Sus valores horarios suman las mediciones de cuarto de hora retenidas. Reservamos las últimas 24 observaciones de un extracto de cinco días y usamos observaciones anteriores para la evaluación histórica. La prueba de orígenes móviles, el pronóstico del día reservado y la reproducción paso a paso comparten la fuente y usan orígenes distintos. Ninguna representa un resultado nuevo de planificación para un cliente. Conservaremos sus resultados por separado incluso cuando compartan el nombre de un método.

## Preparación

Use el entorno declarado para los cuadernos. El registro de etapas descubre adaptadores opcionales entre las bibliotecas instaladas. El conjunto disponible puede diferir del conjunto completo publicado. La celda muestra los adaptadores que efectivamente se ejecutan. Este entorno no descarga pesos de modelos. Las versiones fijadas permiten identificar las implementaciones locales y sus bibliotecas de referencia.

```text
{{PINS}}
```

<!-- code: setup -->

## Datos

La ingestión lee una tabla larga con identidad de serie y fecha como claves. Devuelve registros aceptados, rechazados y observaciones marcadas. Una marca distingue una observación sospechosa de una serie ilegible o inadmisible. Un registro aceptado todavía puede contener faltantes conforme a la política de ingreso. Antes de ajustar un modelo hacen falta condiciones adicionales para usar un prefijo contiguo y finito. El extracto de este ejemplo satisface esas condiciones. Se corta en orden temporal y conserva las posiciones originales, de modo que el rezago 24 corresponde a un día.

<!-- code: data -->

El código parte de un registro y fija el horizonte antes de llamar a las funciones de puntuación. La etapa de inferencia reserva el último bloque, ajusta el prefijo anterior y devuelve las predicciones. Los objetivos se entregan a la puntuación y a la exportación. La misma separación se aplica a los diagnósticos que informan una decisión. Un gráfico retrospectivo puede usar la serie completa para explicar lo ocurrido. Un diagnóstico empleado para elegir un pronóstico requiere solo información disponible en el momento de emisión.

## Método

Ejecute las etapas de características y diagnóstico sobre el prefijo de ajuste. La fila de características conserva cantidades como la correlación de rezago uno en una representación compacta. Describe los datos entregados a la etapa y por sí misma no predice la próxima observación. El registro de análisis agrega paneles cuya aplicabilidad varía. Algunos métodos eliminan observaciones no finitas o requieren dependencias opcionales. Un panel con error o motivo de omisión se interpreta como indisponible. La celda imprime las identidades de los paneles para hacer visible esa frontera.

<!-- code: diagnostics -->

Una predicción puntual desde el origen final se compara con el objetivo reservado del mismo paso. Sean $n$ la longitud del prefijo, $h$ el horizonte y $m$ el rezago estacional. La escala se calcula una vez usando solo el prefijo.

$$
s_m=\frac{1}{n-m}\sum_{i=m+1}^{n}|y_i-y_{i-m}|.
$$

El MASE del bloque final para una trayectoria puntual $\widehat y$ es

$$
\operatorname{MASE}=\frac{1}{h s_m}\sum_{j=1}^{h}|y_{n+j}-\widehat y_{n+j}|.
$$

El denominador mide la variación pasada respecto a la recurrencia estacional. Un valor pequeño puede amplificar errores de tamaño absoluto moderado. El código usa la misma escala del prefijo para todas las trayectorias finales y permite compararlas directamente en ese origen. El evaluador histórico usa su propia escala prequential para un conjunto anterior de orígenes. Comparar las clasificaciones permite diagnosticar sensibilidad al diseño de evaluación. La diferencia de puntajes no estima una degradación medida sobre varios bloques independientes.

## Comparación

La referencia del paquete repite la fase del último día y devuelve tres columnas de cuantiles. Su mediana coincide con el valor registrado en la fase correspondiente para estos 24 pasos. La trayectoria Theta proviene de la etapa de inferencia instalada. La banda corresponde a sus cuantiles inferior y superior, y la línea observada se dibuja después del ajuste. Compare los recorridos durante las subidas y caídas del día. Un error medio puede ocultar un máximo desplazado o una respuesta tardía a una caída.

<!-- code: inference -->

La figura siguiente compara los puntajes históricos y del bloque final de SeasonalNaive, SES, Holt, HoltWinters y Theta. El evaluador histórico ajusta orígenes anteriores dentro del prefijo y puntúa allí los bloques posteriores correspondientes. Los adaptadores pueden tener presupuestos históricos distintos, por lo que la figura compara solo estas cinco implementaciones. Para cada una el bloque final contiene un patrón particular de objetivos. Un método con poco error en orígenes anteriores puede encontrar otro nivel diario o una fase distinta en el bloque reservado. Identifique el método con la menor barra de cada evaluación e informe el diseño temporal junto con la clasificación.

<!-- code: scores -->

### Sensibilidad a la ventana de evaluación

Una reproducción separada de un paso se mantiene dentro del mismo prefijo de ajuste. En cada paso el pronosticador predice antes de ver el resultado siguiente. El controlador puede modificar su próximo intervalo después de conocer si el actual cubrió la observación. Ese orden define el significado de un intervalo adaptativo. Las predicciones vecinas siguen siendo dependientes. La tabla histórica y la trayectoria de cobertura también tienen horizontes diferentes, así que este cálculo no establece cobertura para la banda de 24 pasos.

<!-- code: stream -->

La línea discontinua indica el objetivo marginal declarado. Cuando una curva se aproxima al objetivo, observe cuánto dura esa cercanía y qué ocurrió antes. Un intervalo amplio puede obtener cobertura alta. Una puntuación de intervalos adecuada equilibra amplitud y observaciones que quedan fuera. Las trayectorias no cuantifican incertidumbre sobre una fracción de cobertura futura. Permiten ver cuándo responde un controlador a una secuencia de fallos en este prefijo. El adaptador de un paso reajusta el pronóstico con la historia disponible. El tiempo de ese adaptador es distinto del tiempo para actualizar un estimador con estado persistente nativo.

## Resultados

**Respuesta:** La clasificación histórica resume orígenes anteriores dentro de las 96 observaciones disponibles. La clasificación final usa las 24 observaciones reservadas. La cobertura móvil usa actualizaciones de un paso dentro del prefijo. Los valores cambian cuando cambian los orígenes, horizontes y observaciones disponibles. Interprete cada salida con su propia ventana objetivo y denominador.

El selector de entrenamiento de la siguiente celda usa dos historias generadas. Promedia el MASE histórico de cada uno de los mismos cinco pronosticadores en esas historias y registra un método por defecto. No utiliza los objetivos eléctricos ni elige al ganador del día eléctrico. La exportación escribe una trayectoria, un manifiesto, un análisis y una reproducción en un directorio temporal. Registra el costo medido de la llamada de pronóstico de los cinco adaptadores en esa ejecución, sin imprimirlo como resultado reproducible de otra máquina. El manifiesto guarda una ruta y un tamaño en bytes. El índice identifica el manifiesto de cada caso. Se comprueba esa relación antes de retirar el directorio temporal.

<!-- code: export -->

El inventario de una entrega utiliza las mismas relaciones de archivos para todo el producto. Una trayectoria bien formada por sí sola no demuestra que la aplicación tenga cada caso o evidencia declarada. El registro de disponibilidad identifica el resumen criptográfico del catálogo y su versión. El índice admitido conserva el total de casos. Las validaciones de esquema, vinculaciones numéricas y comprobaciones de cohortes completas acompañan al registro. Lea el inventario y sus identidades por separado del pequeño ejercicio de entrenamiento.

<!-- code: readiness -->

### Identifique el origen de un puntaje publicado

La comparación nueva completa tiene una fila eléctrica con el mismo identificador de caso y horizonte. Usa el bloque final de la historia admitida completa. El corte didáctico usa un día anterior, por lo que identificar el caso y el horizonte no basta para establecer que los objetivos coinciden. Compare longitudes y objetivos antes de trasladar un puntaje. El estudio externo de combinaciones agrega otro nivel de identidad. Su índice apunta a una serie concreta y su registro de caso contiene orígenes elegibles con resúmenes de prefijos, escalas, objetivos y trayectorias. Siga una entrada del índice e interprete la forma de la primera trayectoria ValidationMix como observaciones reservadas por niveles de cuantil. El índice compacto permite navegar. El registro de caso aporta lo necesario para examinar un resultado numérico de la serie.

<!-- code: comparison_records -->

El experimento del navegador emplea otra frontera. El grafo lineal congelado recibe un prefijo normalizado de longitud fija y produce doce valores puntuales. El estudio inicial con cresta cambió el estimador puntual. La confirmación conserva el grafo y los puntos y cambia solo los intervalos. Recalcule los estudios retenidos antes de comparar errores normalizados. El verificador independiente comprueba el resumen del grafo, la identidad de configuraciones, la separación de particiones y la aritmética sobre trayectorias retenidas. Este cálculo usa sus salidas guardadas y no reajusta el grafo ni mide otro tiempo de navegador.

<!-- code: browser_calibration -->

En el estudio de cresta, compare primero el MAE puntual con el modelo congelado. Un intervalo más estrecho puede mejorar su puntuación aunque empeore el centro. En la confirmación compare las puntuaciones de intervalos con la misma trayectoria puntual. El grupo de calibración depende de la rugosidad dentro del prefijo observado. Sus radios residuales empíricos se calculan con series separadas de calibración y se puntúan sobre series generadas reservadas. Una puntuación normalizada se expresa respecto a la escala del prefijo. No corresponde a un error en unidades eléctricas, y la prueba sintética no establece la cobertura del medidor del ejemplo.

### Repite la comparación con tus propios datos

Elija un horizonte que corresponda a una acción, como asignar personal para el siguiente turno. Preserve fechas y frecuencia de muestreo, incluidas transiciones de hora legal. Declare el tratamiento de huecos y fechas repetidas antes de ingerir la tabla. Use historias separadas para entrenar un método por defecto cuando estén disponibles. Reserve los bloques finales antes de puntuar. Mantenga el prefijo contiguo y decida si el controlador recibe los objetivos de inmediato o con retraso. Aplique la misma condición a cada método comparado.

Si hay historia suficiente, examine ambos diseños de evaluación sobre varios días reservados sucesivos. Guarde la trayectoria completa de cada día, la revisión del método y sus unidades. Cuando un adaptador no pueda pronosticar un origen, informe el fallo y analice explícitamente los orígenes comunes. Conserve los registros largos disponibles y sus resúmenes versionados, de modo que un lector pueda recuperar las observaciones de cada resultado. Antes de publicar una exportación, compruebe los derechos de redistribución de la serie y revise si las predicciones o diagnósticos por paso revelan valores restringidos.

## Resumen

Identifique primero los orígenes y los conjuntos de información. Elija un puntaje apropiado para el horizonte de decisión, conserve pronósticos y objetivos, y documente las historias de entrenamiento y los métodos disponibles. La trayectoria y el manifiesto permiten inspeccionar estas decisiones. Las comprobaciones de inventario y evidencia determinan si una entrega completa está lista.

## Referencias

- [Fuente eléctrica de UCI](https://doi.org/10.24432/C58C86).
- [Evaluación prequential de Dawid](https://doi.org/10.2307/2981683).
- [Inferencia conforme adaptativa](https://arxiv.org/abs/2106.00170).
- [PreqTS 0.3.0](https://pypi.org/project/preqts/0.3.0/).
