"""Recalcula o cenário financeiro A10 por sobreposição, preservando o histórico.

Por omissão valida apenas RB6-ATU-BAU-comPV. --matriz é para execução pelo
decisor, depois de receber o comando. Não importa correr_matriz_artigo10.py.
"""
import argparse
import csv
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')

from auditar_base_e_sensibilidades import ROOT,avaliar
from e4.dinamica import carregar

DEFAULT_PROFILE=Path(__file__).with_name('perfil_financeiro_PV_adotado_2026-11-03.json')
HIST=ROOT/'studies/a10_tecnoeconomia/resultados/matriz_artigo10.csv'


def validar_base(armazenado,calculado):
    for k in ('fin','lcgwp','embc','custo_energia_vp'):
        if not math.isclose(float(armazenado[k]),calculado[k],rel_tol=1e-12,abs_tol=1e-8):
            raise ValueError(f'Linha de base divergente em {armazenado["run_id"]}/{k}: parar, não regenerar o histórico')


def comparar_grupos(linhas):
    grupos=defaultdict(list)
    for l in linhas:
        key=tuple(l[k] for k in ('edificio','cenario','horizonte_clima','pv','trajetoria'))
        grupos[key].append(l)
    for key,grupo in grupos.items():
        referencias=[x for x in grupo if x['sistema']=='BAU']
        if len(referencias)!=1:raise ValueError(f'Referência BAU não única em {key}')
        ref=referencias[0]
        for l in grupo:
            for campo in ('fin_historico','fin_financeiro','lcgwp'):
                l['rank_'+campo]=1+sum(x[campo]<l[campo]-1e-8 for x in grupo)
            l['delta_fin_vs_BAU_historico']=ref['fin_historico']-l['fin_historico']
            l['delta_fin_vs_BAU_financeiro']=ref['fin_financeiro']-l['fin_financeiro']
            l['mudou_rank_financeiro']=l['rank_fin_historico']!=l['rank_fin_financeiro']
    return linhas


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--perfil',type=Path,default=DEFAULT_PROFILE)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--matriz',action='store_true')
    args=p.parse_args()
    perfil=json.loads(args.perfil.read_text(encoding='utf-8'))
    if perfil.get('autorizado_para_recalculo') is not True:
        raise ValueError('Perfil não autorizado para recálculo')
    if perfil.get('decisao_preco_PV')!='reconstituir_4050_dividido_1.06':
        raise ValueError('A decisão do PV não está identificada')
    with HIST.open(encoding='utf-8') as f:historico=list(csv.DictReader(f))
    pares={(l['run_id'],l['trajetoria']):l for l in historico}
    if len(pares)!=len(historico):raise ValueError('Duplicados no histórico')
    # Por omissão carrega só um bloco e avalia uma única célula.
    blocos=['blocoA','blocoB'] if args.matriz else ['blocoA']
    corridas={}
    for bloco in blocos:
        for rid,c in carregar(ROOT/'data/motor'/bloco).items():
            if args.matriz or rid=='RB6-ATU-BAU-comPV':
                if rid in corridas:raise ValueError('run_id duplicado '+rid)
                corridas[rid]=c
    if args.matriz and set(corridas)!={x['run_id'] for x in historico}:
        raise ValueError('Cobertura das corridas difere do histórico')
    linhas=[]
    for rid,c in sorted(corridas.items()):
        for rotulo,tipo in [('DGEG2025','central'),('EF_constante','constante_historico')]:
            base=avaliar(c,tipo_rede=tipo)
            validar_base(pares[(rid,rotulo)],base)
            # A autorização abrange o cálculo deste cenário explicitamente descrito.
            # Não certifica o tratamento fiscal real da UC nem valida preços de mercado.
            novo=avaliar(c,tipo_rede=tipo,perfil_fiscal=perfil,diagnostico_fiscal=True)
            if novo['lcgwp']!=base['lcgwp'] or novo['custo_energia_vp']!=base['custo_energia_vp']:
                raise ValueError('Uma alteração fiscal não deve alterar carbono ou tarifa da energia')
            linhas.append(dict(run_id=rid,edificio=c.meta['edificio'].strip(),
                cenario=c.meta['cenario'].strip(),horizonte_clima=c.meta['horizonte'].strip(),
                sistema=c.meta['sistema'].strip(),pv=c.meta['pv'].strip(),trajetoria=rotulo,
                perfil_fiscal=perfil['id'],fin_historico=base['fin'],fin_financeiro=novo['fin'],
                diferenca_fin=novo['fin']-base['fin'],lcgwp=novo['lcgwp'],
                cinv=novo['capital']['cinv'],crep=novo['capital']['crep'],
                cmnt=novo['capital']['cmnt'],cres=novo['capital']['cres'],
                energia_vp=novo['custo_energia_vp']))
    if args.matriz:comparar_grupos(linhas)
    args.out.mkdir(parents=True,exist_ok=False)
    arquivo=args.out/('matriz_financeira.csv' if args.matriz else 'celula_financeira.csv')
    with arquivo.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=linhas[0]);w.writeheader();w.writerows(linhas)
    inputs=[HIST,args.perfil]
    for b in blocos:
        inputs.extend(ROOT/'data/motor'/b/f for f in ('runs.csv','resultados_mensais.csv'))
    resumo=dict(tipo='matriz' if args.matriz else 'uma_celula',perfil=perfil,
        linhas=len(linhas),corridas=len(corridas),
        historico_reproduzido=True,carbono_e_energia_preservados=True,
        resultados_prontos_para_manuscrito=False,
        motivo='Cenário financeiro explícito; conferir classificações e pressupostos antes de editar o manuscrito',
        inputs_sha256={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in inputs})
    if args.matriz:
        resumo['linhas_com_mudanca_rank']=sum(x['mudou_rank_financeiro'] for x in linhas)
        grupos={tuple(x[k] for k in ('edificio','cenario','horizonte_clima','pv','trajetoria')) for x in linhas}
        resumo['grupos_comparados']=len(grupos)
    (args.out/'resumo_recalculo.json').write_text(json.dumps(resumo,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'PASS: {len(corridas)} corrida(s), {len(linhas)} linhas; histórico reproduzido; carbono e energia preservados.')
    if args.matriz:print('Linhas com mudança de posição:',resumo['linhas_com_mudanca_rank'])
    else:print('DGEG2025 FIN:',next(x['fin_financeiro'] for x in linhas if x['trajetoria']=='DGEG2025'))
    print('Resultados em:',args.out)


if __name__=='__main__':main()
