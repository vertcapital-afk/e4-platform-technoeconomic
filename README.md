# e4-platform Techno-economic — Prospective HVAC+PV Assessment

This repository contains the standardised simulation inputs and outputs, weather files, cost/carbon catalogue and evaluation scripts supporting the prospective techno-economic assessment of HVAC+PV(+battery) system sets under future climate and grid decarbonisation scenarios presented in the associated Applied Energy submission (two Portuguese case studies: a residential multi-family dwelling fraction, RB6, and a non-residential university building, iiiUC).

The files are provided to support the reproducibility of the published results. The proprietary e4/ILLIANCe³ evaluation engine itself is **not** included; the scripts in `scripts/` serve as the executable specification of the data interface and of the evaluation run, and require the engine to execute.

## Contents

```
data/
  blocoA_runs.csv                  Run registry, RB6 (24 runs: 12 simulated + 12 derived)
  blocoA_resultados_mensais.csv    Normalised energy results, RB6
  blocoB_runs.csv                  Run registry, iiiUC (24 runs: 12 simulated + 12 derived)
  blocoB_resultados_mensais.csv    Normalised energy results, iiiUC
  component_catalogue.csv          HVAC/PV/battery components: CAPEX, embodied carbon,
                                   service life, EN 15459 maintenance group (paper Table 2)
  matriz_artigo10.csv              Full evaluation matrix: FIN30, LC-GWP30, self-consumption
                                   and decompositions, 48 runs × 2 emission-factor trajectories
models/
  MFH/                             RB6 dynamic-simulation results workbook (DesignBuilder)
  iiiUC/                           EnergyPlus IDF models (BAU / MultiSplit / HP), occupancy
                                   and HVAC schedules, results workbook
weather/
  *.epw, *.stat                    Coimbra weather files: TMYx 2007–2021 (present) and
                                   FWG v4.3.0 CMIP6-ensemble morphs (SSP2-4.5/2050,
                                   SSP3-7.0/2050, SSP3-7.0/2080)
scripts/
  transcrever_resultados.py        Transcription of the simulation workbooks into the
                                   normalised CSV interface (incl. the no-PV derivation rule)
  correr_matriz_artigo10.py        Evaluation run: ingestion, catalogue composition and
                                   scenario matrix (requires the e4 engine, not included)
```

## Reproducibility notes

- Simulated runs are the 12 with-PV cases per building (3 system sets × 4 climates); the 12 without-PV cases are derived arithmetically (total electricity as grid import; PV/storage set to zero), as documented in the paper's methods.
- Ingestion validation (energy vectors, monthly-to-annual consistency within 1%, mandatory fields) is enforced by the engine; all 48 runs in `data/` pass it.
- The `DGEG2025` trajectory in `matriz_artigo10.csv` follows the DGEG (2025) emission-factor anchors (0.138/0.055/0.009/0.005 kgCO₂eq/kWh at 2023/2030/2040/2050, linear interpolation; natural gas constant at 0.203); `EF_constante` holds the present-day factor for comparison.

## Attribution

Present-climate weather file (TMYx.2007–2021) sourced from climate.onebuilding.org; future files morphed with the open-source Future Weather Generator v4.3.0 (Rodrigues, Fernandes & Carvalho, 2023, Building and Environment 233, 110104), CMIP6 all-model ensemble.

## Associated publication

*Prospective techno-economic assessment of HVAC+PV system sets under future climate and grid decarbonisation scenarios: a Portuguese residential and non-residential case study.* Submitted to Applied Energy. A citation with DOI will be added upon publication.

## License

- **Scripts** (`scripts/`): MIT — see [LICENSE](LICENSE).
- **Data and models** (`data/`, `models/`): Creative Commons Attribution 4.0
  International (CC BY 4.0) — see [LICENSE-DATA](LICENSE-DATA). Please cite
  the associated publication when reusing this material.
- **Weather files** (`weather/`): redistributed third-party and derivative
  data, **not** relicensed here. The present-climate TMYx file originates
  from [climate.onebuilding.org](https://climate.onebuilding.org) (free use
  with credit, under that project's terms); the future-climate files are
  derivatives morphed with the open-source Future Weather Generator v4.3.0
  (Rodrigues, Fernandes & Carvalho, 2023, Building and Environment 233,
  110104). Preserve this attribution when redistributing.
