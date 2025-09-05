class LottoApp {
    constructor() {
        this.apiTimeout = 15000; // 15초
        this.retryCount = 0;
        this.maxRetries = 3;
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.initLoadingStates();
        this.checkHealth(); // 앱 시작 시 헬스체크
    }
    
    initLoadingStates() {
        this.loadingStates = {
            aiPrediction: false,
            statistics: false,
            qrScan: false
        };
    }
    
    // 🔧 누락된 bindEvents 메서드 추가
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
    }
    
    // 🔧 헬스체크 메서드 추가
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
    
    async fetchWithTimeout(url, options = {}) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.apiTimeout);
        
        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal
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
        this.updateUI('prediction-status', '🤖 AI가 분석 중입니다...');
        
        try {
            // 사용자 입력 번호 수집
            const userNumbers = this.getUserNumbers();
            
            const result = await this.fetchWithTimeout('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_numbers: userNumbers })
            });
            
            if (result.error) {
                throw new Error(result.message);
            }
            
            this.displayPredictions(result);
            this.retryCount = 0;
            
        } catch (error) {
            this.handleError(error, 'prediction');
        } finally {
            this.setLoadingState('aiPrediction', false);
        }
    }
    
    // 🔧 사용자 번호 수집 메서드 추가
    getUserNumbers() {
        const numbers = [];
        for (let i = 1; i <= 6; i++) {
            const input = document.getElementById(`number-${i}`);
            if (input && input.value) {
                const num = parseInt(input.value);
                if (num >= 1 && num <= 45) {
                    numbers.push(num);
                }
            }
        }
        return numbers;
    }
    
    // 🔧 누락된 displayPredictions 메서드 추가
    displayPredictions(result) {
        const container = document.getElementById('predictions-container');
        if (!container) return;
        
        let html = '<div class="predictions-result">';
        html += '<h3>🎯 AI 예상번호</h3>';
        
        if (result.models) {
            Object.entries(result.models).forEach(([modelName, modelData]) => {
                html += `<div class="model-predictions">`;
                html += `<h4>${modelName}</h4>`;
                html += `<p class="model-desc">${modelData.description}</p>`;
                
                if (modelData.predictions && modelData.predictions.length > 0) {
                    html += '<div class="predictions-grid">';
                    modelData.predictions.forEach((prediction, index) => {
                        html += `<div class="prediction-set">`;
                        html += `<span class="set-label">추천 ${index + 1}</span>`;
                        html += `<div class="numbers">`;
                        prediction.forEach(num => {
                            html += `<span class="number">${num}</span>`;
                        });
                        html += `</div></div>`;
                    });
                    html += '</div>';
                }
                
                html += `<div class="model-stats">`;
                html += `<span class="accuracy">정확도: ${modelData.accuracy}%</span>`;
                html += `<span class="confidence">신뢰도: ${modelData.confidence}%</span>`;
                html += `</div></div>`;
            });
        }
        
        if (result.top_recommendations) {
            html += '<div class="top-recommendations">';
            html += '<h4>🌟 최고 추천 번호</h4>';
            html += '<div class="predictions-grid">';
            result.top_recommendations.forEach((prediction, index) => {
                html += `<div class="prediction-set highlight">`;
                html += `<span class="set-label">TOP ${index + 1}</span>`;
                html += `<div class="numbers">`;
                prediction.forEach(num => {
                    html += `<span class="number">${num}</span>`;
                });
                html += `</div></div>`;
            });
            html += '</div></div>';
        }
        
        html += '</div>';
        container.innerHTML = html;
        
        this.updateUI('prediction-status', '✅ AI 분석 완료!');
    }
    
    // 🔧 랜덤 번호 생성 메서드 추가
    generateRandomNumbers() {
        const numbers = [];
        while (numbers.length < 6) {
            const num = Math.floor(Math.random() * 45) + 1;
            if (!numbers.includes(num)) {
                numbers.push(num);
            }
        }
        numbers.sort((a, b) => a - b);
        
        // 입력 필드에 채우기
        numbers.forEach((num, index) => {
            const input = document.getElementById(`number-${index + 1}`);
            if (input) {
                input.value = num;
            }
        });
    }
    
    // 🔧 통계 로드 메서드 추가
    async loadStatistics() {
        if (this.loadingStates.statistics) return;
        
        this.setLoadingState('statistics', true);
        
        try {
            const result = await this.fetchWithTimeout('/api/stats');
            this.displayStatistics(result);
        } catch (error) {
            this.handleError(error, 'statistics');
        } finally {
            this.setLoadingState('statistics', false);
        }
    }
    
    // 🔧 통계 표시 메서드 추가
    displayStatistics(result) {
        const container = document.getElementById('statistics-container');
        if (!container) return;
        
        let html = '<div class="statistics-result">';
        html += '<h3>📊 로또 통계 분석</h3>';
        
        if (result.hot_numbers) {
            html += '<div class="stat-section">';
            html += '<h4>🔥 자주 나오는 번호 (HOT)</h4>';
            html += '<div class="numbers-list">';
            result.hot_numbers.slice(0, 10).forEach(([num, count]) => {
                html += `<span class="number hot">${num} <small>(${count}회)</small></span>`;
            });
            html += '</div></div>';
        }
        
        if (result.cold_numbers) {
            html += '<div class="stat-section">';
            html += '<h4>❄️ 적게 나오는 번호 (COLD)</h4>';
            html += '<div class="numbers-list">';
            result.cold_numbers.slice(0, 10).forEach(([num, count]) => {
                html += `<span class="number cold">${num} <small>(${count}회)</small></span>`;
            });
            html += '</div></div>';
        }
        
        html += '</div>';
        container.innerHTML = html;
    }
    
    // 🔧 저장된 번호 로드 메서드 추가
    async loadSavedNumbers() {
        try {
            const result = await this.fetchWithTimeout('/api/saved-numbers');
            this.displaySavedNumbers(result);
        } catch (error) {
            console.error('Failed to load saved numbers:', error);
        }
    }
    
    // 🔧 저장된 번호 표시 메서드 추가
    displaySavedNumbers(result) {
        // TODO: 저장된 번호 표시 로직
        console.log('Saved numbers:', result);
    }
    
    handleError(error, type) {
        console.error(`Error in ${type}:`, error);
        
        if (this.retryCount < this.maxRetries) {
            this.retryCount++;
            this.updateUI('prediction-status', 
                `⚠️ 연결 재시도 중... (${this.retryCount}/${this.maxRetries})`
            );
            
            setTimeout(() => {
                if (type === 'prediction') this.generatePrediction();
                if (type === 'statistics') this.loadStatistics();
            }, 2000 * this.retryCount); // 점진적 지연
            
        } else {
            const statusElement = type === 'prediction' ? 'prediction-status' : 'statistics-status';
            this.updateUI(statusElement, 
                `❌ ${error.message}\n<button onclick="lottoApp.retry${type.charAt(0).toUpperCase() + type.slice(1)}()">다시 시도</button>`
            );
        }
    }
    
    retryPrediction() {
        this.retryCount = 0;
        this.generatePrediction();
    }
    
    retryStatistics() {
        this.retryCount = 0;
        this.loadStatistics();
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

// 🔧 전역 함수들 추가 (HTML에서 직접 호출 가능)
function generatePrediction() {
    if (window.lottoApp) {
        window.lottoApp.generatePrediction();
    }
}

function generateRandomNumbers() {
    if (window.lottoApp) {
        window.lottoApp.generateRandomNumbers();
    }
}

function loadStatistics() {
    if (window.lottoApp) {
        window.lottoApp.loadStatistics();
    }
}

// 앱 초기화 (전역에서 접근 가능하도록)
document.addEventListener('DOMContentLoaded', function() {
    window.lottoApp = new LottoApp();
});

// 즉시 실행 (DOMContentLoaded 이벤트 이후)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        window.lottoApp = new LottoApp();
    });
} else {
    window.lottoApp = new LottoApp();
}
