#!/usr/bin/env python3
"""
WordPress SEO Optimizer - Sistema de otimização automática de posts
Autor: Sistema baseado nas especificações fornecidas
"""

import argparse
import schedule
import time
import logging
import signal
import sys
from datetime import datetime

from config import config
from seo_optimizer import seo_optimizer
from database import db

# Importa o app Flask do dashboard para compatibilidade com gunicorn
from dashboard import app

class SEOOptimizerApp:
    """Aplicação principal do WordPress SEO Optimizer"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = False
        
        # Configura handler para sinais de sistema
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handler para sinais de sistema (Ctrl+C, etc.)"""
        self.logger.info(f"Recebido sinal {signum}, encerrando...")
        self.running = False
    
    def run_once(self):
        """Executa otimização uma única vez"""
        self.logger.info("WordPress SEO Optimizer - Modo TESTE")
        self.logger.info("="*50)
        
        try:
            # Valida configuração
            self.logger.info("Validando configuração...")
            config.validate_config()
            
            # Executa ciclo de otimização
            result = seo_optimizer.run_once()
            
            # Exibe resultados
            self.logger.info("="*50)
            self.logger.info("RESULTADOS DO TESTE:")
            self.logger.info(f"Posts encontrados: {result.get('posts_found', 0)}")
            self.logger.info(f"Posts processados: {result.get('posts_processed', 0)}")
            self.logger.info(f"Sucessos: {result.get('posts_success', 0)}")
            self.logger.info(f"Erros: {result.get('posts_error', 0)}")
            self.logger.info(f"Tempo total: {result.get('processing_time', 0):.2f}s")
            
            if result.get('errors'):
                self.logger.error("ERROS ENCONTRADOS:")
                for error in result['errors']:
                    self.logger.error(f"  - {error}")
            
            if result.get('posts_success', 0) > 0:
                self.logger.info("Teste concluído com sucesso!")
            else:
                self.logger.warning("Teste concluído, mas nenhum post foi otimizado")
                
        except Exception as e:
            self.logger.error(f"Erro durante o teste: {e}")
            sys.exit(1)

    def show_stats(self):
        """Exibe as estatísticas do banco de dados e sai."""
        self.logger.info("Buscando estatísticas do banco de dados...")
        try:
            stats = db.get_statistics()
            quota_info = db.get_gemini_quota_info()
            last_post_id = db.get_last_processed_post_id()

            print("\n" + "="*50)
            print("📊 ESTATÍSTICAS - WordPress SEO Optimizer")
            print("="*50)
            print(f"Total de posts otimizados: {stats.get('total_processed', 0)}")
            print(f"Otimizados hoje: {stats.get('today_processed', 0)}")
            print(f"Erros hoje: {stats.get('today_errors', 0)}")
            print(f"ID do último post processado: {last_post_id}")
            if stats.get('last_processing'):
                last_proc_time = datetime.fromisoformat(stats['last_processing']).strftime('%d/%m/%Y %H:%M:%S')
                print(f"Última atividade registrada: {last_proc_time}")
            print("-"*50)
            print("🤖 Status da Quota Gemini")
            print(f"Índice da chave atual: {quota_info.get('api_key_index', 0)}")
            print(f"Requisições feitas (chave atual): {quota_info.get('requests_made', 0)}")
            print(f"Quota excedida: {'Sim' if quota_info.get('quota_exceeded') else 'Não'}")
            print("="*50 + "\n")
        except Exception as e:
            self.logger.error(f"Erro ao buscar estatísticas: {e}", exc_info=True)
            sys.exit(1)
    
    def run_continuous(self):
        """Executa otimização continuamente"""
        self.logger.info("WordPress SEO Optimizer - Modo PRODUÇÃO")
        self.logger.info("="*50)
        
        try:
            # Valida configuração
            self.logger.info("Validando configuração...")
            config.validate_config()
            
            # Configura agendamento
            interval_minutes = config.check_interval_minutes
            self.logger.info(f"Agendando execução a cada {interval_minutes} minutos")
            
            schedule.every(interval_minutes).minutes.do(self._scheduled_optimization)
            
            # Primeira execução imediata
            self.logger.info("Executando primeira otimização...")
            self._scheduled_optimization()
            
            self.running = True
            self.logger.info("Sistema iniciado! Pressione Ctrl+C para parar")
            self.logger.info(f"⏰ Próxima execução em {interval_minutes} minutos")
            
            # Loop principal
            while self.running:
                schedule.run_pending()
                time.sleep(30)  # Verifica a cada 30 segundos
                
        except Exception as e:
            self.logger.error(f"Erro durante execução contínua: {e}")
            sys.exit(1)
        
        self.logger.info("Sistema encerrado")
    
    def _scheduled_optimization(self):
        """Função chamada pelo agendador"""
        try:
            self.logger.info("Executando otimização agendada...")
            result = seo_optimizer.run_optimization_cycle()
            
            # Log resumido dos resultados
            self.logger.info(f"Resumo: {result.get('posts_success', 0)} sucessos, "
                           f"{result.get('posts_error', 0)} erros em "
                           f"{result.get('processing_time', 0):.2f}s")
            
            # Salva estatísticas no banco
            db.set_statistic('last_cycle_result', result)
            
            if result.get('posts_success', 0) > 0:
                next_run = datetime.now().strftime("%H:%M")
                self.logger.info(f"Otimização concluída. Próxima execução: {next_run}")
            
        except Exception as e:
            self.logger.error(f"Erro na otimização agendada: {e}")
            db.log_processing(0, "Sistema", "scheduled_optimization", "error", str(e))

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="WordPress SEO Optimizer - Otimização automática com IA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py --once     # Executa uma vez (teste)
  python main.py --stats    # Exibe estatísticas e sai
  python main.py           # Executa continuamente (produção)

Para acessar o painel web:
  python dashboard.py      # Em outro terminal
        """
    )
    
    parser.add_argument(
        '--once',
        action='store_true',
        help='Executa otimização apenas uma vez (modo teste)'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Exibe estatísticas de otimização e sai'
    )
    
    args = parser.parse_args()
    
    app = SEOOptimizerApp()
    
    if args.stats:
        app.show_stats()
    elif args.once:
        app.run_once()
    else:
        app.run_continuous()

if __name__ == "__main__":
    main()
