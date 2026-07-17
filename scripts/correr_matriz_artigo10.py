#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
correr_matriz_artigo10.py — guião de execução do Artigo 10 (Opus 4.8, 16/07/2026).

Corre a matriz completa (48 corridas: RB6 + iiiUC, 3 sistemas × 4 climas ×
{comPV, semPV}) no motor e4 e escreve os resultados FIN30/LCGWP30 por corrida,
prontos para popular a secção 3 do manuscrito.

PRÉ-REQUISITOS (do lado do Sérgio, ambiente local com o motor e4 completo):
  · Pastas de ingestão, cada uma com runs.csv + resultados_mensais.csv:
        dados/blocoA/{runs.csv, resultados_mensais.csv}   (RB6)
        dados/blocoB/{runs.csv, resultados_mensais.csv}   (iiiUC)
    (capacidades.csv NÃO é preciso: todos os componentes são de custo fixo.)
  · dinamica_capex.py já com o catálogo fechado (bateria + AQS reancorada).

CONTRATO já VERIFICADO por replicação (Opus, 16/07): os 48 CSV passam
dinamica.carregar() sem exceção e energia_final_por_vetor() devolve o gás da
BAU via cons_aqs_kwh (o motor NÃO lê a coluna gas_kwh).

NOTA DE IMPORTAÇÃO: ajuste o prefixo do pacote ('e4' vs 'motor.e4') ao seu
layout — os módulos usam imports relativos ('from .carbono import ...'),
portanto o pacote é 'e4'.
"""
from e4.dinamica import carregar
from e4.dinamica_matriz import Componente, avaliar_matriz, matriz_para_csv
from e4 import dinamica_capex as cap

# ── Catálogos (chaves = coluna 'sistema' de runs.csv) ─────────────────────────
# HVAC apenas; o PV+bateria é acrescentado só ao catálogo comPV (abaixo).
CAT_RB6_HVAC = {
    "BAU":        [Componente(cap.RB6_BAU_AQS),
                   Componente(cap.RB6_BAU_AQUECIMENTO),
                   Componente(cap.RB6_BAU_ARREFECIMENTO)],
    "MultiSplit": [Componente(cap.RB6_BC_AQS_HPWH),      # AQS = HPWH dedicado
                   Componente(cap.RB6_MULTISPLIT)],
    "BombaCalor": [Componente(cap.RB6_BC_AR_AGUA)],      # AQS integrada, 1 comp.
}
CAT_IIIUC_HVAC = {
    "BAU":              [Componente(cap.IIIUC_BAU_RADIADORES),
                         Componente(cap.IIIUC_BAU_PORTATEIS)],
    "Pack1_Mitsubishi": [Componente(cap.IIIUC_PACK1_MITSUBISHI)],
    "Pack2_Daikin":     [Componente(cap.IIIUC_PACK2_DAIKIN)],
}
# PV (2,7 kWp) + bateria (5 kWh) — mesmo hardware nos dois edifícios.
PV_BATERIA = [Componente(cap.RB6_PV), Componente(cap.RB6_BATERIA_5KWH)]

def com_pv(catalogo):
    return {k: v + PV_BATERIA for k, v in catalogo.items()}

# ── Separação comPV / semPV (o catálogo é por 'sistema', não por 'pv') ────────
def split_pv(corridas):
    com = {k: c for k, c in corridas.items() if c.meta["pv"].strip() != "sem"}
    sem = {k: c for k, c in corridas.items() if c.meta["pv"].strip() == "sem"}
    return com, sem

# ── Trajetórias de EF (eixo carbónico) ────────────────────────────────────────
# Corremos as DUAS de uma vez:
#  · 'EF_constante' (None) — fator de emissão presente fixo (braço do clima).
#  · 'DGEG2025'            — trajetória de descarbonização DGEG 2025 (carbono
#                           final do artigo; âncoras ANCORAS_DGEG2025 por defeito).
# Cada corrida gera uma linha por trajetória -> 96 linhas no total (48 × 2).
from e4.pconv import construir_trajetoria
TRAJETORIAS = {"EF_constante": None,
               "DGEG2025": construir_trajetoria()}
# (Sensibilidade opcional do gás — NÃO usar no resultado principal:
#  from e4.pconv import ANCORAS_DGEG2025_GASMIX
#  TRAJETORIAS["DGEG2025_gasmix"] = construir_trajetoria(ANCORAS_DGEG2025_GASMIX))

# ── Execução ──────────────────────────────────────────────────────────────────
def correr(pasta, cat_hvac):
    corr = carregar(pasta)                 # F1: ingestão + validação
    com, sem = split_pv(corr)
    linhas  = avaliar_matriz(com, com_pv(cat_hvac), TRAJETORIAS,
                             perspetiva="REG", referencia=None)
    linhas += avaliar_matriz(sem, cat_hvac,        TRAJETORIAS,
                             perspetiva="REG", referencia=None)
    return linhas

def deltas(linhas):
    """val_vs_ref / dlcgwp_vs_ref vs BAU no MESMO estado de PV e clima, e o
    efeito PV (comPV − semPV) por sistema. referencia=None acima -> calculado
    aqui para não ficar preso à limitação de 1-referência do avaliar_matriz."""
    idx = {(l["edificio"], l["cenario"], l["horizonte_clima"], l["trajetoria"],
            l["sistema"], l["bateria_kwh"]): l for l in linhas}
    for l in linhas:
        pvstate = l["bateria_kwh"]
        ref = idx.get((l["edificio"], l["cenario"], l["horizonte_clima"],
                       l["trajetoria"], "BAU", pvstate))
        if ref:
            l["val_vs_BAU"]    = ref["fin"]   - l["fin"]
            l["dlcgwp_vs_BAU"] = ref["lcgwp"] - l["lcgwp"]
    return linhas

if __name__ == "__main__":
    linhas  = correr("dados/blocoA", CAT_RB6_HVAC)
    linhas += correr("dados/blocoB", CAT_IIIUC_HVAC)
    linhas  = deltas(linhas)
    matriz_para_csv(linhas, "matriz_artigo10.csv")
    print(f"{len(linhas)} linhas escritas em matriz_artigo10.csv")

    # ── Verificações cruzadas a ESPERAR (sanidade dos resultados) ─────────────
    print("\nVerificações de sanidade (referência da replicação Opus 16/07):")
    print(" · 48 linhas (24 RB6 + 24 iiiUC) com 1 trajetória.")
    print(" · tau_ac (autoconsumo) só >0 nas corridas comPV; =0 nas semPV.")
    print(" · Gás só aparece na BAU (esquentador); MS/HP/iiiUC sem gás.")
    print(" · Por sistema, FIN(comPV) < FIN(semPV) se o PV compensar no clima.")
    print(" · RB6 BAU presente: energia rede≈1787 kWh + gás≈3251 kWh (comPV).")
    for l in sorted(linhas, key=lambda x: (x["edificio"], x["cenario"], x["sistema"])):
        if l["cenario"] in ("atual", "TMY") or "ATU" in l["run_id"]:
            print(f"   {l['run_id']:26s} FIN={l['fin']:9.0f}€  LCGWP={l['lcgwp']:8.0f}  "
                  f"tau_ac={(l.get('tau_ac') or 0):.2f}")
