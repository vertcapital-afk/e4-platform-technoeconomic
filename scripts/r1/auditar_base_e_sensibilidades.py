"""A10: exporta parâmetros e valida UMA célula; nunca corre um sweep.

As opções de sensibilidade são explícitas. Não altera constantes do motor.
Os ficheiros de saída são novos; a matriz histórica nunca é sobrescrita.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from dataclasses import replace
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from e4 import dinamica_capex as cap, finance, pconv
from e4.carbono import n_instalacoes
from e4.dinamica import carregar
from e4.dinamica_avaliador import (
    custo_energia_vp_dinamico, lcgwp_operacional_horizonte_dinamico,
)
from e4.dinamica_matriz import Componente, avaliar_set_composto

ROOT = Path(__file__).resolve().parents[3]
CATALOGOS = {
    'RB6': {
        'BAU': ('RB6_BAU_AQS', 'RB6_BAU_AQUECIMENTO', 'RB6_BAU_ARREFECIMENTO'),
        'MultiSplit': ('RB6_BC_AQS_HPWH', 'RB6_MULTISPLIT'),
        'BombaCalor': ('RB6_BC_AR_AGUA',),
    },
    'iiiUC': {
        'BAU': ('IIIUC_BAU_RADIADORES', 'IIIUC_BAU_PORTATEIS'),
        'Pack1_Mitsubishi': ('IIIUC_PACK1_MITSUBISHI',),
        'Pack2_Daikin': ('IIIUC_PACK2_DAIKIN',),
    },
}
PV = ('RB6_PV', 'RB6_BATERIA_5KWH')


def calendario(vida: float, horizonte: int = 30) -> dict:
    if not math.isfinite(vida) or vida <= 0 or horizonte <= 0:
        raise ValueError('Vida e horizonte devem ser positivos e finitos')
    anos = [k * vida for k in range(math.ceil(horizonte / vida))]
    restante = anos[-1] + vida - horizonte
    return dict(anos_instalacao=anos, anos_substituicao=anos[1:],
                vida_remanescente=restante, fracao_residual=restante / vida,
                instalacoes_completas=len(anos),
                instalacoes_proporcionais=sum(min(vida, horizonte-a) / vida for a in anos))


def componentes(corrida, vida_bateria=None):
    edificio = corrida.meta['edificio'].strip()
    sistema = corrida.meta['sistema'].strip()
    nomes = list(CATALOGOS[edificio][sistema])
    if corrida.meta['pv'].strip() != 'sem':
        nomes += list(PV)
    saida = []
    for nome in nomes:
        s = getattr(cap, nome)
        if nome == 'RB6_BATERIA_5KWH' and vida_bateria is not None:
            calendario(vida_bateria)
            s = replace(s, lc_anos=vida_bateria)
        saida.append(Componente(s))
    return saida


def trajetoria(tipo='central', velocidade=1.0):
    """Varia o ritmo, mantendo o mesmo EF inicial de 2030; não é previsão oficial."""
    if not math.isfinite(velocidade) or velocidade <= 0:
        raise ValueError('Velocidade deve ser positiva e finita')
    central = pconv.construir_trajetoria()
    if tipo == 'constante_historico':
        return None
    if tipo == 'constante_inicial':
        inicial = central(0)
        return lambda t: dict(inicial)
    if tipo == 'central_gasmix':
        # Sensibilidade declarada na Tabela 3 do manuscrito submetido (08/11/2026,
        # [DECISÃO-ST-A10-sens-declaradas]): gás de rede em mistura decrescente.
        gasmix = pconv.construir_trajetoria(pconv.ANCORAS_DGEG2025_GASMIX)
        return lambda t: gasmix(t * velocidade)
    if tipo != 'central':
        raise ValueError(tipo)
    return lambda t: central(t * velocidade)


def avaliar(corrida, *, r=finance.TAXA_DESCONTO, escala_elec=1.0,
            escala_gas=1.0, vida_bateria=None, velocidade=1.0,
            tipo_rede='central', proporcional=False, perspetiva='REG',
            perfil_fiscal=None, diagnostico_fiscal=False,
            horizonte=finance.PERIODO_ANOS, escalada=None):
    if isinstance(horizonte, bool) or not isinstance(horizonte, int) or horizonte <= 0:
        raise ValueError('Horizonte deve ser um inteiro positivo de anos')
    if not math.isfinite(r) or r <= -1:
        raise ValueError('Desconto deve ser finito e superior a -1')
    if any(not math.isfinite(x) or x <= 0 for x in (escala_elec, escala_gas)):
        raise ValueError('Multiplicadores de preços devem ser positivos e finitos')
    comps = componentes(corrida, vida_bateria)
    if perfil_fiscal is None:
        partes = [cap.custo_capex_vp(x.set_hvac, perspetiva=perspetiva, period=horizonte, r=r) for x in comps]
    else:
        from fiscalidade_a10 import custo_componente, validar_perfil
        edificio=corrida.meta['edificio'].strip()
        nomes=list(CATALOGOS[edificio][corrida.meta['sistema'].strip()])
        if corrida.meta['pv'].strip()!='sem': nomes+=list(PV)
        itens=validar_perfil(perfil_fiscal,edificio,nomes,diagnostico=diagnostico_fiscal)
        partes=[custo_componente(c.set_hvac,itens[n],r=r,horizonte=horizonte) for n,c in zip(nomes,comps)]
    precos = dict(finance.PRECO_ENERGIA)
    precos['electricidade'] *= escala_elec
    precos['gas'] *= escala_gas
    # escalada=None mantém ESCALADA_ENERGIA_VETOR (base do A10); um dicionário substitui-a
    # ([DECISÃO-ST-A10-escalada], 08/11/2026: variante uniforme da convenção do A11/A12).
    if escalada is not None and any(not math.isfinite(g) or g <= -1 for g in escalada.values()):
        raise ValueError('Escalada deve ser finita e superior a -1')
    energia = custo_energia_vp_dinamico(corrida, precos=precos, r=r, period=horizonte, escalada=escalada)
    embc = sum(x.set_hvac.embc() * (
        calendario(x.set_hvac.lc_anos, horizonte)['instalacoes_proporcionais'] if proporcional
        else n_instalacoes(x.set_hvac.lc_anos, horizonte)) for x in comps)
    oper = lcgwp_operacional_horizonte_dinamico(
        corrida, ef=pconv.EF_DECISAO, horizonte=horizonte,
        ef_trajetoria=trajetoria(tipo_rede, velocidade))
    termos = {k: sum(v[k] for v in partes) for k in ('cinv','crep','cmnt','cres','total')}
    return dict(fin=termos['total']+energia, lcgwp=embc+oper, embc=embc,
                lcgwp_operacional=oper, custo_energia_vp=energia,
                capital=termos,
                configuracao=dict(r=r, escala_elec=escala_elec, escala_gas=escala_gas,
                    exportacao_eur_kwh=finance.PRECO_OMIE, vida_bateria=vida_bateria,
                    velocidade=velocidade, tipo_rede=tipo_rede, horizonte=horizonte, escalada=escalada,
                    proporcional=proporcional,
                    perspetiva=perspetiva if perfil_fiscal is None else 'FIN_EXPLICITA',
                    perfil_fiscal=None if perfil_fiscal is None else perfil_fiscal['id'],
                    diagnostico_fiscal=diagnostico_fiscal))


def autocontrolos():
    # Casos de fronteira com expectativas independentes do motor.
    for vida, anos, fracao in [(10,[0,10,20],0), (15,[0,15],0),
                               (20,[0,20],.5), (25,[0,25],.8), (30,[0],0)]:
        x = calendario(vida)
        assert x['anos_instalacao'] == anos and x['fracao_residual'] == fracao
    # Residual: 1000 euros, vida 20, horizonte 30 -> 500 euros no ano 30.
    assert math.isclose(finance._vp_residual(1000,20,30,.03),500/1.03**30)
    assert math.isclose(finance._vp_substituicoes(1000,20,30,.03),1000/1.03**20)
    assert calendario(20)['instalacoes_proporcionais'] == 1.5
    assert calendario(25)['instalacoes_proporcionais'] == 1.2
    for vida in (0,-1,float('nan')):
        try:
            calendario(vida)
        except ValueError:
            pass
        else:
            raise AssertionError('Controlo negativo não detetou vida inválida')
    # Todos os ritmos partem do mesmo fator; 2x chega à âncora final em metade do tempo.
    assert trajetoria(velocidade=2)(0) == trajetoria(velocidade=.5)(0)
    assert trajetoria(velocidade=2)(10) == trajetoria()(20)


def escrever_csv(path, linhas):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(linhas[0]))
        w.writeheader();w.writerows(linhas)


def exportar(out):
    linhas=[]
    valores = {
        'horizonte_anos':finance.PERIODO_ANOS, 'desconto_real':finance.TAXA_DESCONTO,
        'exportacao_eur_kwh':finance.PRECO_OMIE, 'ano_base_rede':pconv.ANO_BASE,
        'multiplicador_IVA_REG':finance._iva('REG',False),
        'multiplicador_IVA_INV_geral':finance._iva('INV',False),
        'multiplicador_IVA_INV_renovavel':finance._iva('INV',True),
    }
    for v,x in finance.PRECO_ENERGIA.items(): valores['preco_'+v+'_eur_kwh']=x
    for v,x in finance.ESCALADA_ENERGIA_VETOR.items(): valores['escalada_real_'+v]=x
    for v,x in valores.items():linhas.append(dict(parametro=v,valor=x,proveniencia='runtime do motor; fonte externa ainda por fechar'))
    escrever_csv(out/'parametros_base.csv',linhas)
    nomes=sorted({n for c in CATALOGOS.values() for pack in c.values() for n in pack}|set(PV))
    linhas=[]
    for nome in nomes:
        s=getattr(cap,nome);cal=calendario(s.lc_anos);vp=cap.custo_capex_vp(s,perspetiva='REG')
        linhas.append(dict(componente=nome,nome=s.nome,capex_sem_iva=s.capex(),
            embc_unitario=s.embc(),vida_anos=s.lc_anos,grupo=s.grupo,
            manutencao_fracao_ano=finance.MANUT_GRUPO_PCT[s.grupo],
            manutencao_eur_ano=s.capex()*finance.MANUT_GRUPO_PCT[s.grupo],
            renovavel=s.renovavel,instalacoes=';'.join(map(str,cal['anos_instalacao'])),
            fracao_residual=cal['fracao_residual'],residual_vp=vp['cres'],
            substituicoes_vp=vp['crep'],embc_integral=cap.embc_capex(s),
            embc_proporcional=s.embc()*cal['instalacoes_proporcionais']))
    escrever_csv(out/'componentes_e_substituicoes.csv',linhas)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--run-id',default='RB6-ATU-BAU-comPV')
    parser.add_argument('--desconto',type=float,default=finance.TAXA_DESCONTO)
    parser.add_argument('--escala-eletricidade',type=float,default=1)
    parser.add_argument('--escala-gas',type=float,default=1)
    parser.add_argument('--vida-bateria',type=float)
    parser.add_argument('--velocidade-rede',type=float,default=1)
    parser.add_argument('--rede',choices=['central','central_gasmix','constante_historico','constante_inicial'],default='central')
    parser.add_argument('--carbono-proporcional',action='store_true')
    parser.add_argument('--perfil-fiscal',type=Path)
    parser.add_argument('--diagnostico-fiscal',action='store_true',
                        help='Permite avaliar perfil provisório; não produz resultados finais')
    args=parser.parse_args()
    autocontrolos()
    bloco='blocoA' if args.run_id.startswith('RB6-') else 'blocoB'
    corrida=carregar(ROOT/'data'/'motor'/bloco)[args.run_id]
    base=avaliar(corrida)
    motor=avaliar_set_composto(corrida,componentes(corrida),ef_trajetoria=pconv.construir_trajetoria())
    for k in ('fin','lcgwp','embc','lcgwp_operacional','custo_energia_vp'):
        assert math.isclose(base[k],motor[k],rel_tol=1e-12,abs_tol=1e-8),(k,base[k],motor[k])
    arquivo=ROOT/'studies/a10_tecnoeconomia/resultados/matriz_artigo10.csv'
    with arquivo.open(encoding='utf-8') as f:
        armazenado=next(x for x in csv.DictReader(f) if x['run_id']==args.run_id and x['trajetoria']=='DGEG2025')
    for k in ('fin','lcgwp','embc','custo_energia_vp'):
        assert math.isclose(base[k],float(armazenado[k]),rel_tol=1e-12,abs_tol=1e-8),(k,'divergência arquivo')
    perfil=None if args.perfil_fiscal is None else json.loads(args.perfil_fiscal.read_text(encoding='utf-8'))
    variante=avaliar(corrida,r=args.desconto,escala_elec=args.escala_eletricidade,
        escala_gas=args.escala_gas,vida_bateria=args.vida_bateria,
        velocidade=args.velocidade_rede,tipo_rede=args.rede,proporcional=args.carbono_proporcional,
        perfil_fiscal=perfil,diagnostico_fiscal=args.diagnostico_fiscal)
    # Testes causais sobre a MESMA célula; sem percorrer outros cenários.
    assert avaliar(corrida,r=.05)['lcgwp']==base['lcgwp']
    assert avaliar(corrida,velocidade=2)['fin']==base['fin']
    assert avaliar(corrida,escala_elec=1.1)['fin']!=base['fin']
    assert avaliar(corrida,vida_bateria=15)['embc']!=base['embc']
    inv=avaliar(corrida,perspetiva='INV')
    assert inv['fin']!=base['fin']
    # Destino novo obrigatório: protege a prova original e os relatórios anteriores.
    args.out.mkdir(parents=True,exist_ok=False)
    exportar(args.out)
    report=dict(run_id=args.run_id,baseline=base,variante=variante,
        mesma_celula_INV=inv,baseline_igual_motor_e_arquivo=True,
        autocontrolos='PASS; fronteiras, controlos negativos e invariâncias causais',
        input_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
          for p in [arquivo,ROOT/'data'/'motor'/bloco/'runs.csv',ROOT/'data'/'motor'/bloco/'resultados_mensais.csv']})
    (args.out/'celula_validacao.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS: linha de base igual ao motor e CSV; autocontrolos passaram; uma célula avaliada.')
    print('FIN REG:',base['fin'],'FIN INV:',inv['fin'],'diferença:',inv['fin']-base['fin'])
    print('Saída:',args.out)


if __name__=='__main__':
    main()
