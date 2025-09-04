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
    }
    
    initLoadingStates() {
        this.loadingStates = {
            aiPrediction: false,
            statistics: false,
            qrScan: false
        };
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
            const result = await this.fetchWithTimeout('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (result.error) {
                throw new Error(result.message);
            }
            
            this.displayPredictions(result.data);
            this.retryCount = 0;
            
        } catch (error) {
            this.handleError(error, 'prediction');
        } finally {
            this.setLoadingState('aiPrediction', false);
        }
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
            }, 2000 * this.retryCount); // 점진적 지연
            
        } else {
            this.updateUI('prediction-status', 
                `❌ ${error.message}\n<button onclick="lottoApp.retryPrediction()">다시 시도</button>`
            );
        }
    }
    
    retryPrediction() {
        this.retryCount = 0;
        this.generatePrediction();
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

// 앱 초기화
const lottoApp = new LottoApp();
