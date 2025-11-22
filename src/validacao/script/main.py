import pandas as pd

# PARÂMETROS
CARTEIRA = ['AALR3', 'ZAMP3']
MES = 8
ANO = 2024

def get_cotacao_ativo_mes(df_cotacoes, cod_ativo, mes, ano):
    """
    Retorna as cotações de um ativo para um mês/ano específico.
    Retorna None se não encontrar dados.
    """
    try:
        resultado = df_cotacoes[
            (df_cotacoes['codneg'] == cod_ativo) & 
            (df_cotacoes['mes'] == mes) & 
            (df_cotacoes['ano'] == ano)
        ]
        
        if resultado.empty:
            print(f"⚠️  Aviso: {cod_ativo} não encontrado para {mes}/{ano}")
            return None
        
        premax = resultado['premax'].values[0]
        premin = resultado['premin'].values[0]
        preabe = resultado['preabe'].values[0]
        preult = resultado['preult'].values[0]
        
        return premax, premin, preabe, preult
    
    except Exception as e:
        print(f"❌ Erro ao buscar {cod_ativo} para {mes}/{ano}: {str(e)}")
        return None

def get_ibovespa_mes(df_ibovespa, mes, ano):
    """
    Retorna as cotações do Ibovespa para um mês/ano específico.
    Retorna None se não encontrar dados.
    """
    try:
        resultado = df_ibovespa[
            (df_ibovespa['mes'] == mes) & 
            (df_ibovespa['ano'] == ano)
        ]
        
        if resultado.empty:
            print(f"⚠️  Aviso: Ibovespa não encontrado para {mes}/{ano}")
            return None
        
        premax = resultado['premax'].values[0]
        premin = resultado['premin'].values[0]
        preabe = resultado['preabe'].values[0]
        preult = resultado['preult'].values[0]
        
        return premax, premin, preabe, preult
    
    except Exception as e:
        print(f"❌ Erro ao buscar Ibovespa para {mes}/{ano}: {str(e)}")
        return None

def calcular_variacao(preco_inicial, preco_final):
    """
    Calcula a variação percentual entre dois preços.
    Retorna None se o preço inicial for zero ou None.
    """
    if preco_inicial is None or preco_final is None:
        return None
    
    if preco_inicial == 0:
        print("❌ Erro: Preço inicial não pode ser zero")
        return None
    
    return (preco_final - preco_inicial) / preco_inicial

def comparar_cotacao_prox_mes(df_cotacoes, cod_ativo, mes, ano):
    """
    Compara a cotação de um ativo entre um mês e o próximo.
    Retorna dicionário com variações percentuais de cada tipo.
    """
    cotacao_atual = get_cotacao_ativo_mes(df_cotacoes, cod_ativo, mes, ano)
    cotacao_prox = get_cotacao_ativo_mes(df_cotacoes, cod_ativo, mes + 1, ano)
    
    if cotacao_atual is None or cotacao_prox is None:
        return None
    
    premax, premin, preabe, preult = cotacao_atual
    premax_prox, premin_prox, preabe_prox, preult_prox = cotacao_prox
    
    return {
        'delta_premax': calcular_variacao(premax, premax_prox),
        'delta_premin': calcular_variacao(premin, premin_prox),
        'delta_preabe': calcular_variacao(preabe, preabe_prox),
        'delta_preult': calcular_variacao(preult, preult_prox),
    }

def comparar_ibovespa_prox_mes(df_ibovespa, mes, ano):
    """
    Compara a cotação do Ibovespa entre um mês e o próximo.
    Retorna dicionário com variações percentuais de cada tipo.
    """
    cotacao_atual = get_ibovespa_mes(df_ibovespa, mes, ano)
    cotacao_prox = get_ibovespa_mes(df_ibovespa, mes + 1, ano)
    
    if cotacao_atual is None or cotacao_prox is None:
        return None
    
    premax, premin, preabe, preult = cotacao_atual
    premax_prox, premin_prox, preabe_prox, preult_prox = cotacao_prox
    
    return {
        'delta_premax': calcular_variacao(premax, premax_prox),
        'delta_premin': calcular_variacao(premin, premin_prox),
        'delta_preabe': calcular_variacao(preabe, preabe_prox),
        'delta_preult': calcular_variacao(preult, preult_prox),
    }

def comparar_carteira_com_ibovespa(df_cotacoes, carteira, df_ibovespa, mes, ano):
    """
    Compara a variação média da carteira com a variação do Ibovespa.
    Calcula a variação percentual de cada ativo separadamente,
    depois faz a média simples dos ativos.
    """
    print(f"\n{'='*60}")
    print(f"Comparando Carteira vs Ibovespa - {mes}/{ano}")
    print(f"{'='*60}\n")
    
    # Obter variações de cada ativo
    variacoes_ativos = {}
    for ativo in carteira:
        variacao = comparar_cotacao_prox_mes(df_cotacoes, ativo, mes, ano)
        if variacao is not None:
            variacoes_ativos[ativo] = variacao
            print(f"📊 {ativo}:")
            print(f"   Abertura: {variacao['delta_preabe']:.2%}")
            print(f"   Máxima: {variacao['delta_premax']:.2%}")
            print(f"   Mínima: {variacao['delta_premin']:.2%}")
            print(f"   Fechamento: {variacao['delta_preult']:.2%}\n")
    
    if not variacoes_ativos:
        print("❌ Nenhum ativo foi encontrado na carteira")
        return None
    
    # Calcular média das variações
    num_ativos = len(variacoes_ativos)
    media_delta_preabe = sum(v['delta_preabe'] for v in variacoes_ativos.values()) / num_ativos
    media_delta_premax = sum(v['delta_premax'] for v in variacoes_ativos.values()) / num_ativos
    media_delta_premin = sum(v['delta_premin'] for v in variacoes_ativos.values()) / num_ativos
    media_delta_preult = sum(v['delta_preult'] for v in variacoes_ativos.values()) / num_ativos
    
    print(f"📈 CARTEIRA (média simples):")
    print(f"   Abertura: {media_delta_preabe:.2%}")
    print(f"   Máxima: {media_delta_premax:.2%}")
    print(f"   Mínima: {media_delta_premin:.2%}")
    print(f"   Fechamento: {media_delta_preult:.2%}\n")
    
    # Obter variações do Ibovespa
    variacao_ibov = comparar_ibovespa_prox_mes(df_ibovespa, mes, ano)
    
    if variacao_ibov is None:
        print("❌ Dados do Ibovespa não encontrados")
        return None
    
    print(f"📉 IBOVESPA:")
    print(f"   Abertura: {variacao_ibov['delta_preabe']:.2%}")
    print(f"   Máxima: {variacao_ibov['delta_premax']:.2%}")
    print(f"   Mínima: {variacao_ibov['delta_premin']:.2%}")
    print(f"   Fechamento: {variacao_ibov['delta_preult']:.2%}\n")
    
    # Calcular diferenças
    diff_preabe = media_delta_preabe - variacao_ibov['delta_preabe']
    diff_premax = media_delta_premax - variacao_ibov['delta_premax']
    diff_premin = media_delta_premin - variacao_ibov['delta_premin']
    diff_preult = media_delta_preult - variacao_ibov['delta_preult']
    
    print(f"🔄 DIFERENÇA (Carteira - Ibovespa):")
    print(f"   Abertura: {diff_preabe:+.2%}")
    print(f"   Máxima: {diff_premax:+.2%}")
    print(f"   Mínima: {diff_premin:+.2%}")
    print(f"   Fechamento: {diff_preult:+.2%}\n")
    
    # Retornar resultado estruturado
    return {
        'carteira_media': {
            'delta_preabe': media_delta_preabe,
            'delta_premax': media_delta_premax,
            'delta_premin': media_delta_premin,
            'delta_preult': media_delta_preult,
        },
        'ibovespa': variacao_ibov,
        'diferenca': {
            'delta_preabe': diff_preabe,
            'delta_premax': diff_premax,
            'delta_premin': diff_premin,
            'delta_preult': diff_preult,
        },
        'ativos': variacoes_ativos
    }

def main():
    try:
        #### COTAÇÕES 2024 ####
        print("📥 Carregando cotações...")
        df = pd.read_csv('../input/cotacoes_limpas_2024.csv', sep=';')

        df['data_pregao'] = pd.to_datetime(df['data_pregao'], dayfirst=True)
        df['mes'] = df['data_pregao'].dt.month
        df['ano'] = df['data_pregao'].dt.year

        # Drop colunas desnecessárias
        df = df.drop(columns=['data_pregao', 'totneg', 'quatot', 'premed'])

        # Agrupa por ativo e mês/ano
        df = df.groupby(['codneg', 'mes', 'ano']).agg({
            'preabe': 'first',
            'premax': 'max',
            'premin': 'min',
            'preult': 'last',
        }).reset_index()

        print(f'✅ Cotações carregadas: {len(df)} registros\n')

        #### IBOVESPA 2024 ####
        print("📥 Carregando Ibovespa...")
        df_ibov = pd.read_csv('../input/Dados Históricos - Ibovespa.csv', sep=',')

        # Formatação dados
        df_ibov['Data'] = pd.to_datetime(df_ibov['Data'], dayfirst=True)
        df_ibov['mes'] = df_ibov['Data'].dt.month
        df_ibov['ano'] = df_ibov['Data'].dt.year
        df_ibov['Último'] = pd.to_numeric(df_ibov['Último'], errors='coerce')
        df_ibov['Abertura'] = pd.to_numeric(df_ibov['Abertura'], errors='coerce')
        df_ibov['Máxima'] = pd.to_numeric(df_ibov['Máxima'], errors='coerce')
        df_ibov['Mínima'] = pd.to_numeric(df_ibov['Mínima'], errors='coerce')

        # Renomeia colunas
        df_ibov = df_ibov.rename(columns={
            'Abertura': 'preabe',
            'Máxima': 'premax',
            'Mínima': 'premin',
            'Último': 'preult'
        })

        df_ibov = df_ibov.groupby(['mes', 'ano']).agg({
            'preabe': 'first',
            'premax': 'max',
            'premin': 'min',
            'preult': 'last'
        }).reset_index()

        print(f'✅ Ibovespa carregado: {len(df_ibov)} registros\n')

        # Comparar carteira com Ibovespa
        resultado = comparar_carteira_com_ibovespa(df, CARTEIRA, df_ibov, MES, ANO)

    except FileNotFoundError as e:
        print(f"❌ Erro: Arquivo não encontrado - {str(e)}")
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")

if __name__ == '__main__':
    main()