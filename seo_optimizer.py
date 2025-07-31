import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
from config import config
from database import db
from wordpress_client import wordpress_client
from gemini_client import gemini_client
from tmdb_client import tmdb_client

class SEOOptimizer:
    """Classe principal que orquestra todo o processo de otimização SEO"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.target_author_id = config.target_author_id  # Posts do João (ID 6)
        self.editor_author_id = config.editor_author_id  # Você editando (ID 9)
        self.max_posts_per_cycle = config.max_posts_per_cycle
        
    def run_optimization_cycle(self) -> Dict:
        """
        Executa um ciclo completo de otimização
        
        Returns:
            Dict com estatísticas do ciclo
        """
        cycle_start = time.time()
        
        self.logger.info("=== INICIANDO CICLO DE OTIMIZAÇÃO SEO ===")
        
        stats = {
            'cycle_start': datetime.now().isoformat(),
            'posts_found': 0,
            'posts_processed': 0,
            'posts_success': 0,
            'posts_error': 0,
            'processing_time': 0,
            'errors': []
        }
        
        try:
            # 1. Testa conexão com WordPress
            if not wordpress_client.test_connection():
                raise Exception("Falha na conexão com WordPress")
            
            # 2. Busca posts novos
            new_posts = self._find_new_posts()
            stats['posts_found'] = len(new_posts)
            
            if not new_posts:
                self.logger.info("Nenhum post novo encontrado")
                stats['processing_time'] = time.time() - cycle_start
                return stats
            
            # 3. Processa posts (máximo por ciclo)
            posts_to_process = new_posts[:self.max_posts_per_cycle]
            stats['posts_processed'] = len(posts_to_process)
            
            for post in posts_to_process:
                try:
                    success = self._process_single_post(post)
                    if success:
                        stats['posts_success'] += 1
                    else:
                        stats['posts_error'] += 1
                        
                except Exception as e:
                    error_msg = f"Erro ao processar post {post['id']}: {e}"
                    self.logger.error(error_msg)
                    stats['errors'].append(error_msg)
                    stats['posts_error'] += 1
                    
                    # Log no banco
                    db.log_processing(
                        post['id'],
                        post.get('title', {}).get('rendered', 'N/A'),
                        'optimization',
                        'error',
                        str(e)
                    )
        
        except Exception as e:
            error_msg = f"Erro geral no ciclo de otimização: {e}"
            self.logger.error(error_msg)
            stats['errors'].append(error_msg)
        
        stats['processing_time'] = time.time() - cycle_start
        self.logger.info(f"=== CICLO CONCLUÍDO EM {stats['processing_time']:.2f}s ===")
        self.logger.info(f"Posts encontrados: {stats['posts_found']}")
        self.logger.info(f"Posts processados: {stats['posts_processed']}")
        self.logger.info(f"Sucessos: {stats['posts_success']}")
        self.logger.info(f"Erros: {stats['posts_error']}")
        
        return stats
    
    def _find_new_posts(self) -> List[Dict]:
        """Encontra posts novos para processar"""
        try:
            last_processed_id = db.get_last_processed_post_id()
            self.logger.info(f"Último post processado: {last_processed_id}")
            
            # Busca posts novos do autor alvo (João - ID 6)
            new_posts = wordpress_client.get_new_posts_since_id(
                self.target_author_id, 
                last_processed_id,
                per_page=20  # Busca mais posts para ter opções
            )
            
            # Filtra apenas posts otimizáveis (filmes/séries)
            optimizable_posts = []
            for post in new_posts:
                post_data = wordpress_client.get_post_full_data(post['id'])
                if post_data and wordpress_client.is_post_optimizable(post_data):
                    optimizable_posts.append(post_data)
                    self.logger.info(f"Post otimizável encontrado: {post['id']} - {post.get('title', {}).get('rendered', 'N/A')}")
                else:
                    self.logger.info(f"Post {post['id']} não é otimizável (não é filme/série)")
            
            return optimizable_posts
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar posts novos: {e}")
            return []
    
    def _process_single_post(self, post_data: Dict) -> bool:
        """
        Processa um único post
        
        Args:
            post_data: Dados completos do post
            
        Returns:
            True se processado com sucesso
        """
        post_id = post_data['id']
        post_title = post_data.get('title', {}).get('rendered', 'N/A')
        
        process_start = time.time()
        self.logger.info(f"--- Processando post {post_id}: {post_title} ---")
        
        try:
            # 1. Extrai dados do post
            title = post_data.get('title', {}).get('rendered', '')
            excerpt = post_data.get('excerpt', {}).get('rendered', '')
            content = post_data.get('content', {}).get('rendered', '')
            tags = post_data.get('tags', [])
            
            if not title or not content:
                raise ValueError("Post sem título ou conteúdo")
            
            # 2. Busca de mídia no TMDB desativada temporariamente
            self.logger.info("Busca de mídia no TMDB desativada para simplificar a otimização.")
            media_data = None
            
            # 3. Prepara tags para o prompt
            tags_text = ", ".join([tag.get('name', '') for tag in tags])
            if not tags_text:
                tags_text = "Nenhuma tag disponível"
            
            # 4. Otimiza conteúdo com Gemini
            self.logger.info("Otimizando conteúdo com Gemini...")
            optimized_data = gemini_client.optimize_content(
                title, excerpt, content, tags_text
            )
            
            if not optimized_data:
                raise ValueError("Falha na otimização com Gemini")
            
            # 5. Atualiza post no WordPress
            self.logger.info("Atualizando post no WordPress...")
            update_success = wordpress_client.update_post_complete(post_id, optimized_data)
            
            if not update_success:
                raise ValueError("Falha ao atualizar post no WordPress")
            
            # 6. Registra sucesso
            processing_time = time.time() - process_start
            
            db.log_processing(
                post_id,
                post_title,
                'optimization',
                'success',
                f"SEO Score: {optimized_data.get('seo_score', 'N/A')}",
                processing_time
            )
            
            # Atualiza último post processado
            db.update_last_processed_post_id(post_id)
            
            self.logger.info(f"Post {post_id} otimizado com sucesso em {processing_time:.2f}s")
            self.logger.info(f"SEO Score: {optimized_data.get('seo_score', 'N/A')}")
            
            return True
            
        except Exception as e:
            processing_time = time.time() - process_start
            self.logger.error(f"Erro ao processar post {post_id}: {e}")
            
            db.log_processing(
                post_id,
                post_title,
                'optimization',
                'error',
                str(e),
                processing_time
            )
            
            return False
    
    def get_system_status(self) -> Dict:
        """Retorna status atual do sistema"""
        try:
            stats = db.get_statistics()
            quota_status = gemini_client.get_quota_status()
            
            # Testa conexões
            wp_connected = wordpress_client.test_connection()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'wordpress_connected': wp_connected,
                'gemini_quota': quota_status,
                'statistics': stats,
                'last_processed_post_id': db.get_last_processed_post_id(),
                'system_healthy': wp_connected and not quota_status.get('quota_exceeded', False)
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter status do sistema: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'system_healthy': False
            }
    
    def run_once(self) -> Dict:
        """Executa otimização uma única vez (modo teste)"""
        self.logger.info("Executando otimização em modo TESTE (uma vez apenas)")
        return self.run_optimization_cycle()
    
    def process_post_by_url(self, post_url: str) -> Dict:
        """
        Processa um post específico pela URL
        
        Args:
            post_url: URL do post a ser processado
            
        Returns:
            Dict com resultado do processamento
        """
        process_start = time.time()
        
        self.logger.info(f"=== PROCESSANDO POST ESPECÍFICO: {post_url} ===")
        
        result = {
            'url': post_url,
            'success': False,
            'error': None,
            'processing_time': 0,
            'post_data': None
        }
        
        try:
            # 1. Testa conexão com WordPress
            self.logger.info("Etapa 1: Testando conexão com WordPress...")
            if not wordpress_client.test_connection():
                raise Exception("Falha na conexão com WordPress")
            self.logger.info("✅ Conexão com WordPress OK")
            
            # 2. Busca post pela URL
            self.logger.info("Etapa 2: Buscando post pela URL...")
            post_data = wordpress_client.get_post_by_url(post_url)
            if not post_data:
                raise Exception("Post não encontrado ou não acessível")
            
            self.logger.info(f"✅ Post encontrado: ID {post_data['id']}")
            
            result['post_data'] = {
                'id': post_data['id'],
                'title': post_data.get('title', {}).get('rendered', 'N/A'),
                'author': post_data.get('author', 'N/A')
            }
            
            # 3. Verifica se o post é otimizável
            self.logger.info("Etapa 3: Verificando se o post é otimizável...")
            if not wordpress_client.is_post_optimizable(post_data):
                # Vamos ver as categorias para debug
                categories = post_data.get('categories', [])
                cat_names = [cat.get('name', f'ID:{cat.get("id")}') for cat in categories]
                self.logger.warning(f"Post não é otimizável. Categorias: {cat_names}")
                raise Exception("Post não é otimizável (não é filme/série)")
            
            self.logger.info("✅ Post é otimizável")
            
            # 4. Processa o post
            self.logger.info("Etapa 4: Processando o post...")
            success = self._process_single_post(post_data)
            
            if success:
                result['success'] = True
                self.logger.info(f"✅ Post processado com sucesso!")
            else:
                raise Exception("Falha no processamento do post")
                
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"❌ Erro ao processar post: {error_msg}", exc_info=True)
            result['error'] = error_msg
        
        result['processing_time'] = time.time() - process_start
        self.logger.info(f"=== PROCESSAMENTO CONCLUÍDO EM {result['processing_time']:.2f}s ===")
        
        return result

# Instância global do otimizador
seo_optimizer = SEOOptimizer()
