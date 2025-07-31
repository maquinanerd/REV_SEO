import requests
import logging
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote
import re
from config import config

class TMDBClient:
    """Cliente para integração com The Movie Database (TMDB)"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_key = config.tmdb_api_key
        self.base_url = config.tmdb_base_url
        self.image_base_url = config.tmdb_image_url
        self.session = requests.Session()
        
        # Headers para autenticação
        if config.tmdb_read_token:
            self.session.headers.update({
                'Authorization': f'Bearer {config.tmdb_read_token}',
                'Content-Type': 'application/json'
            })
    
    def search_movie(self, query: str, year: Optional[int] = None) -> Optional[Dict]:
        """Busca filme no TMDB"""
        try:
            url = f"{self.base_url}/search/movie"
            params = {
                'api_key': self.api_key,
                'query': query,
                'language': 'pt-BR',
                'include_adult': 'false'
            }
            
            if year:
                params['year'] = year
            
            self.logger.info(f"Buscando filme: {query}")
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            if results:
                movie = results[0]  # Pega o primeiro resultado
                self.logger.info(f"Filme encontrado: {movie.get('title')}")
                return movie
            else:
                self.logger.warning(f"Nenhum filme encontrado para: {query}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao buscar filme {query}: {e}")
            return None
    
    def search_tv_show(self, query: str, year: Optional[int] = None) -> Optional[Dict]:
        """Busca série de TV no TMDB"""
        try:
            url = f"{self.base_url}/search/tv"
            params = {
                'api_key': self.api_key,
                'query': query,
                'language': 'pt-BR',
                'include_adult': 'false'
            }
            
            if year:
                params['first_air_date_year'] = year
            
            self.logger.info(f"Buscando série: {query}")
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            if results:
                tv_show = results[0]  # Pega o primeiro resultado
                self.logger.info(f"Série encontrada: {tv_show.get('name')}")
                return tv_show
            else:
                self.logger.warning(f"Nenhuma série encontrada para: {query}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao buscar série {query}: {e}")
            return None
    
    def get_movie_details(self, movie_id: int) -> Optional[Dict]:
        """Obtém detalhes completos de um filme"""
        try:
            url = f"{self.base_url}/movie/{movie_id}"
            params = {
                'api_key': self.api_key,
                'language': 'pt-BR',
                'append_to_response': 'videos,images'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Erro ao obter detalhes do filme {movie_id}: {e}")
            return None
    
    def get_tv_details(self, tv_id: int) -> Optional[Dict]:
        """Obtém detalhes completos de uma série"""
        try:
            url = f"{self.base_url}/tv/{tv_id}"
            params = {
                'api_key': self.api_key,
                'language': 'pt-BR',
                'append_to_response': 'videos,images'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Erro ao obter detalhes da série {tv_id}: {e}")
            return None
    
    def extract_youtube_trailer(self, videos: List[Dict]) -> Optional[str]:
        """Extrai URL do trailer do YouTube"""
        try:
            for video in videos:
                if (video.get('site') == 'YouTube' and 
                    video.get('type') in ['Trailer', 'Official Trailer']):
                    video_key = video.get('key')
                    if video_key:
                        return f"https://www.youtube.com/embed/{video_key}"
            return None
        except Exception as e:
            self.logger.error(f"Erro ao extrair trailer: {e}")
            return None
    
    def build_image_url(self, path: str, size: str = 'w500') -> str:
        """Constrói URLs completas para imagens"""
        if not path:
            return ""
        return f"{self.image_base_url}/{size}{path}"
    
    def extract_title_from_content(self, content: str, tags: List[str]) -> Tuple[str, Optional[int]]:
        """
        Extrai título de filme/série do conteúdo e tags
        Retorna (título_limpo, ano_opcional)
        """
        # Palavras comuns a remover
        stopwords = ['filme', 'movie', 'serie', 'series', 'tv', 'show', 'temporada', 'season', 
                    'episodio', 'episode', 'trailer', 'teaser', 'poster', 'wallpaper']
        
        candidates = []
        
        # Extrai candidatos das tags
        for tag in tags:
            tag_clean = tag.lower().strip()
            if len(tag_clean) > 3 and not any(stop in tag_clean for stop in stopwords):
                candidates.append(tag)
        
        # Extrai candidatos do título do post
        title_words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content[:200])
        candidates.extend(title_words)
        
        # Busca por anos no conteúdo
        years = re.findall(r'\b(19|20)\d{2}\b', content)
        year = None
        if years:
            year = int(years[0])
        
        # Retorna o candidato mais provável
        if candidates:
            # Prioriza tags mais longas (geralmente títulos completos)
            best_candidate = max(candidates, key=len)
            return best_candidate.strip(), year
        
        return "", year
    
    def search_media_from_post(self, post_title: str, post_content: str, 
                              post_tags: List[str], is_movie: bool = True) -> Optional[Dict]:
        """
        Busca mídia baseada no conteúdo do post
        
        Args:
            post_title: Título do post
            post_content: Conteúdo do post
            post_tags: Lista de tags do post
            is_movie: True para filme, False para série
            
        Returns:
            Dict com informações da mídia ou None
        """
        
        # Extrai título do conteúdo
        extracted_title, year = self.extract_title_from_content(
            f"{post_title} {post_content}", post_tags
        )
        
        search_queries = []
        
        # Adiciona título extraído
        if extracted_title:
            search_queries.append(extracted_title)
        
        # Adiciona tags relevantes
        for tag in post_tags[:3]:  # Limita a 3 tags principais
            if len(tag) > 3:
                search_queries.append(tag)
        
        # Adiciona palavras do título do post
        title_words = post_title.split()
        if len(title_words) >= 2:
            search_queries.append(" ".join(title_words[:3]))
        
        # Tenta cada query até encontrar algo
        for query in search_queries:
            self.logger.info(f"Tentando busca com: '{query}'")
            
            if is_movie:
                result = self.search_movie(query, year)
                if result:
                    details = self.get_movie_details(result['id'])
                    if details:
                        return self._format_movie_data(details)
            else:
                result = self.search_tv_show(query, year)
                if result:
                    details = self.get_tv_details(result['id'])
                    if details:
                        return self._format_tv_data(details)
        
        self.logger.warning("Nenhuma mídia encontrada para o post")
        return None
    
    def _format_movie_data(self, movie_details: Dict) -> Dict:
        """Formata dados do filme para uso no sistema"""
        videos = movie_details.get('videos', {}).get('results', [])
        trailer_url = self.extract_youtube_trailer(videos)
        
        return {
            'type': 'movie',
            'title': movie_details.get('title', ''),
            'original_title': movie_details.get('original_title', ''),
            'overview': movie_details.get('overview', ''),
            'release_date': movie_details.get('release_date', ''),
            'poster_url': self.build_image_url(movie_details.get('poster_path', '')),
            'backdrop_url': self.build_image_url(movie_details.get('backdrop_path', ''), 'w1280'),
            'trailer_url': trailer_url,
            'genres': [genre['name'] for genre in movie_details.get('genres', [])],
            'runtime': movie_details.get('runtime'),
            'vote_average': movie_details.get('vote_average'),
            'tmdb_id': movie_details.get('id')
        }
    
    def _format_tv_data(self, tv_details: Dict) -> Dict:
        """Formata dados da série para uso no sistema"""
        videos = tv_details.get('videos', {}).get('results', [])
        trailer_url = self.extract_youtube_trailer(videos)
        
        return {
            'type': 'tv',
            'title': tv_details.get('name', ''),
            'original_title': tv_details.get('original_name', ''),
            'overview': tv_details.get('overview', ''),
            'first_air_date': tv_details.get('first_air_date', ''),
            'poster_url': self.build_image_url(tv_details.get('poster_path', '')),
            'backdrop_url': self.build_image_url(tv_details.get('backdrop_path', ''), 'w1280'),
            'trailer_url': trailer_url,
            'genres': [genre['name'] for genre in tv_details.get('genres', [])],
            'number_of_seasons': tv_details.get('number_of_seasons'),
            'number_of_episodes': tv_details.get('number_of_episodes'),
            'vote_average': tv_details.get('vote_average'),
            'tmdb_id': tv_details.get('id')
        }
    
    def get_media_for_post(self, post_data: Dict) -> Optional[Dict]:
        """
        Método principal para obter mídia baseada nos dados do post
        
        Args:
            post_data: Dict com dados do post (title, content, tags, categories)
            
        Returns:
            Dict com dados da mídia ou None
        """
        categories = post_data.get('categories', [])
        is_movie = any(cat.get('id') == config.movie_category_id for cat in categories)
        is_series = any(cat.get('id') == config.series_category_id for cat in categories)
        
        if not (is_movie or is_series):
            self.logger.info("Post não é de filme nem série, pulando busca TMDB")
            return None
        
        tags = [tag.get('name', '') for tag in post_data.get('tags', [])]
        
        return self.search_media_from_post(
            post_data.get('title', {}).get('rendered', ''),
            post_data.get('content', {}).get('rendered', ''),
            tags,
            is_movie=is_movie
        )

# Instância global do cliente TMDB
tmdb_client = TMDBClient()
