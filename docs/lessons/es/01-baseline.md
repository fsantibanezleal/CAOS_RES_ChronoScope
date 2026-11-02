# Una referencia estacional antes de un pronóstico complejo

**Pregunta:** En el caso comprometido con tendencia y estacionalidad, ¿cómo difieren una estación repetida y Theta de historia finita al pronosticar el mismo bloque no observado?

## Objetivos

Construiremos una referencia que una persona pueda inspeccionar antes de considerar un modelo mayor. Separaremos las observaciones disponibles en el origen de las reservadas para evaluar, ejecutaremos tres métodos reales del producto y compararemos sus errores con una escala histórica común. El ejemplo es generado y no corresponde a ventas de una bodega. Su tendencia y estacionalidad permiten explicar mecanismos, pero no aportan evidencia sobre resultados económicos de una política de inventario.

La diferencia central está entre un pronóstico y el denominador de su evaluación. SeasonalNaive produce una trayectoria particular. MASE divide el error de cualquier método por diferencias estacionales históricas. Estas operaciones emplean ideas relacionadas, pero utilizan observaciones distintas. Un MASE inferior a uno no demuestra, por sí solo, que el método superó la trayectoria SeasonalNaive en el futuro. Evaluaremos ambas predicciones explícitamente para evitar esa conclusión injustificada.

## Preparación

Cree el entorno aislado con el flujo de inicialización de cuadernos del repositorio. Estas dependencias directas exactas identifican el entorno de la lección; el cuaderno nunca instala paquetes durante su ejecución.

```text
{{PINS}}
```

Las importaciones siguientes utilizan la implementación del producto. Ninguna celda copia las ecuaciones de pronóstico.

<!-- code: setup -->

## Datos

La traza comprometida `TRND_seasonal` contiene por separado el prefijo de ajuste y el bloque objetivo final. Cargamos ambos para explicar el experimento, pero entregamos solamente el prefijo a las funciones de pronóstico. El período estacional y el horizonte se leen desde la misma traza. Así conservamos la pregunta vinculada al artefacto real, sin sustituirlo por una simulación elegida por conveniencia. Revise los tamaños impresos antes de interpretar cualquier predicción.

<!-- code: data -->

## Método

SeasonalNaive repite el ciclo observado más reciente. Si el horizonte supera un ciclo, vuelve a repetirlo. No extrapola una tendencia, de modo que ofrece facilidad de inspección y poca variabilidad de estimación. Su costo es un retraso esperable cuando el nivel continúa creciendo. Una persona que planifica puede reconocer esta limitación: se copia un valor de una posición comparable del pasado pese al crecimiento posterior. El primer cálculo muestra esa predicción concreta y no una afirmación de precisión ajustada.

<!-- code: naive -->

Theta combina un nivel suavizado localmente con una contribución de deriva derivada de una tendencia lineal ajustada. El producto utiliza la corrección para historia finita descrita por Hyndman y Billah. Esa corrección importa porque el nivel suavizado ya incorpora parte de la deriva; añadir otra deriva completa la contaría dos veces. La implementación local no ejecuta el ajuste estacional automático ni la selección de AutoTheta. Compartir parte del nombre no convierte ambas implementaciones en equivalentes.

<!-- code: theta -->

Holt agrega al nivel una tendencia actualizada de forma separada. Lo incluimos como una explicación deliberadamente incompleta de esta serie estacional. Una tendencia plausible todavía puede perder los máximos y mínimos recurrentes. Ejecutarlo permite ver por qué los componentes de un modelo deben corresponder a un mecanismo explícito, en vez de elegirse porque el método parece más elaborado que repetir una estación. Conservamos su primera predicción como diagnóstico concreto, aunque la comparación siguiente se concentra en los dos métodos de la pregunta.

<!-- code: holt -->

Para cada método, MAE es el error absoluto futuro medio. MASE divide ese valor por la diferencia estacional absoluta media dentro del prefijo de ajuste. La escala se calcula únicamente con información disponible en el origen. Un ciclo histórico muy regular reduce el denominador y puede producir un MASE grande aunque los errores absolutos parezcan modestos. En cambio, una historia ruidosa puede reducir el error escalado sin mejorar la utilidad operativa del pronóstico. Las unidades y la escala histórica deben acompañar la interpretación.

<!-- code: baseline_scores -->

El gráfico coloca las observaciones históricas finales y ambos pronósticos sobre los mismos ejes. La línea discontinua separa la información disponible para ajustar de la revelada después para evaluar. Observe la continuidad del nivel, la alineación de los máximos estacionales y la separación creciente durante el horizonte. La escala vertical compartida evita confundir diferencias de normalización con diferencias reales de valor. Las observaciones reservadas no se suavizan para facilitar una lectura favorable.

<!-- code: baseline_plot -->

La figura permite entender por qué un pronóstico conserva la forma estacional reciente y, aun así, pierde el nuevo nivel. Theta proyecta una deriva y representa menos detalle del ciclo. Ningún patrón visible demuestra una clasificación universal. Los errores relativos dependen de la serie, del origen y de la longitud del bloque reservado. Los MASE impresos responden este experimento particular con mayor precisión que una valoración de qué línea parece más suave.

## Resultados

**Respuesta:** Los métodos pronostican las mismas 12 observaciones reservadas, pero emplean supuestos distintos sobre repetición estacional y continuidad de la deriva. Compare los MASE impresos para identificar el menor error de este caso. La cantidad de observaciones futuras delimita el alcance y no constituye un tamaño de muestra que respalde una afirmación poblacional. Para demostrar una mejora directa debe evaluarse también la predicción SeasonalNaive sobre esos objetivos.

Los cuantiles gaussianos de los métodos ligeros provienen de la escala residual ajustada y de una regla de ampliación. Ordenar sus columnas no les otorga cobertura condicional. Antes de decidir existencias, compare fallos del intervalo, amplitudes y costos asimétricos de faltantes en varios orígenes operativos. Un bloque generado ayuda a comprender un mecanismo y detectar defectos, pero no demuestra una garantía de nivel de servicio.

## Resumen

Comience con un corte temporal visible, conserve el objetivo exacto y ajuste cada competidor sobre el mismo prefijo. Distinga la escala histórica del error de una predicción de referencia futura. La siguiente lección mueve deliberadamente el origen hacia una estación incompleta: una indexación incorrecta puede cambiar qué componente estacional se pronostica. Podemos resolver esa pregunta de implementación antes de aumentar el tamaño del modelo o el costo de entrenamiento.

## Referencias

- Escalamiento: https://doi.org/10.1016/j.ijforecast.2006.03.001
- Ecuación Theta: https://robjhyndman.com/papers/Theta.pdf
- Continuación estacional: https://otexts.com/fpp3/holt-winters.html
- Combinaciones por características: https://doi.org/10.1016/j.ijforecast.2019.02.011
- Ensambles dinámicos: https://doi.org/10.1007/s10994-018-05774-y
