"""Normalização explícita de preços e IVA no pós-processamento do A10.

Não escolhe taxas nem decide se uma operação beneficia de regime especial.
Não toca nos parâmetros partilhados. Perfis provisórios são recusados por omissão.
"""
from __future__ import annotations

import math
from e4 import finance


class PerfilFiscalIncompleto(ValueError):
    pass


def _numero(x, nome, minimo=0, maximo=None):
    if isinstance(x, bool) or not isinstance(x, (int,float)):
        raise ValueError(f'{nome}: número obrigatório')
    if not math.isfinite(x) or x < minimo or (maximo is not None and x > maximo):
        raise ValueError(f'{nome}: fora do intervalo admissível')
    return x


def preco_liquido(item):
    valor=_numero(item['preco_origem'],'preco_origem')
    base=item['base_origem']
    if base=='liquido':
        return valor
    if base=='com_iva':
        taxa=_numero(item['iva_origem'],'iva_origem',maximo=1)
        return valor/(1+taxa)
    raise PerfilFiscalIncompleto('Base de origem desconhecida: '+str(base))


def custo_componente(componente, item, *, r=.03, horizonte=30):
    """Capital/residual e manutenção têm bases fiscais separadas e explícitas."""
    if not math.isfinite(r) or r<=-1 or horizonte<=0:
        raise ValueError('Desconto/horizonte inválido')
    if not math.isfinite(componente.lc_anos) or componente.lc_anos<=0:
        raise ValueError('Vida útil inválida')
    net=preco_liquido(item)
    taxa=_numero(item['iva_investimento'],'iva_investimento',maximo=1)
    taxa_m=_numero(item['iva_manutencao'],'iva_manutencao',maximo=1)
    ded=_numero(item['fracao_iva_dedutivel'],'fracao_iva_dedutivel',maximo=1)
    ci=net*(1+taxa*(1-ded))
    manut=net*finance.MANUT_GRUPO_PCT[componente.grupo]*(1+taxa_m*(1-ded))
    rep=finance._vp_substituicoes(ci,componente.lc_anos,horizonte,r)
    res=finance._vp_residual(ci,componente.lc_anos,horizonte,r)
    mvp=manut*finance._fator_vp_anual(horizonte,r)
    return dict(cinv=ci,crep=rep,cmnt=mvp,cres=res,total=ci+rep+mvp-res,
                preco_liquido=net,manutencao_anual=manut)


def validar_perfil(perfil, edificio, nomes, *, diagnostico=False):
    if perfil.get('schema')!=1:
        raise PerfilFiscalIncompleto('Versão de perfil não reconhecida')
    if not diagnostico and perfil.get('aprovado_para_resultados_finais') is not True:
        raise PerfilFiscalIncompleto('Perfil provisório: não autorizado para resultados finais')
    itens=perfil.get('edificios',{}).get(edificio,{})
    for nome in nomes:
        if nome not in itens:
            raise PerfilFiscalIncompleto('Falta componente '+edificio+'/'+nome)
        item=itens[nome]
        if not item.get('fonte_preco') or not item.get('qualidade_preco'):
            raise PerfilFiscalIncompleto('Falta proveniência de '+nome)
        preco_liquido(item)
    return itens
