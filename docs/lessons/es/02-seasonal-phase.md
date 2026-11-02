# Pronosticar después de una estación incompleta

**Pregunta:** Al mover el origen cinco observaciones hacia atrás, ¿HoltWinters continúa la fase estacional correcta y cómo se comparan sus errores por paso con una estación repetida?

## Objetivos

Investigaremos un riesgo concreto de implementación sin asumir que el nombre conocido de un método garantiza un pronóstico correcto. Acortaremos una historia comprometida, construiremos el objetivo correspondiente con las observaciones posteriores al nuevo origen y ejecutaremos HoltWinters aditivo del producto. Compararemos la trayectoria con métodos más simples e inspeccionaremos errores agregados y por paso. El experimento cambia deliberadamente el corte temporal y mantiene fija la secuencia observada subyacente.

Un modelo estacional almacena componentes indexados según su posición dentro del ciclo. Si la historia termina a mitad de ese ciclo, el pronóstico debe continuar desde esa posición. Reiniciar el componente en la primera casilla puede generar una oscilación plausible, pero desfasada. El defecto pasa inadvertido cuando todas las historias de demostración contienen ciclos completos. Por eso retiramos una cantidad fija y declarada de observaciones antes del ajuste, en lugar de escogerla después de observar los resultados.

## Preparación

Utilice el entorno aislado de cuadernos con estas dependencias directas exactas. El código importa las funciones del producto y no define una segunda implementación cuyo comportamiento pueda diferir del utilizado en la aplicación.

```text
{{PINS}}
```

<!-- code: setup -->

## Datos

La traza generada con tendencia y estacionalidad contiene un prefijo histórico y un bloque final reservado. Para el origen anterior, las cinco observaciones históricas finales pasan a ser los primeros objetivos futuros. Los objetivos restantes provienen del bloque reservado original. Esta concatenación conserva el orden cronológico. Ninguna observación recién reservada entra al ajuste. Las medidas del origen anterior no deben compararse como si utilizaran el objetivo original: cambiaron la información disponible, el bloque futuro y la pregunta experimental.

<!-- code: data -->

## Método

El primer ajuste utiliza el prefijo acortado. El segundo emplea la historia original completa y se conserva solamente para distinguir ambos orígenes. En HoltWinters aditivo, nivel, tendencia y componentes estacionales se actualizan conjuntamente mediante rejillas finitas de parámetros. El pronóstico debe elegir la casilla correspondiente a la longitud completa del prefijo más el paso solicitado. El resto impreso indica si la historia acortada termina en un límite de ciclo. Ese valor verifica la condición experimental y no mide la precisión del método.

<!-- code: partial -->

SeasonalNaive proporciona una referencia alineada porque copia el último ciclo observado respecto del nuevo origen. Theta aporta otra comparación con deriva, sin la misma estructura estacional ajustada automáticamente. Ambos deben volver a ajustarse sobre la historia corta. Mantener una predicción entrenada con el prefijo original daría a ese competidor observaciones que el método del origen anterior no pudo conocer. Esta es una fuga temporal que no se evita simplemente compartiendo el bloque objetivo entre los modelos.

<!-- code: phase_baseline -->

La ecuación Theta local corregida sigue siendo un contraste útil aunque su medida no sea el resultado principal. La corrección de historia finita depende de la cantidad de observaciones disponibles: mover el origen también modifica esa contribución. Una revisión limitada a las formas del pronóstico puede ignorar estas dependencias. Ejecutamos nuevamente la implementación con el prefijo original para dejar explícita su información, manteniendo las medidas del origen anterior vinculadas exclusivamente a sus predicciones correspondientes.

<!-- code: theta -->

La evaluación utiliza el prefijo acortado para calcular la escala histórica estacional y el objetivo recién ensamblado para calcular errores futuros. La cobertura es la proporción de objetivos contenidos entre los cuantiles gaussianos inferior y superior. Es una fracción muestral de un bloque y no una garantía probabilística para la observación siguiente. Debe leerse junto con la amplitud: intervalos muy extensos pueden cubrir más objetivos sin orientar una decisión útil. No optimizamos sus parámetros contra los datos reservados.

<!-- code: phase_scores -->

En la primera figura, compare las posiciones de los máximos predichos y observados. Una implementación correcta todavía puede producir errores grandes porque la tendencia o la amplitud estimada resultan imperfectas. A la inversa, un error agregado bajo en una serie casi plana ofrecería poca evidencia sobre la indexación estacional. Este caso tiene estructura visible para inspeccionar la fase. Además, las pruebas independientes del repositorio ejercitan historias cuyas longitudes no son divisibles por el período, evitando depender únicamente de esta inspección visual.

<!-- code: phase_plot -->

Las trayectorias separan alineación de precisión. Continuar las casillas correctas es necesario para el algoritmo declarado, pero no garantiza que su componente estacional siga siendo apropiado en otro régimen. Revise conjuntamente el origen y la oscilación antes de atribuir cualquier discrepancia a la fase. Un cambio de nivel o una deriva imperfecta puede desplazar toda la predicción y mantener intactas sus posiciones estacionales. Esa diferencia motiva inspeccionar los errores individuales de la figura siguiente.

Los errores absolutos por paso conservan las unidades e identifican qué observaciones dominan el promedio. Cada punto corresponde a un error de un origen, no a una estimación promediada sobre numerosos orígenes. Por ello, un máximo puede reflejar un objetivo inusual y no una debilidad general del horizonte. Mostramos la referencia estacional sobre los mismos ejes para observar la mejora relativa directamente. No adjuntamos intervalos de confianza ni pruebas de significancia a esta pequeña comparación determinista.

<!-- code: phase_errors -->

El gráfico muestra si los métodos fallan en las mismas posiciones o intercambian errores a lo largo del bloque. Sus curvas pueden cruzarse: reducir el promedio no implica mejorar cada paso. Esto importa cuando la planificación valora más el servicio inmediato que un pronóstico distante. Esos costos deben declararse antes de escoger una medida ponderada. Aquí asignamos el mismo peso a cada paso y conservamos el MASE de la referencia calculado de forma independiente.

## Resultados

**Respuesta:** HoltWinters obtiene MASE 0,4948 en el origen anterior, frente a 1,0136 de SeasonalNaive. Retirar cinco observaciones produce una estación incompleta que la implementación corregida continúa desde su posición terminal real. Las trayectorias y medidas impresas cuantifican este caso. La curva compara cada paso con SeasonalNaive sobre el mismo objetivo nuevo; no permite ordenar estos métodos mediante medidas del origen original posterior.

Corrección de implementación y calidad empírica son conclusiones separadas. Una prueba de estación incompleta puede refutar una regla de indexación sin afirmar superioridad poblacional. Un error observado puede refutar una expectativa de precisión sin demostrar que la indexación esté equivocada. Conserve ambos tipos de evidencia al diagnosticar un pronóstico y mantenga los resultados desfavorables, en vez de cambiar el origen hasta que gane el método preferido.

## Resumen

Registre la información exacta cada vez que mueva el corte temporal. Construya su objetivo futuro en orden cronológico, vuelva a ajustar todos los competidores y recalcule la escala histórica con ese prefijo. Use historias adversariales con estaciones incompletas para comprobar un algoritmo estacional. Después examine medidas del bloque completo y errores individuales, recordando que un origen no proporciona una estimación poblacional ni una aceptación de despliegue.

## Referencias

- Continuación estacional: https://otexts.com/fpp3/holt-winters.html
- Corrección Theta: https://robjhyndman.com/papers/Theta.pdf
- Escalamiento: https://doi.org/10.1016/j.ijforecast.2006.03.001
- Combinaciones por características: https://doi.org/10.1016/j.ijforecast.2019.02.011
- Ensambles dinámicos: https://doi.org/10.1007/s10994-018-05774-y
