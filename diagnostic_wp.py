import requests
import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

WORDPRESS_URL = os.getenv("WORDPRESS_URL", "").rstrip('/')
WORDPRESS_USERNAME = os.getenv("WORDPRESS_USERNAME", "")
WORDPRESS_PASSWORD = os.getenv("WORDPRESS_PASSWORD", "")

# --- Verificação Importante ---
if ' ' in WORDPRESS_PASSWORD:
    print("❌ ERRO: A senha no arquivo .env contém espaços. Remova-os e tente novamente.")
    print(f"   Senha atual: '{WORDPRESS_PASSWORD}'")
    exit()

if not all([WORDPRESS_URL, WORDPRESS_USERNAME, WORDPRESS_PASSWORD]):
    print("❌ ERRO: Verifique se WORDPRESS_URL, WORDPRESS_USERNAME, e WORDPRESS_PASSWORD estão no arquivo .env.")
    exit()

print("--- Script de Diagnóstico de Conexão WordPress ---")
print(f"URL: {WORDPRESS_URL}")
print(f"Usuário: {WORDPRESS_USERNAME}")
print(f"Senha: {'*' * len(WORDPRESS_PASSWORD)}")
print("-" * 50)

try:
    print("Tentando conectar...")
    response = requests.get(
        f"{WORDPRESS_URL}/wp-json/wp/v2/users/me",
        auth=(WORDPRESS_USERNAME, WORDPRESS_PASSWORD),
        headers={'User-Agent': 'DiagnosticScript/1.0'}
    )

    print(f"Status da Resposta: {response.status_code}")
    print("\n--- Corpo da Resposta ---")
    try:
        print(response.json())
    except requests.exceptions.JSONDecodeError:
        print(response.text)
    print("-" * 50)

    response.raise_for_status()

    print("\n✅ SUCESSO! A conexão e autenticação com o WordPress funcionaram.")
    print(f"Conectado como: {response.json().get('name')}")

except requests.exceptions.HTTPError as e:
    print(f"\n❌ FALHA: Erro HTTP {e.response.status_code}")
    if e.response.status_code == 401:
        print("   Causa Provável: 'Unauthorized'. A senha de aplicação está incorreta, foi revogada ou um plugin de segurança (ex: Wordfence) está bloqueando.")
    elif e.response.status_code == 403:
        print("   Causa Provável: 'Forbidden'. O servidor ou um firewall (WAF) está bloqueando o acesso à API REST.")

except requests.exceptions.RequestException as e:
    print(f"\n❌ FALHA: Erro de Conexão: {e}")

print("\n--- Próximos Passos ---")
print("1. Se o status for 401: Gere uma NOVA senha de aplicação no WordPress e atualize o .env.")
print("2. Se o status for 403: Desative TEMPORARIAMENTE plugins de segurança e teste de novo.")
print("3. Se ainda falhar: Contate sua hospedagem e pergunte se eles bloqueiam a 'Autenticação Básica' (Basic Auth) na API REST.")