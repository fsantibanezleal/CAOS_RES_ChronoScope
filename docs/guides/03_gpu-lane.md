# GPU and native reference runtimes

The deployed static application requires no GPU or backend. Native neural and foundation-model fitting happens in separately declared offline environments, and the browser inspects admitted paths or runs its own small TypeScript/ONNX methods.

The [fresh execution guide](fresh-reevaluation.md) specifies the retained twenty-two-configuration runtime, checkpoint revisions and complete-roster admission. The [notebook reference guide](notebook-references.md) specifies actual seven-model lesson execution and its separate pinned Linux interpreter/cache. Do not replace either environment with the latest upstream package versions and assign the old experiment identity to new outputs.

`requirements-gpu.txt` and the precompute requirements describe optional local model dependencies. Match the torch build to the actual CUDA toolchain; TiRex's retained 0.1.1 lane also requires a working native compiler and Ninja. Newer TiRex versions have different runtime and checkpoint requirements. Keep model weights and build caches in configured external roots, preserve existing environments and record actual hardware/thread/checkpoint identities with a new experiment.

A local reduced-runtime bake does not replace the admitted full roster. Current application generation carries and independently scores the source-bound studies; fresh model inference is an explicit separate operation.
