"""Apply the scientific and bilingual editorial policy to authored lesson documents.

This module is part of authoring, not execution. It never supplies computed outputs.
The notebook runner remains the only writer of execution counts and figures.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
from pathlib import Path
import re
import tokenize

ROOT = Path(__file__).resolve().parents[1]

# Translate display literals, never dictionary keys or model/API identifiers.
DISPLAY_ES = {
    "History:": "Historia:", "Season:": "Período:", "Holdout:": "Bloque reservado:",
    "history": "historia", "actual": "observado", "forward": "original", "reversed": "invertida",
    "SeasonalNaive first prediction:": "Primera predicción de SeasonalNaive:",
    "Theta first prediction:": "Primera predicción de Theta:",
    "Holt first prediction:": "Primera predicción de Holt:",
    "SeasonalNaive MASE:": "MASE de SeasonalNaive:", "Theta MASE:": "MASE de Theta:",
    "Observation index": "Índice de observación", "Series value": "Valor en unidades de la fuente",
    "Removed observations:": "Observaciones retiradas:",
    "Partial history remainder:": "Resto del ciclo en la historia parcial:",
    "Forecast horizon:": "Horizonte del pronóstico:",
    "HoltWinters first prediction:": "Primera predicción de HoltWinters:",
    "Earlier-origin MASE:": "MASE del origen anterior:",
    "Earlier-origin coverage:": "Cobertura del origen anterior:",
    "Forecast lead": "Anticipación del pronóstico", "Absolute error": "Error absoluto",
    "Seasonal reference MASE:": "MASE de la referencia estacional:",
    "AutoETS runtime notices:": "Avisos de ejecución de AutoETS:",
    "AutoETS MASE:": "MASE de AutoETS:",
    "AutoTheta first prediction:": "Primera predicción de AutoTheta:",
    "AutoARIMA runtime notices:": "Avisos de ejecución de AutoARIMA:",
    "AutoARIMA first prediction:": "Primera predicción de AutoARIMA:",
    "LightGBM MASE:": "MASE de LightGBM:", "Zero-based lead": "Anticipación desde cero",
    "Final-block MASE": "MASE del bloque final", "Mean interval width": "Anchura media del intervalo",
    "Retained implementation": "Implementación conservada",
    "Leads ": "Anticipaciones ", " to ": " a ", "Scaled absolute error": "Error absoluto escalado",
    "early and late": "inicial y final", "coverage": "cobertura",
    "Completed training origins:": "Orígenes completos de entrenamiento:",
    "Latest training target ends:": "Fin del último objetivo de entrenamiento:",
    "Available history ends:": "Fin de la historia disponible:",
    "Recency weights:": "Pesos de recencia:", "Equal weights:": "Pesos uniformes:",
    "Convex expert weight": "Peso convexo del experto", "case MASE": "MASE del caso",
    "Maximum weight change after unit conversion:": "Cambio máximo de pesos al convertir unidades:",
    "Mean MASE across fifteen final blocks": "MASE medio de los quince bloques finales",
    "mean MASE": "MASE medio", "Case in the published inventory": "Caso del inventario publicado",
    "ContextMemory minus RecencyMean MASE": "MASE de ContextMemory menos RecencyMean",
    "Lower, tied, higher:": "Inferiores, iguales, superiores:",
    "Mean and median difference:": "Diferencia media y mediana:",
    "Cutoff (hourly-labelled observation)": "Corte (observación con etiqueta horaria)",
    "MASE using lag 24": "MASE con rezago 24",
    "Largest difference from direct seasonal indexing:": "Mayor diferencia frente al índice estacional directo:",
    "Cutoff  /  next daily phase  /  daily MASE  /  weekly MASE  /  smoothed MASE":
        "Corte  /  fase diaria siguiente  /  MASE diario  /  MASE semanal  /  MASE suavizado",
    "History, horizon, seasonality:": "Historia, horizonte, período estacional:",
    "ContextMemoryCV selected:": "Selección de ContextMemoryCV:",
    "Historical validation blocks:": "Bloques históricos de validación:",
    "Every inner training target is complete at its query.":
        "Cada objetivo de entrenamiento interno está completo en su consulta.",
    "ValidationMix selected:": "Selección de ValidationMix:", "Smallest weight:": "Peso mínimo:",
    "Total allocation:": "Asignación total:", "Validation blocks:": "Bloques de validación:",
    "Rule:": "Regla:", "Difference from control:": "Diferencia frente al control:",
    "Insufficient validation uses the matching recency control.":
        "La validación insuficiente usa el control de recencia correspondiente.",
    "Unit-transform maximum difference:": "Diferencia máxima después de transformar unidades:",
    "Positive unit change and common shift preserve the forecast transformation.":
        "El cambio positivo de unidades y un desplazamiento común conservan la transformación del pronóstico.",
    "Expert allocation": "Asignación de expertos", "Earlier query prefix:": "Prefijo de la consulta anterior:",
    "Latest remembered target endpoint:": "Fin del último objetivo recordado:",
    "All earlier targets available:": "Todos los objetivos anteriores disponibles:",
    "mean development MASE": "MASE medio de desarrollo", "Mean series MASE": "MASE medio por serie",
    " difference from RecencyMean": " diferencia respecto a RecencyMean",
    "Mean paired difference:": "Diferencia pareada media:",
    "Original observations:": "Observaciones originales:", "Window:": "Ventana:",
    "Profile starts:": "Inicios del perfil:", "Motif pairs:": "Pares de motivos:",
    "Discord windows:": "Ventanas discordantes:",
    "Maximum distance from reference:": "Distancia máxima frente a la referencia:",
    "Original index count:": "Cantidad de índices originales:", "FLUSS candidates:": "Candidatos de FLUSS:",
    "original observations": "observaciones originales", "Original observation index": "Índice original de observación",
    "Value": "Valor en unidades de la fuente", "nearest-shape distance": "distancia a la forma más cercana",
    "Window start": "Inicio de ventana", "Z-normalized distance": "Distancia normalizada por puntuación z",
    "Original tolerance:": "Tolerancia original:", "Scale": "Escala",
    "Constant-series scale-one entropy:": "Entropía de la serie constante en escala uno:",
    "Short coarse estimate:": "Estimación agregada corta:",
    "Forward standardized statistic:": "Estadístico estandarizado de la secuencia original:",
    "Reversed standardized statistic:": "Estadístico estandarizado invertido:",
    "Binary phrase count:": "Cantidad de frases binarias:", "Normalized phrase count:": "Cantidad normalizada de frases:",
    "Phrase count after unit conversion:": "Frases después de convertir unidades:",
    "Scale-one converted entropy:": "Entropía transformada en escala uno:",
    "original sequence": "secuencia original", "constant control": "control constante",
    "Coarse-graining scale": "Escala de agregación", "Sample entropy": "Entropía muestral",
    "Standardized third-order lag statistic": "Estadístico de rezago de tercer orden estandarizado",
    "Source series:": "Series de origen:", "Admitted series:": "Series admitidas:",
    "Origins per series:": "Orígenes por serie:",
    "Features available before the three final blocks:": "Características disponibles antes de los tres bloques finales:",
    "Earliest prefix observations:": "Observaciones del primer prefijo:",
    "Hypotheses per partition:": "Hipótesis por partición:",
    "Rejected in discovery:": "Rechazos en descubrimiento:",
    "Rejected in confirmation:": "Rechazos en confirmación:",
    "Reference feature:": "Característica de referencia:", "Kendall tau:": "Tau de Kendall:",
    "Reference probability:": "Probabilidad de referencia:",
    "Maximum BY reference difference:": "Diferencia máxima frente a BY de referencia:",
    "Confirmation threshold:": "Umbral de confirmación:",
    "Duplicate, partition and corrected-probability checks passed":
        "Se comprobaron duplicados, particiones y probabilidades corregidas",
    "Kendall association with log(1 + oracle MASE)": "Asociación de Kendall con log(1 + MASE del oráculo)",
    "Maximum reproduced selection-score difference:": "Diferencia máxima en la puntuación de selección calculada:",
    "Confirmation mean MASE": "MASE medio de confirmación",
    "Selector minus discovery constant MASE": "MASE del selector menos la constante de descubrimiento",
    "Fraction of confirmation series": "Fracción de series de confirmación",
    "Short-window motif pair:": "Par de motivos en ventana corta:",
    "Short-window candidate boundaries:": "Límites candidatos en ventana corta:",
    "Prefix-only profile difference:": "Diferencia del perfil limitado al prefijo:",
    "Original window start": "Inicio original de ventana", "Normalized RMS distance": "Distancia RMS normalizada",
    "-observation window": " observaciones por ventana", "Correlation dimension:": "Dimensión de correlación:",
    "Repeated robust estimates identical:": "Estimaciones robustas repetidas idénticas:",
    "Matching extended pairs": "Pares extendidos coincidentes",
    "The warmup seasonal error scale must be positive": "La escala de error estacional inicial debe ser positiva",
    "rows / prefix / held out:": "filas / prefijo / reservado:", "first predicted row:": "primera fila pronosticada:",
    "first / last:": "primera / última:",
    "Discovery/confirmation:": "Descubrimiento/confirmación:",
    "manual first point / package median:": "primer punto manual / mediana del paquete:",
    "48-step MAE / MASE / interval coverage:": "MAE / MASE / cobertura del intervalo de 48 pasos:",
    "period / forecasts / MASE / coverage:": "período / pronósticos / MASE / cobertura:",
    "fixed warmup scale:": "escala inicial fija:", "added level:": "nivel añadido:",
    "mean absolute errors, first cycle:": "errores absolutos medios, primer ciclo:",
    "post-cycle error-path difference:": "diferencia entre trayectorias de error después del ciclo:",
    "scales for all model periods:": "escalas para todos los períodos del modelo:",
    "MAE puntual, congelado y cresta:": "MAE puntual del grafo congelado y de la regresión ridge:",
}

COMMENTS_ES = {
    "A declared synthetic intervention isolates the lag after a level change.":
        "Una intervención sintética declarada aísla el retraso después de un cambio de nivel.",
    "A score-width view preserves the point/interval tradeoff on this one case.":
        "La relación entre puntuación y anchura conserva el compromiso entre pronóstico puntual e intervalo.",
    "Associate weights with expert identities rather than an unlabeled vector.":
        "Asocia los pesos con expertos identificados para interpretar la asignación.",
    "AutoTheta is a reference implementation distinct from the local Theta equation.":
        "AutoTheta es una implementación de referencia distinta de la ecuación Theta local.",
    "Calculate the exact normalized self-join and retain original window positions.":
        "Calcula la unión normalizada exacta y conserva las posiciones originales de las ventanas.",
    "Change only the model period, keeping the stream and metric period fixed.":
        "Cambia solo el período del modelo; conserva fijos el flujo y el período de la métrica.",
    "Changing units should preserve the context rule's convex weights.":
        "El cambio de unidades debe conservar los pesos convexos de la regla contextual.",
    "Check the chosen confirmation association against SciPy Kendall tau.":
        "Compara la asociación de confirmación elegida con tau de Kendall de SciPy.",
    "Compare a fixed shorter window without selecting a favorable result.":
        "Compara una ventana corta fijada de antemano sin seleccionar un resultado favorable.",
    "Compare daily phase and a weekly seasonal reference on the same reserved hours.":
        "Compara la fase diaria y la referencia semanal sobre las mismas horas reservadas.",
    "Compare dependent-test BY adjustment with the reference implementation.":
        "Compara el ajuste BY para pruebas dependientes con la implementación de referencia.",
    "Compare each method against its own collection's recency reference.":
        "Compara cada método con la referencia de recencia de su propia colección.",
    "Compare early and late errors within one reserved block.":
        "Compara los errores iniciales y finales dentro del mismo bloque reservado.",
    "Compare external collections separately, retaining the statistical comparator.":
        "Compara las colecciones externas por separado y conserva el comparador estadístico.",
    "Compare freshly executed adapters and the historical seasonal reference.":
        "Compara los adaptadores recién ejecutados y la referencia estacional histórica.",
    "Compare the extended finite candidate family and inspect its allocations.":
        "Compara la familia finita ampliada e inspecciona sus asignaciones.",
    "Compare the observed case with the constant control under the same scale policy.":
        "Compara el caso observado y el control constante con la misma política de escala.",
    "Compare the product adapter with the pinned STUMPY reference.":
        "Compara el adaptador del producto con la versión fijada de STUMPY.",
    "Compare window distances after dividing each by the square root of its length.":
        "Compara distancias de ventanas divididas por la raíz cuadrada de su longitud.",
    "Compute the same lag statistic on forward and reversed observations.":
        "Calcula el mismo estadístico de rezago con las observaciones directas e invertidas.",
    "Configure a portable lesson session; no data are downloaded.":
        "Configura una sesión portátil; no se descargan datos.",
    "Configure a portable session and suppress only the known repeated-shape control warning.":
        "Configura la sesión y omite solo el aviso conocido del control de formas repetidas.",
    "Connect motif intervals and retrospective boundaries to original observations.":
        "Relaciona los intervalos de motivos y los límites retrospectivos con las observaciones originales.",
    "Display phase alignment around the deliberately shifted origin.":
        "Muestra la alineación de fase alrededor del origen desplazado deliberadamente.",
    "Display the signed standardized lag statistic in both directions.":
        "Muestra el estadístico estandarizado con signo en ambas direcciones.",
    "Evaluate the ablations against the same target and the same history scale.":
        "Evalúa las ablaciones contra el mismo objetivo y con la misma escala histórica.",
    "Execute both variants on every original contiguous development prefix.":
        "Ejecuta ambas variantes en cada prefijo contiguo original de desarrollo.",
    "Exercise the no-validation fallback without consulting future targets.":
        "Ejercita la alternativa sin validación sin consultar los objetivos futuros.",
    "Extract features before all three held-out target blocks in the worked case.":
        "Extrae características antes de los tres bloques reservados del ejemplo.",
    "Fit the bounded stepwise, approximate AutoARIMA configuration.":
        "Ajusta la configuración AutoARIMA aproximada con búsqueda acotada.",
    "Fit the finite-history Theta implementation on the same prefix.":
        "Ajusta la implementación Theta de historia finita sobre el mismo prefijo.",
    "Fit the fixed context kernel using only completed targets within the history.":
        "Ajusta el núcleo contextual fijo usando solo objetivos completos dentro de la historia.",
    "Fix the historical scale once; the target is used only after prediction.":
        "Fija la escala histórica una vez; usa el objetivo únicamente después de pronosticar.",
    "Import the released API; the lesson does not install or redefine a method.":
        "Importa la API publicada; esta lección no instala ni redefine métodos.",
    "Inspect confirmation-series differences behind the aggregate selector score.":
        "Inspecciona las diferencias por serie detrás de la puntuación agregada del selector.",
    "Inspect errors by lead; an average can hide phase-specific failures.":
        "Inspecciona errores por anticipación; un promedio puede ocultar fallos de fase.",
    "Inspect median-thresholded binary phrase counts and their normalization.":
        "Inspecciona las frases binarias umbralizadas por la mediana y su normalización.",
    "Keep the original tolerance fixed while coarse-graining at four scales.":
        "Conserva fija la tolerancia original al agregar en cuatro escalas.",
    "Keep the reserved final block visible without passing it into the fit.":
        "Mantén visible el bloque reservado sin entregarlo al ajuste.",
    "Load the admitted contiguous prefix and identify exact runtime versions.":
        "Carga el prefijo contiguo admitido e identifica las versiones exactas del entorno.",
    "Pair the two rules within each case before aggregating the differences.":
        "Empareja las reglas dentro de cada caso antes de agregar sus diferencias.",
    "Plot confirmation scores from the reproduced selection calculation.":
        "Grafica las puntuaciones de confirmación de la selección calculada.",
    "Read every original observation from the admitted structural-break case.":
        "Lee cada observación original del caso sintético con cambio estructural.",
    "Read the already fixed fifteen-case experiment, without tuning to its outcomes.":
        "Lee el experimento fijo de quince casos sin ajustar parámetros a sus resultados.",
    "Read the authentic hourly excerpt and inspect its time axis before forecasting.":
        "Lee el extracto horario auténtico e inspecciona su eje temporal antes de pronosticar.",
    "Read the complete admitted feature and error table with its series partitions.":
        "Lee la tabla admitida de características y errores con sus particiones por serie.",
    "Recompute scores of released neural and pretrained paths without claiming refits.":
        "Recalcula puntuaciones de trayectorias conservadas sin atribuirles un ajuste nuevo.",
    "Refit after a positive change of units and common location shift.":
        "Reajusta después de un cambio positivo de unidades y un desplazamiento común.",
    "Refit an earlier information cutoff, then inspect original-query weights.":
        "Reajusta con un corte anterior e inspecciona los pesos de la consulta original.",
    "Refit the seasonal reference and Theta at the earlier origin as well.":
        "Reajusta también la referencia estacional y Theta en el origen anterior.",
    "Remove context similarity while retaining the expert set and recency rule.":
        "Retira la similitud contextual y conserva los expertos y la regla de recencia.",
    "Remove five known observations to create an incomplete terminal season.":
        "Retira cinco observaciones conocidas para crear un ciclo estacional terminal incompleto.",
    "Repeat all preregistered feature tests in each disjoint series partition.":
        "Repite todas las pruebas predeclaradas en cada partición disjunta de series.",
    "Repeat robust nonlinear estimates with an explicit local seed.":
        "Repite estimaciones no lineales robustas con una semilla local explícita.",
    "Repeat the calculations after a positive affine unit conversion.":
        "Repite los cálculos después de una conversión afín positiva de unidades.",
    "Run the actual installed reference adapter, with the released ETS settings.":
        "Ejecuta el adaptador de referencia instalado con los parámetros ETS publicados.",
    "Run the complete sequence diagnostic with an explicit candidate period.":
        "Ejecuta el diagnóstico completo con un período candidato explícito.",
    "Run the point-regression lag-tree adapter, not a quantile-regression substitute.":
        "Ejecuta el adaptador de árboles con rezagos y regresión puntual.",
    "Select contextual parameters using complete earlier target blocks.":
        "Selecciona parámetros contextuales con bloques objetivo anteriores completos.",
    "Separate a legitimate zero entropy from insufficient coarse observations.":
        "Distingue una entropía cero legítima de la falta de observaciones agregadas.",
    "Show the first twelve features in schema order rather than significance order.":
        "Muestra las primeras doce características según el esquema, sin ordenar por significación.",
    "Start from the prefix, then request all three quantile columns together.":
        "Parte del prefijo y solicita juntas las tres columnas de cuantiles.",
    "The committed trace separates available history from the unseen final block.":
        "La traza versionada separa la historia disponible del bloque final no observado.",
    "The earlier-origin target is different, so its scores form a separate experiment.":
        "El objetivo del origen anterior es distinto; sus puntuaciones forman otro experimento.",
    "The equal-weight ablation removes estimated loss preferences as well.":
        "La ablación de pesos uniformes retira también las preferencias de pérdida estimadas.",
    "Track entropy and matching-pair counts under three declared tolerances.":
        "Sigue la entropía y los pares coincidentes bajo tres tolerancias declaradas.",
    "Train the fixed selector again using discovery rows and discovery-only imputation.":
        "Reentrena el selector fijo usando solo filas e imputación del conjunto de descubrimiento.",
    "Verify a prefix-only profile without admitting future observations.":
        "Calcula el perfil de un prefijo sin admitir observaciones futuras.",
}


def localize_code(source: str) -> str:
    """Translate exact human-facing tokens while retaining schema and API literals."""
    tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    translated = []
    for index, token in enumerate(tokens):
        value = token.string
        if token.type == tokenize.COMMENT:
            text = value.removeprefix("# ")
            if text in COMMENTS_ES:
                value = "# " + COMMENTS_ES[text]
        elif token.type == getattr(tokenize, "FSTRING_MIDDLE", -1):
            for english, spanish in sorted(DISPLAY_ES.items(), key=lambda pair: -len(pair[0])):
                if english.strip() and english not in {"history", "actual", "coverage"}:
                    value = value.replace(english, spanish)
        elif token.type == tokenize.STRING:
            previous = tokens[index - 1].string if index else ""
            following = tokens[index + 1].string if index + 1 < len(tokens) else ""
            if previous != "[" and following != ":":
                try:
                    literal = ast.literal_eval(value)
                except (ValueError, SyntaxError):
                    literal = None
                if isinstance(literal, str) and literal in DISPLAY_ES:
                    value = repr(DISPLAY_ES[literal])
                elif value.startswith(('f"', "f'")):
                    for english, spanish in DISPLAY_ES.items():
                        if english.strip() and english not in {"history", "actual", "coverage"}:
                            value = value.replace(english, spanish)
        translated.append(token._replace(string=value))
    result = tokenize.untokenize(translated)
    for before, after in [('label="discovery"', 'label="descubrimiento"'),
                           ('label="confirmation"', 'label="confirmación"')]:
        result = result.replace(before, after)
    for before in ('f"{window}-observation window"', 'f"{window} observaciones por ventana"'):
        result = result.replace(before, 'f"Ventana de {window} observaciones"')
    for before in ('f"{metric.upper()} difference from RecencyMean"',
                   'f"{metric.upper()} diferencia respecto a RecencyMean"'):
        result = result.replace(before, 'f"Diferencia de {metric.upper()} frente a RecencyMean"')
    return result


def cell(kind: str, text: str, key: str) -> dict:
    result = {"cell_type": kind, "source": text.strip() + "\n", "metadata": {},
              "id": hashlib.sha256(key.encode()).hexdigest()[:12]}
    if kind == "code":
        result.update(execution_count=None, outputs=[])
    return result


def text_of(item: dict) -> str:
    source = item["source"]
    return "".join(source) if isinstance(source, list) else source


def add_before_results(document: dict, additions: list[dict]) -> None:
    cells = document["cells"]
    position = next((i for i, item in enumerate(cells) if item["cell_type"] == "markdown"
                     and re.search(r"(?m)^## (Results|Resultados)\b", text_of(item))), len(cells))
    cells[position:position] = additions


def header(document: dict, lang: str) -> None:
    meta = document["metadata"]["caos"]
    first = document["cells"][0]
    text = text_of(first)
    if "**Reading time:" in text or "**Tiempo de lectura:" in text:
        return
    level = meta["level"]
    if lang == "es":
        prerequisites = ("Python básico y lectura de gráficos" if level == 1 else
                         "Las lecciones anteriores de este tema; arrays NumPy y evaluación temporal")
        details = f"**Nivel:** {level}. **Requisitos previos:** {prerequisites}. **Tiempo de lectura:** {20 + 10 * level} minutos."
    else:
        prerequisites = ("Basic Python and reading charts" if level == 1 else
                         "Earlier lessons in this topic; NumPy arrays and temporal evaluation")
        details = f"**Level:** {level}. **Prerequisites:** {prerequisites}. **Reading time:** {20 + 10 * level} minutes."
    lines = text.splitlines()
    lines.insert(1, "\n" + details)
    first["source"] = "\n".join(lines) + "\n"


def set_data_provenance(document: dict, relative: str, lang: str) -> None:
    """Replace the former generic provenance assurance with the actual source contract."""
    name = Path(relative).stem
    english = {
        "01-baseline": "The source owner is UCI (ElectricityLoadDiagrams20112014, client MT_010), "
            "https://doi.org/10.24432/C58C86, licensed CC BY 4.0. The committed "
            "`data/examples/electricity_sample.csv` contains 480 hourly-labelled rows: `unique_id` is the client, "
            "`ds` the recorded local timestamp and `y` the sum of four consecutive 15-minute power readings in kW. "
            "The grouping is not an integration to kWh. This baseline uses its observed ordering without claiming "
            "timezone-aware duration or a calibrated energy forecast.",
        "02-seasonal-phase": "The initial phase illustration reads the synthetic TRND_seasonal fixture from "
            "`data/derived/TRND_seasonal/trace.json`; it is generated by the product's "
            "`data-pipeline/engine/cases/forecast_cases.py` with seed 42 and period 12, under the MIT licence. "
            "Its history and final actual fields are contiguous source values in generated units. The subsequent "
            "phase sensitivity uses authentic client MT_010 from UCI ElectricityLoadDiagrams20112014 "
            "(https://doi.org/10.24432/C58C86, CC BY 4.0), `data/examples/electricity_sample.csv`. "
            "Its hourly labels group four 15-minute kW readings by summation; no conversion to energy is made.",
        "03-model-comparison": "This shared adapter experiment takes the synthetic trend-plus-season fixture "
            "TRND_seasonal from `data/derived/TRND_seasonal/trace.json`. Its owner is the ChronoScope project, "
            "licence MIT; the seed-42 generator is `data-pipeline/engine/cases/forecast_cases.py`. The "
            "history is the available fitting prefix, actual is its consecutive reserved final block, seasonality "
            "is 12 observations and horizon is 12 predictions. Values have generated source units. Retained "
            "paths are identified separately from calls executed here. The reference package and checkpoint "
            "sources are listed in References; a model's prior pretraining exposure is not ruled out by this example.",
        "04-context-memory": "ContextMemory's worked allocation uses the explicitly synthetic, MIT-licensed "
            "TRND_seasonal history and final block in `data/derived/TRND_seasonal/trace.json`. Its seed-42 "
            "trend-plus-period-12 generator belongs to ChronoScope (`data-pipeline/engine/cases/forecast_cases.py`). "
            "The broader fixed collection in `data/derived/reevaluation.json` has fifteen selected series: four "
            "authentic source series and eleven generated controls. Each case supplies history, actual, horizon, "
            "seasonality and method forecasts; per-method metrics use that case's historical seasonal scale. "
            "These selected cases are a finite development inventory, not random draws from a target population.",
        "05-temporal-validation": "The temporal-selection illustration is the generated BRKV_level_shift "
            "case, owned by ChronoScope under MIT, from `data/derived/reevaluation.json`; its seed-42 generator "
            "is `data-pipeline/engine/cases/forecast_cases.py`. Values have generated units. The separately "
            "admitted M4 Weekly (https://doi.org/10.5281/zenodo.4656522) and M3 Monthly "
            "(https://doi.org/10.5281/zenodo.4656298) collections are supplied through the Monash forecasting "
            "archive under CC BY 4.0. `data/derived/validated-combinations.json` records the archive and TSF "
            "SHA-256 revisions and points to per-series files with source history, reserved origins, all common "
            "forecast paths and their scores. Weekly horizon/seasonality are 13/52; monthly values are 18/12. "
            "The fifteen development cases remain distinct from those external collections.",
        "01-shape-patterns": "The mechanism illustration is the synthetic BRKV_level_shift sequence in "
            "`data/derived/BRKV_level_shift/analysis.json`, generated with seed 42 by ChronoScope's "
            "`data-pipeline/engine/cases/forecast_cases.py` under MIT. Its field sequence.values retains all "
            "300 generated observations and their original index. Its boundaries are retrospective diagnostics, "
            "not measured change-point labels. A second actual API run below uses the authentic UCI MT_010 "
            "electricity excerpt (`data/examples/electricity_sample.csv`, https://doi.org/10.24432/C58C86, "
            "CC BY 4.0): y sums four 15-minute power readings, in kW-sum source units, per hourly label.",
        "02-complexity": "The entropy and reversal controls use the explicitly synthetic BRKV_level_shift "
            "sequence, read without decimation from sequence.values in "
            "`data/derived/BRKV_level_shift/analysis.json`. ChronoScope owns its deterministic seed-42 generator "
            "(`data-pipeline/engine/cases/forecast_cases.py`, MIT); generated observation indices are not "
            "calendar times. A separate volatility calculation uses the observed MT_010 electricity slice from "
            "UCI (https://doi.org/10.24432/C58C86, CC BY 4.0), stored in "
            "`data/examples/electricity_sample.csv`. Each y is a sum of four kW readings; its differences and "
            "conditional standard deviations therefore retain these source units, rather than energy units.",
        "03-corpus-confirmation": "The corpus is M4 Daily from the Monash forecasting archive "
            "(https://doi.org/10.5281/zenodo.4656548, CC BY 4.0). The compact "
            "`data/derived/forecastability.json` records source filename m4_daily_dataset.zip and source "
            "SHA-256 0f07fc3b67a93be1865de7853e06d8ad212f1a8cb8436ba859920cfe5625d889. Each series row "
            "retains its disjoint partition, pre-target features and per-method errors averaged over three origins; "
            "the fixed horizon is 14 and seasonal lag one. Fitting the selector from these rows is a new "
            "selector fit, not a repeat of the original forecast generation. The separately loaded BRKV values "
            "illustrate feature extraction only: they are synthetic seed-42 MIT controls, not M4 observations.",
        "04-information-boundaries": "The real input belongs to UCI ElectricityLoadDiagrams20112014, "
            "client MT_010 (https://doi.org/10.24432/C58C86), distributed under CC BY 4.0. "
            "`data/examples/electricity_sample.csv` stores unique_id, recorded local time ds and target y. "
            "Four consecutive 15-minute power readings are summed into each hourly-labelled y; these source "
            "units do not equal kWh. The teaching prefix and its next-day target are consecutive rows of this "
            "sample; later full-length retained studies use different cutoffs. Generated browser calibration "
            "series and generated training controls remain explicitly separate from this authentic observation stream.",
    }
    spanish = {
        "01-baseline": "El propietario es UCI (ElectricityLoadDiagrams20112014, cliente MT_010), "
            "https://doi.org/10.24432/C58C86, con licencia CC BY 4.0. El archivo versionado "
            "`data/examples/electricity_sample.csv` contiene 480 filas con etiqueta horaria: unique_id identifica "
            "al cliente, ds es la hora local registrada e y suma cuatro lecturas consecutivas de potencia en kW "
            "cada 15 minutos. La agrupación no integra energía en kWh. La referencia utiliza el orden observado "
            "sin atribuirle duraciones corregidas por zona horaria ni calibración de un pronóstico energético.",
        "02-seasonal-phase": "La ilustración inicial usa TRND_seasonal, un control sintético de ChronoScope "
            "con licencia MIT, desde `data/derived/TRND_seasonal/trace.json`. Lo genera "
            "`data-pipeline/engine/cases/forecast_cases.py` con semilla 42 y período 12. History y actual "
            "conservan valores contiguos en unidades generadas. La sensibilidad posterior utiliza observaciones "
            "auténticas del cliente MT_010 de UCI ElectricityLoadDiagrams20112014 "
            "(https://doi.org/10.24432/C58C86, CC BY 4.0), en `data/examples/electricity_sample.csv`. "
            "Sus etiquetas horarias agrupan por suma cuatro lecturas de potencia en kW; no se convierten en energía.",
        "03-model-comparison": "El experimento común de adaptadores utiliza el control sintético TRND_seasonal "
            "con tendencia y ciclo, desde `data/derived/TRND_seasonal/trace.json`. ChronoScope es su propietario, "
            "bajo MIT; el generador con semilla 42 está en `data-pipeline/engine/cases/forecast_cases.py`. "
            "History contiene el prefijo disponible, actual el bloque final consecutivo reservado, seasonality "
            "vale 12 observaciones y horizon vale 12 predicciones. Las unidades son generadas. Se distinguen "
            "las trayectorias conservadas de las llamadas ejecutadas aquí. Referencias identifica paquetes y "
            "modelos; este ejemplo no descarta exposición de los modelos preentrenados a datos semejantes.",
        "04-context-memory": "La asignación trabajada de ContextMemory usa la historia y el bloque final "
            "explícitamente sintéticos de TRND_seasonal en `data/derived/TRND_seasonal/trace.json`, con licencia "
            "MIT. Su generador de tendencia y período 12 pertenece a ChronoScope "
            "(`data-pipeline/engine/cases/forecast_cases.py`, semilla 42). La colección fija en "
            "`data/derived/reevaluation.json` contiene quince series seleccionadas: cuatro auténticas y once "
            "controles generados. Cada caso aporta history, actual, horizon, seasonality y pronósticos; sus "
            "métricas usan la escala estacional histórica del caso. Es un inventario finito de desarrollo, "
            "no una muestra aleatoria de una población objetivo.",
        "05-temporal-validation": "La ilustración de selección temporal usa BRKV_level_shift, un caso "
            "generado de ChronoScope con licencia MIT, desde `data/derived/reevaluation.json`; su generador "
            "con semilla 42 es `data-pipeline/engine/cases/forecast_cases.py` y las unidades son generadas. "
            "M4 Weekly (https://doi.org/10.5281/zenodo.4656522) y M3 Monthly "
            "(https://doi.org/10.5281/zenodo.4656298) proceden separadamente del archivo Monash, con "
            "licencia CC BY 4.0. `data/derived/validated-combinations.json` registra los SHA-256 del archivo "
            "y del TSF, y enlaza archivos por serie con historia, orígenes reservados, trayectorias comunes y "
            "puntuaciones. Horizonte/período son 13/52 en semanal y 18/12 en mensual. Los quince casos "
            "de desarrollo se mantienen separados de estas colecciones externas.",
        "01-shape-patterns": "La ilustración del mecanismo es BRKV_level_shift, una secuencia sintética en "
            "`data/derived/BRKV_level_shift/analysis.json`, generada con semilla 42 por ChronoScope "
            "(`data-pipeline/engine/cases/forecast_cases.py`, MIT). Sequence.values conserva las 300 "
            "observaciones generadas y sus índices originales. Los límites son diagnósticos retrospectivos, "
            "no etiquetas de cambios medidos. Otra ejecución real de la API utiliza el extracto auténtico "
            "MT_010 de UCI (`data/examples/electricity_sample.csv`, https://doi.org/10.24432/C58C86, "
            "CC BY 4.0): y suma cuatro lecturas de potencia cada 15 minutos por etiqueta horaria, en unidades "
            "de suma de lecturas en kW.",
        "02-complexity": "Los controles de entropía e inversión usan BRKV_level_shift, una secuencia "
            "explícitamente sintética leída sin reducción desde sequence.values en "
            "`data/derived/BRKV_level_shift/analysis.json`. ChronoScope es propietario del generador "
            "determinista con semilla 42 (`data-pipeline/engine/cases/forecast_cases.py`, MIT); sus índices "
            "no son fechas. El cálculo separado de volatilidad usa el extracto observado MT_010 de UCI "
            "(https://doi.org/10.24432/C58C86, CC BY 4.0), en `data/examples/electricity_sample.csv`. "
            "Cada y suma cuatro lecturas en kW: las diferencias y desviaciones condicionales conservan "
            "estas unidades de la fuente y no representan energía.",
        "03-corpus-confirmation": "El corpus es M4 Daily del archivo Monash "
            "(https://doi.org/10.5281/zenodo.4656548, CC BY 4.0). La tabla compacta "
            "`data/derived/forecastability.json` identifica m4_daily_dataset.zip y su SHA-256 "
            "0f07fc3b67a93be1865de7853e06d8ad212f1a8cb8436ba859920cfe5625d889. Cada fila conserva "
            "partición disjunta, características anteriores al objetivo y errores por método promediados en "
            "tres orígenes; horizonte 14 y rezago estacional uno. Reajustar el selector con estas filas no "
            "vuelve a generar los pronósticos originales. Los valores BRKV cargados aparte ilustran únicamente "
            "la extracción de características: son controles sintéticos MIT con semilla 42, no observaciones M4.",
        "04-information-boundaries": "La entrada real pertenece a UCI ElectricityLoadDiagrams20112014, "
            "cliente MT_010 (https://doi.org/10.24432/C58C86), con licencia CC BY 4.0. "
            "`data/examples/electricity_sample.csv` guarda unique_id, hora local registrada ds y objetivo y. "
            "Se suman cuatro lecturas de potencia cada 15 minutos por etiqueta horaria; estas unidades "
            "no equivalen a kWh. El prefijo didáctico y el día siguiente son filas consecutivas de la muestra; "
            "los estudios conservados de longitud completa usan cortes distintos. Las series generadas para "
            "calibración del navegador y entrenamiento se distinguen de este flujo auténtico de observaciones.",
    }
    marker = "## Data" if lang == "en" else "## Datos"
    for item in document["cells"]:
        if item["cell_type"] != "markdown":
            continue
        text = text_of(item)
        if marker not in text:
            continue
        description = (english if lang == "en" else spanish)[name]
        item["source"] = re.sub(r"(?ms)^" + re.escape(marker) + r"\s*\n.*?(?=^## |\Z)",
                                marker + "\n\n" + description + "\n\n", text, count=1)
        break


def uncertainty(document: dict, name: str, lang: str) -> None:
    if any(item.get("id") == hashlib.sha256(f"{name}/uncertainty-intro".encode()).hexdigest()[:12]
           for item in document["cells"]):
        return
    if name == "04-context-memory":
        introduction = (
            "### Uncertainty from the finite case composition\n\n"
            "First refit all three rules on each of the fifteen original histories. The target block is passed "
            "only to the scorer, and each series contributes one paired ContextMemory-minus-RecencyMean MASE. "
            "This calculation reproduces the finite primary comparison rather than treating cached aggregate "
            "bars as a model execution. We then draw 4,000 bootstrap inventories, with seed 20261122, by sampling "
            "whole case identities with replacement. The 2.5th and 97.5th percentiles describe sensitivity to "
            "case composition under empirical exchangeability. These selected controls and authentic series "
            "are not a probability sample: the interval is not a population confidence claim or evidence that "
            "the development experiment became independent. Every adverse case remains in the sampling frame."
            if lang == "en" else
            "### Incertidumbre por la composición finita de casos\n\n"
            "Primero reajustamos las tres reglas sobre cada una de las quince historias originales. El bloque "
            "objetivo se entrega únicamente a la puntuación; cada serie aporta una diferencia pareada de MASE "
            "entre ContextMemory y RecencyMean. Así se calcula el contraste primario finito sin presentar barras "
            "agregadas conservadas como ejecución de un modelo. Después generamos 4.000 inventarios bootstrap, "
            "con semilla 20261122, remuestreando identidades completas de casos con reemplazo. Los percentiles "
            "2,5 y 97,5 describen sensibilidad a la composición bajo intercambiabilidad empírica. Los controles "
            "y series auténticas seleccionados no son una muestra probabilística: el intervalo no afirma "
            "cobertura poblacional ni vuelve independiente el experimento de desarrollo. Todos los casos "
            "desfavorables permanecen en el conjunto remuestreado."
        )
        code = '''# Refit each rule before resampling whole paired series, never individual leads.
paired = []
for case in comparison["cases"]:
    available = np.asarray(case["history"], dtype=float)
    reserved = np.asarray(case["actual"], dtype=float)
    case_scores = {}
    for rule in ("context", "recency", "uniform"):
        fitted = fit_context_memory(available, case["seasonality"], case["horizon"], mode=rule)
        q = fitted.quantiles
        case_scores[rule] = metrics(available, reserved, q[:, 1], q[:, 0], q[:, 2],
                                   case["seasonality"])["mase"]
    paired.append(case_scores["context"] - case_scores["recency"])
paired = np.asarray(paired)
rng = np.random.default_rng(20261122)
resampled = paired[rng.integers(len(paired), size=(4000, len(paired)))].mean(axis=1)
lower, upper = np.quantile(resampled, [0.025, 0.975])
print("Series, paired mean, lower and upper:", len(paired), *np.round([paired.mean(), lower, upper], 6))
fig, ax = plt.subplots()
ax.hist(resampled, bins=40, color="#267a6d", alpha=0.8)
ax.axvline(0, color="black", linestyle="--")
ax.axvspan(lower, upper, color="grey", alpha=0.15)
ax.set(xlabel="Mean paired MASE difference (dimensionless)", ylabel="Resampled inventories")
fig.tight_layout()
plt.show()
'''
        interpretation = (
            "The distribution varies the inventory weights, not the observed outcomes or the forecasting rule. "
            "An interval containing zero is compatible with either sign under this particular reweighting. An "
            "interval wholly on one side would still depend on the selected empirical case mixture and would "
            "not establish transportability. The exact finite mean is the primary descriptive result; the "
            "uncertainty plot explains how unstable its sign can be when entire series receive different weights."
            if lang == "en" else
            "La distribución cambia los pesos del inventario, no los resultados observados ni la regla de "
            "pronóstico. Un intervalo que contiene cero admite ambos signos bajo esta reponderación concreta. "
            "Un intervalo de un solo signo seguiría dependiendo de la mezcla empírica seleccionada y no probaría "
            "transferencia a otras series. La media finita exacta conserva su papel descriptivo principal; "
            "el gráfico muestra cuánto puede cambiar su signo al ponderar de otra forma series completas."
        )
    else:
        introduction = (
            "### Series-level uncertainty on the external collections\n\n"
            "The unit of analysis is a source series, not an origin or forecast lead. Only entries with at "
            "least one admitted origin enter the bootstrap: the inventory still retains 65 weekly exclusions "
            "and six monthly duplicates, but their empty origin lists are not observations. For each admitted external "
            "series, recompute ValidationMix-minus-RecencyMean MASE from the retained point paths and target "
            "values using that origin's recorded historical scale, then average its complete common origins. "
            "This rescores retained forecasts; it does not refit the external models. A seeded bootstrap draws "
            "4,000 samples of whole series separately within each collection and reports a percentile interval. "
            "Repeated origins stay together, preserving their within-series dependence. The procedure assumes "
            "exchangeability between source series; common source mechanisms can violate that assumption. "
            "The collections are fixed benchmarks, so these are conditional stability intervals for their "
            "empirical series mix, not guaranteed intervals for operational accuracy on new clients."
            if lang == "en" else
            "### Incertidumbre por serie en las colecciones externas\n\n"
            "La unidad de análisis es la serie original, no un origen ni una anticipación. Solo entran "
            "entradas con al menos un origen admitido: el inventario conserva 65 exclusiones semanales y "
            "seis duplicados mensuales, pero sus listas vacías no son observaciones. Para cada serie "
            "externa admitida recalculamos MASE de ValidationMix menos RecencyMean a partir de trayectorias "
            "puntuales conservadas, objetivos y escala histórica registrada por origen; después promediamos "
            "todos sus orígenes comunes completos. Esto vuelve a puntuar pronósticos conservados, sin reajustar "
            "modelos externos. Un bootstrap con semilla toma 4.000 muestras de series completas por colección "
            "y calcula un intervalo percentil. Los orígenes repetidos permanecen juntos, conservando su "
            "dependencia interna. Se supone intercambiabilidad entre series originales; mecanismos compartidos "
            "pueden incumplirla. Son benchmarks fijos: los intervalos describen estabilidad condicional a su "
            "mezcla empírica, sin garantizar exactitud operativa en clientes nuevos."
        )
        code = '''# Recompute common-origin scores and keep each source series intact in the bootstrap.
intervals = []
rng = np.random.default_rng(20261122)
for dataset in ("m4_weekly", "m3_monthly"):
    paired_series = []
    for entry in (item for item in study["cases"] if item["dataset"] == dataset and item["origins"] > 0):
        record = combination_records[(dataset, entry["id"])]
        differences = []
        for origin in record["origins"]:
            points = {row["name"]: np.asarray(row["quantiles"])[:, 1] for row in origin["methods"]}
            truth = np.asarray(origin["actual"])
            left = np.mean(np.abs(truth - points["ValidationMix"])) / origin["scale"]
            right = np.mean(np.abs(truth - points["RecencyMean"])) / origin["scale"]
            differences.append(left - right)
        paired_series.append(np.mean(differences))
    delta_series = np.asarray(paired_series)
    samples = delta_series[rng.integers(len(delta_series), size=(4000, len(delta_series)))].mean(axis=1)
    lo, hi = np.quantile(samples, [0.025, 0.975])
    intervals.append((dataset, len(delta_series), delta_series.mean(), lo, hi))
    values = np.round([delta_series.mean(), lo, hi], 6)
    print(dataset, "series, mean, lower, upper:", len(delta_series), *values)
fig, ax = plt.subplots()
for index, (dataset, count, mean, lo, hi) in enumerate(intervals):
    ax.plot([lo, hi], [index, index], color="#267a6d", linewidth=3)
    ax.scatter([mean], [index], color="black")
ax.axvline(0, color="black", linestyle="--")
ax.set_yticks(range(len(intervals)), [row[0] for row in intervals])
ax.set(xlabel="ValidationMix minus RecencyMean MASE (dimensionless)", ylabel="Source collection")
fig.tight_layout()
plt.show()
'''
        interpretation = (
            "Each dot is recomputed from per-origin paths, and its horizontal segment changes series "
            "composition while retaining every origin of a drawn series. A negative mean favors ValidationMix "
            "on the point criterion only. It cannot overturn the separately reported interval-score comparison "
            "or AutoTheta's result. Weekly and monthly intervals describe different source populations and "
            "remain separate. These diagnostic intervals do not replace evaluation on a newly acquired "
            "collection with settings fixed before seeing its targets."
            if lang == "en" else
            "Cada punto se recalcula desde las trayectorias por origen; su segmento horizontal modifica la "
            "composición de series conservando todos los orígenes de cada serie extraída. Una media negativa "
            "favorece ValidationMix solo en el criterio puntual. No cambia el contraste separado de puntuación "
            "de intervalos ni el resultado de AutoTheta. Los intervalos semanales y mensuales corresponden "
            "a fuentes distintas y permanecen separados. Este diagnóstico no reemplaza evaluar una colección "
            "nueva con parámetros fijados antes de observar sus objetivos."
        )
    if lang == "es":
        replacements = {
            "# Refit each rule before resampling whole paired series, never individual leads.":
                "# Reajusta las reglas y remuestrea series pareadas completas, nunca anticipaciones aisladas.",
            "# Recompute common-origin scores and keep each source series intact in the bootstrap.":
                "# Recalcula puntuaciones comunes y conserva cada serie completa en el bootstrap.",
            "Series, paired mean, lower and upper:": "Series, media pareada, límite inferior y superior:",
            "Mean paired MASE difference (dimensionless)": "Diferencia media pareada de MASE (adimensional)",
            "Resampled inventories": "Inventarios remuestreados",
            "series, mean, lower, upper:": "series, media, límite inferior y superior:",
            "ValidationMix minus RecencyMean MASE (dimensionless)":
                "MASE de ValidationMix menos RecencyMean (adimensional)",
            "Source collection": "Colección de origen",
        }
        for before, after in replacements.items():
            code = code.replace(before, after)
    additions = [cell("markdown", introduction, f"{name}/uncertainty-intro"),
                 cell("code", code, f"{name}/uncertainty-code"),
                 cell("markdown", interpretation, f"{name}/uncertainty-result")]
    add_before_results(document, additions)


def numerical_distance(document: dict, lang: str) -> None:
    key = "context/rms-distance"
    if any(item.get("id") == hashlib.sha256(key.encode()).hexdigest()[:12] for item in document["cells"]):
        return
    explanation = (
        "### The distance that actually determines the kernel\n\n"
        "The four coordinates are normalized slope, level shift, log volatility ratio and seasonal "
        "correlation, each clipped to [-4, 4]. This is not a fitted standardization across memory rows. "
        "Let z_o be an origin's four-vector and z_q the query vector. The distance is RMS coordinate "
        "distance, and the bandwidth has an explicit dimensionless lower bound:\n\n"
        "$$d_o=\\left(\\frac14\\sum_{\\ell=1}^{4}(z_{o\\ell}-z_{q\\ell})^2\\right)^{1/2},\\qquad "
        "b=\\max\\{\\operatorname{median}_o d_o,0.25\\},\\qquad K_o=\\exp[-d_o^2/(2b^2)].$$\n\n"
        "The next diagnostic calls the released feature helper on remembered prefixes, then shows one "
        "distance and the bandwidth. It does not replace the package's forecast fit. Away from the floor, "
        "a common rescaling of every distance also rescales the median; at the floor the convention matters."
        if lang == "en" else
        "### La distancia que determina el núcleo\n\n"
        "Las cuatro coordenadas son pendiente normalizada, cambio de nivel, logaritmo de la razón de "
        "volatilidades y correlación estacional, recortadas a [-4, 4]. No se ajusta una estandarización "
        "entre filas de memoria. Sea z_o el vector de cuatro coordenadas de un origen y z_q el de la "
        "consulta. La distancia es la raíz de la media de cuadrados y el ancho tiene un piso adimensional:\n\n"
        "$$d_o=\\left(\\frac14\\sum_{\\ell=1}^{4}(z_{o\\ell}-z_{q\\ell})^2\\right)^{1/2},\\qquad "
        "b=\\max\\{\\operatorname{median}_o d_o,0.25\\},\\qquad K_o=\\exp[-d_o^2/(2b^2)].$$\n\n"
        "El diagnóstico llama al extractor publicado sobre los prefijos recordados y muestra una "
        "distancia y el ancho. No reemplaza el ajuste del paquete. Lejos del piso, reescalar todas "
        "las distancias también reescala la mediana; cerca del piso la convención sí cambia el núcleo."
    )
    code = '''# Inspect normalized feature distances without replacing the forecast implementation.
remembered = np.asarray([context_features(history[:origin], m) for origin in context_fit.origins])
distances = np.sqrt(np.mean((remembered - context_fit.context) ** 2, axis=1))
bandwidth = max(float(np.median(distances)), 0.25)
print("Query features:", np.round(context_fit.context, 6))
print("First RMS distance and bandwidth:", round(float(distances[0]), 6), round(bandwidth, 6))
print("First Gaussian kernel:", round(float(np.exp(-0.5 * (distances[0] / bandwidth) ** 2)), 6))
'''
    if lang == "es":
        code = code.replace("# Inspect normalized feature distances without replacing the forecast implementation.",
                            "# Inspecciona distancias de características sin reemplazar el pronosticador.")
        for before, after in {"Query features:": "Características de la consulta:",
                              "First RMS distance and bandwidth:": "Primera distancia RMS y ancho:",
                              "First Gaussian kernel:": "Primer peso del núcleo gaussiano:"}.items():
            code = code.replace(before, after)
    position = next(i for i, item in enumerate(document["cells"]) if item["cell_type"] == "code"
                    and "context_fit = fit_context_memory" in text_of(item)) + 1
    document["cells"][position:position] = [cell("markdown", explanation, key), cell("code", code, key + "/code")]


def authentic_shapes(document: dict, lang: str) -> None:
    key = "shapes/authentic-input"
    if any(item.get("id") == hashlib.sha256(key.encode()).hexdigest()[:12] for item in document["cells"]):
        return
    introduction = (
        "### Repeated shapes in measured electricity readings\n\n"
        "A synthetic level shift explains a mechanism but cannot establish the behavior of an observed "
        "customer. Now use the complete authentic MT_010 excerpt through the same public matrix-profile API, "
        "with a 24-observation window matching one labelled day. The raw upper panel remains in sums of "
        "power readings; the profile below measures z-normalized shape distance, with no physical unit. "
        "Normalization removes each window's mean and scale, so a similar daily shape need not imply equal "
        "absolute load. Neither nearest-neighbor similarity nor a low profile value establishes a future "
        "forecast advantage. The exclusion zone still removes trivial overlapping neighbors."
        if lang == "en" else
        "### Formas repetidas en lecturas eléctricas medidas\n\n"
        "Un cambio de nivel sintético explica un mecanismo, pero no establece cómo se comporta un cliente "
        "observado. Usamos ahora el extracto auténtico MT_010 completo mediante la misma API pública de "
        "perfil matricial, con ventana de 24 observaciones que corresponde a un día etiquetado. El panel "
        "superior conserva la suma de lecturas de potencia; el inferior mide distancia de formas "
        "normalizadas por puntuación z, sin unidad física. Normalizar retira media y escala por ventana: "
        "una forma diaria similar no implica igual carga absoluta. La similitud ni un perfil bajo prueban "
        "ventaja predictiva futura. La zona de exclusión elimina vecinos triviales solapados."
    )
    code = '''# Apply the same sequence API to authentic measurements with their original row axis.
real_profile = matrix_profile(electricity_values, window=24)
fig, axes = plt.subplots(2, 1, figsize=(8, 5))
axes[0].plot(electricity_values, color="#267a6d")
axes[0].set(xlabel="Hourly-labelled observation", ylabel="Sum of kW readings")
axes[1].plot(real_profile["profile"], color="#a65132")
axes[1].set(xlabel="Original window start", ylabel="Z-normalized distance (dimensionless)")
fig.tight_layout()
plt.show()
print("Observed rows and profile starts:", len(electricity_values), len(real_profile["profile"]))
print("Authentic motif pairs:", real_profile["motifs"])
'''
    interpretation = (
        "The second profile is newly computed from authentic observations; no generated breakpoint is "
        "transferred to the customer. Compare a low-distance pair's shapes with its absolute level in the "
        "upper panel before interpreting recurrence as similar demand. The window start remains an index "
        "of the original hourly-labelled rows. The picture is retrospective across all observed rows, "
        "and therefore is not an online alert or a held-out accuracy assessment."
        if lang == "en" else
        "El segundo perfil se calcula de nuevo con observaciones auténticas; ningún punto de cambio "
        "generado se transfiere al cliente. Antes de interpretar recurrencia como demanda similar, "
        "compara las formas cercanas con sus niveles absolutos en el panel superior. El inicio de ventana "
        "conserva el índice de las filas originales. Es una imagen retrospectiva de todas las filas "
        "observadas, no una alerta en línea ni una evaluación de exactitud sobre datos reservados."
    )
    if lang == "es":
        for before, after in {
            "# Apply the same sequence API to authentic measurements with their original row axis.":
                "# Aplica la misma API a mediciones auténticas con sus índices originales.",
            "Hourly-labelled observation": "Observación con etiqueta horaria",
            "Sum of kW readings": "Suma de lecturas en kW",
            "Original window start": "Inicio original de ventana",
            "Z-normalized distance (dimensionless)": "Distancia normalizada z (adimensional)",
            "Observed rows and profile starts:": "Filas observadas e inicios de perfil:",
            "Authentic motif pairs:": "Pares de motivos auténticos:",
        }.items():
            code = code.replace(before, after)
    add_before_results(document, [cell("markdown", introduction, key), cell("code", code, key + "/code"),
                                 cell("markdown", interpretation, key + "/reading")])


def volatility_lesson(document: dict, lang: str) -> None:
    key = "complexity/forecastscope-volatility"
    if any(item.get("id") == hashlib.sha256(key.encode()).hexdigest()[:12] for item in document["cells"]):
        return
    explanation = (
        "### Variability and conditional volatility on authentic observations\n\n"
        "Entropy summarizes regularity after a declared encoding or tolerance; conditional volatility "
        "answers a different question about the scale of an innovation. Use ForecastScope 0.1.1 directly "
        "on first differences of the observed electricity values, keeping all 479 consecutive differences. "
        "A difference ending at original row t remains aligned to t; dropping non-finite observations before "
        "this step would silently change its time interpretation. Here all admitted values are finite. "
        "The first-difference mean is estimated in sample. A day/night pattern can remain, so neither "
        "a small ARCH p-value nor a fitted GARCH recurrence proves stochastic volatility after a correctly "
        "specified conditional mean. These are explicitly descriptive calculations on this finite excerpt.\n\n"
        "For GARCH(1,1), the conditional variance obeys\n\n"
        "$$\\sigma_t^2=\\omega+\\alpha\\epsilon_{t-1}^2+\\beta\\sigma_{t-1}^2.$$\n\n"
        "Here epsilon is the demeaned change, omega is the variance intercept, alpha the squared-shock "
        "coefficient and beta the lagged conditional-variance coefficient; the reported persistence is "
        "alpha+beta (Bollerslev, 1986, "
        "https://doi.org/10.1016/0304-4076(86)90063-1). The package returns sigma, a standard deviation "
        "in the original change units. Its parameter dictionary and likelihood concern the estimation "
        "scale; fit_scale records the multiplier applied before fitting. Comparing omega across unit "
        "conversions without undoing that multiplier would be misleading. We expose that multiplier and "
        "the fitted persistence, without equating a short fit with a causal energy model."
        if lang == "en" else
        "### Variabilidad y volatilidad condicional en observaciones auténticas\n\n"
        "La entropía resume regularidad después de fijar codificación o tolerancia; la volatilidad "
        "condicional pregunta por la escala de una innovación. Usamos directamente ForecastScope 0.1.1 "
        "sobre las primeras diferencias eléctricas, conservando las 479 diferencias consecutivas. "
        "Una diferencia que termina en la fila original t sigue alineada con t; retirar valores no finitos "
        "antes de calcularla cambiaría su interpretación temporal. Aquí todos los valores admitidos son "
        "finitos. La media de diferencias se estima dentro de la muestra. Puede permanecer el patrón "
        "día/noche: ni un p-valor ARCH pequeño ni una recurrencia GARCH prueban volatilidad estocástica "
        "tras especificar correctamente la media condicional. Son cálculos descriptivos del extracto finito.\n\n"
        "La varianza condicional GARCH(1,1) sigue\n\n"
        "$$\\sigma_t^2=\\omega+\\alpha\\epsilon_{t-1}^2+\\beta\\sigma_{t-1}^2.$$\n\n"
        "Epsilon es el cambio centrado, omega el intercepto de varianza, alpha el coeficiente del choque "
        "cuadrático y beta el coeficiente de varianza condicional rezagada; la persistencia informada es "
        "alpha+beta (Bollerslev, 1986, "
        "https://doi.org/10.1016/0304-4076(86)90063-1). El paquete devuelve sigma como desviación estándar "
        "en las unidades originales del cambio. Los parámetros y la verosimilitud pertenecen a la escala "
        "de estimación; fit_scale registra el multiplicador aplicado. Comparar omega entre conversiones "
        "sin deshacer el multiplicador sería engañoso. Mostramos escala y persistencia sin interpretar "
        "un ajuste corto como modelo causal de energía."
    )
    fitting = '''# Separate a second-moment description from the forecast-error experiment.
changes = np.diff(electricity_values)
test = arch_lm(changes, nlags=12)
with warnings.catch_warnings(record=True) as volatility_notices:
    warnings.simplefilter("always")
    fitted_garch = garch(changes, p=1, q=1)
print("ForecastScope version:", importlib.metadata.version("forecastscope"))
print("ARCH lags, statistic and p-value:", test.nlags, round(test.lm_stat, 6), f"{test.lm_pvalue:.3e}")
print("Fit scale and persistence:", fitted_garch.fit_scale, round(fitted_garch.persistence, 6))
print("Numerical warning classes:", sorted({type(item.message).__name__ for item in volatility_notices}))
fig, axes = plt.subplots(2, 1, figsize=(8, 5), sharex=True)
indices = np.arange(1, len(electricity_values))
axes[0].plot(indices, changes, color="grey")
axes[0].set(ylabel="Change in source sum")
axes[1].plot(indices, fitted_garch.conditional_volatility, label="GARCH(1,1)")
axes[1].set(xlabel="Original observation index", ylabel="Conditional standard deviation")
axes[1].legend()
fig.tight_layout()
plt.show()
'''
    reading = (
        "The upper panel preserves the actual changes; the lower panel is the fitted conditional standard "
        "deviation, in matching source units. A large fitted sigma means a wider conditional scale under "
        "this model, not a larger expected change or proof of a structural break. Numerical warning classes "
        "are printed rather than hidden: convergence trouble limits interpretation even when a curve is "
        "returned. ARCH's lag choice is 12 consecutive changes and its p-value depends on residual assumptions.\n\n"
        "### Sensitivity to the volatility window and the transformation\n\n"
        "Compare rolling sample standard deviations at windows 12, 24 and 48, all on the same changes. "
        "A larger window reacts more slowly and omits more leading values: the undefined prefix remains "
        "missing rather than shifting the observed axis. This is a sensitivity analysis, not selection "
        "of the most attractive curve. Separately call the Box-Cox API on original levels with fixed "
        "log and fitted MLE choices. If a positive-domain shift is necessary it is returned explicitly; "
        "a transformed axis cannot be labelled as original power. The shift is based only on the supplied "
        "values, so an operational use must fit it on available history and preserve it for later values."
        if lang == "en" else
        "El panel superior conserva cambios observados; el inferior muestra desviación estándar "
        "condicional ajustada, con las mismas unidades. Una sigma grande indica mayor escala bajo ese "
        "modelo, no mayor cambio esperado ni prueba de ruptura estructural. Se imprimen las clases de "
        "avisos numéricos: problemas de convergencia restringen la interpretación aunque exista una curva. "
        "ARCH usa 12 cambios consecutivos y su p-valor depende de supuestos sobre residuos.\n\n"
        "### Sensibilidad a la ventana de volatilidad y la transformación\n\n"
        "Comparamos desviaciones muestrales móviles con ventanas 12, 24 y 48 sobre los mismos cambios. "
        "Una ventana mayor reacciona más lentamente y omite más valores iniciales: el prefijo indefinido "
        "permanece ausente sin desplazar el eje. Es sensibilidad, no selección de la curva más atractiva. "
        "Por separado llamamos Box-Cox sobre niveles originales con logaritmo fijo y MLE ajustada. "
        "Si hace falta un desplazamiento al dominio positivo se devuelve explícitamente; el eje "
        "transformado no puede rotularse como potencia original. El desplazamiento depende solo de "
        "valores entregados: en operación se ajusta con historia disponible y se conserva para valores futuros."
    )
    sensitivity = '''# Keep missing leading windows in place when comparing scale estimates.
fig, ax = plt.subplots()
for window in (12, 24, 48):
    rolling = rolling_volatility(changes, window=window)
    ax.plot(indices, rolling["rolling_std"], label=str(window))
ax.set(xlabel="Original observation index", ylabel="Rolling standard deviation (source units)")
ax.legend(title="Window (observations)")
fig.tight_layout()
plt.show()
for method in ("log", "mle"):
    transformed = box_cox(electricity_values, method=method)
    print(method, "lambda and positive-domain shift:", round(transformed.lam, 6), transformed.shift)
'''
    ending = (
        "The rolling curves trade responsiveness for stability and differ from the fitted GARCH recurrence. "
        "Their leading gaps are intentional consequences of a complete-window estimate. A small fitted "
        "Box-Cox lambda suggests a transformation near logarithmic on this excerpt; it does not make "
        "seasonal mean structure or dependence disappear. Neither choosing a transformation after seeing "
        "reserved errors nor reporting an in-sample volatility fit establishes a calibrated prediction band.\n\n"
        "### Using ForecastScope on your own data\n\n"
        "Supply a one-dimensional finite sequence in chronological order and state whether it contains "
        "levels, returns or differences. Preserve the mapping between any transformation and original row "
        "indices. Call arch_lm with an explicitly chosen nlags smaller than the usable residual sample; "
        "call rolling_volatility with a justified complete window, and garch only after considering the "
        "conditional-mean specification and numerical warnings. Inspect conditional_volatility length, "
        "fit_scale and parameter meaning before plotting. A constant sequence, very short history or "
        "undefined Box-Cox likelihood requires a documented alternative, not a fabricated p-value. "
        "ForecastScope is consumed from its published API; the notebook contains no replacement GARCH fitter."
        if lang == "en" else
        "Las curvas móviles intercambian respuesta rápida por estabilidad y difieren de la recurrencia "
        "GARCH ajustada. Sus huecos iniciales son consecuencias intencionales de exigir ventanas completas. "
        "Una lambda Box-Cox cercana a cero sugiere una transformación aproximadamente logarítmica del "
        "extracto, pero no elimina estructura estacional ni dependencia. Elegir una transformación después "
        "de observar errores reservados o mostrar volatilidad dentro de muestra no calibra una banda predictiva.\n\n"
        "### Úsalo con tus propios datos: ForecastScope\n\n"
        "Entrega una secuencia finita unidimensional en orden cronológico e indica si contiene niveles, "
        "retornos o diferencias. Conserva la correspondencia de cada transformación con las filas originales. "
        "Llama arch_lm con nlags explícito menor que la muestra residual utilizable; rolling_volatility "
        "con una ventana completa justificada, y garch después de considerar media condicional y avisos "
        "numéricos. Inspecciona longitud de conditional_volatility, fit_scale y significado de parámetros "
        "antes de graficar. Una secuencia constante, historia corta o verosimilitud Box-Cox indefinida exige "
        "una alternativa documentada, no un p-valor inventado. Se consume la API publicada de ForecastScope; "
        "el notebook no contiene un ajuste GARCH de reemplazo."
    )
    if lang == "es":
        replacements = {
            "# Separate a second-moment description from the forecast-error experiment.":
                "# Separa la descripción del segundo momento del experimento de error predictivo.",
            "# Keep missing leading windows in place when comparing scale estimates.":
                "# Conserva ventanas iniciales ausentes al comparar estimaciones de escala.",
            "ForecastScope version:": "Versión de ForecastScope:",
            "ARCH lags, statistic and p-value:": "Rezagos, estadístico y p-valor ARCH:",
            "Fit scale and persistence:": "Escala de ajuste y persistencia:",
            "Numerical warning classes:": "Clases de avisos numéricos:",
            "Change in source sum": "Cambio de la suma de la fuente",
            "Original observation index": "Índice original de observación",
            "Conditional standard deviation": "Desviación estándar condicional",
            "Rolling standard deviation (source units)": "Desviación móvil (unidades de la fuente)",
            "Window (observations)": "Ventana (observaciones)",
            "lambda and positive-domain shift:": "lambda y desplazamiento al dominio positivo:",
        }
        for before, after in replacements.items():
            fitting = fitting.replace(before, after)
            sensitivity = sensitivity.replace(before, after)
    add_before_results(document, [cell("markdown", explanation, key), cell("code", fitting, key + "/fit"),
                                 cell("markdown", reading, key + "/sensitivity-text"),
                                 cell("code", sensitivity, key + "/sensitivity"),
                                 cell("markdown", ending, key + "/own-data")])


FIGURE_TITLES = {
    "02-seasonal-phase": (["Forecast paths at the earlier seasonal origin", "Absolute errors by reserved lead",
                           "Daily and weekly references across nine fixed cutoffs"],
                          ["Trayectorias en el origen estacional anterior", "Errores absolutos por anticipación reservada",
                           "Referencias diaria y semanal en nueve cortes fijos"]),
    "03-model-comparison": (["Installed reference adapters on the common target", "Retained path score and interval width",
                             "Early and late errors from the same reserved block"],
                            ["Adaptadores instalados sobre el objetivo común", "Puntuación y anchura de trayectorias conservadas",
                             "Errores iniciales y finales del mismo bloque reservado"]),
    "04-context-memory": (["Convex weights of the three matched combination rules", "Finite fifteen-case mean errors",
                           "Paired case differences before any reweighting", "Sensitivity to whole-case resampling"],
                          ["Pesos convexos de las tres combinaciones comparables", "Errores medios de los quince casos",
                           "Diferencias pareadas antes de reponderar", "Sensibilidad al remuestreo de casos completos"]),
    "05-temporal-validation": (["Temporally selected expert allocations", "Mean series errors in separate external collections",
                                "Point and interval score differences against recency", "Whole-series stability intervals"],
                               ["Asignaciones de expertos seleccionadas temporalmente", "Errores por serie en colecciones externas separadas",
                                "Diferencias puntuales y de intervalos frente a recencia", "Intervalos de estabilidad por serie completa"]),
    "01-shape-patterns": (["Fixed window-length comparison", "Synthetic level shifts and their retrospective profile",
                           "Authentic electricity values and normalized shape distance"],
                          ["Comparación con ventanas fijadas", "Cambios sintéticos de nivel y perfil retrospectivo",
                           "Valores eléctricos auténticos y distancia normalizada de formas"]),
    "02-complexity": (["Entropy across fixed coarse-graining scales", "Reversing the third-order lag statistic",
                       "Entropy and the number of matched pairs", "Observed changes and fitted conditional scale",
                       "Rolling scale sensitivity with original row alignment"],
                      ["Entropía en escalas de agregación fijadas", "Inversión del estadístico de tercer orden",
                       "Entropía y número de pares coincidentes", "Cambios observados y escala condicional ajustada",
                       "Sensibilidad de escala móvil sobre índices originales"]),
    "03-corpus-confirmation": (["Feature associations in disjoint series partitions", "Selector and reference errors in confirmation",
                                "Series-level selector differences"],
                               ["Asociaciones en particiones disjuntas de series", "Errores del selector y referencias en confirmación",
                                "Diferencias del selector por serie"]),
    "04-information-boundaries": (["Common-origin forecasts on the authentic reserved day",
                                    "Historical selection and reserved final errors", "Coverage during one-step replay"],
                                   ["Pronósticos del mismo origen sobre el día auténtico reservado",
                                    "Selección histórica y errores finales reservados", "Cobertura durante la reproducción de un paso"]),
}


def figure_titles(document: dict, name: str, lang: str) -> None:
    titles = FIGURE_TITLES.get(name, ([], []))[lang == "es"]
    index = 0
    for item in document["cells"]:
        if item["cell_type"] != "code":
            continue
        text = text_of(item)
        if "plt.show()" not in text:
            continue
        if name == "01-baseline":
            continue
        scientific_titles = [
            ("fitted_garch.conditional_volatility", "Observed changes and fitted conditional scale",
             "Cambios observados y escala condicional ajustada"),
            ("rolling_volatility(changes", "Rolling scale sensitivity with original row alignment",
             "Sensibilidad de escala móvil sobre índices originales"),
            ("real_profile", "Authentic electricity values and normalized shape distance",
             "Valores eléctricos auténticos y distancia normalizada de formas"),
            ("ax.hist(resampled", "Sensitivity to whole-case resampling",
             "Sensibilidad al remuestreo de casos completos"),
            ("delta_series", "Whole-series stability intervals", "Intervalos de estabilidad por serie completa"),
        ]
        explicit = next((es if lang == "es" else en for marker, en, es in scientific_titles if marker in text), None)
        if "suptitle(" not in text:
            figure_names = re.findall(r"(?m)^(\w+),\s*\w+\s*=\s*plt.subplots", text)
            if figure_names:
                figure = figure_names[-1]
                title = explicit or (titles[index] if index < len(titles) else document["metadata"]["caos"]["title"])
                if ".set_title(" not in text:
                    text = text.replace(f"{figure}.tight_layout()", f"{figure}.suptitle({title!r}, fontsize=11)\n"
                                        f"{figure}.tight_layout()", 1)
        item["source"] = text
        if explicit is None and ".set_title(" not in text:
            index += 1


def setup_and_imports(document: dict, name: str, lang: str) -> None:
    """Move imports to setup and declare the small read-only data loaders there."""
    cells = document["cells"]
    first = next(item for item in cells if item["cell_type"] == "code")
    source = text_of(first)
    imports = []
    for item in cells:
        if item is first or item["cell_type"] != "code":
            continue
        lines = text_of(item).splitlines()
        retained = []
        for line in lines:
            if re.match(r"^(?:import |from \S+ import )", line):
                if line not in source and line not in imports:
                    imports.append(line)
            else:
                retained.append(line)
        item["source"] = "\n".join(retained) + "\n"
    extras = {
        "04-context-memory": ["from forecastscope.combinations.context_memory import context_features"],
        "02-complexity": ["from forecastscope.diagnostics.volatility import arch_lm, garch, rolling_volatility, box_cox"],
        "03-model-comparison": ["from engine.notebook_reference import reference_forecasts"],
        "04-information-boundaries": [
            "from engine.notebook_browser import observed_graph, ridge_experiment, calibration_experiment",
            "from engine.notebook_browser import release_context, exported_pair",
            "from IPython.display import Markdown, display",
            "from os import environ"],
    }.get(name, [])
    for line in extras:
        if line not in source and line not in imports:
            imports.append(line)
    if imports:
        lines = source.splitlines()
        insertion = next((i + 1 for i, line in enumerate(lines) if 'sys.path.insert(0, str(root / "data-pipeline"))' in line), 0)
        lines[insertion:insertion] = imports
        source = "\n".join(lines) + "\n"
    if name in {"01-shape-patterns", "02-complexity", "02-seasonal-phase"} and "electricity_values =" not in source:
        source += ('\n# Load the observed source once; later cells contain only scientific operations.\n'
                   'electricity_values = np.loadtxt(root / "data/examples/electricity_sample.csv",\n'
                   '                                delimiter=",", skiprows=1, usecols=2)\n')
        if lang == "es":
            source = source.replace("# Load the observed source once; later cells contain only scientific operations.",
                                    "# Carga la fuente observada una vez; las celdas posteriores operan científicamente.")
    if name == "05-temporal-validation" and "combination_records =" not in source:
        source += ('\n# Resolve the admitted per-series evidence through its declared index.\n'
                   'study = json.loads((root / "data/derived/validated-combinations.json").read_text(encoding="utf-8"))\n'
                   'combination_records = {(entry["dataset"], entry["id"]):\n'
                   '    json.loads((root / "data/derived" / entry["path"]).read_text(encoding="utf-8"))\n'
                   '    for entry in study["cases"]}\n')
        if lang == "es":
            source = source.replace("# Resolve the admitted per-series evidence through its declared index.",
                                    "# Resuelve la evidencia admitida por serie mediante su índice declarado.")
    if name == "04-information-boundaries" and "release_inputs =" not in source:
        source += "\nrelease_inputs = release_context()\n"
    if name != "01-baseline" and 'importlib.metadata.version("forecastscope")' not in source:
        source += '\nprint("ForecastScope", importlib.metadata.version("forecastscope"))\n'
    if name == "03-corpus-confirmation" and lang == "es" and "display_labels =" not in source:
        source += ('\ndisplay_labels = {"selected": "selector",\n'
                   '                  "discovery_constant": "constante de descubrimiento",\n'
                   '                  "oracle": "oráculo"}\n')
    first["source"] = source


def comparison_tables(document: dict, name: str, lang: str) -> None:
    key = f"{name}/numerical-table"
    if any(item.get("id") == hashlib.sha256(key.encode()).hexdigest()[:12] for item in document["cells"]):
        return
    if name == "03-model-comparison":
        intro = ("The numerical table scores every path on the same reserved block and history scale. "
                 "Execution status identifies the newly fitted local adapters, the actual reference inference "
                 "calls and the retained adaptation paths. MASE is dimensionless, width has generated source units, and coverage is an empirical "
                 "fraction over this one block. A low error and narrow interval are not interchangeable criteria."
                 if lang == "en" else
                 "La tabla numérica puntúa cada trayectoria sobre el mismo bloque y escala histórica. "
                 "El estado distingue adaptadores recién ajustados, inferencias de referencia ejecutadas "
                 "y trayectorias adaptadas conservadas. MASE es adimensional, la anchura conserva unidades generadas "
                 "y la cobertura es una fracción empírica de este bloque. Error bajo e intervalo estrecho "
                 "no son criterios intercambiables.")
        code = '''# Compare point accuracy and interval behavior without mixing evaluation targets.
table_rows = []
for name, q in (("AutoETS", ets_q), ("AutoTheta", auto_theta_q), ("AutoARIMA", arima_q), ("LightGBM", tree_q)):
    score = metrics(history, actual, q[:, 1], q[:, 0], q[:, 2], m)
    table_rows.append((name, "executed", score["mase"], score["mean_width"], score["coverage"]))
for name, score in frozen_scores:
    table_rows.append((name, "retained path", score["mase"], score["mean_width"], score["coverage"]))
for name, row in reference_run["methods"].items():
    q = np.asarray(row["quantiles"])
    score = metrics(history, actual, q[:, 1], q[:, 0], q[:, 2], m)
    table_rows.append((name, "reference executed", score["mase"], score["mean_width"], score["coverage"]))
print("| Method | Execution | MASE | Mean width | Coverage |")
print("|---|---|---:|---:|---:|")
for name, status, mase, width, coverage in table_rows:
    print(f"| {name} | {status} | {mase:.6f} | {width:.6f} | {coverage:.6f} |")
'''
    elif name == "04-information-boundaries":
        intro = ("The final numerical comparison uses common targets, and the historical column stays "
                 "separate. Rank final MASE only after all models have issued their paths; print interval "
                 "coverage together with its width rather than declaring a high coverage fraction sufficient. "
                 "The displayed winner is computed from the current run and need not equal the method "
                 "selected from completed historical windows."
                 if lang == "en" else
                 "La comparación final utiliza objetivos comunes y mantiene separada la columna histórica. "
                 "Ordena MASE final solo después de emitir todas las trayectorias; muestra cobertura junto "
                 "con anchura en vez de considerar suficiente una cobertura alta. El ganador visible se "
                 "calcula en esta ejecución y no tiene por qué coincidir con la selección histórica.")
        code = '''# Keep historical and final scores in different columns with a common final target.
final_rows = []
print("| Method | Historical MASE | Final MASE | Coverage | Mean width |")
print("|---|---:|---:|---:|---:|")
for row in eligible:
    score = metrics(prefix, target, row.point, row.lower, row.upper, spec.seasonality)
    old = historical["methods"][row.name]["mase"]
    final_rows.append((score["mase"], row.name, score))
    print(f"| {row.name} | {old:.6f} | {score['mase']:.6f} | {score['coverage']:.6f} | {score['mean_width']:.6f} |")
best_final = min(final_rows)
print("Final winner and MASE:", best_final[1], round(best_final[0], 6))
print("Winner coverage and mean width:", best_final[2]["coverage"], round(best_final[2]["mean_width"], 6))
'''
    else:
        return
    if lang == "es":
        display_translations = {
            "# Compare point accuracy and interval behavior without mixing evaluation targets.":
                "# Compara exactitud puntual e intervalos sin mezclar objetivos de evaluación.",
            "# Keep historical and final scores in different columns with a common final target.":
                "# Separa puntuaciones históricas y finales manteniendo el objetivo final común.",
            "executed": "ejecutado", "retained path": "trayectoria conservada",
            "reference executed": "referencia ejecutada",
            "| Method | Execution | MASE | Mean width | Coverage |":
                "| Método | Ejecución | MASE | Anchura media | Cobertura |",
            "| Method | Historical MASE | Final MASE | Coverage | Mean width |":
                "| Método | MASE histórico | MASE final | Cobertura | Anchura media |",
            "Final winner and MASE:": "Ganador final y MASE:",
            "Winner coverage and mean width:": "Cobertura y anchura media del ganador:",
        }
        for before, after in sorted(display_translations.items(), key=lambda pair: -len(pair[0])):
            code = code.replace(before, after)
    if name == "03-model-comparison":
        reading = (
            "The reference rows expose the extra cost and changed error of a newly fitted architecture, "
            "while the retained rows describe earlier paths without an inference claim. Their point scores "
            "and interval widths use one common target. Compare the fresh NeuralForecast names with their "
            "explicit direct-torch adaptations rather than merging their identities. These finite numbers "
            "cannot determine an expected winner on another series or a different operational horizon."
            if lang == "en" else
            "Las filas de referencia muestran el error de arquitecturas ajustadas ahora; las conservadas "
            "describen trayectorias anteriores sin atribuirles inferencia nueva. Puntuaciones y anchuras "
            "utilizan un objetivo común. Compara los nombres de NeuralForecast con sus adaptaciones "
            "explícitas en torch sin fundir sus identidades. Estos números finitos no determinan el "
            "ganador esperado de otra serie o de un horizonte operativo diferente.")
    else:
        reading = (
            "The historical selection was available before the final day arrived. Its score averages "
            "different targets from the final column, so the two values should not be subtracted as a "
            "paired accuracy improvement. The final winner is useful as a retrospective outcome only. "
            "Inspect its interval width alongside coverage: covering all twenty-four targets with a very "
            "wide band could be less useful than the empirical coverage alone suggests."
            if lang == "en" else
            "La selección histórica estaba disponible antes de llegar el día final. Su puntuación "
            "promedia objetivos distintos de la columna final, por lo que no se deben restar como "
            "mejora pareada. El ganador final es un resultado retrospectivo. Inspecciona anchura junto "
            "con cobertura: cubrir los veinticuatro objetivos con una banda muy amplia puede aportar "
            "menos utilidad de la que sugiere la cobertura empírica por sí sola.")
    add_before_results(document, [cell("markdown", intro, key), cell("code", code, key + "/code"),
                                 cell("markdown", reading, key + "/reading")])


def actual_references(document: dict, lang: str) -> None:
    key = "comparison/actual-reference-execution"
    if any(item.get("id") == hashlib.sha256(key.encode()).hexdigest()[:12] for item in document["cells"]):
        return
    introduction = (
        "### Fitting and inferring the published neural and pretrained references\n\n"
        "Retained paths above answer a reproducibility question but are not a fresh model run. Now call "
        "the product's reference_forecasts entry point with only the same available history, period and "
        "horizon supplied to the installed adapters. It actually fits NLinear, DLinear and NHITS from the "
        "pinned NeuralForecast implementation and runs Chronos-Bolt, Chronos-2, TimesFM 2.5 and TiRex-2 "
        "on their revision-pinned checkpoint weights. Every model returns the same three quantiles and "
        "the same horizon; the reserved actual array is not an argument. This small instructional experiment "
        "does not rerun all fifteen cases or either external collection.\n\n"
        "The helper uses the separately declared Linux reference runtime; on Windows the configured WSL "
        "lane supplies that runtime because TiRex-2 needs Linux CUDA dependencies. Prepare it through the "
        "documented foundation environment and model-download workflow before execution. No package is "
        "installed and no checkpoint is silently substituted by a cell. The helper checks package versions "
        "and checkpoint revisions against the retained fresh-comparison provenance and rejects missing "
        "weights or mismatched identities. Runtime and checkpoint identities are returned with the newly "
        "computed paths. The direct-torch adaptations remain separately named retained results: their "
        "quantile heads and NHITS design differ from the maintained reference implementations.\n\n"
        "References: NLinear and DLinear, https://arxiv.org/abs/2205.13504; NHITS, "
        "https://arxiv.org/abs/2201.12886; package https://github.com/Nixtla/neuralforecast; "
        "Chronos, https://github.com/amazon-science/chronos-forecasting; TimesFM, "
        "https://github.com/google-research/timesfm; TiRex-2, https://huggingface.co/NX-AI/TiRex-2."
        if lang == "en" else
        "### Ajustar y ejecutar referencias neuronales y preentrenadas\n\n"
        "Las trayectorias conservadas responden a reproducibilidad, pero no constituyen una ejecución "
        "nueva. Llamamos ahora reference_forecasts del producto solo con la misma historia disponible, "
        "período y horizonte entregados a los adaptadores instalados. Ajusta realmente NLinear, DLinear "
        "y NHITS mediante NeuralForecast fijado, y ejecuta Chronos-Bolt, Chronos-2, TimesFM 2.5 y TiRex-2 "
        "con pesos fijados por revisión. Cada modelo devuelve los mismos tres cuantiles y horizonte; "
        "actual no es argumento. Este experimento didáctico pequeño no repite los quince casos ni "
        "las colecciones externas.\n\n"
        "El auxiliar usa el entorno de referencia Linux declarado por separado; en Windows lo aporta "
        "la ruta WSL configurada porque TiRex-2 requiere dependencias CUDA de Linux. Prepara el entorno "
        "y los modelos mediante el flujo documentado antes de ejecutar. Ninguna celda instala paquetes "
        "ni sustituye modelos silenciosamente. Se comprueban versiones y revisiones frente a la procedencia "
        "de la comparación fresca conservada, y se rechazan pesos ausentes o identidades distintas. "
        "El entorno y las revisiones se devuelven junto a las nuevas trayectorias. Las adaptaciones "
        "directas en torch siguen identificadas como resultados conservados: sus cabezas de cuantiles "
        "y su diseño NHITS difieren de las implementaciones de referencia mantenidas.\n\n"
        "Referencias: NLinear y DLinear, https://arxiv.org/abs/2205.13504; NHITS, "
        "https://arxiv.org/abs/2201.12886; paquete https://github.com/Nixtla/neuralforecast; "
        "Chronos, https://github.com/amazon-science/chronos-forecasting; TimesFM, "
        "https://github.com/google-research/timesfm; TiRex-2, https://huggingface.co/NX-AI/TiRex-2."
    )
    code = '''# Send only available history to the version-checked reference runtime.
reference_run = reference_forecasts(history, m, h)
print("Available-history SHA-256:", reference_run["input_sha256"])
for name, row in reference_run["methods"].items():
    print(name, row["package"], row["package_version"], row.get("checkpoint_revision", "fitted from history"))
fig, ax = plt.subplots()
ax.plot(np.arange(1, h + 1), actual, color="black", linewidth=2, label="actual")
for name, row in reference_run["methods"].items():
    q = np.asarray(row["quantiles"])
    ax.plot(np.arange(1, h + 1), q[:, 1], label=name)
ax.set(xlabel="Reserved forecast lead", ylabel="Generated source units")
ax.set_title("Actual reference fits and inference on one common target")
ax.legend(ncol=3, fontsize=7)
fig.tight_layout()
plt.show()
'''
    interpretation = (
        "These plotted medians were returned by the live reference calls, with exact runtime identities "
        "printed above them. Their differences from retained paths can reflect implementation, precision "
        "or training-runtime differences and must not be relabelled as agreement. The comparison table "
        "below scores all newly returned paths against the same target and retains old paths as explicitly "
        "separate rows. One successful fit does not demonstrate repeatability across seeds, pretraining "
        "independence, calibration or general superiority over the inexpensive statistical references."
        if lang == "en" else
        "Las medianas graficadas provienen de llamadas reales de referencia, con identidades exactas "
        "impresas arriba. Sus diferencias frente a trayectorias conservadas pueden depender de "
        "implementación, precisión o entorno de ajuste y no deben presentarse como acuerdo. La tabla "
        "siguiente puntúa las nuevas trayectorias contra el mismo objetivo y conserva las antiguas en "
        "filas separadas. Un ajuste exitoso no prueba repetibilidad entre semillas, independencia del "
        "preentrenamiento, calibración ni superioridad general frente a referencias estadísticas económicas."
    )
    if lang == "es":
        for before, after in {
            "# Send only available history to the version-checked reference runtime.":
                "# Envía solo historia disponible al entorno de referencia con versiones comprobadas.",
            "Available-history SHA-256:": "SHA-256 de la historia disponible:",
            "fitted from history": "ajustado con la historia", 'label="actual"': 'label="observado"',
            "Reserved forecast lead": "Anticipación reservada del pronóstico",
            "Generated source units": "Unidades generadas de la fuente",
            "Actual reference fits and inference on one common target":
                "Ajustes e inferencias reales de referencia sobre un objetivo común",
        }.items():
            code = code.replace(before, after)
    add_before_results(document, [cell("markdown", introduction, key), cell("code", code, key + "/code"),
                                 cell("markdown", interpretation, key + "/reading")])


def terminal_sections(document: dict, name: str, lang: str) -> None:
    """Keep later method experiments before the closing Results and Summary sections."""
    if name not in {"02-seasonal-phase", "02-complexity", "03-corpus-confirmation", "04-information-boundaries"}:
        return
    result_heading = "Results" if lang == "en" else "Resultados"
    summary_heading = "Summary" if lang == "en" else "Resumen"
    reference_heading = "References" if lang == "en" else "Referencias"
    answer_name = "Answer" if lang == "en" else "Respuesta"
    answers, summaries, references = [], [], []
    retained = []
    for item in document["cells"]:
        if item.get("id") == hashlib.sha256(f"{name}/computed-answer".encode()).hexdigest()[:12]:
            continue
        if item["cell_type"] != "markdown":
            retained.append(item)
            continue
        text = text_of(item)
        if re.search(r"(?m)^## " + result_heading + r"\s*$", text):
            text = re.sub(r"(?m)^## " + result_heading + r"\s*\n", "", text)
            pattern = r"(?ms)^\*\*" + answer_name + r":\*\*.*?(?=\n\s*\n|\Z)"
            answers.extend(re.findall(pattern, text))
            text = re.sub(pattern, "", text)
        pattern = r"(?ms)^## " + summary_heading + r"\s*\n(.*?)(?=^###? |\Z)"
        summaries.extend(re.findall(pattern, text))
        text = re.sub(pattern, "", text)
        pattern = r"(?ms)^## " + reference_heading + r"\s*\n(.*)\Z"
        references.extend(re.findall(pattern, text))
        text = re.sub(pattern, "", text)
        if text.strip():
            item["source"] = text.strip() + "\n"
            retained.append(item)
    if answers or summaries or references:
        ending = f"## {result_heading}\n\n" + "\n\n".join(answer.strip() for answer in answers)
        ending += f"\n\n## {summary_heading}\n\n" + "\n\n".join(text.strip() for text in summaries)
        ending += f"\n\n## {reference_heading}\n\n" + "\n\n".join(text.strip() for text in references)
        if name == "04-information-boundaries":
            results, remainder = ending.split(f"## {summary_heading}", 1)
            retained.append(cell("markdown", results, f"{name}/terminal-results"))
            if lang == "en":
                answer_code = '''# State the actual current winner with its point score and interval cost.
answer = (f"The final winner among the common-origin candidates is **{best_final[1]}**, "
          f"with MASE **{best_final[0]:.6f}**, empirical coverage **{best_final[2]['coverage']:.6f}** "
          f"and mean interval width **{best_final[2]['mean_width']:.6f}** in source-sum units. "
          f"The earlier rolling selection was **{historical['best_method']}**.")
display(Markdown(answer))
'''
            else:
                answer_code = '''# Indica el ganador calculado junto con puntuación puntual y costo de sus intervalos.
answer = (f"El ganador final entre candidatos del mismo origen es **{best_final[1]}**, "
          f"con MASE **{best_final[0]:.6f}**, cobertura empírica **{best_final[2]['coverage']:.6f}** "
          f"y anchura media **{best_final[2]['mean_width']:.6f}** en unidades de suma de la fuente. "
          f"La selección histórica anterior fue **{historical['best_method']}**.")
display(Markdown(answer))
'''
            retained.append(cell("code", answer_code, f"{name}/computed-answer"))
            retained.append(cell("markdown", f"## {summary_heading}" + remainder, f"{name}/terminal-summary"))
        else:
            retained.append(cell("markdown", ending, f"{name}/terminal-sections"))
    document["cells"] = retained


def declarations(document: dict, name: str, lang: str) -> None:
    meta = document["metadata"]["caos"]
    pins = (ROOT / "notebooks/requirements.txt").read_text(encoding="utf-8").splitlines()
    scope_pin = next(pin for pin in pins if pin.startswith("forecastscope=="))
    for item in document["cells"]:
        if item["cell_type"] == "markdown":
            item["source"] = re.sub(r"forecastscope==[0-9.]+", scope_pin, text_of(item))
    if name != "01-baseline":
        meta["packages"] = [pin for pin in meta["packages"] if not pin.startswith("forecastscope==")]
        meta["packages"].append(scope_pin)
    setup_marker = "## Setup" if lang == "en" else "## Preparación"
    for item in document["cells"]:
        if item["cell_type"] == "markdown" and setup_marker in text_of(item):
            text = text_of(item)
            for pin in meta["packages"]:
                if pin not in "\n".join(text_of(c) for c in document["cells"] if c["cell_type"] == "markdown"):
                    text += f"\n```sh\npip install {pin}\n```\n"
            item["source"] = text
            break

    if name in {"01-shape-patterns", "02-complexity"}:
        for value in ("data/examples/electricity_sample.csv",):
            if value not in meta["data"]:
                meta["data"].append(value)
        if "https://doi.org/10.24432/C58C86" not in meta["sources"]:
            meta["sources"].append("https://doi.org/10.24432/C58C86")
    if name == "02-complexity":
        for value in ("https://pypi.org/project/forecastscope/", "https://doi.org/10.1016/0304-4076(86)90063-1"):
            if value not in meta["sources"]:
                meta["sources"].append(value)
    reference_marker = "## References" if lang == "en" else "## Referencias"
    for item in reversed(document["cells"]):
        if item["cell_type"] == "markdown" and reference_marker in text_of(item):
            text = text_of(item)
            for source in meta["sources"]:
                if source not in text:
                    text += "\n- " + source + "\n"
            item["source"] = text
            break


def browser_operations(document: dict, lang: str) -> None:
    key = "information/actual-browser-operations"
    if any(item.get("id") == hashlib.sha256(key.encode()).hexdigest()[:12] for item in document["cells"]):
        return
    # Remove the checker call: checks belong to tests, not the lesson's scientific evidence.
    retained = []
    for item in document["cells"]:
        if item["cell_type"] == "code" and "validated = validate(root)" in text_of(item):
            continue
        retained.append(item)
    document["cells"] = retained
    introduction = (
        "### Executing the browser point graph before changing its intervals\n\n"
        "The graph contract has lookback 48 and horizon 12. Its input is a single normalized row x; "
        "the output is twelve normalized point values, not an already calibrated probabilistic forecast. "
        "For last available level a and positive prefix standard deviation s, the caller forms "
        "x_j=(history_j-a)/s and restores point values as a+s f(x). Only the observed prefix determines "
        "a and s. The target is reserved for scoring after inference. The next call executes the frozen "
        "ONNX graph on the authentic electricity prefix, then displays its twelve predictions in original "
        "source units. It does not extend the graph to the twenty-four-step horizon of the earlier comparison.\n\n"
        "The model metadata's lookback and horizon therefore govern real tensor construction, rather than "
        "merely appearing in an inventory printout. A constant prefix has unavailable positive scale and "
        "must be rejected or handled by a separately declared fallback. This example does not quietly "
        "replace that scale with an arbitrary number. Graph identity is checked by the pipeline helper "
        "before numerical inference; the notebook itself contains no ONNX replacement implementation."
        if lang == "en" else
        "### Ejecutar el grafo puntual antes de cambiar sus intervalos\n\n"
        "El contrato del grafo fija historia 48 y horizonte 12. La entrada es una fila normalizada x; "
        "la salida contiene doce valores puntuales normalizados, no un pronóstico probabilístico "
        "calibrado. Con último nivel disponible a y desviación positiva del prefijo s, el llamador forma "
        "x_j=(history_j-a)/s y restaura puntos como a+s f(x). Solo el prefijo observado determina a y s. "
        "El objetivo se reserva para puntuar después. La llamada siguiente ejecuta ONNX congelado sobre "
        "el prefijo eléctrico auténtico y muestra doce predicciones en unidades originales. No extiende "
        "el grafo al horizonte de veinticuatro pasos de la comparación anterior.\n\n"
        "Historia y horizonte de los metadatos gobiernan tensores reales, en lugar de limitarse al "
        "inventario. Un prefijo constante carece de escala positiva disponible: se rechaza o usa una "
        "alternativa declarada por separado, sin reemplazarla silenciosamente por un número arbitrario. "
        "El auxiliar del pipeline comprueba la identidad del grafo antes de inferir; el notebook no "
        "contiene una implementación ONNX de reemplazo."
    )
    graph_code = '''# Infer from the observed prefix before looking at its next twelve targets.
graph_result = observed_graph(prefix)
graph_point = graph_result["point"]
print("Lookback, horizon and observed-prefix scale:", graph_result["lookback"],
      graph_result["horizon"], round(graph_result["scale"], 6))
fig, ax = plt.subplots()
leads = np.arange(1, len(graph_point) + 1)
ax.plot(leads, target[:len(graph_point)], color="black", label="observed")
ax.plot(leads, graph_point, label="Frozen ONNX graph")
ax.set(xlabel="Reserved lead (observations)", ylabel="Sum of kW readings")
ax.set_title("Actual frozen graph inference on the authentic prefix")
ax.legend()
fig.tight_layout()
plt.show()
'''
    fitting_text = (
        "The graph points above are actual runtime outputs. Their alignment to the reserved twelve "
        "observations is meaningful, while the synthetic calibration's normalized score cannot be copied "
        "onto this meter as a real-data coverage guarantee. We next separate changing the point function "
        "from changing its intervals. The canonical ridge producer generates disjoint training (400), "
        "validation (200), calibration (400) and test (400) series using its fixed seeds. All four "
        "families are generated controls, not additional electricity customers.\n\n"
        "For normalized training matrices X and Y, its ridge weights minimize mean squared error plus "
        "lambda times squared weight magnitude. It solves (X'X/n+lambda I)W=X'Y/n for positive lambda "
        "and uses least squares at zero. The seven penalties are fixed before evaluation. Validation "
        "MSE chooses the weights; calibration targets determine absolute-residual interval radii only "
        "after that choice. The final test targets choose neither weights nor radii. The following "
        "table computes the frozen-versus-ridge point and interval scores on that common test split."
        if lang == "en" else
        "Los puntos anteriores son salidas reales del entorno. Alinearlos con doce observaciones "
        "reservadas tiene sentido, pero la puntuación normalizada de calibración sintética no garantiza "
        "cobertura real de este medidor. Ahora distinguimos cambiar la función puntual de cambiar sus "
        "intervalos. El productor ridge genera series disjuntas de entrenamiento (400), validación (200), "
        "calibración (400) y prueba (400), con semillas fijas. Las cuatro familias son controles generados, "
        "no clientes eléctricos adicionales.\n\n"
        "Para matrices normalizadas X e Y, los pesos ridge minimizan error cuadrático medio más lambda "
        "por magnitud cuadrática de pesos. Con lambda positiva se resuelve (X'X/n+lambda I)W=X'Y/n; "
        "con cero se usa mínimos cuadrados. Se fijan siete penalizaciones antes de evaluar. El MSE de "
        "validación elige pesos; los objetivos de calibración determinan radios de residuos absolutos "
        "solo después. Los objetivos finales no eligen pesos ni radios. La tabla siguiente calcula "
        "puntuaciones puntuales y de intervalos del grafo congelado y ridge sobre esa prueba común."
    )
    ridge_code = '''# Fit and select the ridge point function on disjoint generated training and validation series.
ridge_result = ridge_experiment()
print("Generated series per partition:", ridge_result["counts"])
print("| Penalty | Validation normalized MSE | Selected |")
print("|---:|---:|---|")
for candidate in ridge_result["validation"]:
    print(f"| {candidate['penalty']:.6g} | {candidate['normalized_mse']:.6f} | {candidate.get('selected', False)} |")
print("| Point function | Normalized MAE | Coverage | Normalized width | Interval score |")
print("|---|---:|---:|---:|---:|")
for name, score in ridge_result["scores"].items():
    values = [score[k] for k in ("normalized_mae", "coverage", "normalized_width", "normalized_interval_score")]
    print("| " + name + " | " + " | ".join(f"{value:.6f}" for value in values) + " |")
fig, ax = plt.subplots()
for name in ("frozen", "ridge"):
    score = ridge_result["scores"][name]
    ax.scatter(score["normalized_mae"], score["normalized_interval_score"], label=name, s=55)
ax.set(xlabel="Normalized point MAE", ylabel="Normalized interval score")
ax.set_title("A new point fit can change point and interval quality differently")
ax.legend()
fig.tight_layout()
plt.show()
'''
    calibration_text = (
        "The penalty table exposes selection before the test, and the second table keeps point MAE "
        "separate from interval score. A fitted ridge point function can have a different error and "
        "still gain or lose under its calibrated interval score. That difference is a result to inspect, "
        "not a reason to change the grid after evaluation. The next experiment fixes the browser graph "
        "points and changes only interval construction on the independently generated confirmation split.\n\n"
        "For alpha=0.2, a per-lead calibration radius is the order statistic at ceil((n+1)(1-alpha)) "
        "of absolute normalized residuals. It is not the sample's interpolated 80th percentile. The "
        "stratified alternative groups prefixes by mean squared first difference divided by prefix "
        "variance, with frozen thresholds 0.5 and 1.25. Each of three groups must have at least twenty "
        "independent calibration series. Group selection uses prefix information only. The helper "
        "recomputes graph predictions on 400 calibration and 800 untouched test series, derives global "
        "and grouped radii and scores both around the identical test point path. Gaussian widths are "
        "the retained fixed-scale comparator. A high marginal coverage alone can be bought with wide "
        "intervals, which is why coverage, width and interval score are reported together."
        if lang == "en" else
        "La tabla de penalizaciones muestra selección anterior a la prueba; la segunda distingue MAE "
        "puntual de puntuación de intervalos. Ridge puede cambiar el error puntual y mejorar o empeorar "
        "otra medida de intervalos. Se inspecciona ese resultado sin cambiar la grilla después. El "
        "siguiente experimento fija puntos del grafo y cambia solo la construcción de intervalos sobre "
        "la partición de confirmación generada independientemente.\n\n"
        "Con alpha=0,2, el radio por anticipación es el estadístico ordenado en ceil((n+1)(1-alpha)) "
        "de residuos absolutos normalizados, no el percentil 80 interpolado. La alternativa estratificada "
        "agrupa prefijos según media de primeras diferencias cuadradas dividida por varianza, con "
        "umbrales fijos 0,5 y 1,25. Cada grupo exige veinte series independientes de calibración. "
        "La asignación usa únicamente el prefijo. El auxiliar recalcula el grafo en 400 series de "
        "calibración y 800 series intactas de prueba, deriva radios globales y por grupo, y los puntúa "
        "alrededor de los mismos puntos. Las anchuras gaussianas son el comparador de escala fija. "
        "Una cobertura alta puede comprarse con bandas amplias; por eso se informan juntas cobertura, "
        "anchura y puntuación de intervalos."
    )
    calibration_code = '''# Learn only radii from calibration outcomes and keep every test point forecast fixed.
calibration_result = calibration_experiment()
print("Calibration series per prefix group:", calibration_result["counts"])
print("Untouched test series:", calibration_result["test_series"])
print("| Interval rule | Coverage | Normalized width | Normalized interval score |")
print("|---|---:|---:|---:|")
for name, score in calibration_result["scores"].items():
    values = [score[key] for key in ("coverage", "normalized_width", "normalized_interval_score")]
    print("| " + name + " | " + " | ".join(f"{value:.6f}" for value in values) + " |")
fig, ax = plt.subplots()
for group, radii in enumerate(calibration_result["radii"]):
    ax.plot(np.arange(1, 13), radii, marker="o", label=str(group))
ax.plot(np.arange(1, 13), calibration_result["global_radii"], color="black", linestyle="--", label="global")
ax.set(xlabel="Forecast lead (observations)", ylabel="Absolute residual radius (normalized units)")
ax.set_title("Calibration radii change while point forecasts remain fixed")
ax.legend(title="Observed-prefix group")
fig.tight_layout()
plt.show()
'''
    conclusion = (
        "The radius curves show lead-specific scale and prefix-group differences, all estimated before "
        "test outcomes are consulted. The table evaluates their cost on the separate test series. A lower "
        "normalized interval score on these generated families supports only this confirmation design; "
        "it does not establish calibrated electricity coverage or adaptive validity under arbitrary drift.\n\n"
        "### Using the graph and calibration on your own data\n\n"
        "Provide at least 48 finite contiguous observations with stated units, call observed_graph on "
        "history only, and reserve the next twelve rows for later evaluation. Its returned scale and "
        "last value restore units; they must not be recomputed from the targets. A new interval study "
        "needs a separate calibration collection, a defined exchangeability or shift assumption and "
        "enough independent series in each prefix group. Fit any new ridge coefficients using separate "
        "training/validation information. Keep the graph digest, radii, grouping thresholds, input horizon "
        "and source revision together: model and calibration contracts describe different learned objects."
        if lang == "en" else
        "Las curvas muestran escalas por anticipación y grupo de prefijos, estimadas antes de consultar "
        "resultados de prueba. La tabla evalúa su costo en series separadas. Un menor puntaje normalizado "
        "en familias generadas respalda solo este diseño de confirmación; no establece cobertura "
        "eléctrica calibrada ni validez adaptativa bajo cambios arbitrarios.\n\n"
        "### Úsalo con tus propios datos: grafo y calibración\n\n"
        "Entrega al menos 48 observaciones finitas contiguas con unidades declaradas, llama observed_graph "
        "solo con historia y reserva las doce filas siguientes para evaluación posterior. La escala y "
        "último valor devueltos restauran unidades; no se recalculan con objetivos. Un estudio nuevo "
        "necesita otra colección de calibración, supuestos de intercambiabilidad o cambio y suficientes "
        "series independientes por grupo. Ajusta pesos ridge con entrenamiento y validación separados. "
        "Conserva juntos resumen del grafo, radios, umbrales, horizonte y revisión de datos: contratos "
        "de modelo y calibración describen objetos aprendidos distintos."
    )
    if lang == "es":
        translations = {
            "# Infer from the observed prefix before looking at its next twelve targets.":
                "# Infiere desde el prefijo observado antes de consultar los doce objetivos siguientes.",
            "# Fit and select the ridge point function on disjoint generated training and validation series.":
                "# Ajusta y selecciona la función ridge en series generadas disjuntas de entrenamiento y validación.",
            "# Learn only radii from calibration outcomes and keep every test point forecast fixed.":
                "# Aprende solo radios con calibración y conserva fijos todos los puntos de prueba.",
            "Lookback, horizon and observed-prefix scale:": "Historia, horizonte y escala del prefijo observado:",
            'label="observed"': 'label="observado"', "Frozen ONNX graph": "Grafo ONNX congelado",
            "Reserved lead (observations)": "Anticipación reservada (observaciones)",
            "Sum of kW readings": "Suma de lecturas en kW",
            "Actual frozen graph inference on the authentic prefix": "Inferencia real del grafo sobre el prefijo auténtico",
            "Generated series per partition:": "Series generadas por partición:",
            "| Penalty | Validation normalized MSE | Selected |": "| Penalización | MSE normalizado de validación | Elegida |",
            "| Point function | Normalized MAE | Coverage | Normalized width | Interval score |":
                "| Función puntual | MAE normalizado | Cobertura | Anchura normalizada | Puntaje de intervalos |",
            "Normalized point MAE": "MAE puntual normalizado", "Normalized interval score": "Puntaje normalizado de intervalos",
            "A new point fit can change point and interval quality differently":
                "Cambiar el ajuste puntual afecta de forma distinta puntos e intervalos",
            "Calibration series per prefix group:": "Series de calibración por grupo de prefijos:",
            "Untouched test series:": "Series intactas de prueba:",
            "| Interval rule | Coverage | Normalized width | Normalized interval score |":
                "| Regla del intervalo | Cobertura | Anchura normalizada | Puntaje normalizado de intervalos |",
            "Forecast lead (observations)": "Anticipación (observaciones)",
            "Absolute residual radius (normalized units)": "Radio residual absoluto (unidades normalizadas)",
            "Calibration radii change while point forecasts remain fixed": "Cambian los radios; se conservan los puntos",
            "Observed-prefix group": "Grupo del prefijo observado",
        }
        for before, after in sorted(translations.items(), key=lambda pair: -len(pair[0])):
            graph_code = graph_code.replace(before, after)
            ridge_code = ridge_code.replace(before, after)
            calibration_code = calibration_code.replace(before, after)
        ridge_code = ridge_code.replace(
            'print("Series generadas por partición:", ridge_result["counts"])',
            'split_labels = {"training": "entrenamiento", "validation": "validación",\n'
            '                "calibration": "calibración", "test": "prueba"}\n'
            'point_labels = {"frozen": "congelado", "ridge": "ridge"}\n'
            'print("Series generadas por partición:",\n'
            '      [(split_labels[key], count) for key, count in ridge_result["counts"].items()])')
        ridge_code = ridge_code.replace('"| " + name + " | "', '"| " + point_labels[name] + " | "')
        ridge_code = ridge_code.replace('label=name, s=55', 'label=point_labels[name], s=55')
        calibration_code = calibration_code.replace(
            'calibration_result = calibration_experiment()',
            'calibration_result = calibration_experiment()\n'
            'interval_labels = {"gaussian": "gaussiana", "global": "global", "stratified": "estratificada"}')
        calibration_code = calibration_code.replace('"| " + name + " | "', '"| " + interval_labels[name] + " | "')
    add_before_results(document, [cell("markdown", introduction, key), cell("code", graph_code, key + "/graph"),
                                 cell("markdown", fitting_text, key + "/ridge-text"),
                                 cell("code", ridge_code, key + "/ridge"),
                                 cell("markdown", calibration_text, key + "/calibration-text"),
                                 cell("code", calibration_code, key + "/calibration"),
                                 cell("markdown", conclusion, key + "/own-data")])


def corpus_tables(document: dict, lang: str) -> None:
    key = "corpus/numerical-comparisons"
    if any(item.get("id") == hashlib.sha256(key.encode()).hexdigest()[:12] for item in document["cells"]):
        return
    explanation = (
        "The first table compares the independently called Kendall reference with the adapter's same-feature "
        "confirmation statistic. The second table contrasts the newly fitted selector, the discovery-chosen "
        "constant and the retrospective oracle on the confirmation series. Each contributes one mean over "
        "its three forecast origins; individual leads are not additional series. The oracle observes the "
        "future scoring outcome and is a lower bound, not an available forecast-selection rule."
        if lang == "en" else
        "La primera tabla compara la referencia independiente de Kendall con el estadístico del adaptador "
        "para la misma característica y confirmación. La segunda contrasta el selector recién ajustado, "
        "la constante elegida en descubrimiento y el oráculo retrospectivo sobre series de confirmación. "
        "Cada serie aporta una media de tres orígenes; las anticipaciones no añaden series. El oráculo "
        "observa resultados futuros: es una cota, no una regla de selección disponible al pronosticar."
    )
    code = '''# Tabulate the actually executed reference statistic and the newly fitted selector outcome.
adapter = next(row for row in confirmation_tests if row["feature"] == chosen)
print("| Implementation | Kendall tau | Probability |")
print("|---|---:|---:|")
print(f"| product adapter | {adapter['tau']:.8f} | {adapter['p']:.8g} |")
print(f"| SciPy reference | {float(tau):.8f} | {float(probability):.8g} |")
print("| Rule | Confirmation series | Mean MASE |")
print("|---|---:|---:|")
for rule, score in reproduced["selection_mean_mase"].items():
    print(f"| {rule} | {len(confirmation)} | {score:.6f} |")
'''
    reading = (
        "Agreement between reference and adapter concerns a precisely matched statistic, not a forecast "
        "accuracy claim. The selector's table measures a different decision: whether features estimated "
        "before targets can choose a lower-error method on untouched series. Its unfavorable mean relative "
        "to the discovery constant remains visible. Confirmed association alone cannot justify replacing "
        "that constant with this selector, because association and useful out-of-sample selection are "
        "different hypotheses."
        if lang == "en" else
        "El acuerdo de referencia y adaptador corresponde a un estadístico comparable, no a exactitud "
        "predictiva. La tabla del selector mide otra decisión: si características anteriores al objetivo "
        "eligen un método de menor error en series intactas. Su media desfavorable frente a la constante "
        "de descubrimiento sigue visible. Una asociación confirmada no justifica reemplazar la constante "
        "por este selector: asociación y selección útil fuera de muestra son hipótesis diferentes."
    )
    if lang == "es":
        for before, after in {
            "# Tabulate the actually executed reference statistic and the newly fitted selector outcome.":
                "# Tabula el estadístico de referencia ejecutado y el resultado del selector reajustado.",
            "| Implementation | Kendall tau | Probability |": "| Implementación | Tau de Kendall | Probabilidad |",
            "| product adapter |": "| adaptador del producto |", "| SciPy reference |": "| referencia SciPy |",
            "| Rule | Confirmation series | Mean MASE |": "| Regla | Series de confirmación | MASE medio |",
        }.items():
            code = code.replace(before, after)
    add_before_results(document, [cell("markdown", explanation, key), cell("code", code, key + "/code"),
                                 cell("markdown", reading, key + "/reading")])


def narrative_and_loader_corrections(document: dict, name: str, lang: str) -> None:
    for item in document["cells"]:
        text = text_of(item)
        if name == "03-corpus-confirmation" and lang == "es" and item["cell_type"] == "code":
            text = text.replace('ax.bar(list(scores), list(scores.values()))',
                                'ax.bar([display_labels[name] for name in scores], list(scores.values()))')
            text = text.replace('print(name, round(score, 4))', 'print(display_labels[name], round(score, 4))')
            text = text.replace('{rule} | {len(confirmation)}', '{display_labels[rule]} | {len(confirmation)}')
        if name == "03-model-comparison" and item["cell_type"] == "markdown":
            if lang == "en":
                text = text.replace(
                    "Four statistical/tree adapters execute here. The neural and pretrained entries are rescored frozen paths, "
                    "so this lesson supplies no new fitting or current-checkpoint evidence for them. Their printed error and "
                    "coverage values remain useful when interpreted with that provenance.",
                    "Four statistical/tree adapters and seven neural/pretrained reference implementations execute here. "
                    "Reference package versions and checkpoint revisions accompany the fresh returned paths. "
                    "Earlier frozen paths remain separately identified, including direct-torch adaptations. "
                    "The numerical table scores fresh and retained rows without merging their provenance.")
            else:
                text = text.replace(
                    "Aquí se ejecutan cuatro adaptadores estadísticos y de árboles. Las entradas neuronales y preentrenadas "
                    "son rutas congeladas reevaluadas: la lección no aporta un ajuste nuevo ni evidencia de checkpoints "
                    "actuales. Sus errores y coberturas siguen siendo útiles si se interpretan junto con esa procedencia.",
                    "Aquí se ejecutan cuatro adaptadores estadísticos y de árboles y siete referencias neuronales o "
                    "preentrenadas. Las trayectorias nuevas incluyen versiones de paquetes y revisiones de modelos. "
                    "Se identifican por separado las rutas congeladas anteriores y las adaptaciones directas en torch. "
                    "La tabla puntúa filas nuevas y conservadas sin mezclar su procedencia.")
        if name == "04-context-memory" and item["cell_type"] == "markdown" and "k_i=" in text:
            text = text.replace(r"\|u-u_i\|^2", "d_i^2")
            if lang == "en":
                text = re.sub(r"At a query origin, let \$u\$.*?The relative weight for its loss is",
                              "Use the four clipped normalized context coordinates and RMS distance $d_i$ "
                              "defined above. Let $a_i$ be the age in remembered origins and "
                              "$b=\\\\max(\\\\operatorname{median}_i d_i,0.25)$. "
                              "The combined recency and similarity weight for the memory's loss is", text)
            else:
                text = re.sub(r"En un origen de consulta, sea \$u\$.*?El peso relativo de su pérdida es",
                              "Usa las cuatro coordenadas contextuales normalizadas y recortadas y la distancia "
                              "RMS $d_i$ definida arriba. Sea $a_i$ la antigüedad en orígenes recordados y "
                              "$b=\\\\max(\\\\operatorname{median}_i d_i,0.25)$. "
                              "El peso conjunto de recencia y similitud para esa pérdida es", text)
        if name == "04-information-boundaries":
            if item["cell_type"] == "code":
                replacements = {
                    'current = json.loads((root / "data/derived/readiness.json").read_text(encoding="utf-8"))':
                        'current = release_inputs["readiness"]',
                    'admitted = json.loads((root / "data/derived/manifests/index.json").read_text(encoding="utf-8"))':
                        'admitted = release_inputs["admitted"]',
                    'derived = root / "data/derived"\n': '',
                    'fresh = json.loads((derived / "fresh-reevaluation.json").read_text(encoding="utf-8"))':
                        'fresh = release_inputs["fresh"]',
                    'combination_index = json.loads((derived / "validated-combinations.json").read_text(encoding="utf-8"))':
                        'combination_index = release_inputs["combination_index"]',
                    'combination_case = json.loads((derived / entry["path"]).read_text(encoding="utf-8"))':
                        'combination_case = release_inputs["combination_case"]',
                    'trace = json.loads(path.read_text(encoding="utf-8"))': 'trace, _ = exported_pair(output, case.id)',
                    'with TemporaryDirectory() as directory:': 'with TemporaryDirectory(dir=environ["CAOS_TEMP_ROOT"]) as directory:',
                    'print("Ingestión", table.summary())':
                        'print("Ingestión: aceptadas, rechazadas, señaladas:",\n'
                        '      len(table.accepted), len(table.rejected), len(table.flagged))',
                }
                for before, after in replacements.items():
                    text = text.replace(before, after)
            else:
                text = re.sub(
                    r"The browser experiment uses a different boundary again\..*?(?=\n\s*\n|\Z)",
                    "The actual graph, ridge and calibration calls above use three different information boundaries. "
                    "The observed graph receives history only; ridge weights use generated training and validation "
                    "data; interval radii use separate calibration outcomes. The final tests choose none of these "
                    "objects. Source identities explain the relationship to retained studies without treating "
                    "a checksum or a checker invocation as a new scientific execution.", text, flags=re.S)
                text = re.sub(
                    r"El experimento del navegador emplea otra frontera\..*?(?=\n\s*\n|\Z)",
                    "Las llamadas reales al grafo, ridge y calibración de arriba usan tres fronteras distintas. "
                    "El grafo observado recibe solo historia; los pesos ridge usan entrenamiento y validación "
                    "generados; los radios usan resultados separados de calibración. Las pruebas finales no "
                    "eligen ninguno de esos objetos. La procedencia enlaza estudios conservados sin presentar "
                    "un resumen criptográfico ni un verificador como ejecución científica nueva.", text, flags=re.S)
        item["source"] = text
    if name == "02-complexity":
        first = document["cells"][0]
        text = text_of(first)
        title = ("Distinguishing sequence complexity from changing volatility" if lang == "en" else
                 "Distinguir complejidad secuencial y volatilidad cambiante")
        lines = text.splitlines()
        lines[0] = "# " + title
        text = "\n".join(lines) + "\n"
        question = (
            "**Question:** What do ordering-based complexity and scale-based volatility diagnostics measure "
            "on a generated control and an authentic electricity excerpt, and which conclusions do neither justify?"
            if lang == "en" else
            "**Pregunta:** ¿Qué miden los diagnósticos de complejidad del orden y volatilidad de la escala "
            "en un control generado y un extracto eléctrico auténtico, y qué conclusiones no justifican?"
        )
        text = re.sub(r"(?m)^\*\*(?:Question|Pregunta):\*\*.*$", question, text)
        first["source"] = text
        for item in document["cells"]:
            if item["cell_type"] != "markdown":
                continue
            text = text_of(item)
            marker = "**Answer:**" if lang == "en" else "**Respuesta:**"
            if marker in text:
                extra = (
                    " The later volatility section uses a separate authentic electricity sequence: its fitted "
                    "conditional standard deviation describes scale in source units, while entropy and binary "
                    "phrase counts concern the generated control's representation and ordering. These are "
                    "different inputs and questions; neither calculation alone establishes chaos or calibrated "
                    "future forecast intervals."
                    if lang == "en" else
                    " La sección de volatilidad utiliza otra secuencia eléctrica auténtica: su desviación "
                    "condicional ajustada describe escala en unidades de la fuente; entropía y frases binarias "
                    "describen representación y orden del control generado. Son entradas y preguntas distintas; "
                    "ningún cálculo por sí solo establece caos ni intervalos futuros calibrados."
                )
                text = re.sub(r"(?ms)(^" + re.escape(marker) + r".*?)(?=\n\s*\n|\Z)",
                              lambda match: match.group(1) if extra.strip() in match.group(1)
                              else match.group(1) + extra, text, count=1)
                item["source"] = text


def revise(document: dict, relative: str) -> dict:
    """Finalize one authored document; idempotent for an existing source notebook."""
    lang = document["metadata"]["caos"]["language"]
    name = Path(relative).stem
    header(document, lang)
    for item in document["cells"]:
        text = text_of(item).replace("chronoscopelab", "engine")
        if lang == "es":
            if item["cell_type"] == "code":
                text = localize_code(text)
            else:
                replacements = {"cuadernos": "notebooks", "cuaderno": "notebook",
                                "Cuadernos": "Notebooks", "Cuaderno": "Notebook",
                                "una estación incompleta": "un ciclo estacional incompleto",
                                "estación terminal": "ciclo estacional terminal",
                                "historia comprometida": "historia versionada",
                                "valores comprometidos": "valores conservados en el repositorio",
                                "regresión de cresta": "regresión ridge",
                                "cresta": "regresión ridge",
                                "un caso real del producto": "un caso sintético del producto"}
                for before, after in replacements.items():
                    text = text.replace(before, after)
        item["source"] = text
    set_data_provenance(document, relative, lang)
    if name == "04-context-memory":
        numerical_distance(document, lang)
        uncertainty(document, name, lang)
    elif name == "05-temporal-validation":
        uncertainty(document, name, lang)
    elif name == "01-shape-patterns":
        authentic_shapes(document, lang)
    elif name == "02-complexity":
        volatility_lesson(document, lang)
    elif name == "03-model-comparison":
        actual_references(document, lang)
    elif name == "04-information-boundaries":
        browser_operations(document, lang)
    elif name == "03-corpus-confirmation":
        corpus_tables(document, lang)
    comparison_tables(document, name, lang)
    narrative_and_loader_corrections(document, name, lang)
    setup_and_imports(document, name, lang)
    figure_titles(document, name, lang)
    terminal_sections(document, name, lang)
    declarations(document, name, lang)
    scope_pin = next(pin for pin in (ROOT / "notebooks/requirements.txt").read_text(encoding="utf-8").splitlines()
                     if pin.startswith("forecastscope=="))
    for item in document["cells"]:
        text = text_of(item).replace("ForecastScope 0.1.1", "ForecastScope " + scope_pin.split("==")[1])
        if name == "02-seasonal-phase" and item["cell_type"] == "code":
            text = re.sub(r'electricity = np.loadtxt\(root / "data/examples/electricity_sample.csv"[^\n]*\)',
                          "electricity = electricity_values", text)
        item["source"] = text
    document["metadata"]["caos"]["title"] = text_of(document["cells"][0]).splitlines()[0].removeprefix("# ")
    return document


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", help="Relative notebook path inside each language tree")
    parser.add_argument("--sources", action="store_true", help="Reconcile the authored Markdown templates before building")
    args = parser.parse_args()
    if args.sources:
        revise_authoring_sources()
        return
    for lang in ("en", "es"):
        paths = ([ROOT / "notebooks" / lang / args.only] if args.only else
                 sorted((ROOT / "notebooks" / lang).rglob("*.ipynb")))
        for path in paths:
            document = json.loads(path.read_text(encoding="utf-8"))
            revise(document, path.relative_to(ROOT / "notebooks" / lang).as_posix())
            path.write_text(json.dumps(document, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def revise_authoring_sources() -> None:
    """Persist literal corrections in source templates rather than hiding stale claims."""
    levels = {"01-baseline": 1, "02-seasonal-phase": 2, "03-model-comparison": 3,
              "04-context-memory": 4, "01-shape-patterns": 1, "02-complexity": 2,
              "03-corpus-confirmation": 3, "01-information-boundaries": 3}
    for lang in ("en", "es"):
        for path in sorted((ROOT / "docs/lessons" / lang).rglob("*.md")):
            if path.stem not in levels:
                continue
            name = "04-information-boundaries" if path.stem == "01-information-boundaries" else path.stem
            pieces = re.split(r"(<!-- code: [a-z_]+ -->)", path.read_text(encoding="utf-8"))
            cells = [{"cell_type": "marker" if index % 2 else "markdown", "source": piece}
                     for index, piece in enumerate(pieces)]
            document = {"cells": cells, "metadata": {"caos": {"level": levels[path.stem], "language": lang}}}
            header(document, lang)
            for item in cells:
                text = text_of(item).replace("chronoscopelab", "engine")
                if lang == "es":
                    for before, after in {"cuadernos": "notebooks", "cuaderno": "notebook",
                                           "Cuadernos": "Notebooks", "Cuaderno": "Notebook",
                                           "una estación incompleta": "un ciclo estacional incompleto",
                                           "estación terminal": "ciclo estacional terminal",
                                           "historia comprometida": "historia versionada",
                                           "valores comprometidos": "valores conservados en el repositorio",
                                           "regresión de cresta": "regresión ridge",
                                           "cresta": "regresión ridge",
                                           "un caso real del producto": "un caso sintético del producto"}.items():
                        text = text.replace(before, after)
                item["source"] = text
            set_data_provenance(document, name + ".ipynb", lang)
            narrative_and_loader_corrections(document, name, lang)
            source = "\n\n".join(text_of(item).strip() for item in document["cells"] if text_of(item).strip()) + "\n"
            path.write_text(source, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
