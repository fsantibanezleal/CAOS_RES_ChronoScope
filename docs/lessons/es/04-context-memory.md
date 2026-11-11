# Evaluar si recordar contextos mejora una combinación

**Pregunta:** ¿La regla fija ContextMemory mejora el MASE final medio respecto de una combinación equivalente que utiliza solamente recencia en los quince casos seleccionados?

## Objetivos

Evaluaremos una propuesta de pronóstico con una condición explícita para rechazar su beneficio supuesto. ContextMemory estima pérdidas de expertos en orígenes históricos completos y favorece contextos similares al actual. La hipótesis sostiene que la recurrencia aporta información adicional a la recencia. Ejecutaremos la regla y dos ablaciones, inspeccionaremos pesos, disponibilidad temporal y cambios de unidades, y leeremos el experimento común ya fijado. Conservaremos su resultado agregado desfavorable en lugar de modificar la configuración después de observarlo.

La literatura ya contiene combinaciones dependientes de características y ensambles dinámicos. FFORMA aprende combinaciones mediante una colección de referencia; los ensambles arbitrados estiman competencia de expertos. Aquí se evalúa una construcción específica de memoria dentro de una serie y con pocos datos. No se afirma prioridad sobre la ponderación contextual. Se investiga un mecanismo concreto y reproducible, no la existencia de un sistema de evaluación, un envoltorio de calibración o un nombre favorable para un promedio conocido.

## Preparación

Utilice el entorno aislado definido por las dependencias directas exactas siguientes. Las tres combinaciones importan los mismos expertos. El cuaderno no busca configuraciones después de observar los resultados reservados finales.

```text
{{PINS}}
```

<!-- code: setup -->

## Datos

El caso generado seleccionado permite explicar visualmente el ajuste. El artefacto completo proporciona la comparación agregada declarada sobre quince bloques finales. Cumplen funciones distintas: un caso muestra cómo aparecen los pesos y la colección fija evalúa el criterio medio. Ambos utilizan historias y objetivos comprometidos. La configuración está registrada en el artefacto y en el dossier de investigación. Un resultado decepcionante o un éxito individual conveniente no justifican cambiar silenciosamente el núcleo, los expertos o la colección comparativa.

<!-- code: data -->

## Método

En un máximo de doce orígenes históricos, el método ajusta cinco expertos: SeasonalNaive, SES, Holt, HoltWinters y Theta. Cada objetivo de entrenamiento debe terminar dentro de la historia disponible. El bloque futuro final queda excluido. Cuatro resúmenes describen pendiente normalizada, cambio de nivel, cambio de volatilidad y correlación estacional. Un núcleo gaussiano compara contextos recordados con el actual. La recencia decae con semivida fija de seis orígenes. Son configuraciones de implementación y no estimaciones elegidas a partir de errores finales.

<!-- code: context -->

Compare directamente el último extremo objetivo impreso con la longitud histórica disponible. Se permite igualdad: el último objetivo recordado puede terminar en la observación ya conocida más reciente. Sobrepasar ese extremo constituiría fuga. Los orígenes no equivalen a los extremos de sus objetivos, especialmente con horizontes extensos. Las pruebas ejercitan esa frontera independientemente. Aquí los extremos impresos permiten inspeccionar la restricción sin confundir observaciones futuras cargadas para evaluar con entradas efectivamente entregadas al ajuste.

RecencyMean elimina el núcleo de distancia contextual y conserva expertos, objetivos históricos completos, decaimiento temporal y transformación de pérdidas en pesos. Así permite aislar si la similitud añade valor a la estimación reciente. Comparar ContextMemory solamente con un pronóstico ingenuo no respondería esa pregunta: una mejora podría deberse a combinar expertos y no a recordar contextos. Una ablación útil retira un componente propuesto y mantiene las otras decisiones relevantes del diseño.

<!-- code: recency -->

EqualMean asigna el mismo peso a cada experto y elimina también las preferencias de competencia estimada. Sigue produciendo un pronóstico real con las mismas trayectorias actuales. Los intervalos se combinan con los mismos pesos convexos que los puntos. Cuantiles ordenados y pesos no negativos conservan el orden, pero no demuestran calibración probabilística. Promediar cuantiles marginales no suele producir los cuantiles de una distribución mezcla. Esa distinción matemática limita la interpretación de las bandas combinadas.

<!-- code: uniform -->

Las pérdidas locales se contraen una cuarta parte hacia la estimación de recencia antes de aplicar la transformación exponencial. Un piso uniforme de cinco por ciento mantiene positivos todos los pesos. Estos regularizadores reducen concentración cuando existen pocos contextos informativos, pero también pueden diluir un especialista útil. La primera figura asocia cada peso con su experto en el caso elegido. Explica la regla ajustada y no atribuye causalmente a un experto la responsabilidad del error final.

<!-- code: weight_plot -->

El gráfico permite inspeccionar cuánto modifica realmente el núcleo la asignación por recencia. Barras semejantes indican poca influencia contextual en esta historia. Barras distintas demuestran una decisión diferente, no una decisión mejor. Sus consecuencias requieren objetivos futuros. EqualMean aporta una referencia fija para observar la concentración. Ningún experto se elimina después de conocer su error final: la comparación conserva el conjunto declarado antes de evaluar y mantiene los resultados que podrían resultar inconvenientes.

## Comparación

Evalúe las tres trayectorias recién calculadas sobre el mismo objetivo final y la misma escala estacional. Un MASE menor en este caso aporta evidencia descriptiva, pero un ejemplo favorable no resuelve la hipótesis agregada. La celda imprime los tres resultados, sin seleccionar solamente al ganador. La similitud contextual puede ayudar en un régimen y perjudicar en otro. Si la pregunta se refiere al promedio de una colección fija, deben conservarse ambos resultados individuales.

<!-- code: context_scores -->

Cambiar unidades permite comprobar estructura independientemente de la clasificación. Los resúmenes contextuales y las pérdidas normalizadas se diseñaron para mantener sus pesos ante un cambio positivo de escala y un desplazamiento común. Multiplicar por diez y añadir cien debería conservarlos salvo redondeo numérico. Esta comprobación no mide precisión futura: pregunta si una transformación que mantiene la estructura relativa de la serie altera innecesariamente la regla de combinación propuesta.

<!-- code: affine -->

## Evidencia

El criterio primario declarado es el MASE medio sobre los quince bloques finales comunes. ContextMemory debe mejorar RecencyMean para respaldar el beneficio contextual en este experimento. La figura final lee los agregados ya persistidos, incluidos casos desfavorables, sin reajustar ni seleccionar parámetros. Hay solamente un origen por serie seleccionada: no permite concluir significancia ni generalización poblacional. Sin embargo, sí permite rechazar una mejora agregada afirmada sobre esta colección concreta.

<!-- code: proposal_plot -->

Las barras muestran una diferencia pequeña entre las variantes contextual y de recencia, y una separación mayor respecto de EqualMean. Como la media contextual resulta ligeramente superior, el experimento no respalda ese componente en el criterio declarado. Redondear a dos decimales ocultaría el resultado; las cuatro cifras impresas lo conservan. Una comparación fallida sigue siendo evidencia y debe limitar la afirmación del manuscrito, en vez de provocar ajustes no declarados contra el conjunto reservado.

### Sensibilidad entre los casos seleccionados

En un origen de consulta, sea $u$ el contexto estandarizado, $u_i$ el contexto de una memoria completada, $a_i$ su antigüedad en orígenes almacenados y $b$ el ancho derivado de las distancias a los contextos disponibles. El peso relativo de su pérdida es

$$
k_i=2^{-a_i/6}\exp\!\left(-\frac{\|u-u_i\|^2}{2b^2}\right).
$$

Sea $L_j$ la pérdida resultante del experto $j$, después de contraerla hacia la estimación por recencia. Con temperatura $T=1$ y piso uniforme $\eta=.05$, el peso final es

$$
w_j=(1-\eta)\frac{\exp[-(L_j-\min_k L_k)/T]}{\sum_r\exp[-(L_r-\min_k L_k)/T]}+\frac{\eta}{5}.
$$

Restar la pérdida mínima deja la mayor exponencial en uno y mejora la estabilidad numérica. La ablación por recencia conserva la transformación de pérdidas y el piso, con el núcleo contextual fijado en uno. El ajuste requiere suficientes memorias completadas para estimar una pérdida local interpretable. Un contexto cercano puede pesar poco si es antiguo. Uno distante pero reciente puede conservar influencia cuando todas las distancias observadas son grandes. Los pesos pueden cambiar aunque el pronóstico combinado apenas varíe, porque distintos expertos a veces predicen trayectorias muy similares.

La siguiente figura empareja los dos puntajes dentro de cada caso. Una barra negativa significa que ContextMemory obtuvo menor MASE en ese caso. La media refleja magnitudes: algunas pérdidas grandes pueden contrarrestar mejoras pequeñas más frecuentes. La mediana y los conteos por dirección describen otras propiedades de los mismos quince casos. Su orden en el gráfico sigue el inventario publicado y carece de interpretación temporal.

<!-- code: case_differences -->

Estas comparaciones reutilizan los resultados reservados. Sirven para diagnosticar la variación del experimento fijo y no eligen parámetros nuevos. Eliminar un caso adverso por tener una barra grande cambiaría silenciosamente el criterio. Un ensayo futuro puede declarar de antemano grupos de mecanismos y tamaños de muestra, con la serie como unidad de remuestreo si contribuye varios orígenes. La sensibilidad de la media histórica a la composición de los casos justifica conservar tanto las trayectorias emparejadas como la procedencia de los datos.

### Aplica la comparación a tus propios datos

Parta de observaciones contiguas y un período estacional declarado. Elija el horizonte y use los mismos cinco expertos en todas las ablaciones. En cada origen de evaluación, admita solo memorias cuyos objetivos completos ya se observaron. Guarde el origen, el extremo, el contexto y los puntajes de expertos de cada memoria antes de calcular los pesos. Si combina historias de tiendas o instrumentos distintos, preserve cada identidad y escala. Una escala MASE común dentro de cada caso permite obtener una diferencia emparejada adimensional. Los anchos absolutos de intervalos con unidades incompatibles requieren otro tratamiento.

Reserve un conjunto final de orígenes antes de explorar temperaturas, anchos o pisos alternativos. Si ajusta un parámetro, selecciónelo sobre bloques históricos completos dentro del prefijo de ajuste y evalúelo una vez sobre los objetivos reservados. Registre si el control por recencia participa en la selección. La pregunta concreta es cuánto aporta el cálculo contextual adicional con trayectorias y evaluación fijas. Conserve la referencia uniforme para mostrar por separado el efecto de estimar preferencias entre expertos.

## Resultados

**Respuesta:** ContextMemory obtiene MASE medio 1,4504 y RecencyMean 1,4489. La regla contextual falla su criterio declarado de error medio en esta colección. EqualMean obtiene 1,8970. Estimar pérdidas recientes ayudó frente al promedio uniforme en estos casos, pero el núcleo contextual adicional no mejoró la comparación primaria. Las cifras conservan la precisión de la salida computada.

Estos valores no establecen equivalencia ni demuestran que ponderar contextos nunca pueda ayudar. Identifican un experimento fijo sin éxito. Un seguimiento debe declarar datos más amplios, varios orígenes, incertidumbre que considere dependencia y costos computacionales antes de ejecutarse. Modificar parámetros define otro experimento y no debe sobrescribir este. Los orígenes empleados para estimar pesos aportan entrenamiento, no repeticiones independientes adicionales de la evaluación final.

## Resumen

Una propuesta evaluable necesita mecanismo, ablaciones equivalentes, una frontera de información temporal y un criterio explícito de fallo. ContextMemory aporta esas piezas y recibe un resultado inicial negativo. Conserve implementación, configuraciones, predicciones individuales y agregados para permitir inspeccionar el fallo. La investigación posterior puede mejorar la regla o rechazar su premisa; ninguna alternativa permite afirmar superioridad a partir del experimento actual.

## Referencias

- Promedios por características: https://doi.org/10.1016/j.ijforecast.2019.02.011
- Ensambles dinámicos: https://doi.org/10.1007/s10994-018-05774-y
- Escalamiento: https://doi.org/10.1016/j.ijforecast.2006.03.001
- Experto Theta: https://robjhyndman.com/papers/Theta.pdf
- Experto estacional: https://otexts.com/fpp3/holt-winters.html
