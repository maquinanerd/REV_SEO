import requests
import logging
from typing import Dict, List, Optional
import base64
from datetime import datetime
from config import config

class WordPressClient:
    """Cliente para integração com WordPress REST API"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = config.wordpress_url.rstrip('/')
        self.username = config.wordpress_username
        self.password = config.wordpress_password
        self.session = requests.Session()
        
        # Configura autenticação básica
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.session.headers.update({
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json'
        })
    
    def test_connection(self) -> bool:
        """Testa a conexão com a API do WordPress"""
        try:
            url = f"{self.base_url}/wp-json/wp/v2/users/me"
            response = self.session.get(url)
            response.raise_for_status()
            
            user_data = response.json()
            self.logger.info(f"Conectado como: {user_data.get('name', 'N/A')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao testar conexão: {e}")
            return False
    
    def get_posts_by_author(self, author_id: int, per_page: int = 10, 
                           offset: int = 0, status: str = 'publish') -> List[Dict]:
        """
        Busca posts de um autor específico
        
        Args:
            author_id: ID do autor
            per_page: Número de posts por página
            offset: Offset para paginação
            status: Status dos posts (publish, draft, etc.)
        """
        try:
            url = f"{self.base_url}/wp-json/wp/v2/posts"
            params = {
                'author': author_id,
                'per_page': per_page,
                'offset': offset,
                'status': status,
                'orderby': 'date',
                'order': 'desc',
                '_embed': 1  # Inclui dados relacionados
            }
            
            self.logger.info(f"Buscando posts do autor {author_id}")
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            posts = response.json()
            self.logger.info(f"Encontrados {len(posts)} posts")
            return posts
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar posts: {e}")
            return []
    
    def get_new_posts_since_id(self, author_id: int, last_post_id: int, 
                              per_page: int = 10) -> List[Dict]:
        """
        Busca posts novos desde um ID específico
        
        Args:  
            author_id: ID do autor
            last_post_id: ID do último post processado
            per_page: Limite de posts
        """
        try:
            url = f"{self.base_url}/wp-json/wp/v2/posts"
            params = {
                'author': author_id,
                'per_page': per_page,
                'status': 'publish',
                'orderby': 'id',
                'order': 'desc',
                '_embed': 1
            }
            
            self.logger.info(f"Buscando posts novos desde ID {last_post_id}")
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            posts = response.json()
            
            # Filtra posts com ID maior que o último processado
            new_posts = [post for post in posts if post['id'] > last_post_id]
            
            self.logger.info(f"Encontrados {len(new_posts)} posts novos")
            return new_posts
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar posts novos: {e}")
            return []
    
    def get_post_categories(self, post_id: int) -> List[Dict]:
        """Obtém categorias de um post"""
        try:
            url = f"{self.base_url}/wp-json/wp/v2/posts/{post_id}"
            params = {'_embed': 1}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            post_data = response.json()
            categories = post_data.get('_embedded', {}).get('wp:term', [[]])[0]
            
            return categories
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar categorias do post {post_id}: {e}")
            return []
    
    def get_post_tags(self, post_id: int) -> List[Dict]:
        """Obtém tags de um post"""
        try:
            url = f"{self.base_url}/wp-json/wp/v2/posts/{post_id}"
            params = {'_embed': 1}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            post_data = response.json()
            # Tags são o segundo array em wp:term
            embedded_terms = post_data.get('_embedded', {}).get('wp:term', [[], []])
            tags = embedded_terms[1] if len(embedded_terms) > 1 else []
            
            return tags
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar tags do post {post_id}: {e}")
            return []
    
    def update_post_content(self, post_id: int, title: str, excerpt: str, 
                           content: str) -> bool:
        """
        Atualiza conteúdo básico do post
        
        Args:
            post_id: ID do post
            title: Novo título
            excerpt: Novo resumo
            content: Novo conteúdo
        """
        try:
            # Trunca o excerpt inteligentemente para máximo 180 caracteres
            truncated_excerpt = self._truncate_excerpt_intelligently(excerpt, 180)
            
            # Log da truncagem se foi aplicada
            if len(excerpt.strip()) > 180:
                self.logger.info(f"Excerpt truncado: {len(excerpt)} → {len(truncated_excerpt)} caracteres")
            
            url = f"{self.base_url}/wp-json/wp/v2/posts/{post_id}"
            
            data = {
                'title': title,
                'excerpt': truncated_excerpt,
                'content': content
            }
            
            self.logger.info(f"Atualizando conteúdo do post {post_id}")
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            self.logger.info(f"Post {post_id} atualizado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar post {post_id}: {e}")
            return False
    
    def update_yoast_meta(self, post_id: int, seo_title: str, meta_description: str, 
                         focus_keyword: str) -> bool:
        """
        Atualiza campos meta do Yoast SEO
        
        Args:
            post_id: ID do post
            seo_title: Título SEO
            meta_description: Descrição meta
            focus_keyword: Palavra-chave foco
        """
        try:
            # Trunca a meta description também para 180 caracteres
            truncated_meta_desc = self._truncate_excerpt_intelligently(meta_description, 180)
            
            # Log da truncagem se foi aplicada
            if len(meta_description.strip()) > 180:
                self.logger.info(f"Meta description truncada: {len(meta_description)} → {len(truncated_meta_desc)} caracteres")
            
            url = f"{self.base_url}/wp-json/wp/v2/posts/{post_id}"
            
            data = {
                'meta': {
                    '_yoast_wpseo_title': seo_title,
                    '_yoast_wpseo_metadesc': truncated_meta_desc,
                    '_yoast_wpseo_focuskw': focus_keyword
                }
            }
            
            self.logger.info(f"Atualizando meta Yoast do post {post_id}")
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            self.logger.info(f"Meta Yoast do post {post_id} atualizada")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar meta Yoast do post {post_id}: {e}")
            return False
    
    def update_post_complete(self, post_id: int, optimized_data: Dict) -> bool:
        """
        Atualização completa do post incluindo conteúdo e meta Yoast
        
        Args:
            post_id: ID do post
            optimized_data: Dict com title, excerpt, content, focus_keyword
        """
        
        # Extrai palavra-chave foco do título
        focus_keyword = self._extract_focus_keyword(
            optimized_data.get('title', ''),
            optimized_data.get('content', '')
        )
        
        # Atualiza conteúdo básico
        content_updated = self.update_post_content(
            post_id,
            optimized_data.get('title', ''),
            optimized_data.get('excerpt', ''),
            optimized_data.get('content', '')
        )
        
        if not content_updated:
            return False
        
        # Atualiza meta Yoast
        meta_updated = self.update_yoast_meta(
            post_id,
            optimized_data.get('title', ''),
            optimized_data.get('excerpt', ''),
            focus_keyword
        )
        
        return meta_updated
    
    def _truncate_excerpt_intelligently(self, excerpt: str, max_length: int = 180) -> str:
        """
        Trunca o excerpt de forma inteligente, cortando em pontos naturais
        
        Args:
            excerpt: Texto do excerpt
            max_length: Tamanho máximo (padrão 180 caracteres)
            
        Returns:
            Excerpt truncado de forma inteligente
        """
        import re
        
        # Remove tags HTML do excerpt
        clean_excerpt = re.sub(r'<[^>]+>', '', excerpt).strip()
        
        # Se já está dentro do limite, retorna como está
        if len(clean_excerpt) <= max_length:
            return clean_excerpt
        
        # Trunca no limite máximo
        truncated = clean_excerpt[:max_length]
        
        # Tenta cortar no final de uma frase (. ! ?)
        sentence_match = re.search(r'^(.+[.!?])\s*', truncated)
        if sentence_match and len(sentence_match.group(1)) >= max_length * 0.6:
            return sentence_match.group(1).strip()
        
        # Se não encontrou fim de frase, tenta cortar no final de uma palavra
        # Procura o último espaço antes do limite
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.7:  # Pelo menos 70% do limite
            truncated = truncated[:last_space]
        
        # Remove pontuação final incompleta se houver
        truncated = re.sub(r'[,;:]$', '', truncated.strip())
        
        # Adiciona reticências se foi truncado
        if len(clean_excerpt) > max_length:
            truncated += '...'
        
        return truncated.strip()

    def _extract_focus_keyword(self, title: str, content: str) -> str:
        """Extrai palavra-chave foco do título e conteúdo"""
        import re
        
        # Remove tags HTML do conteúdo
        clean_content = re.sub(r'<[^>]+>', '', content)
        
        # Busca por termos em negrito no conteúdo
        bold_terms = re.findall(r'<b>([^<]+)</b>', content)
        if bold_terms:
            # Pega o primeiro termo em negrito
            return bold_terms[0].strip()
        
        # Se não encontrou, usa as primeiras palavras do título
        title_words = title.split()
        if len(title_words) >= 2:
            return ' '.join(title_words[:2])
        
        return title_words[0] if title_words else 'cultura pop'
    
    def get_post_full_data(self, post_id: int) -> Optional[Dict]:
        """
        Obtém dados completos de um post incluindo categories e tags
        
        Args:
            post_id: ID do post
            
        Returns:
            Dict com dados completos do post
        """
        try:
            url = f"{self.base_url}/wp-json/wp/v2/posts/{post_id}"
            params = {'_embed': 1}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            post_data = response.json()
            
            # Extrai categorias e tags dos dados embedded
            embedded_terms = post_data.get('_embedded', {}).get('wp:term', [[], []])
            categories = embedded_terms[0] if len(embedded_terms) > 0 else []
            tags = embedded_terms[1] if len(embedded_terms) > 1 else []
            
            # Adiciona categorias e tags ao post data
            post_data['categories'] = categories
            post_data['tags'] = tags
            
            return post_data
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar dados completos do post {post_id}: {e}")
            return None
    
    def is_post_optimizable(self, post_data: Dict) -> bool:
        """
        Verifica se um post pode ser otimizado baseado nas categorias
        
        Args:
            post_data: Dados do post
            
        Returns:
            True se o post é de filme ou série
        """
        categories = post_data.get('categories', [])
        
        # Verifica se tem categoria de filme ou série
        movie_category = any(cat.get('id') == config.movie_category_id for cat in categories)
        series_category = any(cat.get('id') == config.series_category_id for cat in categories)
        
        return movie_category or series_category
    
    def get_post_by_url(self, post_url: str) -> Optional[Dict]:
        """
        Obtém dados de um post específico pela URL
        
        Args:
            post_url: URL do post
            
        Returns:
            Dict com dados do post ou None
        """
        try:
            # Extrai o slug do post da URL
            import re
            slug_match = re.search(r'/([^/]+)/?$', post_url.rstrip('/'))
            if not slug_match:
                self.logger.error(f"Não foi possível extrair slug da URL: {post_url}")
                return None
            
            slug = slug_match.group(1)
            
            url = f"{self.base_url}/wp-json/wp/v2/posts"
            params = {
                'slug': slug,
                '_embed': 1
            }
            
            self.logger.info(f"Buscando post pelo slug: {slug}")
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            posts = response.json()
            
            if posts:
                post_data = posts[0]
                
                # Extrai categorias e tags dos dados embedded
                embedded_terms = post_data.get('_embedded', {}).get('wp:term', [[], []])
                categories = embedded_terms[0] if len(embedded_terms) > 0 else []
                tags = embedded_terms[1] if len(embedded_terms) > 1 else []
                
                # Adiciona categorias e tags ao post data
                post_data['categories'] = categories
                post_data['tags'] = tags
                
                self.logger.info(f"Post encontrado: {post_data['id']} - {post_data.get('title', {}).get('rendered', 'N/A')}")
                return post_data
            else:
                self.logger.warning(f"Nenhum post encontrado para o slug: {slug}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao buscar post pela URL {post_url}: {e}")
            return None

# Instância global do cliente WordPress
wordpress_client = WordPressClient()
