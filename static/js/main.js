class LottoApp {
    constructor() {
        this.apiTimeout = 15000; // 15초
        this.retryCount = 0;
        this.maxRetries = 3;
        this.loadingStates = {
            aiPrediction: false,
            statistics: false,
            qrScan: false,
            health: false
        };
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.initLoadingStates();
        this.checkHealth(); // 앱 시작 시 헬스체크
    }
    
    initLoadingStates() {
        this.updateLoadingUI();
    }
    
    // 🔧 이벤트 바인딩
    bindEvents() {
        // AI 예상번호 생성 버튼
        const predictBtn = document.getElementById('predict-btn');
        if (predictBtn) {
            predictBtn.addEventListener('click', () => this.generatePrediction());
        }
        
        // 기타 버튼들 이벤트 바인딩
        const randomBtn = document.getElementById('random-btn');
        if (randomBtn) {
            randomBtn.addEventListener('click', () => this.generateRandomNumbers());
        }
        
        // 저장된 번호 불러오기
        const loadBtn = document.getElementById('load-saved-btn');
        if (loadBtn) {
            loadBtn.addEventListener('click', () => this.loadSavedNumbers());
        }
        
        // 통계 버튼
        const statsBtn = document.getElementById('stats-btn');
        if (statsBtn) {
            statsBtn.addEventListener('click', () => this.loadStatistics());
        }

        // 상태확인 버튼
        const healthBtn = document.getElementById('health-check-btn');
        if (healthBtn) {
            healthBtn.addEventListener('click', () => this.checkSystemHealth());
        }
    }
    
    // 🔧 헬스체크 메서드
    async checkHealth() {
        try {
            const response = await this.fetchWithTimeout('/api/health');
            console.log('Health check OK:', response);
            this.updateUI('system-status', '✅ 시스템 정상');
        } catch (error) {
            console.error('Health check failed:', error);
            this.updateUI('system-status', '⚠️ 시스템 점검 중');
        }
    }

    // 🔧 시스템 상태 확인 (전역에서 호출 가능)
    async checkSystemHealth() {
        if (this.loadingStates.health) return;
        
        this.setLoadingState('health', true);
        
        const healthModal = document.getElementById('healthModal');
        const healthResults = document.getElementById('health-results');
        
        if (healthModal && healthResults) {
            // 모달 표시
            const modal = new bootstrap.Modal(healthModal);
            modal.show();
            
            // 로딩 상태 표시
            healthResults.innerHTML = `
                <div class="text-center py-3">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">상태 확인 중...</span>
                    </div>
                    <p class="mt-2">시스템 상태를 확인하고 있습니다...</p>
                </div>
            `;
        }

        try {
            const response = await this.fetchWithTimeout('/api/health', {}, 5000);
            
            if (healthResults) {
                healthResults.innerHTML = `
                    <div class="row g-3">
                        <div class="col-md-6">
                            <div class="card border-success">
                                <div class="card-body">
                                    <h6 class="card-title text-success">
                                        <i class="fas fa-check-circle me-2"></i>서비스 상태
                                    </h6>
                                    <p class="card-text">${response.status || 'healthy'}</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="card border-info">
                                <div class="card-body">
                                    <h6 class="card-title text-info">
                                        <i class="fas fa-clock me-2"></i>응답 시간
                                    </h6>
                                    <p class="card-text">${response.timestamp ? '정상' : '측정 불가'}</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-12">
                            <div class="card border-primary">
                                <div class="card-body">
                                    <h6 class="card-title text-primary">
                                        <i class="fas fa-info-circle me-2"></i>시스템 정보
                                    </h6>
                                    <ul class="list-unstyled mb-0">
                                        <li><strong>버전:</strong> ${response.version || '2.1'}</li>
                                        <li><strong>상태:</strong> 정상 운영</li>
                                        <li><strong>마지막 업데이트:</strong> ${response.timestamp || new Date().toLocaleString()}</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Health check failed:', error);
            if (healthResults) {
                healthResults.innerHTML = `
                    <div class="alert alert-danger" role="alert">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        <strong>연결 오류</strong>
                        <p class="mb-2">${error.message}</p>
                        <button class="btn btn-danger btn-sm" onclick="window.lottoApp.checkSystemHealth()">
                            <i class="fas fa-redo me-2"></i>다시 시도
                        </button>
                    </div>
                `;
            }
        } finally {
            this.setLoadingState('health', false);
        }
    }
    
    async fetchWithTimeout(url, options = {}, timeout = this.apiTimeout) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);
        
        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            clearTimeout(timeoutId);
            
            if (error.name === 'AbortError') {
                throw new Error('요청 시간이 초과되었습니다. 다시 시도해주세요.');
            }
            throw error;
        }
    }
    
    async generatePrediction() {
        if (this.loadingStates.aiPrediction) return;
        
        this.setLoadingState('aiPrediction', true);
        this.showPredictionProgress(true);
        this.updateUI('prediction-status', 'AI가 분석 중입니다...');
        
        try {
            // 사용자 입력 번호 수집
            const userNumbers = this.getUserNumbers();
            
            // 진행률 업데이트
            this.updateProgress(33, 'AI 모델 분석 중...');
            
            try {
                const result = await this.fetchWithTimeout('/api/predict', {
                    method: 'POST',
                    body: JSON.stringify({ user_numbers: userNumbers })
                });
                
                if (result.error) {
                    throw new Error(result.message);
                }
                
                this.updateProgress(66, '결과 생성 중...');
                this.displayPredictions(result);
                
            } catch (apiError) {
                console.warn('API 호출 실패, 오프라인 모드로 전환:', apiError.message);
                
                // 오프라인 모드: 클라이언트에서 간단한 예측 생성
                const offlineResult = this.generateOfflinePrediction(userNumbers);
                this.updateProgress(66, '오프라인 모드로 결과 생성 중...');
                this.displayPredictions(offlineResult);
                
                // 사용자에게 오프라인 모드임을 알림
                this.showToast('서버 연결 문제로 오프라인 모드로 동작합니다.', 'warning');
            }
            
            this.retryCount = 0;
            this.updateProgress(100, '완료!');
            setTimeout(() => this.showPredictionProgress(false), 1000);
            
        } catch (error) {
            this.handleError(error, 'prediction');
            this.showPredictionProgress(false);
        } finally {
            this.setLoadingState('aiPrediction', false);
        }
    }
    
    // 오프라인 예측 생성 (API 실패 시 백업)
    generateOfflinePrediction(userNumbers = []) {
        const predictions = [];
        
        // 5개 세트 생성
        for (let i = 0; i < 5; i++) {
            const numbers = [...userNumbers];
            
            // 부족한 번호를 랜덤으로 채움
            while (numbers.length < 6) {
                const randomNum = Math.floor(Math.random() * 45) + 1;
                if (!numbers.includes(randomNum)) {
                    numbers.push(randomNum);
                }
            }
            
            predictions.push(numbers.sort((a, b) => a - b));
        }
        
        return {
            success: true,
            models: {
                '오프라인 모드': {
                    description: '서버 연결 문제로 클라이언트에서 생성된 번호입니다.',
                    predictions: predictions,
                    accuracy: '연결 복구 후 정확한 AI 분석을 받으세요',
                    confidence: 'N/A',
                    algorithm: '로컬 랜덤 생성'
                }
            },
            top_recommendations: predictions.slice(0, 3),
            total_combinations: predictions.length,
            data_source: '오프라인 모드',
            analysis_timestamp: new Date().toISOString(),
            processing_time: 0.1,
            version: '2.1-offline',
            request_id: Math.random().toString(36).substr(2, 8),
            cached: false,
            offline_mode: true
        };
    }
    
    // 토스트 메시지 표시
    showToast(message, type = 'info') {
        console.log(`[${type.toUpperCase()}] ${message}`);
        
        // 간단한 알림 표시 (토스트 라이브러리가 없는 경우)
        if (typeof bootstrap !== 'undefined') {
            // Bootstrap 토스트 사용
            const toastContainer = document.getElementById('global-notifications');
            if (toastContainer) {
                const toastId = 'toast-' + Date.now();
                const toastHTML = `
                    <div id="${toastId}" class="toast align-items-center text-bg-${type} border-0" role="alert">
                        <div class="d-flex">
                            <div class="toast-body">${message}</div>
                            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                        </div>
                    </div>
                `;
                toastContainer.insertAdjacentHTML('beforeend', toastHTML);
                
                const toastElement = document.getElementById(toastId);
                const toast = new bootstrap.Toast(toastElement);
                toast.show();
            }
        } else {
            // 기본 브라우저 알림
            alert(message);
        }
    }
    
    // 🔧 사용자 번호 수집 메서드
    getUserNumbers() {
        const numbers = [];
        for (let i = 1; i <= 6; i++) {
            const input = document.getElementById(`num${i}`);
            if (input && input.value) {
                const num = parseInt(input.value);
                if (num >= 1 && num <= 45) {
                    numbers.push(num);
                }
            }
        }
        return numbers;
    }
    
    // 🔧 예측 결과 표시
    displayPredictions(result) {
        const resultsContainer = document.getElementById('results');
        const topRecommendationsContainer = document.getElementById('top-recommendations');
        const modelResultsContainer = document.getElementById('model-results');
        
        if (!resultsContainer) return;
        
        // 결과 섹션 표시
        resultsContainer.classList.remove('d-none');
        
        // TOP 추천 번호 표시
        if (topRecommendationsContainer && result.top_recommendations) {
            let topHtml = '';
            result.top_recommendations.slice(0, 3).forEach((prediction, index) => {
                topHtml += `
                    <div class="col-md-4 mb-3">
                        <div class="card border-warning shadow-sm">
                            <div class="card-body text-center">
                                <h6 class="text-warning mb-3">
                                    <i class="fas fa-crown me-2"></i>TOP ${index + 1}
                                </h6>
                                <div class="number-display">
                                    ${prediction.map(num => `<span class="number-ball">${num}</span>`).join('')}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            topRecommendationsContainer.innerHTML = topHtml;
        }
        
        // 모델별 결과 표시
        if (modelResultsContainer && result.models) {
            let modelHtml = '';
            Object.entries(result.models).forEach(([modelName, modelData]) => {
                modelHtml += `
                    <div class="col-lg-6 mb-4">
                        <div class="card h-100 shadow-sm">
                            <div class="card-header bg-primary text-white">
                                <h6 class="mb-0">
                                    <i class="fas fa-robot me-2"></i>${modelName}
                                </h6>
                            </div>
                            <div class="card-body">
                                <p class="text-muted small mb-3">${modelData.description}</p>
                                <div class="predictions-list">
                                    ${modelData.predictions ? modelData.predictions.slice(0, 3).map((prediction, index) => `
                                        <div class="prediction-item mb-2">
                                            <small class="text-muted">추천 ${index + 1}:</small>
                                            <div class="number-display-small">
                                                ${prediction.map(num => `<span class="number-ball-sm">${num}</span>`).join('')}
                                            </div>
                                        </div>
                                    `).join('') : ''}
                                </div>
                                <div class="model-stats mt-3">
                                    <div class="row text-center">
                                        <div class="col-6">
                                            <small class="text-muted d-block">정확도</small>
                                            <strong class="text-success">${modelData.accuracy || 0}%</strong>
                                        </div>
                                        <div class="col-6">
                                            <small class="text-muted d-block">신뢰도</small>
                                            <strong class="text-info">${modelData.confidence || 0}%</strong>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            modelResultsContainer.innerHTML = modelHtml;
        }
        
        this.updateUI('prediction-status', '✅ AI 분석 완료!');
        
        // 결과 섹션으로 스크롤
        resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    // 🔧 랜덤 번호 생성 메서드
    generateRandomNumbers(count = 1) {
        try {
            const results = [];
            for (let i = 0; i < count; i++) {
                const numbers = [];
                while (numbers.length < 6) {
                    const num = Math.floor(Math.random() * 45) + 1;
                    if (!numbers.includes(num)) {
                        numbers.push(num);
                    }
                }
                numbers.sort((a, b) => a - b);
                results.push(numbers);
            }
            
            // 첫 번째 세트를 입력 필드에 채우기 (count가 1인 경우)
            if (count === 1 && results.length > 0) {
                results[0].forEach((num, index) => {
                    const input = document.getElementById(`num${index + 1}`);
                    if (input) {
                        input.value = num;
                        input.classList.add('is-valid');
                    }
                });
            } else {
                // 여러 세트인 경우 결과 표시
                const randomResults = document.getElementById('random-results');
                if (randomResults) {
                    let html = '<div class="random-numbers-result">';
                    results.forEach((numbers, index) => {
                        html += `
                            <div class="mb-2">
                                <small class="text-muted">세트 ${index + 1}:</small>
                                <div class="number-display-small">
                                    ${numbers.map(num => `<span class="number-ball-sm">${num}</span>`).join('')}
                                </div>
                            </div>
                        `;
                    });
                    html += '</div>';
                    randomResults.innerHTML = html;
                }
            }
            
            return results;
        } catch (error) {
            console.error('Random number generation failed:', error);
            this.showError('random-error', '랜덤 번호 생성 중 오류가 발생했습니다.');
            return [];
        }
    }
    
    // 🔧 통계 로드 메서드
    async loadStatistics() {
        if (this.loadingStates.statistics) return;
        
        this.setLoadingState('statistics', true);
        this.showStatsLoading(true);
        
        try {
            const result = await this.fetchWithTimeout('/api/stats');
            this.displayStatistics(result);
            this.showStatsLoading(false);
        } catch (error) {
            this.handleError(error, 'statistics');
            this.showStatsLoading(false);
        } finally {
            this.setLoadingState('statistics', false);
        }
    }
    
    // 🔧 통계 표시 메서드
    displayStatistics(result) {
        const statsContent = document.getElementById('stats-content');
        const hotNumbers = document.getElementById('hotNumbers');
        const coldNumbers = document.getElementById('coldNumbers');
        const carryOverAnalysis = document.getElementById('carryOverAnalysis');
        const companionAnalysis = document.getElementById('companionAnalysis');
        const patternAnalysis = document.getElementById('patternAnalysis');
        
        if (statsContent) {
            statsContent.classList.remove('d-none');
        }
        
        // 핫 넘버 표시
        if (hotNumbers && result.hot_numbers) {
            let html = '<div class="numbers-grid">';
            result.hot_numbers.slice(0, 10).forEach(([num, count]) => {
                html += `<span class="number-ball hot-number" title="${count}회 출현">${num}</span>`;
            });
            html += '</div>';
            hotNumbers.innerHTML = html;
        }
        
        // 콜드 넘버 표시
        if (coldNumbers && result.cold_numbers) {
            let html = '<div class="numbers-grid">';
            result.cold_numbers.slice(0, 10).forEach(([num, count]) => {
                html += `<span class="number-ball cold-number" title="${count}회 출현">${num}</span>`;
            });
            html += '</div>';
            coldNumbers.innerHTML = html;
        }
        
        // 이월수 분석
        if (carryOverAnalysis && result.carry_over_analysis) {
            let html = '<div class="analysis-list">';
            result.carry_over_analysis.slice(0, 5).forEach(item => {
                html += `
                    <div class="analysis-item">
                        <small class="text-muted">${item.round}회차</small>
                        <div>${item.carry_over_numbers.map(num => `<span class="number-ball-xs">${num}</span>`).join('')}</div>
                    </div>
                `;
            });
            html += '</div>';
            carryOverAnalysis.innerHTML = html;
        }
        
        // 궁합수 분석
        if (companionAnalysis && result.companion_analysis) {
            let html = '<div class="analysis-list">';
            result.companion_analysis.slice(0, 5).forEach(([pair, count]) => {
                html += `
                    <div class="analysis-item">
                        <div>${pair[0]} ↔ ${pair[1]}</div>
                        <small class="text-muted">${count}회</small>
                    </div>
                `;
            });
            html += '</div>';
            companionAnalysis.innerHTML = html;
        }
        
        // 패턴 분석
        if (patternAnalysis && result.pattern_analysis) {
            let html = '<div class="pattern-stats">';
            
            if (result.pattern_analysis.odd_even_ratio) {
                const ratios = result.pattern_analysis.odd_even_ratio.slice(0, 3);
                html += `<div class="stat-item"><strong>홀짝 비율:</strong> ${ratios.join(', ')}</div>`;
            }
            
            if (result.pattern_analysis.consecutive_count) {
                const avg = result.pattern_analysis.consecutive_count.reduce((a, b) => a + b, 0) / result.pattern_analysis.consecutive_count.length;
                html += `<div class="stat-item"><strong>평균 연속번호:</strong> ${avg.toFixed(1)}개</div>`;
            }
            
            html += '</div>';
            patternAnalysis.innerHTML = html;
        }
    }
    
    // 🔧 저장된 번호 로드 메서드
    async loadSavedNumbers() {
        try {
            const result = await this.fetchWithTimeout('/api/saved-numbers');
            this.displaySavedNumbers(result);
        } catch (error) {
            console.error('Failed to load saved numbers:', error);
            this.showError('saved-numbers-error', '저장된 번호를 불러올 수 없습니다.');
        }
    }
    
    // 🔧 저장된 번호 표시 메서드
    displaySavedNumbers(result) {
        console.log('Saved numbers:', result);
        // TODO: 저장된 번호 표시 로직 구현
    }
    
    // 🔧 진행률 표시 메서드
    showPredictionProgress(show) {
        const progressContainer = document.getElementById('prediction-progress');
        if (progressContainer) {
            if (show) {
                progressContainer.classList.remove('d-none');
                this.updateProgress(0, '데이터 준비 중...');
            } else {
                progressContainer.classList.add('d-none');
            }
        }
    }
    
    updateProgress(percent, message) {
        const progressBar = document.getElementById('prediction-progress-bar');
        const progressMessage = document.getElementById('progress-message');
        
        if (progressBar) {
            progressBar.style.width = `${percent}%`;
        }
        
        if (progressMessage) {
            progressMessage.textContent = message;
        }
    }
    
    // 🔧 통계 로딩 표시
    showStatsLoading(show) {
        const statsLoading = document.getElementById('stats-loading');
        const statsError = document.getElementById('stats-error');
        const statsContent = document.getElementById('stats-content');
        
        if (show) {
            if (statsLoading) statsLoading.classList.remove('d-none');
            if (statsError) statsError.classList.add('d-none');
            if (statsContent) statsContent.classList.add('d-none');
        } else {
            if (statsLoading) statsLoading.classList.add('d-none');
        }
    }
    
    // 🔧 에러 처리
    handleError(error, type) {
        console.error(`Error in ${type}:`, error);
        
        if (this.retryCount < this.maxRetries) {
            this.retryCount++;
            this.updateUI(`${type}-status`, 
                `⚠️ 연결 재시도 중... (${this.retryCount}/${this.maxRetries})`
            );
            
            setTimeout(() => {
                if (type === 'prediction') this.generatePrediction();
                if (type === 'statistics') this.loadStatistics();
            }, 2000 * this.retryCount); // 점진적 지연
            
        } else {
            this.showPredictionError(error);
        }
    }
    
    // 🔧 예측 에러 표시
    showPredictionError(error) {
        const errorContainer = document.getElementById('prediction-error');
        const errorMessage = document.getElementById('prediction-error-message');
        const errorCode = document.getElementById('prediction-error-code');
        
        if (errorContainer && errorMessage) {
            errorMessage.textContent = error.message || '알 수 없는 오류가 발생했습니다.';
            if (errorCode) {
                errorCode.textContent = error.code || 'ERR_UNKNOWN';
            }
            errorContainer.classList.remove('d-none');
        }
    }
    
    // 🔧 에러 표시 일반 메서드
    showError(containerId, message) {
        const container = document.getElementById(containerId);
        const messageElement = document.getElementById(containerId.replace('-error', '-error-message'));
        
        if (container && messageElement) {
            messageElement.textContent = message;
            container.classList.remove('d-none');
        }
    }
    
    retryPrediction() {
        this.retryCount = 0;
        this.hidePredictionError();
        this.generatePrediction();
    }
    
    retryStatistics() {
        this.retryCount = 0;
        this.loadStatistics();
    }
    
    hidePredictionError() {
        const errorContainer = document.getElementById('prediction-error');
        if (errorContainer) {
            errorContainer.classList.add('d-none');
        }
    }
    
    setLoadingState(key, value) {
        this.loadingStates[key] = value;
        this.updateLoadingUI();
    }
    
    updateLoadingUI() {
        // 로딩 상태에 따른 UI 업데이트
        const isAnyLoading = Object.values(this.loadingStates).some(state => state);
        const loadingIndicator = document.getElementById('global-loading');
        
        if (loadingIndicator) {
            loadingIndicator.style.display = isAnyLoading ? 'block' : 'none';
        }
    }
    
    updateUI(elementId, content) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = content;
        }
    }
}

// 🔧 전역 함수들 - HTML에서 직접 호출 가능
function generatePrediction() {
    if (window.lottoApp) {
        window.lottoApp.generatePrediction();
    } else {
        console.error('LottoApp not initialized');
    }
}

function generateRandomNumbers() {
    if (window.lottoApp) {
        window.lottoApp.generateRandomNumbers();
    } else {
        console.error('LottoApp not initialized');
    }
}

function generateRandomAndPredict() {
    if (window.lottoApp) {
        window.lottoApp.generateRandomNumbers();
        setTimeout(() => {
            window.lottoApp.generatePrediction();
        }, 500);
    } else {
        console.error('LottoApp not initialized');
    }
}

function loadStatistics() {
    if (window.lottoApp) {
        window.lottoApp.loadStatistics();
    } else {
        console.error('LottoApp not initialized');
    }
}

function checkSystemHealth() {
    if (window.lottoApp) {
        window.lottoApp.checkSystemHealth();
    } else {
        console.error('LottoApp not initialized');
    }
}

function retryPrediction() {
    if (window.lottoApp) {
        window.lottoApp.retryPrediction();
    }
}

function hidePredictionError() {
    if (window.lottoApp) {
        window.lottoApp.hidePredictionError();
    }
}

function retryStatsLoad() {
    if (window.lottoApp) {
        window.lottoApp.loadStatistics();
    }
}

// 🔧 추가 유틸리티 함수들
function clearAllInputs() {
    for (let i = 1; i <= 6; i++) {
        const input = document.getElementById(`num${i}`);
        if (input) {
            input.value = '';
            input.classList.remove('is-valid', 'is-invalid');
        }
    }
}

function fillRandomNumbers() {
    if (window.lottoApp) {
        window.lottoApp.generateRandomNumbers(1);
    }
}

function showNumberHelper() {
    const modal = document.getElementById('numberHelpModal');
    if (modal) {
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
    }
}

function saveTopRecommendation() {
    // TODO: 최고 추천 번호 저장 로직
    console.log('Save top recommendation');
}

function generateQRFromResults() {
    // TODO: QR 코드 생성 로직
    console.log('Generate QR from results');
}

function calculateTax() {
    // TODO: 세금 계산 로직
    console.log('Calculate tax');
}

function runSimulation() {
    // TODO: 시뮬레이션 실행 로직
    console.log('Run simulation');
}

function generateQRCode() {
    // TODO: QR 코드 생성 로직
    console.log('Generate QR code');
}

function searchStores() {
    // TODO: 판매점 검색 로직
    console.log('Search stores');
}

function getCurrentLocation() {
    // TODO: 현재 위치 확인 로직
    console.log('Get current location');
}

function checkWinning() {
    // TODO: 당첨 확인 로직
    console.log('Check winning');
}

// 🔧 앱 초기화 (전역에서 접근 가능하도록)
document.addEventListener('DOMContentLoaded', function() {
    window.lottoApp = new LottoApp();
    console.log('LottoApp initialized successfully');
});

// 즉시 실행 (DOMContentLoaded 이벤트 이후)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        if (!window.lottoApp) {
            window.lottoApp = new LottoApp();
            console.log('LottoApp initialized on ready state');
        }
    });
} else {
    if (!window.lottoApp) {
        window.lottoApp = new LottoApp();
        console.log('LottoApp initialized immediately');
    }
}
