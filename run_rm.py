import csv
import os
import subprocess
import requests

csv_path = 'repositories.csv'

clone_dir = 'repositories'
if not os.path.exists(clone_dir):
    os.makedirs(clone_dir)

refactoring_miner_path = r'RefactoringMiner-3.0.7\bin\RefactoringMiner.bat'

def get_default_branch(repo_name):
    with open('github-oauth.properties', 'r') as f:
        oauth_token = f.read().strip().split('=')[1]
    
    url = f"https://api.github.com/repos/{repo_name}"
    headers = {'Authorization': f'token {oauth_token}'}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return data.get('default_branch')
    else:
        print(f"Erro ao acessar o repositório: {response.status_code}")
        return None

# Função para clonar um repositório
def clone_repository(repo_name, repo_url):
    repo_path = os.path.join(clone_dir, repo_name.split('/')[-1])
    
    # Verifica se o repositório já foi clonado
    if not os.path.exists(repo_path):
        print(f'Clonando {repo_name} em {repo_path}')
        subprocess.run(['git', 'clone', repo_url, repo_path], check=True)
    else:
        print(f'Repositório {repo_name} já clonado.')
    
    return repo_path

# Função para executar o RefactoringMiner
def run_refactoring_miner(repo_path, repo_name, default_branch):
    json_output = os.path.join(clone_dir, f'{repo_name.split("/")[-1]}.json')
    print(f'Executando RefactoringMiner para {repo_name} no branch {default_branch}')
    
    subprocess.run([refactoring_miner_path, '-a', repo_path, default_branch, '-json', json_output], check=True)

# Função para escrever logs em um arquivo
def write_log(repo_name, message):
    log_file = os.path.join(clone_dir, f'{repo_name.split("/")[-1]}.log')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(message + '\n')

# Lê o arquivo CSV e clona os repositórios
with open(csv_path, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    
    for row in reader:
        repo_name = row['name']
        repo_url = f"https://github.com/{repo_name}.git"
        default_branch = get_default_branch(repo_name)

        # Log inicial para cada repositório
        write_log(repo_name, f"Processando repositório {repo_name}, branch padrão: {default_branch}")
        print(default_branch)
        
        try:
            # Clona o repositório e obtém o caminho do clone
            repo_path = clone_repository(repo_name, repo_url)
        except subprocess.CalledProcessError as e:
            error_message = f"Erro ao clonar repositório {repo_name}: {str(e)}"
            print(error_message)
            write_log(repo_name, error_message)
            continue  # Pula para o próximo repositório
        
        try:
            # Executa o RefactoringMiner no repositório clonado
            run_refactoring_miner(repo_path, repo_name, default_branch)
        except subprocess.CalledProcessError as e:
            error_message = f"Erro ao executar RefactoringMiner para {repo_name}: {str(e)}"
            print(error_message)
            write_log(repo_name, error_message)
            continue  # Pula para o próximo repositório

        write_log(repo_name, f"Processamento concluído para {repo_name}")

print("Todos os repositórios foram processados.")
