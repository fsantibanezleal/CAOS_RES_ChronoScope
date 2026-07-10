// The citation library (ADR-0016 §7 / ADR-0017 §4). Every entry carries a real DOI or URL; inline <Cite>
// and per-section <Refs> resolve against these ids. Transcribed from docs/research (the persisted, verified
// reference library). NEVER a bare author-year without a link, NEVER a bottom-of-page bibliography dump.
import type { Citation } from '@fasl-work/caos-app-shell';

export const CITATIONS: Citation[] = [
  // --- scoring / classical ---
  { id: 'mase', label: 'Hyndman & Koehler 2006', citation: 'Hyndman, R. J., & Koehler, A. B. (2006). Another look at measures of forecast accuracy. International Journal of Forecasting, 22(4), 679-688.', doi: '10.1016/j.ijforecast.2006.03.001' },
  { id: 'msis', label: 'Gneiting & Raftery 2007', citation: 'Gneiting, T., & Raftery, A. E. (2007). Strictly Proper Scoring Rules, Prediction, and Estimation. Journal of the American Statistical Association, 102(477), 359-378.', doi: '10.1198/016214506000001437' },
  { id: 'theta', label: 'Assimakopoulos & Nikolopoulos 2000', citation: 'Assimakopoulos, V., & Nikolopoulos, K. (2000). The theta model: a decomposition approach to forecasting. International Journal of Forecasting, 16(4), 521-530.', doi: '10.1016/S0169-2070(00)00066-2' },
  { id: 'theta-ses', label: 'Hyndman & Billah 2003', citation: 'Hyndman, R. J., & Billah, B. (2003). Unmasking the Theta method. International Journal of Forecasting, 19(2), 287-290.', doi: '10.1016/S0169-2070(01)00143-1' },
  { id: 'hyndman-fpp', label: 'Hyndman & Athanasopoulos 2021', citation: 'Hyndman, R. J., & Athanasopoulos, G. (2021). Forecasting: Principles and Practice (3rd ed.). OTexts.', url: 'https://otexts.com/fpp3/' },
  { id: 'lightgbm', label: 'Ke et al. 2017', citation: 'Ke, G., et al. (2017). LightGBM: A Highly Efficient Gradient Boosting Decision Tree. NeurIPS 30.', url: 'https://papers.nips.cc/paper/6907-lightgbm-a-highly-efficient-gradient-boosting-decision-tree' },
  { id: 'm5', label: 'Makridakis et al. 2022 (M5)', citation: 'Makridakis, S., Spiliotis, E., & Assimakopoulos, V. (2022). The M5 competition: Background, organization, and implementation. International Journal of Forecasting, 38(4), 1325-1336.', doi: '10.1016/j.ijforecast.2021.07.007' },

  // --- transformers (LTSF lineage) + the linear debate ---
  { id: 'informer', label: 'Zhou et al. 2021 (Informer)', citation: 'Zhou, H., et al. (2021). Informer: Beyond Efficient Transformer for Long Sequence Time-Series Forecasting. AAAI-21.', url: 'https://arxiv.org/abs/2012.07436' },
  { id: 'autoformer', label: 'Wu et al. 2021 (Autoformer)', citation: 'Wu, H., et al. (2021). Autoformer: Decomposition Transformers with Auto-Correlation for Long-Term Series Forecasting. NeurIPS 34.', url: 'https://arxiv.org/abs/2106.13008' },
  { id: 'patchtst', label: 'Nie et al. 2023 (PatchTST)', citation: 'Nie, Y., et al. (2023). A Time Series is Worth 64 Words: Long-term Forecasting with Transformers. ICLR-23.', url: 'https://arxiv.org/abs/2211.14730' },
  { id: 'itransformer', label: 'Liu et al. 2024 (iTransformer)', citation: 'Liu, Y., et al. (2024). iTransformer: Inverted Transformers Are Effective for Time Series Forecasting. ICLR-24.', url: 'https://arxiv.org/abs/2310.06625' },
  { id: 'dlinear', label: 'Zeng et al. 2023 (DLinear/NLinear)', citation: 'Zeng, A., et al. (2023). Are Transformers Effective for Time Series Forecasting? AAAI-23.', url: 'https://arxiv.org/abs/2205.13504' },
  { id: 'nhits', label: 'Challu et al. 2023 (NHITS)', citation: 'Challu, C., Olivares, K.G., Oreshkin, B.N., et al. (2023). NHITS: Neural Hierarchical Interpolation for Time Series Forecasting. AAAI-23.', url: 'https://arxiv.org/abs/2201.12886' },
  { id: 'tft', label: 'Lim et al. 2021 (TFT)', citation: 'Lim, B., et al. (2021). Temporal Fusion Transformers for interpretable multi-horizon time series forecasting. International Journal of Forecasting, 37(4), 1748-1764.', doi: '10.1016/j.ijforecast.2021.03.012' },

  // --- foundation models ---
  { id: 'fm-survey', label: 'Kottapalli et al. 2025 (FM survey)', citation: 'Kottapalli, S. R. K., et al. (2025). Foundation Models for Time Series: A Survey. arXiv:2504.04011.', url: 'https://arxiv.org/abs/2504.04011' },
  { id: 'chronos', label: 'Ansari et al. 2024 (Chronos)', citation: 'Ansari, A. F., et al. (2024). Chronos: Learning the Language of Time Series. arXiv:2403.07815.', url: 'https://arxiv.org/abs/2403.07815' },
  { id: 'chronos2', label: 'Amazon 2025 (Chronos-2)', citation: 'Amazon Science (2025). Chronos-2: universal, covariate-aware zero-shot forecasting. arXiv:2510.15821.', url: 'https://arxiv.org/abs/2510.15821' },
  { id: 'timesfm', label: 'Das et al. 2024 (TimesFM)', citation: 'Das, A., et al. (2024). A decoder-only foundation model for time-series forecasting. ICML-24. arXiv:2310.10688.', url: 'https://arxiv.org/abs/2310.10688' },
  { id: 'moirai', label: 'Woo et al. 2024 (Moirai)', citation: 'Woo, G., et al. (2024). Unified Training of Universal Time Series Forecasting Transformers. arXiv:2402.02592.', url: 'https://arxiv.org/abs/2402.02592' },
  { id: 'tirex', label: 'Auer et al. 2025 (TiRex)', citation: 'Auer, A., et al. (2025). TiRex: Zero-Shot Forecasting Across Long and Short Horizons. arXiv:2505.23719.', url: 'https://arxiv.org/abs/2505.23719' },
  { id: 'tirex2', label: 'Podest et al. 2026 (TiRex-2)', citation: 'Podest, P., et al. (2026). TiRex-2: Generalizing TiRex to Multivariate Data and Streaming. arXiv:2607.01204.', url: 'https://arxiv.org/abs/2607.01204' },
  { id: 'flowstate', label: 'IBM 2025 (FlowState)', citation: 'IBM Research (2025). FlowState: Sampling Rate Invariant Time Series Forecasting. arXiv:2508.05287.', url: 'https://arxiv.org/abs/2508.05287' },
  { id: 'ttm', label: 'Ekambaram et al. 2024 (Granite TTM)', citation: 'Ekambaram, V., et al. (2024). Tiny Time Mixers (TTM): Fast Pre-trained Models for Enhanced Zero/Few-Shot Forecasting. arXiv:2401.03955.', url: 'https://arxiv.org/abs/2401.03955' },

  // --- benchmarks + evaluation ---
  { id: 'gifteval', label: 'Aksu et al. 2024 (GIFT-Eval)', citation: 'Aksu, T., et al. (2024). GIFT-Eval: A Benchmark for General Time Series Forecasting Model Evaluation. arXiv:2410.10393.', url: 'https://arxiv.org/abs/2410.10393' },
  { id: 'fevbench', label: 'AutoGluon 2025 (fev-bench)', citation: 'Shchur, O., et al. (2025). fev-bench: A Realistic Benchmark for Time Series Forecasting. arXiv:2509.26468.', url: 'https://arxiv.org/abs/2509.26468' },
  { id: 'tfb', label: 'Qiu et al. 2024 (TFB)', citation: 'Qiu, X., et al. (2024). TFB: Towards Comprehensive and Fair Benchmarking of Time Series Forecasting Methods. PVLDB 17. arXiv:2403.20150.', url: 'https://arxiv.org/abs/2403.20150' },
  { id: 'prequential', label: 'Dawid 1984', citation: 'Dawid, A. P. (1984). Present Position and Potential Developments: Some Personal Views. Journal of the Royal Statistical Society A, 147(2), 278-292.', doi: '10.2307/2981683' },

  // --- data ---
  { id: 'uci-electricity', label: 'Trindade 2015 (UCI Electricity)', citation: 'Trindade, A. (2015). ElectricityLoadDiagrams20112014. UCI Machine Learning Repository (CC BY 4.0).', doi: '10.24432/C58C86' },
];
