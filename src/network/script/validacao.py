import pandas as pd
import os
import glob
from typing import Dict, List, Tuple
import re

# Variáveis globais para cache dos dados
_df_cotacoes = None
_df_ibov = None

def carregar_dados_validacao():
    """
    Carrega os dados necessários para validação uma única vez.
    
    Returns:
        Tupla (df_cotacoes, df_ibov)
    """
    global _df_cotacoes, _df_ibov
    
    if _df_cotacoes is not None and _df_ibov is not None:
        return _df_cotacoes, _df_ibov
    
    try:
        print("📥 Carregando dados para validação...")
        
        # Carrega cotações
        _df_cotacoes = pd.read_csv('../input/cotacoes_limpas_2024.csv', sep=';')
        _df_cotacoes['data_pregao'] = pd.to_datetime(_df_cotacoes['data_pregao'], dayfirst=True)
        _df_cotacoes['mes'] = _df_cotacoes['data_pregao'].dt.month
        _df_cotacoes['ano'] = _df_cotacoes['data_pregao'].dt.year
        _df_cotacoes = _df_cotacoes.drop(columns=['data_pregao', 'totneg', 'quatot', 'premed'])
        _df_cotacoes = _df_cotacoes.groupby(['codneg', 'mes', 'ano']).agg({
            'preabe': 'first',
            'premax': 'max',
            'premin': 'min',
            'preult': 'last',
        }).reset_index()
        
        # Carrega Ibovespa
        _df_ibov = pd.read_csv('../input/Dados Históricos - Ibovespa.csv', sep=',')
        _df_ibov['Data'] = pd.to_datetime(_df_ibov['Data'], dayfirst=True)
        _df_ibov['mes'] = _df_ibov['Data'].dt.month
        _df_ibov['ano'] = _df_ibov['Data'].dt.year
        _df_ibov['Último'] = pd.to_numeric(_df_ibov['Último'], errors='coerce')
        _df_ibov['Abertura'] = pd.to_numeric(_df_ibov['Abertura'], errors='coerce')
        _df_ibov['Máxima'] = pd.to_numeric(_df_ibov['Máxima'], errors='coerce')
        _df_ibov['Mínima'] = pd.to_numeric(_df_ibov['Mínima'], errors='coerce')
        _df_ibov = _df_ibov.rename(columns={
            'Abertura': 'preabe',
            'Máxima': 'premax',
            'Mínima': 'premin',
            'Último': 'preult'
        })
        _df_ibov = _df_ibov.groupby(['mes', 'ano']).agg({
            'preabe': 'first',
            'premax': 'max',
            'premin': 'min',
            'preult': 'last'
        }).reset_index()
        
        print("✅ Dados carregados com sucesso\n")
        return _df_cotacoes, _df_ibov
        
    except FileNotFoundError as e:
        print(f"⚠️  Aviso: Dados de validação não encontrados - {str(e)}")
        print("   Prosseguindo sem validação...\n")
        return None, None

def extrair_periodo_arquivo(nome_arquivo: str) -> Tuple[int, int]:
    """
    Extrai mês e ano do nome do arquivo.
    Formato esperado: {cnpj}_{abordagem}_{YYYYMM}.csv
    
    Args:
        nome_arquivo: Nome do arquivo
        
    Returns:
        Tupla (mês, ano)
    """
    match = re.search(r'(\d{6})\.csv$', nome_arquivo)
    if match:
        periodo = match.group(1)
        ano = int(periodo[:4])
        mes = int(periodo[4:])
        return mes, ano
    return None, None

def get_cotacao_ativo_mes(df_cotacoes, cod_ativo, mes, ano):
    """
    Retorna as cotações de um ativo para um mês/ano específico.
    Retorna None se não encontrar dados.
    """
    if df_cotacoes is None:
        return None
    
    try:
        resultado = df_cotacoes[
            (df_cotacoes['codneg'] == cod_ativo) & 
            (df_cotacoes['mes'] == mes) & 
            (df_cotacoes['ano'] == ano)
        ]
        
        if resultado.empty:
            return None
        
        premax = resultado['premax'].values[0]
        premin = resultado['premin'].values[0]
        preabe = resultado['preabe'].values[0]
        preult = resultado['preult'].values[0]
        
        return premax, premin, preabe, preult
    
    except Exception as e:
        return None

def get_ibovespa_mes(df_ibovespa, mes, ano):
    """
    Retorna as cotações do Ibovespa para um mês/ano específico.
    Retorna None se não encontrar dados.
    """
    if df_ibovespa is None:
        return None
    
    try:
        resultado = df_ibovespa[
            (df_ibovespa['mes'] == mes) & 
            (df_ibovespa['ano'] == ano)
        ]
        
        if resultado.empty:
            return None
        
        premax = resultado['premax'].values[0]
        premin = resultado['premin'].values[0]
        preabe = resultado['preabe'].values[0]
        preult = resultado['preult'].values[0]
        
        return premax, premin, preabe, preult
    
    except Exception as e:
        return None

def calcular_variacao(preco_inicial, preco_final):
    """
    Calcula a variação percentual entre dois preços.
    Retorna None se o preço inicial for zero ou None.
    """
    if preco_inicial is None or preco_final is None:
        return None
    
    if preco_inicial == 0:
        return None
    
    return (preco_final - preco_inicial) / preco_inicial

def comparar_cotacao_prox_mes(df_cotacoes, cod_ativo, mes, ano):
    """
    Compara a cotação de um ativo entre um mês e o próximo.
    Retorna dicionário com variações percentuais de cada tipo.
    """
    if df_cotacoes is None:
        return None
    
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
    if df_ibovespa is None:
        return None
    
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

def adicionar_validacao_recomendacoes(df_recomendacoes, mes, ano):
    """
    Adiciona colunas de validação ao DataFrame de recomendações.
    
    Args:
        df_recomendacoes: DataFrame com as recomendações (colunas: ativo, pontuacao)
        mes: Mês para validação
        ano: Ano para validação
        
    Returns:
        DataFrame com colunas de validação adicionadas
    """
    # Carrega dados se necessário
    df_cotacoes, df_ibov = carregar_dados_validacao()
    
    if df_cotacoes is None or df_ibov is None:
        # Se não conseguir carregar dados, retorna apenas as colunas originais
        return df_recomendacoes
    
    # Obtém variação do Ibovespa
    variacao_ibov = comparar_ibovespa_prox_mes(df_ibov, mes, ano)
    
    if variacao_ibov is None:
        # Se não conseguir validar, retorna apenas as colunas originais
        return df_recomendacoes
    
    # Adiciona colunas de validação
    variacoes_abertura = []
    variacoes_maxima = []
    variacoes_minima = []
    variacoes_fechamento = []
    
    diferenca_abertura = []
    diferenca_maxima = []
    diferenca_minima = []
    diferenca_fechamento = []
    
    for ativo in df_recomendacoes['ativo']:
        variacao = comparar_cotacao_prox_mes(df_cotacoes, ativo, mes, ano)
        
        if variacao is not None:
            variacoes_abertura.append(variacao['delta_preabe'])
            variacoes_maxima.append(variacao['delta_premax'])
            variacoes_minima.append(variacao['delta_premin'])
            variacoes_fechamento.append(variacao['delta_preult'])
            
            diferenca_abertura.append(variacao['delta_preabe'] - variacao_ibov['delta_preabe'])
            diferenca_maxima.append(variacao['delta_premax'] - variacao_ibov['delta_premax'])
            diferenca_minima.append(variacao['delta_premin'] - variacao_ibov['delta_premin'])
            diferenca_fechamento.append(variacao['delta_preult'] - variacao_ibov['delta_preult'])
        else:
            # Se não encontrar dados, adiciona None
            variacoes_abertura.append(None)
            variacoes_maxima.append(None)
            variacoes_minima.append(None)
            variacoes_fechamento.append(None)
            
            diferenca_abertura.append(None)
            diferenca_maxima.append(None)
            diferenca_minima.append(None)
            diferenca_fechamento.append(None)
    
    # Adiciona colunas ao DataFrame
    df_recomendacoes['variacao_abertura'] = variacoes_abertura
    df_recomendacoes['variacao_maxima'] = variacoes_maxima
    df_recomendacoes['variacao_minima'] = variacoes_minima
    df_recomendacoes['variacao_fechamento'] = variacoes_fechamento
    
    df_recomendacoes['diferenca_abertura'] = diferenca_abertura
    df_recomendacoes['diferenca_maxima'] = diferenca_maxima
    df_recomendacoes['diferenca_minima'] = diferenca_minima
    df_recomendacoes['diferenca_fechamento'] = diferenca_fechamento
    
    return df_recomendacoes

def validar_recomendacoes_arquivo(arquivo_recomendacoes, mes, ano):
    """
    Valida as recomendações de um arquivo calculando a diferença com Ibovespa.
    
    Args:
        arquivo_recomendacoes: Caminho do arquivo de recomendações
        mes: Mês para análise
        ano: Ano para análise
        
    Returns:
        DataFrame com os ativos recomendados e a diferença de performance
    """
    # Carrega dados se necessário
    df_cotacoes, df_ibov = carregar_dados_validacao()
    
    if df_cotacoes is None or df_ibov is None:
        return None
    
    try:
        # Carrega as recomendações
        df_recomendacoes = pd.read_csv(arquivo_recomendacoes, sep=';')
        
        if df_recomendacoes.empty:
            return None
        
        # Obtém lista de ativos recomendados
        ativos_recomendados = df_recomendacoes['ativo'].tolist()
        
        # Valida cada ativo recomendado
        resultados = []
        variacoes_validas = []
        
        for ativo in ativos_recomendados:
            variacao = comparar_cotacao_prox_mes(df_cotacoes, ativo, mes, ano)
            
            if variacao is not None:
                variacao_preult = variacao['delta_preult']
                variacoes_validas.append(variacao_preult)
                
                resultados.append({
                    'ativo': ativo,
                    'variacao_abertura': variacao['delta_preabe'],
                    'variacao_maxima': variacao['delta_premax'],
                    'variacao_minima': variacao['delta_premin'],
                    'variacao_fechamento': variacao['delta_preult']
                })
        
        if not resultados:
            return None
        
        # Obtém variação do Ibovespa
        variacao_ibov = comparar_ibovespa_prox_mes(df_ibov, mes, ano)
        
        if variacao_ibov is None:
            return None
        
        # Calcula diferença para cada ativo
        df_resultados = pd.DataFrame(resultados)
        df_resultados['diferenca_abertura'] = df_resultados['variacao_abertura'] - variacao_ibov['delta_preabe']
        df_resultados['diferenca_maxima'] = df_resultados['variacao_maxima'] - variacao_ibov['delta_premax']
        df_resultados['diferenca_minima'] = df_resultados['variacao_minima'] - variacao_ibov['delta_premin']
        df_resultados['diferenca_fechamento'] = df_resultados['variacao_fechamento'] - variacao_ibov['delta_preult']
        
        return df_resultados
        
    except Exception as e:
        print(f"❌ Erro ao processar arquivo {arquivo_recomendacoes}: {str(e)}")
        return None

def obter_arquivos_periodos(diretorio_base: str = '../output') -> Dict[str, List[str]]:
    """
    Obtém todos os arquivos agrupados por período.
    
    Args:
        diretorio_base: Diretório base contendo as pastas periodo_*
        
    Returns:
        Dicionário com período como chave e lista de arquivos como valor
    """
    periodos = {}
    
    # Procura por todas as pastas periodo_*
    pasta_periodos = glob.glob(os.path.join(diretorio_base, 'periodo_*'))
    
    for pasta in pasta_periodos:
        periodo = os.path.basename(pasta)
        arquivos = glob.glob(os.path.join(pasta, '*.csv'))
        
        if arquivos:
            periodos[periodo] = sorted(arquivos)
    
    return periodos

def salvar_resultados_validacao(df_resultados, arquivo_original, diretorio_saida='../output'):
    """
    Salva os resultados da validação no mesmo arquivo com novas colunas.
    
    Args:
        df_resultados: DataFrame com resultados
        arquivo_original: Caminho do arquivo original
        diretorio_saida: Diretório de saída
    """
    # Cria diretório se não existir
    os.makedirs(diretorio_saida, exist_ok=True)
    
    # Usa o mesmo nome do arquivo original
    nome_arquivo = os.path.basename(arquivo_original)
    caminho_saida = os.path.join(diretorio_saida, nome_arquivo)
    
    # Salva com as novas colunas
    df_resultados.to_csv(
        caminho_saida, 
        sep=';', 
        encoding='utf-8-sig', 
        index=False
    )
    
    print(f"✅ Resultados salvos em: {caminho_saida}")

def main():
    try:
        # Carrega dados
        df_cotacoes, df_ibov = carregar_dados_validacao()
        
        if df_cotacoes is None or df_ibov is None:
            print("❌ Não foi possível carregar dados de validação")
            return

        print(f'✅ Cotações carregadas: {len(df_cotacoes)} registros')
        print(f'✅ Ibovespa carregado: {len(df_ibov)} registros\n')

        # Obtém arquivos por período
        print("📂 Procurando arquivos de recomendações...")
        periodos = obter_arquivos_periodos()
        
        if not periodos:
            print("❌ Nenhum arquivo encontrado em ../output/periodo_*")
            return
        
        print(f"✅ Encontrados {len(periodos)} período(s)\n")
        
        # Processa cada período
        for periodo, arquivos in periodos.items():
            print(f"\n{'='*60}")
            print(f"PROCESSANDO PERÍODO: {periodo}")
            print(f"{'='*60}")
            print(f"Arquivos encontrados: {len(arquivos)}\n")
            
            # Extrai mês e ano do nome da pasta
            match = re.search(r'(\d{6})', periodo)
            if not match:
                print(f"⚠️  Não foi possível extrair período de {periodo}")
                continue
            
            periodo_str = match.group(1)
            ano = int(periodo_str[:4])
            mes = int(periodo_str[4:])
            
            print(f"Mês/Ano: {mes}/{ano}\n")
            
            # Processa cada arquivo
            for i, arquivo in enumerate(arquivos, 1):
                nome_arquivo = os.path.basename(arquivo)
                print(f"[{i}/{len(arquivos)}] Processando: {nome_arquivo}")
                
                try:
                    # Valida recomendações
                    df_resultados = validar_recomendacoes_arquivo(
                        arquivo, 
                        mes, 
                        ano
                    )
                    
                    if df_resultados is not None:
                        # Salva resultados
                        salvar_resultados_validacao(df_resultados, arquivo)
                        print(f"   ✅ {len(df_resultados)} ativos processados\n")
                    else:
                        print(f"   ⚠️  Nenhum resultado para este arquivo\n")
                        
                except Exception as e:
                    print(f"   ❌ Erro: {str(e)}\n")
                    continue
        
        print(f"\n{'='*60}")
        print("✅ VALIDAÇÃO CONCLUÍDA")
        print(f"{'='*60}")

    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")

if __name__ == '__main__':
    main()