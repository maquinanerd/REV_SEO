#!/usr/bin/env python3
"""
Dashboard web para WordPress SEO Optimizer
Interface de monitoramento em tempo real
"""

import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from config import config
from database import db
from seo_optimizer import seo_optimizer
from gemini_client import gemini_client

# Configuração do Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Configuração de logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/')
def dashboard():
    """Página principal do dashboard"""
    return render_template('dashboard.html')

@app.route('/api/status')
def api_status():
    """API endpoint para status do sistema"""
    try:
        status = seo_optimizer.get_system_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        logger.error(f"Erro ao obter status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/process-post', methods=['POST'])
def api_process_post():
    """API endpoint para processar um post específico"""
    try:
        data = request.get_json()
        post_url = data.get('url', '').strip()
        
        if not post_url:
            return jsonify({
                'success': False,
                'error': 'URL do post é obrigatória'
            }), 400
        
        logger.info(f"Processando post específico: {post_url}")
        result = seo_optimizer.process_post_by_url(post_url)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Erro ao processar post específico: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/statistics')
def api_statistics():
    """API endpoint para estatísticas detalhadas"""
    try:
        stats = db.get_statistics()
        quota_info = db.get_gemini_quota_info()
        
        # Estatísticas por período
        recent_logs = db.get_recent_logs(100)
        
        # Agrupa logs por data
        daily_stats = {}
        for log in recent_logs:
            date = log['created_at'][:10]  # YYYY-MM-DD
            if date not in daily_stats:
                daily_stats[date] = {'success': 0, 'error': 0}
            daily_stats[date][log['status']] += 1
        
        return jsonify({
            'success': True,
            'data': {
                'general': stats,
                'quota': quota_info,
                'daily_stats': daily_stats,
                'total_api_keys': len(config.gemini_api_keys)
            }
        })
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/logs')
def api_logs():
    """API endpoint para logs recentes"""
    try:
        limit = int(request.args.get('limit', 50))
        logs = db.get_recent_logs(limit)
        
        return jsonify({
            'success': True,
            'data': logs
        })
    except Exception as e:
        logger.error(f"Erro ao obter logs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/run-test')
def api_run_test():
    """API endpoint para executar teste manual"""
    try:
        logger.info("Executando teste manual via dashboard")
        result = seo_optimizer.run_once()
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        logger.error(f"Erro ao executar teste: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/reset-quota')
def api_reset_quota():
    """API endpoint para resetar quota do Gemini"""
    try:
        db.reset_gemini_quota()
        
        # Reinicializa cliente Gemini
        gemini_client.current_key_index = 0
        gemini_client.initialize_client()
        
        logger.info("Quota do Gemini resetada via dashboard")
        
        return jsonify({
            'success': True,
            'message': 'Quota resetada com sucesso'
        })
    except Exception as e:
        logger.error(f"Erro ao resetar quota: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/config')
def api_config():
    """API endpoint para informações de configuração"""
    try:
        config_info = {
            'wordpress_url': config.wordpress_url,
            'wordpress_username': config.wordpress_username,
            'target_author_id': config.target_author_id,  # Posts do João (ID 6)
            'editor_author_id': config.editor_author_id,  # Você editando (ID 9)
            'movie_category_id': config.movie_category_id,
            'series_category_id': config.series_category_id,
            'max_posts_per_cycle': config.max_posts_per_cycle,
            'check_interval_minutes': config.check_interval_minutes,
            'gemini_keys_count': len(config.gemini_api_keys),
            'tmdb_configured': bool(config.tmdb_api_key)
        }
        
        return jsonify({
            'success': True,
            'data': config_info
        })
    except Exception as e:
        logger.error(f"Erro ao obter configuração: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint não encontrado'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Erro interno do servidor'
    }), 500

def main():
    """Função principal do dashboard"""
    print("🌐 WordPress SEO Optimizer - Dashboard Web")
    print("="*50)
    print(f"📍 Acesse: http://localhost:{5000}")
    print(f"⚙️  WordPress: {config.wordpress_url}")
    print(f"🤖 Gemini APIs: {len(config.gemini_api_keys)} chaves configuradas")
    print(f"🎬 TMDB: {'Configurado' if config.tmdb_api_key else 'Não configurado'}")
    print("="*50)
    print("💡 Para executar otimização: python main.py")
    print("🛑 Para parar: Ctrl+C")
    print("="*50)
    
    # Inicia servidor Flask
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False  # Evita problemas com múltiplas instâncias
    )

if __name__ == "__main__":
    main()
