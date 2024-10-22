import os
import json
import requests

# Função para ler o token do GitHub do arquivo de propriedades
def read_github_token(filename):
    with open(filename, 'r') as f:
        line = f.readline().strip()
        token = line.split('=')[1].strip()  # Pega somente o valor após '='
        return token

# Lê o token do GitHub do arquivo
GITHUB_TOKEN = read_github_token('github-oauth.properties')

# Função para obter o diff do commit
def get_commit_diff(repo_owner, repo_name, sha1):
    url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{sha1}'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    commit_data = response.json()
    return commit_data.get('files', [])

# Função para filtrar e salvar o código para um arquivo específico
def save_code_diff(files, target_file, output_dir, commit_sha, is_after):
    # Cria o diretório para o SHA do commit
    sha_dir = os.path.join(output_dir, commit_sha)
    os.makedirs(sha_dir, exist_ok=True)

    # Define o nome do arquivo
    suffix = 'refactored' if is_after else 'original'
    output_file = os.path.join(sha_dir, f"{suffix}.java")

    with open(output_file, 'w') as f:
        for file in files:
            if file['filename'] == target_file:
                patch = file.get('patch', '')
                if patch:
                    lines = patch.splitlines()
                    for line in lines:
                        # Ignora linhas de contexto que começam com @@
                        if line.startswith('@@'):
                            continue

                        # Para o arquivo "original.java", mantenha todas as linhas,
                        # mas remova as que começam com '+' e escreva as que começam com '-'
                        if not is_after:
                            if line.startswith('-'):
                                f.write(line[1:] + '\n')  # Remove o sinal -
                            elif not line.startswith('+'):
                                f.write(line + '\n')  # Mantém linhas sem sinal

                        # Para o arquivo "refactored.java", mantenha todas as linhas,
                        # mas remova as que começam com '-' e escreva as que começam com '+'
                        else:
                            if line.startswith('+'):
                                f.write(line[1:] + '\n')  # Remove o sinal +
                            elif not line.startswith('-'):
                                f.write(line + '\n')  # Mantém linhas sem sinal

# Função principal para carregar o JSON e salvar os códigos
def main(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)

    for commit in data['commits']:
        repo_url = commit['repository']
        repo_parts = repo_url.strip('/').split('/')[-2:]
        repo_owner = repo_parts[0]
        repo_name = repo_parts[1].replace('.git', '')  # Remove '.git' se presente
        sha1 = commit['sha1']
        
        # Verifica se a refatoração é do tipo "Extract Method"
        refactorings = commit.get('refactorings', [])
        for refactoring in refactorings:
            if refactoring['type'] == 'Extract Method':
                target_file = refactoring['leftSideLocations'][0]['filePath']
                
                print(f"Diffs for the commit {sha1} in {repo_owner}/{repo_name}...\n")
                files = get_commit_diff(repo_owner, repo_name, sha1)

                # Define o diretório para salvar os arquivos
                output_dir = f'./code/{repo_name}/'
                
                # Salva os arquivos como .java dentro do diretório SHA
                save_code_diff(files, target_file, output_dir, sha1, is_after=False)
                save_code_diff(files, target_file, output_dir, sha1, is_after=True)
                break  # Se uma refatoração "Extract Method" for encontrada, não precisa verificar mais

if __name__ == '__main__':
    json_file = './repositories/activemq.json'  # Substitua pelo caminho do seu arquivo JSON
    main(json_file)
