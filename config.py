import os
import logging
from typing import List, Optional
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

class Config:
    """Classe para gerenciar todas as configurações do sistema"""
    
    def __init__(self):
        self.setup_logging()
        self.validate_config()
    
    def setup_logging(self):
        """Configura o sistema de logging com fuso horário de Brasília (UTC-3)"""
        import logging
        from datetime import datetime, timezone, timedelta
        
        # Define o fuso horário de Brasília (UTC-3)
        brasilia_tz = timezone(timedelta(hours=-3))
        
        class BrasiliaFormatter(logging.Formatter):
            def formatTime(self, record, datefmt=None):
                dt = datetime.fromtimestamp(record.created, tz=brasilia_tz)
                if datefmt:
                    s = dt.strftime(datefmt)
                else:
                    s = dt.strftime('%Y-%m-%d %H:%M:%S')
                return s
        
        formatter = BrasiliaFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Remove handlers existentes para evitar duplicação
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Configura novos handlers com o formatter correto e encoding UTF-8
        file_handler = logging.FileHandler('seo_optimizer.log', encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        
        logging.basicConfig(
            level=logging.INFO,
            handlers=[file_handler, stream_handler]
        )
        self.logger = logging.getLogger(__name__)
    
    # WordPress Configuration
    @property
    def wordpress_url(self) -> str:
        return os.getenv("WORDPRESS_URL", "").rstrip('/')
    
    @property
    def wordpress_username(self) -> str:
        return os.getenv("WORDPRESS_USERNAME", "")
    
    @property
    def wordpress_password(self) -> str:
        return os.getenv("WORDPRESS_PASSWORD", "")
    
    @property
    def wordpress_domain(self) -> str:
        return os.getenv("WORDPRESS_DOMAIN", self.wordpress_url)
    
    # Gemini Configuration
    @property
    def gemini_api_keys(self) -> List[str]:
        """Retorna lista de todas as chaves Gemini disponíveis"""
        keys = []
        # Chave principal
        main_key = os.getenv("GEMINI_API_KEY")
        if main_key:
            keys.append(main_key)
        
        # Chaves alternativas
        for i in range(1, 10):  # Suporte para até 9 chaves adicionais
            key = os.getenv(f"GEMINI_API_KEY_{i}")
            if key:
                keys.append(key)
        
        return keys
    
    # TMDB Configuration
    @property
    def tmdb_api_key(self) -> str:
        return os.getenv("TMDB_API_KEY", "")
    
    @property
    def tmdb_read_token(self) -> str:
        return os.getenv("TMDB_READ_TOKEN", "")
    
    @property
    def tmdb_base_url(self) -> str:
        return os.getenv("TMDB_BASE_URL", "https://api.themoviedb.org/3")
    
    @property
    def tmdb_image_url(self) -> str:
        return os.getenv("TMDB_IMAGE_URL", "https://image.tmdb.org/t/p")
    
    # Rank Math Configuration
    @property
    def rank_math_api_key(self) -> str:
        return os.getenv("RANK_MATH_API_KEY", "")
    
    # Flask Configuration
    @property
    def session_secret(self) -> str:
        return os.getenv("SESSION_SECRET", "default_secret_key_for_development")
    
    # Sistema Configuration
    @property
    def target_author_id(self) -> int:
        """ID do autor cujos posts serão otimizados (João)"""
        return int(os.getenv("TARGET_AUTHOR_ID", "6"))
    
    @property
    def editor_author_id(self) -> int:
        """ID do autor que fará as edições (você)"""
        return int(os.getenv("EDITOR_AUTHOR_ID", "9"))
    
    @property
    def movie_category_id(self) -> int:
        """ID da categoria Filme"""
        return int(os.getenv("MOVIE_CATEGORY_ID", "24"))
    
    @property
    def series_category_id(self) -> int:
        """ID da categoria Série"""
        return int(os.getenv("SERIES_CATEGORY_ID", "21"))
    
    @property
    def max_posts_per_cycle(self) -> int:
        """Máximo de posts a processar por ciclo"""
        return int(os.getenv("MAX_POSTS_PER_CYCLE", "2"))
    
    @property
    def check_interval_minutes(self) -> int:
        """Intervalo entre verificações em minutos"""
        return int(os.getenv("CHECK_INTERVAL_MINUTES", "20"))
    
    @property
    def wordpress_fetch_limit(self) -> int:
        """Número de posts a buscar do WordPress por ciclo (para encontrar novos)"""
        return int(os.getenv("WORDPRESS_FETCH_LIMIT", "50"))
    
    def validate_config(self):
        """Valida se todas as configurações necessárias estão presentes"""
        errors = []
        
        if not self.wordpress_url:
            errors.append("WORDPRESS_URL não configurado")
        
        if not self.wordpress_username:
            errors.append("WORDPRESS_USERNAME não configurado")
        
        if not self.wordpress_password:
            errors.append("WORDPRESS_PASSWORD não configurado")
        
        if not self.gemini_api_keys:
            errors.append("Nenhuma GEMINI_API_KEY configurada")
        
        if not self.tmdb_api_key:
            errors.append("TMDB_API_KEY não configurado")
        
        if not self.rank_math_api_key or self.rank_math_api_key == "sua_chave_api_do_rank_math_aqui":
            self.logger.warning("RANK_MATH_API_KEY não configurado ou está com o valor padrão. A indexação instantânea será desativada.")
        
        if errors:
            error_msg = "Configurações faltando:\n" + "\n".join(f"- {error}" for error in errors)
            raise ValueError(error_msg)
        
        self.logger.info(f"Configuração validada com sucesso")
        self.logger.info(f"WordPress: {self.wordpress_url}")
        self.logger.info(f"Gemini API Keys: {len(self.gemini_api_keys)} chaves configuradas")
        self.logger.info(f"TMDB configurado: Sim")

# Instância global de configuração
config = Config()
