# ¿Cambiar la escala modifica la evidencia sobre el orden?

**Pregunta:** ¿Cómo describen la entropía, la complejidad simbólica y la reversión temporal distintos aspectos de una misma secuencia? Usamos el caso de quiebres estructurales sin sustituirlo por un proceso idealizado y conservamos una secuencia constante como control de respuesta conocida. El objetivo es comprender la información y las unidades de cada cálculo. Ninguno de estos resúmenes identifica por sí solo un método ganador ni demuestra un mecanismo físico determinista.

## Objetivos

Calcule entropía con tolerancia original fija, examine frases binarias, compare inversión temporal y repita el ajuste robusto con semilla local. Identifique estimaciones ausentes antes de interpretar una curva.

## Preparación

El entorno incluye la implementación de secuencias, sus bibliotecas numéricas y el estimador robusto con semilla. Todas las entradas del caso trabajado están comprometidas. Un índice representa el mismo intervalo original a lo largo de la lección. Esto importa cuando un bloque reducido reúne varias observaciones: la escala es una operación sobre los datos originales, no una etiqueta añadida a un eje gráfico remuestreado.

{{PINS}}

<!-- code: setup -->

## Datos

El artefacto admitido conserva la identidad y las observaciones utilizadas a continuación.

<!-- code: data -->

## Método

La entropía multiescala de Costa forma una secuencia reducida por escala promediando bloques sin superposición. Una escala de cuatro conserva la media de cada bloque sucesivo de cuatro observaciones y descarta únicamente el bloque terminal incompleto. Luego compara patrones cortos de esa secuencia. El orden es dos: se pregunta si patrones similares de dos observaciones mantienen su similitud al añadir una tercera, excluyendo autocoincidencias de ambos conteos.

<!-- code: entropy -->

La tolerancia se fija como fracción de la desviación original. No se reduce ni amplía por separado con cada secuencia promediada. Recalcularla en cada escala podría hacer que algunas curvas parecieran artificialmente similares y respondería otra pregunta. La salida incluye pares coincidentes y observaciones disponibles, lo que permite interpretar la ausencia de una estimación. Puede faltar porque quedan pocas observaciones o porque ninguna extensión de plantilla coincide; ninguna situación significa complejidad cero.

<!-- code: constant -->

El control constante distingue la imposibilidad de estimar de un cero legítimo. Cuando hay suficientes observaciones, coinciden todos los pares y sus extensiones, por lo que la entropía es cero. En una escala con menos de veinte observaciones, el producto decide no informar la estimación. Este límite es una regla declarada de presentación, no un teorema que garantice resultados fiables en muestras mayores. Incluso una muestra más larga puede tener conteos inestables cerca del umbral de similitud.

La asimetría de reversión temporal examina un momento de tercer orden con rezago. Usamos rezago dos y repetimos la operación invirtiendo las observaciones. El resultado bruto tiene unidades cúbicas; estandarizar antes del cálculo elimina ubicación y escala. Invertir todo el orden intercambia ambos términos y cambia el signo, proporcionando una comprobación estructural exacta. Eso no produce un valor p ni establece que una diferencia finita sea estadísticamente significativa.

<!-- code: reversal -->

Lempel-Ziv adopta otra representación. Los valores superiores a la mediana se convierten en uno y los restantes en cero. La secuencia binaria se analiza mediante frases nuevas. Conservamos el conteo de frases y su normalización asintótica, c(n) log2(n)/n. Una muestra finita puede dar un resultado normalizado superior a uno y no se recorta. La codificación elimina amplitudes y asigna los empates de manera consistente; cambiar el umbral o el alfabeto cambia el método.

<!-- code: symbols -->

Un cambio positivo de unidades y un desplazamiento deberían conservar el orden respecto a la mediana y las estadísticas estandarizadas, salvo precisión numérica. También multiplican la tolerancia original de entropía por el mismo factor que las observaciones. Ejecutamos nuevamente la implementación después de la transformación, sin suponer que todas las magnitudes son adimensionales. El momento bruto de tercer orden no debe compararse entre unidades ignorando su transformación cúbica.

<!-- code: units -->

## Resultados

**Respuesta:** El conteo de frases binarias es 13 y su normalización es 0.3566. La curva de entropía cambia con la escala bajo una tolerancia original fija, mientras el conteo de frases binarias describe otra representación. Invertir el orden cambia el signo del estadístico. Ninguno de estos valores descriptivos certifica por sí solo caos, significancia o precisión de pronóstico.

<!-- code: entropy_plot -->

Las curvas comparten una convención de tolerancia, pero describen secuencias diferentes. La curva del caso puede cambiar al eliminarse detalles de orden mediante promedios; el control constante permanece en cero donde la regla de tamaño permite estimarlo. Los extremos ausentes deben seguir viéndose como ausentes. Una curva descendente no demuestra aleatoriedad, y una curva persistente tampoco prueba información predictiva de largo alcance en este registro finito y no estacionario.

<!-- code: reversal_plot -->

Las barras muestran el cambio de signo ante una transformación conocida del orden. Sus magnitudes corresponden a observaciones estandarizadas y no heredan unidades cúbicas de la fuente. La simetría aparente es una propiedad de la estadística al invertir el orden, no evidencia independiente de una dirección física del tiempo. Interpretar diferencias estadísticas exigiría un experimento de sustitutos u otra prueba correctamente especificada bajo una hipótesis nula concreta.

Respuesta: la tolerancia del caso es {{TOLERANCE}} y permanece fija entre escalas. El control constante tiene entropía cero en escala uno, mientras que su extremo corto no está disponible. Las salidas distinguen un cero calculado de un límite de estimación. El conteo simbólico conserva su valor al convertir unidades positivas y la estadística estandarizada cambia de signo al invertir el orden. Así se observa la utilidad de varios diagnósticos sin confundirlos con estimaciones intercambiables de una única cantidad oculta llamada complejidad.

El ajuste no lineal con semilla responde otra pregunta de reproducibilidad. Su regresión robusta usa un estado aleatorio local sobre los datos logarítmicos expuestos por la biblioteca. Repetir el ajuste no debería depender de sorteos realizados por otro usuario de la función. El pipeline deriva una semilla de la identidad del caso y la semilla suministrada, y conserva la condición de sustitutos antes de emitir un dictamen de caos. La repetibilidad numérica es una propiedad necesaria de la implementación, no prueba de que el proceso observado sea determinista.

<!-- code: seeded -->

### Limitaciones

El caso incluye niveles cambiantes y una cantidad finita de observaciones. Los resúmenes globales pueden combinar varios regímenes en lugar de identificar un mecanismo estable. La simbolización binaria oculta amplitudes y puede ser sensible a empates. Los conteos dependen de orden, tolerancia y longitud. Por ello, el estudio M4 usa estas magnitudes como características de prefijos bajo un protocolo declarado, contrasta su relación con errores posteriores y conserva los resultados negativos sin interpretar cualquier curva irregular como estructura predictiva.

## Resumen

Entropía, frases y momentos con rezago descartan información distinta. Unidades, valores ausentes y condiciones de repetibilidad forman parte del resultado.

### Reproducir

Ejecute las llamadas y ambas figuras en orden. Compruebe tolerancia, cero y extremo ausente del control, conteo de frases y estimaciones robustas repetidas. Las pruebas independientes de conteo de pares y conservación del generador aleatorio cubren propiedades adicionales; la lección aporta un ejemplo interpretable sin reemplazar esas pruebas por un gráfico.

## Referencias

Costa, Goldberger y Peng, DOI 10.1103/PhysRevLett.89.068102. Lempel y Ziv, DOI 10.1109/TIT.1976.1055501. La definición tsfresh especifica el momento con rezago, y nolds documenta los datos de ajuste utilizados por el adaptador con semilla.

[Nolds fitting documentation](https://cschoel.github.io/nolds/nolds.html).
