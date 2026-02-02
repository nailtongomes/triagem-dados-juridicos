import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Configurações de estilo
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

def load_data(directory):
    all_processos = []
    summary = {
        'total_files': 0,
        'with_processos': 0,
        'without_processos': 0
    }
    
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    
    for filename in files:
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                summary['total_files'] += 1
                
                if data.get('processos'):
                    summary['with_processos'] += 1
                    for proc in data['processos']:
                        proc['cpf_consulta'] = data.get('chave_pesquisa')
                        proc['data_consulta_ref'] = data.get('data_consulta')
                        all_processos.append(proc)
                else:
                    summary['without_processos'] += 1
        except Exception as e:
            print(f"Erro ao ler {filename}: {e}")
            
    return pd.DataFrame(all_processos), summary

def clean_data(df):
    if df.empty:
        return df
    
    # Converter datas
    df['data_distribuicao_dt'] = pd.to_datetime(df['data_distribuicao'], format='%d/%m/%Y', errors='coerce')
    df['ano_distribuicao'] = df['data_distribuicao_dt'].dt.year
    
    # Tratar valores nulos em valor_causa
    df['valor_causa'] = pd.to_numeric(df['valor_causa'], errors='coerce').fillna(0)
    
    return df

def create_visualizations(df, summary):
    if df.empty:
        print("Nenhum dado de processo encontrado para visualizar.")
        return

    # 1. Resumo de Consultas (Encontrados vs Não Encontrados)
    plt.figure(figsize=(8, 6))
    labels = ['Com Processos', 'Sem Processos']
    sizes = [summary['with_processos'], summary['without_processos']]
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=['#4CAF50', '#FFC107'])
    plt.title('Proporção de CPFs com Processos Encontrados')
    plt.savefig('resumo_consultas.png')
    plt.close()

    # 2. Top 10 Assuntos
    plt.figure(figsize=(12, 8))
    top_assuntos = df['assunto'].value_counts().head(10)
    sns.barplot(x=top_assuntos.values, y=top_assuntos.index, palette='viridis')
    plt.title('Top 10 Assuntos Mais Recorrentes')
    plt.xlabel('Quantidade de Processos')
    plt.tight_layout()
    plt.savefig('top_assuntos.png')
    plt.close()

    # 3. Distribuição por Tribunal
    plt.figure(figsize=(10, 6))
    sns.countplot(data=df, x='tribunal', palette='magma')
    plt.title('Distribuição de Processos por Tribunal')
    plt.ylabel('Quantidade')
    plt.savefig('distribuicao_tribunal.png')
    plt.close()

    # 4. Evolução Temporal (Por Ano)
    plt.figure(figsize=(12, 6))
    procs_per_year = df['ano_distribuicao'].value_counts().sort_index()
    sns.lineplot(x=procs_per_year.index.astype(int), y=procs_per_year.values, marker='o')
    plt.title('Evolução de Distribuição de Processos ao Longo dos Anos')
    plt.xlabel('Ano')
    plt.ylabel('Quantidade de Processos')
    plt.savefig('evolucao_temporal.png')
    plt.close()

    # 5. Top 10 Classes Processuais
    plt.figure(figsize=(12, 8))
    top_classes = df['classe'].value_counts().head(10)
    sns.barplot(x=top_classes.values, y=top_classes.index, palette='rocket')
    plt.title('Top 10 Classes Processuais')
    plt.xlabel('Quantidade')
    plt.tight_layout()
    plt.savefig('top_classes.png')
    plt.close()

    print("Visualizações geradas com sucesso!")

if __name__ == "__main__":
    base_dir = "consultas"
    if not os.path.exists(base_dir):
        print(f"Diretório {base_dir} não encontrado.")
    else:
        print("Lendo dados...")
        df_procs, summary_stats = load_data(base_dir)
        print(f"Total de processos carregados: {len(df_procs)}")
        
        df_procs = clean_data(df_procs)
        
        print("Gerando visualizações...")
        create_visualizations(df_procs, summary_stats)
        
        # Salvar um CSV consolidado também pode ser útil
        df_procs.to_csv('processos_consolidados.csv', index=False, encoding='utf-8-sig')
        print("Dados consolidados salvos em 'processos_consolidados.csv'")
