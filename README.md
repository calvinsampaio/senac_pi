# senac_pi

## Integrantes
- Calvin Klein Sampaio Batista
- ????????????????????????????

# Dataset
‘Brazil Dengue Dataset (SINAN 2000–2025)’
https://www.kaggle.com/datasets/gallo33henrique/dengue-no-brasil-sinan-20002025

## Contexto
O conjunto de dados “Brazil Dengue Dataset (SINAN 2000–2025)” agrega registros de ocorrências de dengue no território brasileiro por mais de vinte anos, provenientes do sistema oficial de vigilância epidemiológica do Ministério da Saúde. Tais informações são constantemente atualizadas e contemplam registros pormenorizados conforme período, município e aspectos dos acometimentos.
A dengue constitui um desafio recorrente para a saúde coletiva no país, apresentando acentuada oscilação conforme a estação do ano e a região. A exploração dessas informações possibilita identificar perfis epidemiológicos e subsidiar estratégias de controle.

## Objetivo
•	Identificar tendências temporais (crescimento, sazonalidade, surtos);
•	Analisar a distribuição geográfica dos casos;
•	Investigar o perfil dos pacientes (idade, sexo, evolução);
•	Gerar insights para apoio à vigilância epidemiológica.

## Planejamento geral
Primeira etapa:

1. Planejamento e Implementação do ETL [Integrante: Calvin Klein Sampaio Batista]
•	Definição dos objetivos da análise; 
•	Exploração inicial e entendimento da estrutura do dataset; 
•	Definição das ferramentas e arquitetura do projeto.

2. Processo de ETL: [Integrante: ????????????????????????????]
•	Extração: leitura e validação inicial dos dados; 
•	Transformação: limpeza, remoção de duplicidades, padronização e ajuste de tipos; 
•	Carga: geração de uma base inicial tratada para uso nas próximas etapas.

Segunda etapa:

1. Tratamento, Armazenamento e Desenvolvimento do Dashboard [Integrante: Calvin Klein Sampaio Batista]
•	Uso da biblioteca Pandas para análise exploratória e transformações adicionais; 
•	Tratamento de valores nulos e criação de novas variáveis (ano, mês, indicadores); 
•	Agregações e preparação final dos dados.

2. Armazenamento: [Integrante: ????????????????????????????]
•	Modelagem e criação de uma base estruturada (ex: SQLite/PostgreSQL); 
•	Inserção e validação dos dados tratados.

3. Dashboard com Streamlit: [Integrante: Calvin Klein Sampaio Batista e ????????????????????????????]
•	Desenvolvimento da aplicação interativa; 
•	Criação de gráficos, KPIs e filtros; 
•	Integração com a base de dados; 
•	Publicação e validação final do dashboard.

## Planejamento do Dashboard
1. Tendências Temporais (crescimento, sazonalidade, surtos)
Métricas (KPIs):
•	Total de casos ao longo do tempo
•	Casos no último ano/mês
•	Taxa de crescimento (%) período a período
•	Média mensal de casos
•	Pico máximo de casos (maior surto registrado)
Visualizações:
•	Gráfico de linha: evolução de casos por ano e por mês
•	Gráfico de linha com média móvel (tendência)
•	Heatmap: casos por mês vs ano (sazonalidade)
•	Gráfico de barras: comparação anual de casos

2. Distribuição Geográfica dos Casos
Métricas (KPIs):
•	Total de casos por estado
•	Top 5 estados com mais casos
•	Taxa de incidência por região (se houver população)
•	Participação percentual por estado
Visualizações:
•	Mapa coroplético do Brasil (casos por estado)
•	Gráfico de barras: ranking de estados
•	Gráfico de barras empilhadas: casos por região
•	Tabela interativa com estados e indicadores

3. Perfil dos Pacientes (idade, sexo, evolução)
Métricas (KPIs):
•	Distribuição percentual por sexo
•	Idade média dos pacientes
•	Faixa etária com maior incidência
•	Taxa de óbitos (%)
•	Taxa de cura (%)
Visualizações:
•	Gráfico de barras: casos por faixa etária
•	Gráfico de pizza ou barras: distribuição por sexo
•	Gráfico de barras empilhadas: evolução dos casos (cura, óbito, etc.)
•	Histograma: distribuição de idade

4. Indicadores para Vigilância Epidemiológica
Métricas (KPIs):
•	Tempo médio entre início dos sintomas e notificação
•	Proporção de casos graves
•	Taxa de letalidade
•	Número de surtos identificados (picos anormais)
Visualizações:
•	Boxplot: tempo entre sintomas e notificação
•	Gráfico de linha: evolução de casos graves ao longo do tempo
•	Gráfico de dispersão: relação entre variáveis (ex: idade vs gravidade)
•	Linha com destaque de picos (detecção de surtos)

5. Interatividade Essencial no Dashboard
•	Filtros por:
•	Ano
•	Estado / Região
•	Faixa etária
•	Sexo
•	Drill-down (ex: Brasil → Estado → Município)
•	Seleção de período (range de datas)


