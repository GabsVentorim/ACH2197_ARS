import pandas as pd
import sys
import os
from typing import Dict, List
import glob
import random
import re

import filtro_grafo_compra_venda
import filtro_colaborativo
import filtro_conteudo
import filtro_hibrido
import funcoes_auxiliares
import validacao

class SistemaRecomendadorAcoes:
    """
    Sistema Abrangente de Recomendação de Ações implementando múltiplas abordagens:
    1. Filtragem Colaborativa (similaridade baseada em fundos)
    2. Filtragem por Conteúdo (baseada em setor/atributos)
    3. Análise de Co-ocorrência (cesta de mercado)
    4. Abordagem baseada em Grafo (análise de rede)
    """
    
    def __init__(self, caminho_csv: str):
        """
        Inicializa o sistema de recomendação com dados.
        
        Args:
            caminho_csv: Caminho para o arquivo CSV com dados de carteiras
        """
        self.caminho_csv = caminho_csv
        self.df = pd.read_csv(caminho_csv, sep=';', encoding='utf-8-sig')
        self._preprocessar_dados()
        
    def _preprocessar_dados(self):
        """Limpa e prepara os dados."""
        # Converte colunas numéricas
        colunas_numericas = ['QT_POS_FINAL', 'VL_MERC_POS_FINAL', 
                            'QT_VENDA_NEGOC', 'VL_VENDA_NEGOC',
                            'QT_AQUIS_NEGOC', 'VL_AQUIS_NEGOC']
        
        for col in colunas_numericas:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)
        
        # Filtra apenas posições com saldo
        self.df_fundos_ativos = self.df[self.df['QT_POS_FINAL'] > 0].copy()

        # Converte CNPJ para string
        self.df_fundos_ativos['CNPJ_FUNDO_CLASSE'] = self.df_fundos_ativos['CNPJ_FUNDO_CLASSE'].astype("string")
        
        # Cria matriz fundo-ação
        self.matriz_fundo_acao = self.df_fundos_ativos.pivot_table(
            index='CNPJ_FUNDO_CLASSE',
            columns='CD_ATIVO',
            values='VL_MERC_POS_FINAL',
            fill_value=0
        )
        
        print(f"✅ Dados carregados: {len(self.df_fundos_ativos)} posições")
        print(f"📊 Fundos únicos: {self.df_fundos_ativos['CNPJ_FUNDO_CLASSE'].nunique()}")
        print(f"📈 Ações únicas: {self.df_fundos_ativos['CD_ATIVO'].nunique()}")
    
    def obter_fundos_disponiveis(self) -> List[str]:
        """
        Retorna lista de fundos disponíveis no dataset.
        
        Returns:
            Lista com CNPJs dos fundos
        """
        return sorted(self.df_fundos_ativos['CNPJ_FUNDO_CLASSE'].unique().tolist())
    
    def obter_periodo_arquivo(self) -> str:
        """
        Extrai o período (mês/ano) do nome do arquivo.
        
        Returns:
            String no formato YYYYMM
        """
        nome_arquivo = os.path.basename(self.caminho_csv)
        match = re.search(r'(\d{6})', nome_arquivo)
        if match:
            return match.group(1)
        return "000000"
    
    def obter_perfil_fundo(self, cnpj_fundo: str) -> Dict:
        """
        Obtém o perfil do fundo.
        
        Args:
            cnpj_fundo: CNPJ do fundo alvo
            
        Returns:
            Dicionário com informações do perfil do fundo
        """
        funcoes_auxiliares.obtem_perfil_fundo(self.df_fundos_ativos, cnpj_fundo)
    
    def recomendar_filtragem_colaborativa(self, cnpj_fundo: str, top_n: int = 10) -> pd.DataFrame:
        """
        Recomenda ações usando filtragem colaborativa.
        
        Args:
            cnpj_fundo: CNPJ do fundo alvo
            top_n: Número de recomendações
            
        Returns:
            DataFrame com recomendações
        """
        print("\n🔍 Executando recomendação por filtragem colaborativa...")
        resultados = filtro_colaborativo.filtro_colaborativo(
            self.df_fundos_ativos, 
            self.matriz_fundo_acao, 
            cnpj_fundo, 
            top_n
        )
        return resultados
    
    def recomendar_filtragem_conteudo(self, cnpj_fundo: str, top_n: int = 10) -> pd.DataFrame:
        """
        Recomenda ações usando filtragem por conteúdo.
        
        Args:
            cnpj_fundo: CNPJ do fundo alvo
            top_n: Número de recomendações
            
        Returns:
            DataFrame com recomendações
        """
        print("\n🔍 Executando recomendação por filtragem de conteúdo...")
        resultados = filtro_conteudo.filtro_baseado_conteudo(
            self.df_fundos_ativos, 
            cnpj_fundo, 
            top_n
        )
        return resultados
    
    def recomendar_analise_grafo(self, cnpj_fundo: str, top_n: int = 10) -> pd.DataFrame:
        """
        Recomenda ações usando análise de grafo/rede.
        
        Args:
            cnpj_fundo: CNPJ do fundo alvo
            top_n: Número de recomendações
            
        Returns:
            DataFrame com recomendações
        """
        print("\n🔍 Executando recomendação por análise de grafo...")
        resultados = filtro_grafo_compra_venda.recomendacao_baseada_em_grafo_compra_venda(
            self.df_fundos_ativos, 
            cnpj_fundo, 
            top_n
        )
        return resultados
    
    def recomendar_filtro_hibrido(self, cnpj_fundo: str, top_n: int = 10) -> pd.DataFrame:
        """
        Recomenda ações usando filtro híbrido (combinação de todas as abordagens).
        
        Args:
            cnpj_fundo: CNPJ do fundo alvo
            top_n: Número de recomendações
            
        Returns:
            DataFrame com recomendações
        """
        print("\n🔍 Executando recomendação por filtro híbrido...")
        resultados = filtro_hibrido.filtro_hibrido(
            self.df_fundos_ativos, 
            self.matriz_fundo_acao,
            cnpj_fundo, 
            top_n
        )
        return resultados
    
    def processar_recomendacoes(self, cnpj_fundo: str, top_n: int = 10) -> Dict[str, pd.DataFrame]:
        """
        Processa todas as recomendações para um fundo.
        
        Args:
            cnpj_fundo: CNPJ do fundo alvo
            top_n: Número de recomendações
            
        Returns:
            Dicionário com resultados de cada abordagem
        """
        print(f"\n{'='*60}")
        print(f"PROCESSANDO RECOMENDAÇÕES PARA FUNDO: {cnpj_fundo}")
        print(f"{'='*60}")
        
        resultados = {}
        
        print("🔍 Filtragem Colaborativa...")
        resultados['filtragem_colaborativa'] = self.recomendar_filtragem_colaborativa(cnpj_fundo, top_n)
        
        print("🔍 Filtragem por Conteúdo...")
        resultados['filtragem_conteudo'] = self.recomendar_filtragem_conteudo(cnpj_fundo, top_n)
        
        print("🔍 Análise de Grafo...")
        resultados['analise_grafo'] = self.recomendar_analise_grafo(cnpj_fundo, top_n)
        
        print("🔍 Filtro Híbrido...")
        resultados['hibrido'] = self.recomendar_filtro_hibrido(cnpj_fundo, top_n)
        
        return resultados
    
    def salvar_recomendacoes(self, cnpj_fundo: str, resultados: Dict[str, pd.DataFrame], 
                            diretorio_saida: str = '../output') -> None:
        """
        Salva as recomendações em arquivos CSV com formato específico.
        Cria uma pasta para cada período e adiciona colunas de validação.
        
        Args:
            cnpj_fundo: CNPJ do fundo
            resultados: Dicionário com resultados de cada abordagem
            diretorio_saida: Diretório de saída base
        """
        periodo = self.obter_periodo_arquivo()
        
        # Cria subdiretório para o período
        diretorio_periodo = os.path.join(diretorio_saida, f"periodo_{periodo}")
        os.makedirs(diretorio_periodo, exist_ok=True)
        
        # Extrai mês e ano para validação
        ano = int(periodo[:4])
        mes = int(periodo[4:])
        
        for abordagem, df in resultados.items():
            if df.empty:
                print(f"⚠️  Nenhuma recomendação para {abordagem}")
                continue
            
            # Seleciona apenas as colunas necessárias
            colunas_necessarias = ['ativo', 'pontuacao'] if 'ativo' in df.columns else ['CD_ATIVO', 'pontuacao']
            
            if colunas_necessarias[0] not in df.columns:
                colunas_possiveis = [col for col in df.columns if 'ativo' in col.lower()]
                if colunas_possiveis:
                    colunas_necessarias[0] = colunas_possiveis[0]
            
            df_saida = df[colunas_necessarias].copy()
            df_saida.columns = ['ativo', 'pontuacao']
            
            # Adiciona validação
            df_saida = validacao.adicionar_validacao_recomendacoes(
                df_saida, 
                mes, 
                ano
            )
            
            # Nome do arquivo: {cnpj}_{abordagem}_{periodo}.csv
            nome_arquivo = f"{cnpj_fundo}_{abordagem}_{periodo}.csv"
            caminho_saida = os.path.join(diretorio_periodo, nome_arquivo)
            
            df_saida.to_csv(caminho_saida, sep=';', encoding='utf-8-sig', index=False)
            print(f"✅ Salvo: {nome_arquivo} ({len(df_saida)} recomendações)")


def obter_arquivos_saida(diretorio: str = '../../output') -> List[str]:
    """
    Obtém lista de arquivos CSV na pasta de saída.
    
    Args:
        diretorio: Diretório de saída
        
    Returns:
        Lista com caminhos dos arquivos CSV
    """
    arquivos = glob.glob(os.path.join(diretorio, "carteiras_com_setores_*.csv"))
    return sorted(arquivos)


def selecionar_fundos_aleatorios(sistema: SistemaRecomendadorAcoes, quantidade: int) -> List[str]:
    """
    Seleciona fundos aleatoriamente para recomendação.
    
    Args:
        sistema: Instância do SistemaRecomendadorAcoes
        quantidade: Número de fundos a selecionar
        
    Returns:
        Lista com CNPJs dos fundos selecionados
    """
    fundos_disponiveis = sistema.obter_fundos_disponiveis()
    
    print(f"\n📊 Fundos disponíveis: {len(fundos_disponiveis)}")
    
    if quantidade > len(fundos_disponiveis):
        print(f"⚠️  Quantidade solicitada ({quantidade}) maior que fundos disponíveis.")
        print(f"🔄 Selecionando todos os {len(fundos_disponiveis)} fundos disponíveis.\n")
        quantidade = len(fundos_disponiveis)
    
    # Seleciona fundos aleatoriamente
    fundos_selecionados = random.sample(fundos_disponiveis, quantidade)
    
    print(f"✅ {len(fundos_selecionados)} fundos selecionados aleatoriamente para análise\n")
    
    return fundos_selecionados


# ==================== EXEMPLO DE USO ====================

if __name__ == "__main__":
    # Carrega dados de validação uma única vez
    validacao.carregar_dados_validacao()
    
    # Obtém arquivos disponíveis
    print("📂 Procurando arquivos de saída...")
    arquivos = obter_arquivos_saida()
    
    if not arquivos:
        print("❌ Nenhum arquivo encontrado em ../../output/")
        sys.exit(1)
    
    print(f"✅ Encontrados {len(arquivos)} arquivo(s)\n")
    
    # Processa cada arquivo
    for arquivo in arquivos:
        print(f"\n{'#'*60}")
        print(f"PROCESSANDO: {os.path.basename(arquivo)}")
        print(f"{'#'*60}")
        
        # Inicializa sistema
        sistema = SistemaRecomendadorAcoes(arquivo)
        
        # Define quantidade de fundos a processar
        quantidade_fundos = 10
        
        # Seleciona fundos aleatoriamente
        fundos_selecionados = selecionar_fundos_aleatorios(sistema, quantidade_fundos)
        
        # Processa recomendações para cada fundo
        for i, cnpj_fundo in enumerate(fundos_selecionados, 1):
            try:
                print(f"\n[{i}/{len(fundos_selecionados)}] Processando fundo: {cnpj_fundo}")
                
                # Obtém perfil do fundo
                sistema.obter_perfil_fundo(cnpj_fundo)
                
                # Processa todas as recomendações
                recomendacoes = sistema.processar_recomendacoes(cnpj_fundo, top_n=10)
                
                # Salva recomendações com validação
                sistema.salvar_recomendacoes(cnpj_fundo, recomendacoes)
                
            except Exception as e:
                print(f"❌ Erro ao processar fundo {cnpj_fundo}: {str(e)}")
                continue
        
        print(f"\n{'='*60}")
        print("✅ PROCESSAMENTO CONCLUÍDO")
        print(f"{'='*60}")