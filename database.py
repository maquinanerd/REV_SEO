import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

class Database:
    """Classe para gerenciar o banco de dados SQLite"""

    def __init__(self, db_path: str = "seo_dashboard.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.init_database()

    def init_database(self):
        """Inicializa as tabelas do banco de dados"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Tabela para controle de processamento
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processing_control (
                    id INTEGER PRIMARY KEY,
                    last_processed_post_id INTEGER,
                    last_processed_date TEXT,
                    total_posts_processed INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Tabela para logs de processamento
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processing_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER,
                    post_title TEXT,
                    action TEXT,
                    status TEXT,
                    details TEXT,
                    processing_time REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Tabela para controle de quota Gemini
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gemini_quota (
                    id INTEGER PRIMARY KEY,
                    api_key_index INTEGER DEFAULT 0,
                    requests_made INTEGER DEFAULT 0,
                    last_reset_date TEXT,
                    quota_exceeded BOOLEAN DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Tabela para estatísticas gerais
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY,
                    key TEXT UNIQUE,
                    value TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Inicializa registros padrão se não existirem
            cursor.execute('SELECT COUNT(*) FROM processing_control')
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO processing_control (last_processed_post_id, last_processed_date, total_posts_processed)
                    VALUES (0, ?, 0)
                ''', (datetime.now().isoformat(),))

            cursor.execute('SELECT COUNT(*) FROM gemini_quota')
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO gemini_quota (api_key_index, requests_made, last_reset_date, quota_exceeded)
                    VALUES (0, 0, ?, 0)
                ''', (datetime.now().isoformat(),))

            conn.commit()
            self.logger.info("Banco de dados inicializado com sucesso")

    @contextmanager
    def get_connection(self):
        """Context manager para conexões com o banco"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def get_last_processed_post_id(self) -> int:
        """Retorna o ID do último post processado"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT last_processed_post_id FROM processing_control WHERE id = 1')
            result = cursor.fetchone()
            return result[0] if result else 0

    def update_last_processed_post_id(self, post_id: int):
        """Atualiza o ID do último post processado"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE processing_control 
                SET last_processed_post_id = ?, 
                    last_processed_date = ?,
                    updated_at = ?,
                    total_posts_processed = total_posts_processed + 1
                WHERE id = 1
            ''', (post_id, datetime.now().isoformat(), datetime.now().isoformat()))
            conn.commit()
            self.logger.info(f"Último post processado atualizado para ID: {post_id}")

    def log_processing(self, post_id: int, post_title: str, action: str, 
                      status: str, details: str = "", processing_time: float = 0.0):
        """Registra log de processamento"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO processing_logs 
                (post_id, post_title, action, status, details, processing_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (post_id, post_title, action, status, details, processing_time))
            conn.commit()
            self.logger.info(f"Log registrado: {action} - {status} para post {post_id}")

    def get_recent_logs(self, limit: int = 50) -> List[Dict]:
        """Retorna logs recentes"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM processing_logs 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_gemini_quota_info(self) -> Dict:
        """Retorna informações sobre quota do Gemini"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM gemini_quota WHERE id = 1')
                result = cursor.fetchone()

                if result:
                    return {
                        'api_key_index': result['api_key_index'],
                        'requests_made': result['requests_made'],
                        'quota_exceeded': bool(result['quota_exceeded']),
                        'last_reset_date': result['last_reset_date']
                    }
                else:
                    return {
                        'api_key_index': 0,
                        'requests_made': 0,
                        'quota_exceeded': False,
                        'last_reset_date': None
                    }
        except Exception as e:
            self.logger.error(f"Erro ao obter quota do Gemini: {e}")
            return {
                'api_key_index': 0,
                'requests_made': 0,
                'quota_exceeded': False,
                'last_reset_date': None
            }

    def update_gemini_quota(self, api_key_index: int, requests_made: int, quota_exceeded: bool = False):
        """Atualiza informações de quota do Gemini"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE gemini_quota 
                SET api_key_index = ?, 
                    requests_made = ?, 
                    quota_exceeded = ?,
                    updated_at = ?
                WHERE id = 1
            ''', (api_key_index, requests_made, quota_exceeded, datetime.now().isoformat()))
            conn.commit()

    def reset_gemini_quota(self):
        """Reseta quota do Gemini (usado diariamente)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE gemini_quota 
                SET requests_made = 0, 
                    quota_exceeded = 0,
                    last_reset_date = ?,
                    updated_at = ?
                WHERE id = 1
            ''', (datetime.now().isoformat(), datetime.now().isoformat()))
            conn.commit()
            self.logger.info("Quota do Gemini resetada")

    def get_statistics(self) -> Dict:
        """Retorna estatísticas gerais do sistema"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Total de posts processados
                cursor.execute('SELECT COUNT(*) FROM processing_logs WHERE status = "success"')
                total_processed = cursor.fetchone()[0]

                # Posts processados hoje
                cursor.execute('''
                    SELECT COUNT(*) FROM processing_logs 
                    WHERE DATE(created_at) = DATE('now') AND status = 'success'
                ''')
                today_processed = cursor.fetchone()[0]

                # Posts com erro hoje
                cursor.execute('''
                    SELECT COUNT(*) FROM processing_logs 
                    WHERE DATE(created_at) = DATE('now') AND status = 'error'
                ''')
                today_errors = cursor.fetchone()[0]

                # Último processamento
                cursor.execute('''
                    SELECT created_at FROM processing_logs 
                    ORDER BY created_at DESC LIMIT 1
                ''')
                last_processing = cursor.fetchone()
                last_processing = last_processing[0] if last_processing else None

                return {
                    'total_processed': total_processed,
                    'today_processed': today_processed,
                    'today_errors': today_errors,
                    'last_processing': last_processing
                }
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas: {e}")
            return {
                'total_processed': 0,
                'today_processed': 0,
                'today_errors': 0,
                'last_processing': None
            }

    def set_statistic(self, key: str, value: Any):
        """Define uma estatística personalizada"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO statistics (key, value, updated_at)
                    VALUES (?, ?, ?)
                ''', (key, json.dumps(value), datetime.now().isoformat()))
                conn.commit()
                self.logger.info(f"Estatística definida: {key} = {value}")
        except Exception as e:
            self.logger.error(f"Erro ao definir estatística {key}: {e}")

    def get_statistic(self, key: str) -> Any:
        """Retorna uma estatística personalizada"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM statistics WHERE key = ?', (key,))
            result = cursor.fetchone()
            if result:
                try:
                    return json.loads(result[0])
                except json.JSONDecodeError:
                    return result[0]
            return None

    def get_processed_count_for_date(self, target_date: str) -> int:
        """
        Retorna o número de posts otimizados com sucesso em uma data específica.

        Args:
            target_date: A data no formato 'YYYY-MM-DD'.

        Returns:
            O número de posts otimizados.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM processing_logs 
                WHERE action = 'optimization' AND status = 'success' AND DATE(created_at) = ?
            ''', (target_date,))
            return cursor.fetchone()[0]

# Instância global do banco
db = Database()