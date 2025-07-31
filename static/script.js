/**
 * WordPress SEO Optimizer - Dashboard JavaScript
 * Gerencia a interface do dashboard em tempo real
 */

class SEODashboard {
    constructor() {
        this.refreshInterval = null;
        this.chart = null;
        this.init();
    }

    init() {
        console.log('🚀 Inicializando WordPress SEO Optimizer Dashboard');
        
        // Bind event listeners
        this.bindEvents();
        
        // Initial data load
        this.loadAllData();
        
        // Start auto-refresh
        this.startAutoRefresh();
    }

    bindEvents() {
        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.loadAllData();
        });

        // Test execution button
        document.getElementById('testBtn').addEventListener('click', () => {
            this.runTest();
        });

        // Reset quota button
        document.getElementById('resetQuotaBtn').addEventListener('click', () => {
            this.resetQuota();
        });

        // Log limit selector
        document.getElementById('logLimit').addEventListener('change', (e) => {
            this.loadLogs(parseInt(e.target.value));
        });
    }

    async loadAllData() {
        console.log('📊 Carregando dados do dashboard...');
        
        // Show loading states
        this.showLoadingStates();
        
        try {
            // Load data in parallel
            await Promise.all([
                this.loadSystemStatus(),
                this.loadStatistics(),
                this.loadConfiguration(),
                this.loadLogs()
            ]);
            
            console.log('✅ Dados carregados com sucesso');
        } catch (error) {
            console.error('❌ Erro ao carregar dados:', error);
            this.showError('Erro ao carregar dados do dashboard');
        }
    }

    async loadSystemStatus() {
        try {
            const response = await fetch('/api/status');
            const result = await response.json();
            
            if (result.success) {
                this.updateSystemStatus(result.data);
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Erro ao carregar status:', error);
            this.updateSystemStatus(null);
        }
    }

    async loadStatistics() {
        try {
            const response = await fetch('/api/statistics');
            const result = await response.json();
            
            if (result.success) {
                this.updateStatistics(result.data);
                this.updateChart(result.data.daily_stats);
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Erro ao carregar estatísticas:', error);
        }
    }

    async loadConfiguration() {
        try {
            const response = await fetch('/api/config');
            const result = await response.json();
            
            if (result.success) {
                this.updateConfiguration(result.data);
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Erro ao carregar configuração:', error);
        }
    }

    async loadLogs(limit = 50) {
        try {
            const response = await fetch(`/api/logs?limit=${limit}`);
            const result = await response.json();
            
            if (result.success) {
                this.updateLogs(result.data);
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Erro ao carregar logs:', error);
            this.updateLogs([]);
        }
    }

    updateSystemStatus(data) {
        const statusIcon = document.getElementById('systemStatusIcon');
        const statusText = document.getElementById('systemStatus');
        const lastUpdate = document.getElementById('lastUpdate');
        const wordpressStatus = document.getElementById('wordpressStatus');
        const geminiStatus = document.getElementById('geminiStatus');
        const geminiQuota = document.getElementById('geminiQuota');
        const tmdbStatus = document.getElementById('tmdbStatus');

        if (!data) {
            statusIcon.innerHTML = '<i class="fas fa-exclamation-triangle fa-2x text-danger"></i>';
            statusText.textContent = 'Erro de Conexão';
            lastUpdate.textContent = new Date().toLocaleTimeString();
            wordpressStatus.textContent = 'Desconectado';
            geminiStatus.textContent = 'Erro';
            tmdbStatus.textContent = 'Erro';
            return;
        }

        // System health
        if (data.system_healthy) {
            statusIcon.innerHTML = '<i class="fas fa-check-circle fa-2x text-success"></i>';
            statusText.textContent = 'Sistema Operacional';
        } else {
            statusIcon.innerHTML = '<i class="fas fa-exclamation-circle fa-2x text-warning"></i>';
            statusText.textContent = 'Atenção Necessária';
        }

        // WordPress status
        wordpressStatus.textContent = data.wordpress_connected ? 'Conectado' : 'Desconectado';
        wordpressStatus.className = data.wordpress_connected ? 'card-text text-success' : 'card-text text-danger';

        // Gemini status
        const quotaInfo = data.gemini_quota || {};
        if (quotaInfo.quota_exceeded) {
            geminiStatus.textContent = 'Quota Excedida';
            geminiStatus.className = 'card-text text-danger';
            geminiQuota.textContent = `Chave ${quotaInfo.current_key_index + 1}/${quotaInfo.total_keys}`;
        } else {
            geminiStatus.textContent = 'Operacional';
            geminiStatus.className = 'card-text text-success';
            geminiQuota.textContent = `${quotaInfo.requests_made || 0} requisições`;
        }

        // TMDB status (sempre operacional se configurado)
        tmdbStatus.textContent = 'Configurado';
        tmdbStatus.className = 'card-text text-success';

        // Last update
        lastUpdate.textContent = new Date().toLocaleTimeString();
    }

    updateStatistics(data) {
        const general = data.general || {};
        
        // Update numeric statistics
        document.getElementById('totalProcessed').textContent = general.total_processed || 0;
        document.getElementById('todayProcessed').textContent = general.today_processed || 0;
        document.getElementById('todayErrors').textContent = general.today_errors || 0;
        
        // Last processed post ID from system status
        const lastPostElement = document.getElementById('lastPostId');
        if (lastPostElement) {
            lastPostElement.textContent = data.last_processed_post_id || 0;
        }
    }

    updateConfiguration(data) {
        const configContainer = document.getElementById('configInfo');
        
        const configHtml = `
            <div class="config-item">
                <span class="config-label">WordPress:</span>
                <span class="config-value">${this.truncateUrl(data.wordpress_url)}</span>
            </div>
            <div class="config-item">
                <span class="config-label">Usuário:</span>
                <span class="config-value">${data.wordpress_username}</span>
            </div>
            <div class="config-item">
                <span class="config-label">Autor ID:</span>
                <span class="config-value">${data.author_id}</span>
            </div>
            <div class="config-item">
                <span class="config-label">Posts/Ciclo:</span>
                <span class="config-value">${data.max_posts_per_cycle}</span>
            </div>
            <div class="config-item">
                <span class="config-label">Intervalo:</span>
                <span class="config-value">${data.check_interval_minutes}min</span>
            </div>
            <div class="config-item">
                <span class="config-label">Gemini APIs:</span>
                <span class="config-value">${data.gemini_keys_count} chaves</span>
            </div>
            <div class="config-item">
                <span class="config-label">TMDB:</span>
                <span class="config-value">${data.tmdb_configured ? 'Configurado' : 'Não configurado'}</span>
            </div>
        `;
        
        configContainer.innerHTML = configHtml;
    }

    updateLogs(logs) {
        const container = document.getElementById('logsContainer');
        
        if (!logs || logs.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-inbox fa-2x mb-2"></i>
                    <p>Nenhum log encontrado</p>
                </div>
            `;
            return;
        }

        const tableHtml = `
            <div class="table-responsive logs-container">
                <table class="table table-hover logs-table">
                    <thead>
                        <tr>
                            <th>Data/Hora</th>
                            <th>Post</th>
                            <th>Ação</th>
                            <th>Status</th>
                            <th>Tempo</th>
                            <th>Detalhes</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${logs.map(log => this.renderLogRow(log)).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        container.innerHTML = tableHtml;
    }

    renderLogRow(log) {
        const date = new Date(log.created_at);
        const timeString = date.toLocaleString('pt-BR');
        const processingTime = log.processing_time ? `${log.processing_time.toFixed(2)}s` : '-';
        
        const statusClass = log.status === 'success' ? 'status-success' : 
                           log.status === 'error' ? 'status-error' : 'status-warning';
        
        const statusIcon = log.status === 'success' ? 'fa-check' : 
                          log.status === 'error' ? 'fa-times' : 'fa-exclamation';

        return `
            <tr class="fade-in">
                <td>${timeString}</td>
                <td>
                    <strong>ID ${log.post_id}</strong><br>
                    <small class="text-muted">${this.truncateText(log.post_title, 30)}</small>
                </td>
                <td>
                    <span class="badge bg-secondary">${log.action}</span>
                </td>
                <td>
                    <span class="status-badge ${statusClass}">
                        <i class="fas ${statusIcon} me-1"></i>
                        ${log.status}
                    </span>
                </td>
                <td>${processingTime}</td>
                <td>
                    <small class="text-muted">${this.truncateText(log.details, 50)}</small>
                </td>
            </tr>
        `;
    }

    updateChart(dailyStats) {
        const ctx = document.getElementById('processingChart');
        if (!ctx) return;

        // Prepare data for last 7 days
        const last7Days = this.getLast7Days();
        const successData = [];
        const errorData = [];

        last7Days.forEach(date => {
            const stats = dailyStats[date] || { success: 0, error: 0 };
            successData.push(stats.success);
            errorData.push(stats.error);
        });

        // Destroy existing chart
        if (this.chart) {
            this.chart.destroy();
        }

        // Create new chart
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: last7Days.map(date => {
                    const d = new Date(date);
                    return d.toLocaleDateString('pt-BR', { month: '2-digit', day: '2-digit' });
                }),
                datasets: [
                    {
                        label: 'Sucessos',
                        data: successData,
                        borderColor: 'rgb(34, 197, 94)',
                        backgroundColor: 'rgba(34, 197, 94, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Erros',
                        data: errorData,
                        borderColor: 'rgb(239, 68, 68)',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Processamento dos Últimos 7 Dias'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }

    async runTest() {
        const testBtn = document.getElementById('testBtn');
        const originalText = testBtn.innerHTML;
        
        testBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Executando...';
        testBtn.disabled = true;

        try {
            const response = await fetch('/api/run-test');
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('Teste executado com sucesso!');
                
                // Show test results
                const data = result.data;
                const message = `
                    Posts encontrados: ${data.posts_found}<br>
                    Posts processados: ${data.posts_processed}<br>
                    Sucessos: ${data.posts_success}<br>
                    Erros: ${data.posts_error}<br>
                    Tempo: ${data.processing_time?.toFixed(2)}s
                `;
                
                this.showInfo('Resultados do Teste', message);
                
                // Refresh data after test
                setTimeout(() => this.loadAllData(), 2000);
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Erro no teste:', error);
            this.showError(`Erro ao executar teste: ${error.message}`);
        } finally {
            testBtn.innerHTML = originalText;
            testBtn.disabled = false;
        }
    }

    async resetQuota() {
        const resetBtn = document.getElementById('resetQuotaBtn');
        const original = resetBtn.innerHTML;
        
        resetBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Resetando...';
        resetBtn.disabled = true;

        try {
            const response = await fetch('/api/reset-quota');
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('Quota do Gemini resetada!');
                this.loadSystemStatus(); // Refresh status
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Erro ao resetar quota:', error);
            this.showError(`Erro ao resetar quota: ${error.message}`);
        } finally {
            resetBtn.innerHTML = original;
            resetBtn.disabled = false;
        }
    }

    showLoadingStates() {
        // System status
        const statusIcon = document.getElementById('systemStatusIcon');
        statusIcon.innerHTML = '<i class="fas fa-circle-notch fa-spin fa-2x text-warning"></i>';
        
        document.getElementById('systemStatus').textContent = 'Carregando...';
        document.getElementById('wordpressStatus').textContent = 'Verificando...';
        document.getElementById('geminiStatus').textContent = 'Verificando...';
        document.getElementById('tmdbStatus').textContent = 'Verificando...';
        
        // Statistics
        document.getElementById('totalProcessed').textContent = '-';
        document.getElementById('todayProcessed').textContent = '-';
        document.getElementById('todayErrors').textContent = '-';
        document.getElementById('lastPostId').textContent = '-';
    }

    startAutoRefresh() {
        // Refresh every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.loadSystemStatus();
            this.loadStatistics();
        }, 30000);
        
        console.log('🔄 Auto-refresh ativado (30 segundos)');
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    // Utility methods
    truncateText(text, maxLength) {
        if (!text) return 'N/A';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }

    truncateUrl(url) {
        if (!url) return 'N/A';
        try {
            const urlObj = new URL(url);
            return urlObj.hostname;
        } catch {
            return url.length > 20 ? url.substring(0, 20) + '...' : url;
        }
    }

    getLast7Days() {
        const days = [];
        for (let i = 6; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            days.push(date.toISOString().split('T')[0]);
        }
        return days;
    }

    // Toast notification methods
    showSuccess(message) {
        this.showToast(message, 'success');
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    showInfo(title, message) {
        this.showToast(`<strong>${title}</strong><br>${message}`, 'info');
    }

    showToast(message, type = 'info') {
        // Create toast container if it doesn't exist
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }

        // Create toast
        const toastId = 'toast-' + Date.now();
        const toastHtml = `
            <div id="${toastId}" class="toast toast-${type}" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header">
                    <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
                    <strong class="me-auto">SEO Optimizer</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;

        container.insertAdjacentHTML('beforeend', toastHtml);

        // Show toast
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: 5000 });
        toast.show();

        // Remove from DOM after hiding
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SEODashboard();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        console.log('📱 Página oculta, pausando atualizações');
    } else {
        console.log('📱 Página visível, retomando atualizações');
        // Refresh immediately when page becomes visible
        if (window.dashboard) {
            window.dashboard.loadAllData();
        }
    }
});

// Global error handler
window.addEventListener('error', (event) => {
    console.error('❌ Erro global capturado:', event.error);
});

// Expose dashboard globally for debugging
window.dashboard = null;
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new SEODashboard();
});
