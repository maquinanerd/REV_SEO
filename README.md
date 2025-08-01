 # WordPress SEO Optimizer
 
 ## 1. Visão Geral
 
 O **WordPress SEO Optimizer** é um sistema automatizado desenvolvido em Python para otimizar o SEO de posts em um site WordPress. Ele utiliza a API do Google Gemini para reescrever e enriquecer o conteúdo, a API do TMDB para buscar metadados de filmes e séries, e a API REST do WordPress para publicar as atualizações, incluindo campos específicos do plugin Yoast SEO.
 
 O sistema foi projetado para rodar de forma contínua (por exemplo, no Replit), com um painel de monitoramento em Flask que exibe o status da operação em tempo real.
 
 ## 2. Arquitetura do Sistema
 
 A aplicação é modular, separando as responsabilidades em diferentes componentes para facilitar a manutenção e escalabilidade.
 
 - **Orquestrador (`seo_optimizer.py`)**: É o cérebro do sistema. Coordena a busca por novos posts, chama os clientes de API para enriquecimento e otimização, e atualiza os posts no WordPress.
 - **Clientes de API**:
   - `wordpress_client.py`: Gerencia toda a comunicação com o WordPress (buscar posts, atualizar conteúdo, metadados, etc.).
   - `gemini_client.py`: Interage com a IA do Google Gemini, gerenciando a rotação de chaves e as quotas de uso.
   - `tmdb_client.py`: Busca informações de filmes e séries no The Movie Database.
 - **Banco de Dados (`database.py`)**: Utiliza SQLite para persistir dados de logs, controle de posts processados e status da quota de API.
 - **Configuração (`config.py`)**: Carrega e valida todas as variáveis de ambiente (chaves, URLs, senhas) a partir de um arquivo `.env`.
 - **Painel (`dashboard.py`)**: Uma aplicação Flask que fornece uma interface web para monitorar o status do sistema, logs e estatísticas.
 
 ### Fluxo de Dados
 
 O processo de otimização segue os seguintes passos:
 
 1.  **Busca de Posts**: O sistema verifica o WordPress em busca de novos posts publicados pelo autor alvo (ID 6).
 2.  **De-duplicação**: Posts com títulos idênticos são identificados. O mais recente é mantido e os demais são movidos para a lixeira para evitar conteúdo duplicado.
 3.  **Verificação**: O sistema analisa as categorias do post para garantir que ele é otimizável (Filme ou Série).
 4.  **Otimização com IA**: O conteúdo do post é enviado para o Google Gemini, que o reescreve seguindo um prompt focado em SEO para notícias.
 5.  **Atualização no WordPress**: O post original é atualizado com o novo título, resumo (excerpt), conteúdo e metadados do Yoast SEO (título SEO, meta descrição e palavra-chave em foco). A edição é atribuída ao usuário editor (ID 9).
 6.  **Log e Controle**: Todas as operações são registradas no banco de dados SQLite, e o ID do último post processado é salvo para o próximo ciclo.
 
 ## 3. Estrutura de Arquivos
 
 ```
 /
 ├── main.py                 # Ponto de entrada, agendamento e CLI
 ├── seo_optimizer.py        # Orquestrador principal da otimização
 ├── wordpress_client.py     # Cliente para a API do WordPress
 ├── gemini_client.py        # Cliente para a API do Google Gemini
 ├── tmdb_client.py          # Cliente para a API do TMDB
 ├── database.py             # Gerenciador do banco de dados SQLite
 ├── dashboard.py            # Aplicação Flask para o painel de controle
 ├── config.py               # Módulo de configuração e variáveis de ambiente
 ├── .env                    # Arquivo com as chaves e senhas (NÃO versionar)
 ├── requirements.txt        # Dependências do Python
 ├── seo_dashboard.db        # Banco de dados SQLite
 └── seo_optimizer.log       # Arquivo de log
 ```
 
 ## 4. Configuração do Ambiente (`.env`)
 
 Para rodar o projeto, crie um arquivo chamado `.env` na raiz do diretório com o seguinte conteúdo. Substitua os valores conforme necessário.
 
 ```env
 # WordPress
 WORDPRESS_URL=https://www.maquinanerd.com.br/
 WORDPRESS_USERNAME=Abel
 WORDPRESS_PASSWORD=Hl7M 5ZOE hMNQ M7A9 gFVy IEsB
 WORDPRESS_DOMAIN=https://www.maquinanerd.com.br/
 
 # IDs de Autor
 TARGET_AUTHOR_ID=6
 EDITOR_AUTHOR_ID=9
 
 # IDs de Categoria
 MOVIE_CATEGORY_ID=24
 SERIES_CATEGORY_ID=21
 
 # Google Gemini
 GEMINI_API_KEY=AIzaSyD7X2_8KPNZrnQnQ_643TjIJ2tpbkuRSms
 GEMINI_API_KEY_1=AIzaSyDDkQ-htQ1WsNL-i6d_a9bwACL6cez8Cjs
 GEMINI_API_KEY_2=AIzaSyDIV2OX6OujMmXzVaxMOREjJ3tGC8DP7wg
 
 # TMDB
 TMDB_API_KEY=cb60717161e33e2972bd217aabaa27f4
 TMDB_READ_TOKEN=eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjYjYwNzE3MTYxZTMzZTI5NzJiZDIxN2FhYmFhMjdmNCIsInN1YiI6IjY2NTRhYjRkYjM4ZDU1M2Q5M2MyYmM4ZCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.2T-x-y_gN5wzZ_Z8Y_X_w_X_w_X_w_X_w_X_w_X_w_X_w_X_w
 TMDB_BASE_URL=https://api.themoviedb.org/3
 TMDB_IMAGE_URL=https://image.tmdb.org/t/p
 
 # Flask
 SESSION_SECRET=5SFn/MRA2tlJluiogVz0oSef30ctJdaCSEG0vQRZrvY6SseayTbK05tQ+prPiLWRBiiQSjbm3p13vybLtvos0Q==
 
 # Configurações do Otimizador
 MAX_POSTS_PER_CYCLE=10
 SCHEDULE_INTERVAL_MINUTES=60
 ```
 
 **Atenção**: O arquivo `.env` contém informações sensíveis e **NUNCA** deve ser enviado para um repositório Git público.
 
 ## 5. Banco de Dados (`seo_dashboard.db`)
 
 O sistema utiliza um banco de dados SQLite com as seguintes tabelas:
 
 - **`processing_control`**: Armazena o ID do último post processado e estatísticas gerais.
 - **`processing_logs`**: Guarda um histórico detalhado de cada tentativa de otimização (sucesso ou falha).
 - **`gemini_quota`**: Controla o uso da API Gemini, incluindo a chave atual e o número de requisições.
 - **`statistics`**: Tabela genérica para armazenar estatísticas diversas para o painel.
 
 ## 6. Como Executar
 
 ### Pré-requisitos
 - Python 3.10+
 - Instalar as dependências:
   ```bash
   pip install -r requirements.txt
   ```
 
 ### Modos de Execução
 
 1.  **Execução Contínua (Produção)**:
     O sistema rodará em ciclos, verificando por novos posts no intervalo definido em `.env`.
     ```bash
     python main.py
     ```
 
 2.  **Execução Única (Teste)**:
     Roda o ciclo de otimização apenas uma vez e finaliza. Útil para testes e depuração.
     ```bash
     python main.py --once
     ```
 
 3.  **Painel de Controle**:
     Inicia o servidor Flask para acessar o painel de monitoramento.
     ```bash
     python dashboard.py
     ```
     Acesse o painel no endereço fornecido (geralmente `http://127.0.0.1:5000`).
 
 ## 7. Prompt da IA (Google Gemini)
 
 O prompt enviado para a IA é projetado para gerar conteúdo otimizado para o Google News, com as seguintes características:
 
 - **Tom Jornalístico**: Linguagem clara, objetiva e informativa.
 - **Estrutura**: Parágrafos curtos e bem definidos.
 - **Ênfase**: Uso de negrito (`<b>`) em termos e palavras-chave importantes.
 - **Links Internos**: Inserção de links para outros conteúdos do site, baseados nas tags do post.
 - **Mídia**: Inclusão de imagens (pôster, backdrop) e trailer do YouTube obtidos do TMDB.