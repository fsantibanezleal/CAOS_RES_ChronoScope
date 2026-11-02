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

## Resultados

**Respuesta:** ContextMemory obtiene MASE medio 1,1921 y RecencyMean 1,1898. La regla contextual falla su criterio declarado de error medio en esta colección. EqualMean obtiene 1,3047. Estimar pérdidas recientes ayudó frente al promedio uniforme en estos casos, pero el núcleo contextual adicional no mejoró la comparación primaria. Las cifras conservan la precisión de la salida computada.

Estos valores no establecen equivalencia ni demuestran que ponderar contextos nunca pueda ayudar. Identifican un experimento fijo sin éxito. Un seguimiento debe declarar datos más amplios, varios orígenes, incertidumbre que considere dependencia y costos computacionales antes de ejecutarse. Modificar parámetros define otro experimento y no debe sobrescribir este. Los orígenes empleados para estimar pesos aportan entrenamiento, no repeticiones independientes adicionales de la evaluación final.

## Resumen

Una propuesta evaluable necesita mecanismo, ablaciones equivalentes, una frontera de información temporal y un criterio explícito de fallo. ContextMemory aporta esas piezas y recibe un resultado inicial negativo. Conserve implementación, configuraciones, predicciones individuales y agregados para permitir inspeccionar el fallo. La investigación posterior puede mejorar la regla o rechazar su premisa; ninguna alternativa permite afirmar superioridad a partir del experimento actual.

## Referencias

- Promedios por características: https://doi.org/10.1016/j.ijforecast.2019.02.011
- Ensambles dinámicos: https://doi.org/10.1007/s10994-018-05774-y
- Escalamiento: https://doi.org/10.1016/j.ijforecast.2006.03.001
- Experto Theta: https://robjhyndman.com/papers/Theta.pdf
- Experto estacional: https://otexts.com/fpp3/holt-winters.html
