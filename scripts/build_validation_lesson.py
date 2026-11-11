"""Author the bilingual lesson on temporal selection; execute with run_notebooks.py."""

from pathlib import Path
import copy
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
CELLS = [
    (
        "markdown",
        """# Choosing a combination before its target arrives

**Question:** Can completed historical forecasts select a more useful combination without allowing the final target to choose its parameters?

## Objectives

This lesson executes ContextMemoryCV and ValidationMix, examines their information sets and compares point accuracy with interval quality. The original fixed ContextMemory rule has a slightly unfavorable mean-error result against its recency-only ablation. That result remains valid for that configuration. It motivates a different, explicitly identified algorithm rather than changing a published number or selecting only successful examples. Temporal validation is the additional mechanism: parameters are chosen from earlier forecast blocks whose targets were already observed when the validation forecast was issued.

The two variants retain the same five experts and context features. ContextMemoryCV selects a context shrinkage and temperature; ValidationMix also considers regularized convex stacking. We will inspect a generated structural-break case, verify complete historical target availability, exercise the insufficient-memory fallback and test a change of measurement units. We then reproduce both methods on the fifteen development cases and inspect the separately evaluated weekly and monthly collections. A useful point forecast and a useful uncertainty interval are different outcomes.""",
        """# Elegir una combinación antes de que llegue su objetivo

**Pregunta:** ¿Pueden los pronósticos históricos completos seleccionar una combinación más útil sin permitir que el objetivo final elija sus parámetros?

## Objetivos

Esta lección ejecuta ContextMemoryCV y ValidationMix, examina su información disponible y compara exactitud puntual con calidad de intervalos. La regla ContextMemory fija tiene un resultado medio ligeramente desfavorable frente a su ablación de recencia. Ese resultado sigue siendo válido para esa configuración. Motiva otro algoritmo, identificado explícitamente, en lugar de cambiar un número publicado o seleccionar solo ejemplos exitosos. La validación temporal es el mecanismo adicional: los parámetros se eligen con bloques anteriores cuyos objetivos ya se conocían al emitir el pronóstico de validación.

Las variantes conservan cinco expertos y las mismas características contextuales. ContextMemoryCV selecciona contracción y temperatura; ValidationMix considera además apilamiento convexo regularizado. Inspeccionaremos un caso generado con cambios de nivel, verificaremos disponibilidad completa de objetivos históricos, ejercitaremos la alternativa sin memoria suficiente y probaremos un cambio de unidades. Después reproduciremos ambos métodos sobre los quince casos de desarrollo e inspeccionaremos las colecciones semanales y mensuales evaluadas separadamente. Un pronóstico puntual útil y un intervalo de incertidumbre útil son resultados distintos.""",
    ),
    (
        "code",
        """from pathlib import Path
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
import importlib.metadata
root = next(p for p in Path.cwd().parents if (p / "VERSION").is_file())
sys.path.insert(0, str(root / "data-pipeline"))
from chronoscopelab.model.validated_combination import fit_validated
from chronoscopelab.model.context_memory import fit_context_memory
from chronoscopelab.reevaluation import metrics
plt.rcParams.update({"figure.figsize": (8, 3.5), "figure.dpi": 95, "font.size": 10})
comparison = json.loads((root / "data/derived/reevaluation.json").read_text(encoding="utf-8"))
case = next(c for c in comparison["cases"] if c["case_id"] == "BRKV_level_shift")
history = np.array(case["history"])
actual = np.array(case["actual"])
m, h = case["seasonality"], case["horizon"]
print("History, horizon, seasonality:", len(history), h, m)
for package in ["numpy", "scipy", "matplotlib", "statsforecast", "lightgbm",
                "mlforecast", "nbformat", "nbclient", "ipykernel"]:
    print(package, importlib.metadata.version(package))
""",
    ),
    (
        "markdown",
        """## Data

The available prefix and final targets come from the corrected contiguous-history comparison. Display-decimated arrays are not used as fitting observations. The structural-break example makes changing competence plausible, but its generator does not inform the algorithm where a change occurred. The reserved final block is loaded only for subsequent scoring. Neither fitting call below accepts that array. The full external inventories are different experiments with their own horizon, seasonal lag, exclusions and source hashes.

## Method

At most twelve completed historical origins form the memory. For an inner query at v, an origin o is eligible for training only when o + H is at most v. At least three completed blocks are required. Candidate scores average scaled absolute errors on those later historical blocks. This is stricter than merely requiring an origin to precede the query: a long forecast target can overlap a later query even though its starting point is earlier.""",
        """## Datos

El prefijo disponible y los objetivos finales provienen de la comparación corregida con historia contigua. Los arreglos reducidos para visualización no se usan para ajustar. El ejemplo de cambios de nivel hace plausible que varíe la competencia, pero su generador no informa al algoritmo dónde cambió el proceso. El bloque final se carga solo para puntuar después. Ninguna llamada de ajuste recibe ese arreglo. Los inventarios externos constituyen otros experimentos, con horizonte, período estacional, exclusiones y hashes propios.

## Método

La memoria contiene hasta doce orígenes históricos completos. Para una consulta interna en v, un origen o es elegible para entrenar solo si o + H no supera v. Se exigen tres bloques completos. Las puntuaciones promedian errores absolutos escalados sobre bloques históricos posteriores. Esto es más estricto que exigir que el origen preceda a la consulta: un objetivo largo puede solaparse con una consulta posterior aunque su inicio sea anterior.""",
    ),
    (
        "code",
        """context_cv = fit_validated(history, m, h, stacking=False)
recency = fit_context_memory(history, m, h, mode="recency")
print("ContextMemoryCV selected:", context_cv.selected)
print("Historical validation blocks:", len(context_cv.validation_splits))
for split in context_cv.validation_splits:
    print(split["query"], max(context_cv.origins[j] + h for j in split["train"]))
print("Every inner training target is complete at its query.")
""",
    ),
    (
        "markdown",
        """Context shrinkage one removes the context kernel. The temperature controls how sharply estimated competence changes expert allocation. A selected contextual-family configuration therefore does not by itself demonstrate a benefit from contextual similarity. RecencyMean and EqualMean are explicit candidates, and a five-percent uniform floor limits concentration. The original finite family was fixed before the new external outcomes were computed. It is not enlarged after inspecting a difficult outer target.

ValidationMix adds a different fitting objective. It chooses nonnegative weights summing to one to minimize normalized historical squared error plus a penalty toward equal weights. Five experts permit enumeration of all nonempty active sets. Candidate ranking still uses temporally held-out absolute error. The fitting objective and selection score are deliberately distinguished; neither sees the final target.""",
        """Contracción contextual uno elimina el núcleo de contexto. La temperatura controla cuánto cambia la asignación de expertos al variar su competencia estimada. Seleccionar una configuración de la familia contextual no demuestra por sí solo un beneficio de la similitud contextual. RecencyMean y EqualMean son candidatos explícitos, y un piso uniforme del cinco por ciento limita la concentración. La familia finita se fijó antes de calcular los nuevos resultados externos. No se amplía después de inspeccionar un objetivo externo difícil.

ValidationMix añade otro objetivo de ajuste. Elige pesos no negativos que suman uno para minimizar error cuadrático histórico normalizado y una penalización hacia pesos iguales. Cinco expertos permiten enumerar todos los conjuntos activos no vacíos. La selección sigue usando error absoluto reservado temporalmente. Se distinguen el objetivo de ajuste y la medida de selección; ninguno observa el objetivo final.""",
    ),
    (
        "code",
        """validated = fit_validated(history, m, h, stacking=True)
print("ValidationMix selected:", validated.selected)
ranked = sorted(validated.candidates, key=lambda c: c["mean_validation_mae_scaled"])
for row in ranked[:4]:
    print(row["configuration"], round(row["mean_validation_mae_scaled"], 6))
print("Smallest weight:", round(float(validated.weights.min()), 6))
print("Total allocation:", round(float(validated.weights.sum()), 6))
""",
    ),
    (
        "code",
        """short = history[:30]
fallback = fit_validated(short, m, h)
short_recency = fit_context_memory(short, m, h, mode="recency")
print("Validation blocks:", len(fallback.validation_splits), "Rule:", fallback.selected)
print("Difference from control:", round(float(np.max(abs(fallback.quantiles - short_recency.quantiles))), 8))
print("Insufficient validation uses the matching recency control.")
""",
    ),
    (
        "markdown",
        """The short-prefix calculation is a real fallback path, not an invented replacement forecast. With too little completed memory, a validation score cannot be estimated. The algorithm then returns the specified recency rule, which may itself use equal weights when no remembered origins are eligible. Quietly choosing an apparently successful expert from the loaded final target would violate this contract.

Changing units should not change competence merely because a series is measured in a different positive scale. The following calculation applies a common shift and scale away from numerical degeneracy thresholds. It compares transformed predictions with the transformation of the original prediction. This checks a structural property of the construction, not predictive accuracy on another dataset.""",
        """El cálculo del prefijo corto ejercita una alternativa real, no un pronóstico de reemplazo inventado. Con poca memoria completa no se puede estimar una puntuación de validación. El algoritmo retorna la regla especificada de recencia, que puede usar pesos iguales si no existen orígenes elegibles. Elegir silenciosamente un experto exitoso utilizando el objetivo final cargado violaría este contrato.

Cambiar unidades no debería alterar la competencia solo porque una serie se mida en otra escala positiva. El cálculo siguiente aplica un desplazamiento y una escala comunes lejos de umbrales de degeneración numérica. Compara pronósticos transformados con la transformación del pronóstico original. Verifica una propiedad estructural de la construcción, no exactitud predictiva en otro conjunto de datos.""",
    ),
    (
        "code",
        """changed_units = fit_validated(2 * history + 7, m, h)
unit_difference = np.max(abs(changed_units.quantiles - (2 * validated.quantiles + 7)))
print("Unit-transform maximum difference:", f"{unit_difference:.8f}")
print("Positive unit change and common shift preserve the forecast transformation.")
""",
    ),
    (
        "code",
        """earlier = fit_validated(history[:-h], m, h)
print("All earlier targets available:", all(o + h <= len(history) - h for o in earlier.origins))
print("Earlier query prefix:", len(history) - h)
print("Latest remembered target endpoint:", max(earlier.origins) + h)
fig, ax = plt.subplots()
positions = np.arange(5)
for offset, label, fit in [(-0.24, "RecencyMean", recency),
                           (0, "ContextMemoryCV", context_cv),
                           (0.24, "ValidationMix", validated)]:
    ax.bar(positions + offset, fit.weights, width=0.23, label=label)
ax.set_xticks(positions, ["SeasonalNaive", "SES", "Holt", "HoltWinters", "Theta"])
ax.set(ylabel="Expert allocation", ylim=(0, 1))
ax.legend()
fig.tight_layout()
plt.show()
""",
    ),
    (
        "markdown",
        """## Comparison

Different bars show different forecasting allocations. They do not attribute an error reduction to one feature or to the context kernel alone. The selected parameter family changes temperature and shrinkage as well as contextual weighting, while ValidationMix can choose stacking. A future component claim would require a matching validation-based ablation. The earlier-prefix calculation also demonstrates that historical endpoints move with the query: the memory is rebuilt from what is available at that earlier cutoff. Training origins are not independent replications, because their fitting histories overlap.

## Evidence

We now execute both new variants on every original case prefix. All fifteen blocks are retained. The comparison is informative about these configurations, but the cases were already examined during development. They cannot supply new external confirmation. The stored public documents provide a numerical cross-check rather than replacing these fitting calls.""",
        """## Comparación

Las barras distintas muestran asignaciones de pronóstico diferentes. No atribuyen una reducción de error a una característica ni exclusivamente al núcleo contextual. La familia seleccionada cambia temperatura y contracción además de ponderación contextual, mientras ValidationMix puede elegir apilamiento. Una afirmación futura sobre componentes necesitaría una ablación equivalente basada en validación. El cálculo del prefijo anterior muestra además que los extremos históricos se mueven con la consulta: la memoria se reconstruye con lo disponible en ese corte. Los orígenes no son réplicas independientes, porque sus historias de ajuste se solapan.

## Evidencia

Ahora ejecutamos ambas variantes nuevas sobre el prefijo original de cada caso. Se conservan los quince bloques. La comparación informa sobre estas configuraciones, pero los casos ya fueron examinados durante el desarrollo y no constituyen confirmación externa nueva. Los documentos públicos proporcionan una comprobación numérica sin reemplazar estas llamadas de ajuste.""",
    ),
    (
        "code",
        """development = {"ContextMemoryCV": [], "ValidationMix": []}
for c in comparison["cases"]:
    prefix = np.array(c["history"])
    target = np.array(c["actual"])
    for name in development:
        fit = fit_validated(prefix, c["seasonality"], c["horizon"], stacking=name == "ValidationMix")
        q = fit.quantiles
        score = metrics(prefix, target, q[:, 1], q[:, 0], q[:, 2], c["seasonality"])
        development[name].append(score["mase"])
study = json.loads((root / "data/derived/validated-combinations.json").read_text(encoding="utf-8"))
selected = next(c for c in study["cohorts"] if c["id"] == "selected_cases")
for name, scores in development.items():
    stored = next(r["mase"] for r in selected["summary"] if r["name"] == name)
    assert np.isclose(np.mean(scores), stored, rtol=1e-10, atol=1e-10)
    print(name, "mean development MASE", f"{np.mean(scores):.4f}")
""",
    ),
    (
        "code",
        """fig, axes = plt.subplots(1, 2, figsize=(9, 3.7))
names = ["RecencyMean", "ContextMemoryCV", "ValidationMix", "AutoTheta"]
for ax, dataset in zip(axes, ["m4_weekly", "m3_monthly"]):
    cohort = next(c for c in study["cohorts"] if c["id"] == dataset)
    values = [next(r["mase"] for r in cohort["summary"] if r["name"] == n) for n in names]
    ax.barh(names, values)
    ax.invert_yaxis()
    ax.set(title=cohort["name"], xlabel="Mean series MASE")
fig.tight_layout()
plt.show()
""",
    ),
    (
        "markdown",
        r"""### Sensitivity to the choice of score

For an earlier query $r$, define $s_r$ from the seasonal differences within the prefix available at that query. A candidate configuration $c$ estimates weights using only memory targets complete by $r$. Write its validation forecast at lead $j$ as $\widehat y_{r+j}^{(c)}$. With $R$ eligible validation queries and horizon $H$, the selection score is

$$
V(c)=\frac{1}{RH}\sum_{r}\sum_{j=1}^{H}
\frac{|y_{r+j}-\widehat y_{r+j}^{(c)}|}{s_r}.
$$

The validation observations belong to the historical prefix of the final query. At a particular validation query they are still future outcomes, so each weight fit excludes them. The final weights for the chosen configuration use all completed historical memory available at the final query. Thus the selected configuration and the weight vector are different objects. Reusing a weight vector fitted on the validation outcomes to compute its own selection score would conflate these operations.

Point selection gives each lead an absolute error. Interval evaluation instead gives credit for a short interval and charges an additional penalty outside its endpoints. For lower and upper endpoints $l,u$ and nominal miscoverage $\alpha$, the contribution at observation $y$ is

$$
I_\alpha(l,u;y)=u-l+\frac{2}{\alpha}(l-y)\mathbf{1}(y<l)
+\frac{2}{\alpha}(y-u)\mathbf{1}(y>u).
$$

MSIS averages this score after seasonal scaling. It can favor a different method because it uses both endpoints, even when the point paths have similar MASE. The next figure expresses both scores as differences from the recency control within each collection. A bar below zero favors the named method for that score. Comparing signs within each panel is more informative than comparing magnitudes between metrics, because their objectives and penalty scales differ.
""",
        r"""### Sensibilidad a la medida de error

Para una consulta anterior $r$, defina $s_r$ usando las diferencias estacionales dentro del prefijo disponible entonces. Una configuración $c$ estima pesos solo con memorias cuyos objetivos están completos en $r$. Sea $\widehat y_{r+j}^{(c)}$ su pronóstico de validación para el paso $j$. Con $R$ consultas de validación elegibles y horizonte $H$, el puntaje de selección es

$$
V(c)=\frac{1}{RH}\sum_{r}\sum_{j=1}^{H}
\frac{|y_{r+j}-\widehat y_{r+j}^{(c)}|}{s_r}.
$$

Las observaciones de validación pertenecen al prefijo histórico de la consulta final. En cada consulta de validación todavía son futuras y por eso quedan excluidas del ajuste de sus pesos. Los pesos finales de la configuración elegida utilizan toda la memoria completada disponible en la consulta final. La configuración y el vector de pesos son objetos distintos. Usar un vector ajustado sobre los objetivos de validación para calcular su propio puntaje de selección mezclaría ambas operaciones.

La selección puntual asigna error absoluto a cada paso. La evaluación de intervalos favorece una banda corta y penaliza observaciones fuera de sus extremos. Con límites $l,u$ y probabilidad nominal de exclusión $\alpha$, la contribución de una observación $y$ es

$$
I_\alpha(l,u;y)=u-l+\frac{2}{\alpha}(l-y)\mathbf{1}(y<l)
+\frac{2}{\alpha}(y-u)\mathbf{1}(y>u).
$$

MSIS promedia esta puntuación con escalamiento estacional. Puede favorecer otro método porque utiliza los dos extremos, incluso si los MASE son similares. La figura siguiente expresa las dos medidas como diferencias respecto al control por recencia dentro de cada colección. Una barra bajo cero favorece al método indicado para esa medida. Compare los signos dentro de cada panel: los objetivos y las penalizaciones difieren y sus magnitudes entre métricas tienen otra interpretación.
""",
    ),
    (
        "code",
        """score_figure, score_axes = plt.subplots(1, 2, figsize=(9, 3.7))
for ax, metric in zip(score_axes, ("mase", "msis"), strict=True):
    x = np.arange(3)
    for offset, identifier in [(-0.18, "m4_weekly"), (0.18, "m3_monthly")]:
        cohort = next(c for c in study["cohorts"] if c["id"] == identifier)
        values = {row["name"]: row[metric] for row in cohort["summary"]}
        ax.bar(x + offset, [values[name] - values["RecencyMean"] for name in names[1:]],
               width=0.34, label=cohort["name"])
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x, names[1:], rotation=15)
    ax.set(ylabel=f"{metric.upper()} difference from RecencyMean")
score_axes[0].legend(fontsize=8)
score_figure.tight_layout()
plt.show()
""",
    ),
    (
        "markdown",
        """### Reproduce the comparison with your own data

Create a record per series with its original sampling frequency, missingness flags, declared seasonal lag and a positive scale based on the fitting prefix. Freeze the roster of methods before reserving final targets. At each eligible final query, lay out earlier nonoverlapping target blocks on a calendar. Record the end of each block and exclude a memory when that endpoint exceeds the query being fit. Test this condition with a short history where the fallback should run. Store the forecast values, scales, weights, candidate scores and fit times with the source digest.

Evaluate each method on the same origins. When a case has several origins, aggregate those scores within series first and compare methods with paired series differences. Examine both the mean and the distribution of differences. Repeat the protocol on a separate collection chosen before looking at these outcomes. If a planner requires a useful interval for high-cost decisions, record its target coverage and width criterion in advance and evaluate them alongside point accuracy.

## Results

**Answer:** The reproduced development mean MASE values are 1.3974 for ContextMemoryCV and 1.4031 for ValidationMix. The variants also improve point error over RecencyMean on both admitted external collections. AutoTheta retains lower monthly point error and lower interval scores on both. Context attribution and calibrated uncertainty remain unresolved.

The external table accounts for every source identity. Sixty-five weekly series have insufficient history for the fixed seasonal/origin protocol; six monthly identities are exact duplicates. Eligible origins are averaged within each series, then series receive equal weight within each collection. The new variants reduce mean MASE against the recency-only control on both admitted collections. AutoTheta nevertheless has lower point error on monthly series, and it has lower interval score on both collections. The figure must therefore be read by collection and comparator, not as a universal ranking or an official M4 competition result.

The Gaussian endpoints of the combinations are broad. Coverage above the nominal level is not automatically useful when width and missed-target penalties are considered together. The original fifteen-case data illustrate the distinction: the new variants improve point error while worsening MSIS against RecencyMean. Neither convex weights nor selecting a point-error parameter calibrates the resulting interval. A future uncertainty method needs its own temporal protocol and held-out assessment.

## Summary

Inspect which candidate wins on the structural-break history and whether it suppresses context. Explain why changing the final targets after fitting cannot legitimately change that selected configuration. Design a matched recency-only validation family before claiming that the context kernel caused a gain. If you propose additional experts or a new interval construction, identify a separate confirmation collection before examining its outcomes. Preserve all earlier results rather than retelling unsuccessful settings as if they had never been evaluated.

The useful improvement here is a qualified one: a fixed temporal selection rule produces better empirical point forecasts than its original recency comparator on the admitted collections. It leaves meaningful limits in component attribution, interval efficiency and generalization. Reproduction requires the declared environment, original contiguous prefixes and the separately identified source inventories; a rendered chart alone does not establish those conditions.

## References

- [MASE and forecast accuracy](https://doi.org/10.1016/j.ijforecast.2006.03.001).
- [FFORMA](https://doi.org/10.1016/j.ijforecast.2019.02.011).
- [Arbitrage of forecasting experts](https://doi.org/10.1007/s10994-018-05774-y).
- [M4 Weekly source](https://doi.org/10.5281/zenodo.4656522).
- [M3 Monthly source](https://doi.org/10.5281/zenodo.4656298).
""",
        """### Reproduce la comparación con tus propios datos

Cree un registro por serie con frecuencia original, indicadores de ausencia, rezago estacional declarado y escala positiva calculada sobre el prefijo de ajuste. Fije los métodos antes de reservar los objetivos finales. Para cada consulta final elegible, ubique en el calendario los bloques anteriores con objetivos disjuntos. Registre el extremo de cada bloque y excluya una memoria cuando ese extremo supera la consulta que está ajustando. Pruebe la condición con una historia corta donde se deba usar la alternativa de recencia. Guarde valores pronosticados, escalas, pesos, puntajes de candidatos y tiempos de ajuste junto con el resumen criptográfico del origen.

Evalúe los métodos en los mismos orígenes. Cuando una serie aporta varios orígenes, agregue sus puntajes dentro de la serie antes de comparar con diferencias emparejadas. Examine la media y la distribución de esas diferencias. Repita el protocolo en una colección separada elegida antes de conocer los resultados. Si el planificador requiere un intervalo para decisiones costosas, declare de antemano el criterio de cobertura y amplitud y evalúelo junto con la precisión puntual.

## Resultados

**Respuesta:** Los MASE medios de desarrollo reproducidos son 1.3974 para ContextMemoryCV y 1.4031 para ValidationMix. Las variantes también mejoran el error puntual frente a RecencyMean en ambas colecciones externas admitidas. AutoTheta mantiene menor error puntual mensual y mejores puntuaciones de intervalos en ambas. La atribución contextual y la incertidumbre calibrada siguen sin resolverse.

La tabla externa contabiliza cada identidad de origen. Sesenta y cinco series semanales tienen historia insuficiente para el protocolo estacional y de orígenes fijado; seis identidades mensuales son duplicados exactos. Se promedian orígenes elegibles por serie y después se asigna igual peso a cada serie dentro de su colección. Las variantes nuevas reducen MASE medio frente al control de recencia en ambas colecciones admitidas. Sin embargo, AutoTheta tiene menor error puntual mensual y menor puntuación de intervalos en ambas. La figura se interpreta por colección y comparador, no como clasificación universal ni resultado oficial de la competición M4.

Los extremos gaussianos de las combinaciones son amplios. Cobertura por encima del nivel nominal no es automáticamente útil al considerar amplitud y penalizaciones por objetivos fuera del intervalo. Los quince casos originales muestran esa distinción: las variantes nuevas mejoran error puntual y empeoran MSIS frente a RecencyMean. Ni los pesos convexos ni seleccionar parámetros por error puntual calibran el intervalo. Un método futuro de incertidumbre necesita protocolo temporal y evaluación reservada propios.

## Resumen

Inspeccione qué candidato gana en la historia con cambios de nivel y si elimina el contexto. Explique por qué cambiar objetivos finales después del ajuste no puede cambiar legítimamente la configuración seleccionada. Diseñe una familia equivalente de validación solo con recencia antes de afirmar que el núcleo contextual causó una mejora. Si propone expertos adicionales o nuevos intervalos, identifique otra colección de confirmación antes de examinar sus resultados. Preserve los resultados anteriores en lugar de relatar configuraciones desfavorables como si nunca se hubiesen evaluado.

La mejora útil es acotada: una regla temporal fija produce mejores pronósticos puntuales empíricos que el comparador original de recencia sobre las colecciones admitidas. Conserva límites importantes en atribución a componentes, eficiencia de intervalos y generalización. Reproducir exige el entorno declarado, prefijos contiguos originales e inventarios identificados separadamente; un gráfico renderizado no establece esas condiciones por sí solo.

## Referencias

- [MASE y exactitud de pronósticos](https://doi.org/10.1016/j.ijforecast.2006.03.001).
- [FFORMA](https://doi.org/10.1016/j.ijforecast.2019.02.011).
- [Arbitrage of forecasting experts](https://doi.org/10.1007/s10994-018-05774-y).
- [Fuente M4 Weekly](https://doi.org/10.5281/zenodo.4656522).
- [Fuente M3 Monthly](https://doi.org/10.5281/zenodo.4656298).
""",
    ),
]


SETUP_EN = """## Setup

Use the declared notebook environment. Recreate its exact direct dependencies before executing the lesson:

```sh
python -m pip install numpy==2.4.6 scipy==1.15.3 matplotlib==3.10.8 statsforecast==2.0.3
python -m pip install lightgbm==4.6.0 mlforecast==1.0.31 nbformat==5.11.1 nbclient==0.11.0 ipykernel==7.4.0
```

The setup cell prints the installed versions so the runtime can be compared with these requirements. All data are already admitted in the repository; no hidden network request or substitute dataset participates in the fitting calls. Start from a clean kernel to keep earlier exploratory state from changing the result.
"""
SETUP_ES = """## Preparación

Utilice el entorno declarado de cuadernos. Reproduzca sus dependencias directas exactas antes de ejecutar la lección:

```sh
python -m pip install numpy==2.4.6 scipy==1.15.3 matplotlib==3.10.8 statsforecast==2.0.3
python -m pip install lightgbm==4.6.0 mlforecast==1.0.31 nbformat==5.11.1 nbclient==0.11.0 ipykernel==7.4.0
```

La celda imprime versiones instaladas para comparar el entorno con estos requisitos. Los datos ya están admitidos en el repositorio; ninguna solicitud de red oculta ni conjunto sustituto participa en el ajuste. Comience con un núcleo limpio para impedir que un estado exploratorio previo cambie el resultado.
"""
CELLS.insert(1, ("markdown", SETUP_EN, SETUP_ES))

EXPLANATIONS = {
    "short =": (
        "The next calculation deliberately removes enough history to make validation unavailable. It compares the resulting path with the specified recency fallback, so an unavailable validation estimate cannot be confused with a fabricated successful candidate.",
        "El cálculo siguiente elimina suficiente historia para que la validación no esté disponible. Compara la trayectoria con la alternativa de recencia especificada, de modo que la falta de una estimación no se confunda con un candidato exitoso inventado.",
    ),
    "earlier =": (
        "Move the query backward by one forecast block and refit using only the remaining prefix. The printed endpoint makes the information boundary visible. The allocation chart then compares the original query's fitted expert weights, rather than using its final targets to choose a convenient explanation.",
        "Se retrocede la consulta un bloque y se ajusta únicamente con el prefijo restante. El extremo impreso hace visible el límite de información. El gráfico compara después los pesos ajustados en la consulta original, sin utilizar objetivos finales para seleccionar una explicación conveniente.",
    ),
    "fig, axes =": (
        "The second figure reads the separately admitted external collection summaries. All displayed methods are compared on identical eligible series within each panel. Keeping the panels separate makes the monthly statistical comparator visible instead of hiding it inside an overall average dominated by another collection.",
        "La segunda figura lee resúmenes externos admitidos separadamente. Cada panel compara métodos sobre las mismas series elegibles. Separar los paneles mantiene visible al comparador estadístico mensual, en lugar de ocultarlo en un promedio general dominado por otra colección.",
    ),
}
annotated = []
for item in CELLS:
    if item[0] == "code":
        first = item[1].splitlines()[0]
        for prefix, pair in EXPLANATIONS.items():
            if first.startswith(prefix):
                annotated.append(("markdown", pair[0], pair[1]))
        comments = {
            "from pathlib": "Load the admitted contiguous prefix and identify exact runtime versions.",
            "context_cv =": "Select contextual parameters using complete earlier target blocks.",
            "validated =": "Compare the extended finite candidate family and inspect its allocations.",
            "short =": "Exercise the no-validation fallback without consulting future targets.",
            "changed_units =": "Refit after a positive change of units and common location shift.",
            "score_figure,": "Compare each method against its own collection's recency reference.",
            "earlier =": "Refit an earlier information cutoff, then inspect original-query weights.",
            "development =": "Execute both variants on every original contiguous development prefix.",
            "fig, axes =": "Compare external collections separately, retaining the statistical comparator.",
        }
        comment = next(v for k, v in comments.items() if first.startswith(k))
        item = ("code", "# " + comment + "\n" + item[1])
    annotated.append(item)
CELLS[:] = annotated


def main():
    for lang in ("en", "es"):
        template = json.loads(
            (ROOT / f"notebooks/{lang}/01-forecast-decisions/04-context-memory.ipynb").read_text(
                encoding="utf-8"
            )
        )
        metadata = copy.deepcopy(template["metadata"])
        metadata["caos"].update(
            language=lang,
            topic="01-forecast-decisions",
            level=4,
            packages=[pin for pin in template["metadata"]["caos"]["packages"] if pin in SETUP_EN],
            title="Choosing a combination before its target arrives"
            if lang == "en"
            else "Elegir una combinación antes de que llegue su objetivo",
            data=["data/derived/reevaluation.json", "data/derived/validated-combinations.json"],
            sources=[
                "https://doi.org/10.1016/j.ijforecast.2006.03.001",
                "https://doi.org/10.1016/j.ijforecast.2019.02.011",
                "https://doi.org/10.1007/s10994-018-05774-y",
                "https://doi.org/10.5281/zenodo.4656522",
                "https://doi.org/10.5281/zenodo.4656298",
            ],
        )
        cells = []
        for i, cell in enumerate(CELLS):
            kind = cell[0]
            text = cell[1 if lang == "en" or kind == "code" else 2]
            item = {
                "cell_type": kind,
                "id": hashlib.sha256(f"validation-{lang}-{i}".encode()).hexdigest()[:12],
                "metadata": {},
                "source": text.splitlines(keepends=True),
            }
            if kind == "code":
                item.update(execution_count=None, outputs=[])
            cells.append(item)
        path = ROOT / f"notebooks/{lang}/01-forecast-decisions/05-temporal-validation.ipynb"
        path.write_text(
            json.dumps(
                {"cells": cells, "metadata": metadata, "nbformat": 4, "nbformat_minor": 5},
                indent=1,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        index = ROOT / f"notebooks/{lang}/README.md"
        text = index.read_text(encoding="utf-8")
        text = "\n".join(line for line in text.splitlines() if "05-temporal-validation.ipynb" not in line)
        title = metadata["caos"]["title"]
        rows = text.splitlines()
        pos = next(i for i, line in enumerate(rows) if "04-context-memory.ipynb" in line) + 1
        rows.insert(pos, f"| 4 | [{title}](01-forecast-decisions/05-temporal-validation.ipynb) |")
        index.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    print("Authored bilingual temporal-validation lessons; execution is required.")


if __name__ == "__main__":
    main()
