import json
import logging
import time
import random
from typing import Dict, List, Optional, Tuple
import google.generativeai as genai
from config import config
from database import db

class GeminiClient:
    """Cliente para integração com Google Gemini AI"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_keys = config.gemini_api_keys
        self.current_key_index = db.get_gemini_quota_info().get('api_key_index', 0)
        self.client = None
        self.initialize_client()
    
    def initialize_client(self):
        """Inicializa o cliente Gemini com a chave atual"""
        try:
            current_key = self.api_keys[self.current_key_index]
            genai.configure(api_key=current_key)
            self.client = genai.GenerativeModel("gemini-1.5-flash")
            self.logger.info(f"Cliente Gemini inicializado com chave {self.current_key_index + 1}")
        except Exception as e:
            self.logger.error(f"Erro ao inicializar cliente Gemini: {e}")
            raise
    
    def switch_api_key(self):
        """Alterna para a próxima chave API disponível"""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        db.update_gemini_quota(self.current_key_index, 0, False)
        self.initialize_client()
        self.logger.info(f"Alternado para chave API {self.current_key_index + 1}")
    
    def _format_media_data(self, media_data: Optional[Dict]) -> str:
        """Formata dados de mídia para o prompt"""
        if not media_data:
            return "Nenhuma mídia encontrada"
        
        formatted = []
        
        if media_data.get('poster_url'):
            formatted.append(f"**Poster:** {media_data['poster_url']}")
        
        if media_data.get('backdrop_url'):
            formatted.append(f"**Backdrop:** {media_data['backdrop_url']}")
        
        if media_data.get('trailer_url'):
            formatted.append(f"**Trailer YouTube:** {media_data['trailer_url']}")
        
        if media_data.get('overview'):
            formatted.append(f"**Sinopse TMDB:** {media_data['overview']}")
        
        return "\n".join(formatted) if formatted else "Mídia encontrada mas sem detalhes"
    
    def create_seo_prompt(self, title: str, excerpt: str, content: str, 
                         tags_text: str, media_data: Optional[Dict] = None) -> str:
        """Cria o prompt otimizado para SEO jornalístico"""
        
        domain = config.wordpress_domain.rstrip('/')
        
        prompt = f"""Você é um jornalista digital especializado em cultura pop, cinema e séries, com experiência em otimização para Google News e SEO técnico. Sua tarefa é revisar e otimizar o conteúdo abaixo sem alterar o sentido original, aprimorando sua estrutura, legibilidade e potencial de ranqueamento.

✅ Diretrizes obrigatórias para otimização:

**Título:**
- Reescreva o título original tornando-o mais atrativo e claro.
- Inclua palavras-chave relevantes para melhorar o SEO.
- Mantenha foco no tema, sem clickbait exagerado.
- ⚠️ IMPORTANTE: O título deve ser APENAS TEXTO PURO, sem HTML, tags ou formatação.
- Não use <b>, <a>, <i>, <span> ou qualquer tag HTML no título.
- O título será usado em meta tags, RSS feeds e Google News onde HTML causa erros.

**Resumo (Excerpt):**
- Reescreva o resumo para ser mais chamativo e informativo.
- Foque em engajamento e performance nos resultados do Google News.

**Conteúdo:**
- Reestruture os parágrafos longos em blocos mais curtos e escaneáveis.
- ⚠️ IMPORTANTE: Envolva cada parágrafo individualmente com a tag HTML <p>. Exemplo: <p>Primeiro parágrafo.</p><p>Segundo parágrafo.</p>
- Não use <br> para criar parágrafos.
- Mantenha o tom jornalístico e objetivo.
- Não altere o sentido da informação.

**Negrito:**
- Destaque os termos mais relevantes usando apenas a tag HTML <b>.
- Ex: nomes de filmes, personagens, diretores, plataformas, datas, eventos.

**Links internos:**
- Baseando-se nas tags fornecidas, insira links internos usando a estrutura:
  <a href="{domain}/tag/NOME-DA-TAG">Texto âncora</a>
- Quando possível, aplique negrito combinado com link:
  <b><a href="{domain}/tag/stranger-things">Stranger Things</a></b>

**Mídia (quando disponível):**
- Imagens:
  <img src="URL_DA_IMAGEM" alt="Descrição da imagem" style="width:100%;max-width:500px;height:auto;margin:10px 0;">
- Trailers (YouTube) — Responsivo (sem fixar tamanho):
  <iframe src="https://www.youtube.com/embed/ID_DO_VIDEO" frameborder="0" allowfullscreen style="width:100%;aspect-ratio:16/9;margin:10px 0;"></iframe>

⚠️ **Regras Técnicas:**
- Use somente HTML puro: <b>, <a>, <img>, <iframe>.
- Não utilize Markdown (**texto** ou [link](url)).
- Não adicione informações novas que não estejam no texto original ou na mídia fornecida.
- Utilize o conteúdo do campo Tags para decidir onde inserir links internos relevantes.

🔽 **DADOS DISPONÍVEIS PARA OTIMIZAÇÃO**

**Mídia (imagens e trailer):**
{self._format_media_data(media_data)}

**Conteúdo original:**

**Título:** {title}

**Resumo:** {excerpt}

**Tags disponíveis:** {tags_text}

**Conteúdo:**
{content}

📤 **FORMATO DA RESPOSTA (obrigatório)**
Responda exatamente no seguinte formato:

## Novo Título:
(título otimizado)

## Novo Resumo:
(resumo otimizado)

## Novo Conteúdo:
(conteúdo reestruturado com parágrafos curtos, <b>negrito</b> e <a href="">links internos</a>)

## SEO Score:
(Nota de 0 a 100 avaliando: uso de palavras-chave, legibilidade, estrutura e escaneabilidade)
"""
        return prompt
    
    def optimize_content(self, title: str, excerpt: str, content: str, 
                        tags_text: str, media_data: Optional[Dict] = None,
                        max_retries: int = 3) -> Optional[Dict]:
        """
        Otimiza conteúdo usando Gemini AI com retry e alternância de chaves
        
        Returns:
            Dict com: {
                'title': str,
                'excerpt': str, 
                'content': str,
                'seo_score': int
            }
        """
        
        prompt = self.create_seo_prompt(title, excerpt, content, tags_text, media_data)
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Tentativa {attempt + 1} de otimização com Gemini")
                
                # Faz a requisição para o Gemini
                response = self.client.generate_content(prompt)
                
                if not response.text:
                    raise ValueError("Resposta vazia do Gemini")
                
                # Atualiza contador de requisições
                quota_info = db.get_gemini_quota_info()
                requests_made = quota_info.get('requests_made', 0) + 1
                db.update_gemini_quota(self.current_key_index, requests_made, False)
                
                # Processa a resposta
                optimized_content = self._parse_gemini_response(response.text)
                
                if optimized_content:
                    self.logger.info("Conteúdo otimizado com sucesso pelo Gemini")
                    return optimized_content
                else:
                    raise ValueError("Erro ao processar resposta do Gemini")
                
            except Exception as e:
                self.logger.warning(f"Tentativa {attempt + 1} falhou: {e}")
                
                error_str = str(e).lower()
                is_api_key_error = "quota" in error_str or "rate limit" in error_str or "api key not valid" in error_str

                # Se erro de quota ou chave inválida, tenta a próxima chave
                if is_api_key_error:
                    if len(self.api_keys) > 1:
                        self.logger.info("Erro de API (quota/inválida), alternando para a próxima chave...")
                        db.update_gemini_quota(self.current_key_index, 999999, True)
                        self.switch_api_key()
                        continue  # Tenta novamente com a nova chave
                    else:
                        self.logger.error("Erro de API e apenas uma chave disponível. Abortando.")
                        db.update_gemini_quota(self.current_key_index, 999999, True)
                        return None # Aborta se não há mais chaves
                
                # Backoff exponencial
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    self.logger.info(f"Aguardando {wait_time:.2f}s antes da próxima tentativa")
                    time.sleep(wait_time)
        
        self.logger.error("Todas as tentativas de otimização falharam")
        return None
    
    def _strip_html_from_title(self, title: str) -> str:
        """Remove qualquer HTML do título para garantir texto puro"""
        import re
        # Remove todas as tags HTML
        clean_title = re.sub(r'<[^>]+>', '', title)
        # Remove múltiplos espaços
        clean_title = re.sub(r'\s+', ' ', clean_title)
        return clean_title.strip()

    def _parse_gemini_response(self, response_text: str) -> Optional[Dict]:
        """Faz parse da resposta estruturada do Gemini"""
        try:
            lines = response_text.strip().split('\n')
            result = {}
            current_section = None
            current_content = []
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('## Novo Título:'):
                    if current_section:
                        result[current_section] = '\n'.join(current_content).strip()
                    current_section = 'title'
                    title_text = line.replace('## Novo Título:', '').strip()
                    # Remove qualquer HTML do título
                    title_text = self._strip_html_from_title(title_text)
                    current_content = [title_text]
                
                elif line.startswith('## Novo Resumo:'):
                    if current_section:
                        result[current_section] = '\n'.join(current_content).strip()
                    current_section = 'excerpt'
                    current_content = [line.replace('## Novo Resumo:', '').strip()]
                
                elif line.startswith('## Novo Conteúdo:'):
                    if current_section:
                        result[current_section] = '\n'.join(current_content).strip()
                    current_section = 'content'
                    current_content = [line.replace('## Novo Conteúdo:', '').strip()]
                
                elif line.startswith('## SEO Score:'):
                    if current_section:
                        result[current_section] = '\n'.join(current_content).strip()
                    current_section = 'seo_score'
                    score_text = line.replace('## SEO Score:', '').strip()
                    # Extrai apenas números do score
                    import re
                    score_match = re.search(r'\d+', score_text)
                    result['seo_score'] = int(score_match.group()) if score_match else 0
                    current_content = []
                
                elif current_section and line:
                    current_content.append(line)
            
            # Adiciona a última seção
            if current_section and current_section != 'seo_score':
                result[current_section] = '\n'.join(current_content).strip()
            
            # Valida se todas as seções necessárias estão presentes
            required_fields = ['title', 'excerpt', 'content']
            if all(field in result and result[field] for field in required_fields):
                self.logger.info("Resposta do Gemini parseada com sucesso")
                return result
            else:
                missing = [field for field in required_fields if field not in result]
                self.logger.error(f"Campos faltando na resposta: {missing}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao fazer parse da resposta do Gemini: {e}")
            return None
    
    def get_quota_status(self) -> Dict:
        """Retorna status atual da quota"""
        quota_info = db.get_gemini_quota_info()
        return {
            'current_key_index': self.current_key_index,
            'total_keys': len(self.api_keys),
            'requests_made': quota_info.get('requests_made', 0),
            'quota_exceeded': quota_info.get('quota_exceeded', False),
            'last_reset': quota_info.get('last_reset_date')
        }

# Instância global do cliente Gemini
gemini_client = GeminiClient()
