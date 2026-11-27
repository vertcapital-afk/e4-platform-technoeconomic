# Prospective techno-economic assessment of heating, ventilation, air conditioning and photovoltaic systems under future climate and grid decarbonisation scenarios: a Portuguese case study

**Status:** Revised manuscript (R1), Applied Energy.

This repository contains the standardised simulation inputs and outputs, weather files, cost/carbon catalogue and evaluation scripts supporting the prospective techno-economic assessment of HVAC+PV(+battery) system sets under future climate and grid decarbonisation scenarios presented in the associated Applied Energy manuscript (two Portuguese case studies: a residential multi-family dwelling fraction, RB6, and a non-residential university building, iiiUC).

The files are provided to support the reproducibility of the reported results. The proprietary e4/ILLIANCe³ evaluation engine itself is **not** included; the scripts in `scripts/` serve as the executable specification of the data interface and of the evaluation runs, and require the engine to execute.

## Changes in revision R1

This version of the repository corresponds to the revised manuscript (R1). The version that accompanied the original submission (July 2026) remains available, unchanged, at:
<https://github.com/vertcapital-afk/e4-platform-technoeconomic/tree/d36502aaae73505a11ae7f3917ee6642d35673ca>

Changes to the data in R1:

- Embodied carbon: several HVAC inventories were corrected against the manufacturers' EPDs (e.g. the non-residential multi-split pack: 12,940 → 3,895 kgCO2eq per installation), and the embodied carbon of the non-residential baseline equipment is now taken from the EU Ecodesign preparatory studies. All carbon results were recomputed.
- VAT: all component prices are now net of VAT (the PV price previously included VAT at 6 %), and VAT at 23 % is applied to investment and maintenance as a non-recoverable cost. This changes the global costs (FIN30).
- Result files of the sensitivity analyses of the revision were added (`data/r1/`).

Changes to the repository in R1:

- `data/component_catalogue.csv` replaced by the catalogue used by the R1 cost basis, with the columns of Table 2 of the revised manuscript.
- `data/matriz_artigo10.csv` replaced by its R1 version (same columns; see the notes below).
- `data/r1/` added: the result files of the revision (one folder per axis) and the hourly simulation series used by two of them (`data/r1/horarios/`).
- `.gitattributes` added, so that `data/r1/horarios/` is stored byte for byte.
- `scripts/r1/` added: the evaluation scripts that produced the R1 cost basis.
- The energy inputs (`data/bloco*`), `models/`, `weather/` and the two July scripts are unchanged.

## Contents

```
data/
  blocoA_runs.csv                  Run registry, RB6 (24 runs: 12 simulated + 12 derived)
  blocoA_resultados_mensais.csv    Normalised energy results, RB6
  blocoB_runs.csv                  Run registry, iiiUC (24 runs: 12 simulated + 12 derived)
  blocoB_resultados_mensais.csv    Normalised energy results, iiiUC
  component_catalogue.csv          HVAC/PV/battery components (paper Table 2): net price,
                                   EN 15459 maintenance group, service life, installation
                                   years, residual fraction, units counted, embodied carbon
  matriz_artigo10.csv              Evaluation matrix, 48 runs × 2 emission-factor trajectories:
                                   carbon on the R1 inventories, costs on the submitted
                                   cost basis (equipment net of VAT; PV price including
                                   VAT at 6 %); self-consumption τAC (Table 4)
  r1/
    base_financeira/               R1 cost basis (VAT 23 %, not recoverable): FIN30 and its terms
                                   for 48 runs × 2 trajectories — Tables 4–5, Figures 4–6
    sensibilidades/                Base case + 14 one-factor-at-a-time variants, 48 runs each
                                   (720 rows) — Tables 6–8, Figure 8; its base rows are those
                                   read for Tables 4–5 and Figures 4–6
    inventario/                    Embodied-carbon inventory axis, 11 scenarios × 48 runs
                                   (528 rows) — Table 9
    dimensionamento_pv/            PV array × battery sizing grid, 9 configurations × 24 runs
                                   with PV (216 rows) — Table 10
    degradacao/                    PV (0.5 and 0.7 %/year) and HVAC performance degradation
                                   (96 rows) — Section 3.5
    incremento_arrefecimento/      Variant without the cooling increments of the two reversible
                                   RB6 units (48 runs) — Section 3.5 (convention of Section 2.5)
    temperatura_pv/                PV module-temperature check (supplementary; not reported in
                                   the tables of the paper), 24 runs with PV
    horarios/                      Hourly simulation outputs (8,760 h) of the 12 with-PV runs of
      MFH/  iiiUC/                 each building (3 system sets × 4 climates), as delivered by
                                   the author of the simulations (24 CSV; RB6 in MFH/); used by
                                   dimensionamento_pv/ and degradacao/
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
  r1/
    auditar_base_e_sensibilidades.py  Component composition per set (catalogue keys), replacement
                                      calendar and single-run evaluation used by the R1 scripts
    fiscalidade_a10.py                Net price and VAT treatment of each component
    recalcular_financeiro_a10.py      R1 cost basis (produces data/r1/base_financeira/)
```

Each folder of `data/r1/` holds the CSV and JSON files of the corresponding result folder of the authors' working repository, copied without change (single exception below). The `resumo_*.json` file of each folder records the run configuration and, where present, the SHA-256 of its inputs. `horarios/` holds input series rather than results: the `series_sha256` field of `dimensionamento_pv/resumo_dimensionamento.json` and of `degradacao/resumo_degradacao.json` records, for each of the 24 runs with PV, the file it used and its SHA-256.

| `data/r1/` folder | Source result folder |
|---|---|
| `base_financeira/` | `resultados_financeiros_adotados_2026-11-23` |
| `sensibilidades/` | `resultados_sensibilidades_A10_R1_v7` |
| `inventario/` | `resultados_inventario_A10_R1_v5` |
| `dimensionamento_pv/` | `resultados_dimensionamento_A10_R1_v1` |
| `degradacao/` | `resultados_degradacao_A10_R1_v1` |
| `incremento_arrefecimento/` | `resultados_incremento_A10_R1_v1` |
| `temperatura_pv/` | `resultados_temperatura_pv_A10_R1_v1` |
| `horarios/` | `horarios_marco_2026-11-26` (`MFH/`, `iiiUC/`) |

## Reproducibility notes

- Simulated runs are the 12 with-PV cases per building (3 system sets × 4 climates); the 12 without-PV cases are derived arithmetically (total electricity as grid import; PV/storage set to zero), as documented in the paper's methods.
- Ingestion validation (energy vectors, monthly-to-annual consistency within 1%, mandatory fields) is enforced by the engine; all 48 runs in `data/` pass it.
- The `DGEG2025` trajectory in `matriz_artigo10.csv` follows the DGEG (2025) emission-factor anchors (0.138/0.055/0.009/0.005 kgCO₂eq/kWh at 2023/2030/2040/2050, linear interpolation; natural gas constant at 0.203); `EF_constante` holds the present-day factor for comparison.

### Notes on the R1 files

- **Catalogue** (`component_catalogue.csv`). Columns and component labels follow Table 2 of the revised manuscript; the footnote markers of Table 2 are omitted (see the notes to Table 2 in the paper). *Net price* excludes VAT; the PV price is the supplier price including 6 % VAT divided by 1.06 (4,050 / 1.06). In the R1 cost basis, VAT at 23 % is applied to investment and maintenance as a non-recoverable cost. *Units counted* gives whole-unit / pro-rata counts over the 30-year period.
- **Evaluation matrix** (`matriz_artigo10.csv`). The columns are the same as in the July version. Only `lcgwp` and `embc` change (64 of 96 rows: the components whose inventories were corrected); the cost columns (`fin`, `capex_vp`, `custo_energia_vp`) remain on the submitted cost basis (equipment net of VAT; PV price including VAT at 6 %), and `tau_ac` is unchanged. The R1 global cost FIN30 is the column `fin_financeiro` of `r1/base_financeira/matriz_financeira.csv` (the column `fin_historico` there reproduces `fin` of this matrix); the base rows of `r1/sensibilidades/matriz_sensibilidades.csv` (`variante = base`) carry the same values.
- **Scripts** (`scripts/r1/`). The scripts that produced the other folders of `data/r1/` belong to the authors' working repository and are not included; each `resumo_*.json` records the configuration of its run and, except in `temperatura_pv/`, the SHA-256 of its inputs.
- **Paths inside the JSON files** refer to the layout of the authors' working repository: `data\motor\blocoA\runs.csv` and `data\motor\blocoA\resultados_mensais.csv` are `data/blocoA_runs.csv` and `data/blocoA_resultados_mensais.csv` here (likewise for `blocoB`); `studies\a10_tecnoeconomia\resultados\matriz_artigo10.csv` is `data/matriz_artigo10.csv`; `studies\a10_tecnoeconomia\revisao\resultados_*` are the folders of `data/r1/` listed above. The same applies to the paths used by the scripts in `scripts/r1/`. Some JSON files also hash source files of the engine, which is not included.
- **Single change to a copied file.** In `r1/base_financeira/resumo_recalculo.json`, absolute paths of the authors' machine were made relative by removing their local prefix, and nothing else was changed: the prefix of the working repository (`C:\e4-platform\`, 6 occurrences) and the prefix of the authors' local document folder (14 occurrences, in the `fonte_preco` fields of the embedded cost profile, which now begin with `6 Artigos\`). The documents cited in `fonte_preco` are not part of this repository.
- **Hourly series** (`horarios/`). EnergyPlus hourly output, one row per hour from `01/01 01:00:00` to `12/31 24:00:00` (8,760 rows), energies in J. Columns: date/time; site outdoor dry-bulb temperature [°C]; incident solar radiation on the PV surface [W/m²]; inverter DC input and AC output; battery charge and discharge; electric load centre production; facility purchased, surplus and produced electricity; and the end uses fans, cooling, heating, interior lights, interior equipment, pumps and water systems. Variants: RB6 BAU reports water systems as natural gas, the RB6 renovations as electricity; iiiUC has no water-systems column, and its BAU and MultiSplit files have no pumps column. The object names of the PV system differ between the two buildings. File names are as delivered (e.g. `Multisplits` in RB6, `Mulltisplit` in iiiUC). The EnergyPlus input files (`.idf`) of the hourly runs are not included.
- **Line endings and hashes.** The SHA-256 values recorded in the JSON files were computed on files with CRLF line endings. The files that already existed in this repository keep their CRLF line endings: the energy inputs `data/bloco*` and `data/matriz_artigo10.csv` match those values byte for byte. The files of `data/r1/` are stored with LF, as in the Git repository of the authors; where a JSON file records the hash of one of them, it matches after converting LF to CRLF. Exception: the files of `data/r1/horarios/` keep their CRLF line endings (`.gitattributes`: `-text`) and match the recorded hashes byte for byte.

## Attribution

Present-climate weather file (TMYx.2007–2021) sourced from climate.onebuilding.org; future files morphed with the open-source Future Weather Generator v4.3.0 (Rodrigues, Fernandes & Carvalho, 2023, Building and Environment 233, 110104), CMIP6 all-model ensemble.

## Associated publication

*Prospective techno-economic assessment of heating, ventilation, air conditioning and photovoltaic systems under future climate and grid decarbonisation scenarios: a Portuguese case study.* Revised manuscript (R1), Applied Energy. A citation with DOI will be added when available.

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
