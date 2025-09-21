/**
 * LottoPro AI v2.0 - Main JavaScript Application (랜덤성 개선 버전)
 * 동적 시드 시스템과 캐시 버스팅 기능 포함
 */

// ===== Global Application Object =====
window.lottoPro = {
    // Configuration - 랜덤성 개선
    config: {
        apiBaseUrl: '/api',
        version: '2.0.1-randomness-improved',
        maxSavedNumbers: 50,
        maxSimulationRounds: 10000,
        debounceDelay: 300,
        animationDuration: 300,
        
        // 랜덤성 개선 설정
        cacheBusting: {
            enabled: true,
            forceRefreshProbability: 0.3,  // 30% 확률로 강제 새로고침
            timestampInterval: 60000,      // 1분마다 새로운 타임스탬프
            randomSeedRange: 1000000
        },
        
        // 문제 알고리즘 목록
        problematicAlgorithms: [
            'hot_cold_analysis',
            'pattern_analysis', 
            'neural_network',
            'markov_chain',
            'co_occurrence',
            'time_series'
        ]
    },
    
    // State management
    state: {
        currentUser: null,
        savedNumbers: [],
        lastPrediction: null,
        systemHealth: null,
        statsData: null,
        isLoading: false,
        lastRefreshTime: 0,
        predictionHistory: [],
        randomnessStats: {
            totalRequests: 0,
            forcedRefreshes: 0,
            uniqueResults: 0,
            duplicateDetections: 0
        }
    },
    
    // Utility functions
    utils: {},
    
    // Feature modules
    modules: {},
    
    // Event handlers
    events: {},
    
    // API client
    api: {}
};

// ===== Enhanced Utility Functions =====
window.lottoPro.utils = {
    
    /**
     * 동적 시드 생성
     */
    generateDynamicSeed: function() {
        const timestamp = Date.now();
        const random = Math.floor(Math.random() * window.lottoPro.config.cacheBusting.randomSeedRange);
        const performance = window.performance ? Math.floor(window.performance.now()) : 0;
        return timestamp + random + performance;
    },
    
    /**
     * 캐시 버스팅 파라미터 생성
     */
    generateCacheBustingParams: function() {
        const config = window.lottoPro.config.cacheBusting;
        
        return {
            timestamp: Date.now(),
            seed: this.generateDynamicSeed(),
            random: Math.floor(Math.random() * config.randomSeedRange),
            version: window.lottoPro.config.version,
            force_refresh: Math.random() < config.forceRefreshProbability
        };
    },
    
    /**
     * 결과 중복 검사
     */
    checkResultDuplication: function(newResults, historyLimit = 10) {
        const history = window.lottoPro.state.predictionHistory;
        const recentHistory = history.slice(-historyLimit);
        
        let duplicateCount = 0;
        const duplicateAlgorithms = [];
        
        Object.entries(newResults).forEach(([algorithmKey, result]) => {
            const currentNumbers = JSON.stringify(result.priority_numbers);
            
            for (let i = 0; i < recentHistory.length; i++) {
                const historyResult = recentHistory[i][algorithmKey];
                if (historyResult && JSON.stringify(historyResult.priority_numbers) === currentNumbers) {
                    duplicateCount++;
                    duplicateAlgorithms.push(algorithmKey);
                    break;
                }
            }
        });
        
        return {
            duplicateCount,
            duplicateAlgorithms,
            isDuplicateDetected: duplicateCount > 3  // 3개 이상 중복 시 문제로 판단
        };
    },
    
    /**
     * Debounce function
     */
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    /**
     * Generate unique ID
     */
    generateId: function() {
        return 'id_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    },
    
    /**
     * Validate lottery numbers
     */
    validateNumbers: function(numbers) {
        if (!Array.isArray(numbers)) return { valid: false, error: '배열이 아닙니다.' };
        if (numbers.length !== 6) return { valid: false, error: '6개 번호가 필요합니다.' };
        
        const uniqueNumbers = [...new Set(numbers)];
        if (uniqueNumbers.length !== 6) return { valid: false, error: '중복된 번호가 있습니다.' };
        
        for (let num of numbers) {
            if (!Number.isInteger(num) || num < 1 || num > 45) {
                return { valid: false, error: '번호는 1-45 사이여야 합니다.' };
            }
        }
        
        return { valid: true };
    },
    
    /**
     * Show toast notification
     */
    showToast: function(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} toast`;
        toast.style.position = 'fixed';
        toast.style.top = '20px';
        toast.style.right = '20px';
        toast.style.zIndex = '9999';
        toast.style.minWidth = '300px';
        
        toast.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <span>${message}</span>
                <button type="button" class="btn-close" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Auto remove
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, duration);
        
        return toast;
    },
    
    /**
     * Show loading spinner
     */
    showLoading: function(element, text = '로딩 중...') {
        const spinner = document.createElement('div');
        spinner.className = 'loading text-center p-4';
        spinner.innerHTML = `
            <div class="spinner-border mb-3" role="status"></div>
            <p class="text-muted">${text}</p>
        `;
        
        element.innerHTML = '';
        element.appendChild(spinner);
        return spinner;
    },
    
    /**
     * Hide loading spinner
     */
    hideLoading: function(element) {
        const loading = element.querySelector('.loading');
        if (loading) {
            loading.remove();
        }
    }
};

// ===== Enhanced API Client =====
window.lottoPro.api = {
    
    /**
     * Generic API request with cache busting
     */
    request: async function(url, options = {}) {
        try {
            // 캐시 버스팅 파라미터 추가
            const cacheBustingParams = window.lottoPro.utils.generateCacheBustingParams();
            
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0',
                    'X-Randomness-Seed': cacheBustingParams.seed.toString(),
                    'X-Request-ID': window.lottoPro.utils.generateId()
                }
            };
            
            const config = { ...defaultOptions, ...options };
            
            // GET 요청인 경우 URL에 파라미터 추가
            if (!config.method || config.method.toUpperCase() === 'GET') {
                const separator = url.includes('?') ? '&' : '?';
                const params = new URLSearchParams(cacheBustingParams);
                url = `${url}${separator}${params.toString()}`;
            } else {
                // POST 요청인 경우 body에 파라미터 추가
                if (config.body) {
                    const bodyData = JSON.parse(config.body);
                    Object.assign(bodyData, cacheBustingParams);
                    config.body = JSON.stringify(bodyData);
                } else {
                    config.body = JSON.stringify(cacheBustingParams);
                }
            }
            
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP Error: ${response.status} ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    },
    
    /**
     * Enhanced AI 예측 API with randomness improvements
     */
    predict: async function(userNumbers = []) {
        const requestId = window.lottoPro.utils.generateId();
        console.log(`🎯 예측 요청 시작 (ID: ${requestId})`);
        
        try {
            // 통계 업데이트
            window.lottoPro.state.randomnessStats.totalRequests++;
            
            const response = await this.request('/api/predictions', {
                method: 'POST',
                body: JSON.stringify({ 
                    user_numbers: userNumbers,
                    request_id: requestId,
                    client_timestamp: Date.now()
                })
            });
            
            if (response.success) {
                // 결과 중복 검사
                const duplicationCheck = window.lottoPro.utils.checkResultDuplication(response.data);
                
                if (duplicationCheck.isDuplicateDetected) {
                    console.warn(`⚠️ 중복 결과 감지: ${duplicationCheck.duplicateCount}개 알고리즘`);
                    window.lottoPro.state.randomnessStats.duplicateDetections++;
                    
                    // 중복 감지 시 강제 새로고침 시도
                    return await this.forceRefreshPrediction(userNumbers, requestId);
                }
                
                // 예측 히스토리에 추가
                window.lottoPro.state.predictionHistory.push(response.data);
                if (window.lottoPro.state.predictionHistory.length > 20) {
                    window.lottoPro.state.predictionHistory.shift(); // 오래된 기록 제거
                }
                
                console.log(`✅ 예측 완료 (ID: ${requestId})`);
                return response;
            } else {
                throw new Error(response.error || '예측 생성에 실패했습니다.');
            }
            
        } catch (error) {
            console.error(`❌ 예측 실패 (ID: ${requestId}):`, error);
            throw error;
        }
    },
    
    /**
     * 강제 새로고침 예측
     */
    forceRefreshPrediction: async function(userNumbers = [], originalRequestId = null) {
        console.log(`🔄 강제 새로고침 시작 (원본: ${originalRequestId})`);
        
        try {
            window.lottoPro.state.randomnessStats.forcedRefreshes++;
            
            // 캐시 클리어 요청
            await this.request('/api/clear-cache', {
                method: 'POST',
                body: JSON.stringify({
                    clear_algorithms: window.lottoPro.config.problematicAlgorithms,
                    reason: 'duplicate_detection'
                })
            });
            
            // 잠시 대기 후 재요청
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // 강제 새로고침 API 호출
            const response = await this.request('/api/force-refresh', {
                method: 'POST',
                body: JSON.stringify({ 
                    user_numbers: userNumbers,
                    force_new_seeds: true,
                    clear_cache: true
                })
            });
            
            if (response.success) {
                console.log(`✅ 강제 새로고침 완료`);
                window.lottoPro.utils.showToast('알고리즘이 새로운 시드로 재실행되었습니다.', 'info');
                return response;
            } else {
                throw new Error(response.error || '강제 새로고침 실패');
            }
            
        } catch (error) {
            console.error('강제 새로고침 실패:', error);
            window.lottoPro.utils.showToast('강제 새로고침 실패: ' + error.message, 'warning');
            throw error;
        }
    },
    
    /**
     * 시스템 상태 확인
     */
    checkHealth: async function() {
        return await this.request('/api/health');
    },
    
    /**
     * 통계 분석 API
     */
    getStats: async function() {
        return await this.request('/api/statistics');
    }
};

// ===== Enhanced Prediction Module =====
window.lottoPro.modules.prediction = {
    
    isGenerating: false,
    lastGenerationTime: 0,
    
    /**
     * Enhanced 예측 생성 with duplicate detection
     */
    generate: async function() {
        if (this.isGenerating) {
            window.lottoPro.utils.showToast('이미 예측을 생성 중입니다.', 'warning');
            return;
        }
        
        // 너무 빠른 연속 요청 방지
        const now = Date.now();
        if (now - this.lastGenerationTime < 2000) {
            window.lottoPro.utils.showToast('잠시 후 다시 시도해주세요.', 'info');
            return;
        }
        
        this.isGenerating = true;
        this.lastGenerationTime = now;
        
        try {
            // 사용자 입력 수집
            const userNumbers = this.collectUserNumbers();
            
            // 로딩 표시
            this.showLoadingState();
            
            // API 호출 (향상된 랜덤성)
            const response = await window.lottoPro.api.predict(userNumbers);
            
            if (response.success) {
                // 결과 표시
                this.displayResults(response);
                
                // 상태 업데이트
                window.lottoPro.state.lastPrediction = response;
                window.lottoPro.state.lastRefreshTime = now;
                
                // 랜덤성 통계 표시
                this.displayRandomnessStats(response);
                
                window.lottoPro.utils.showToast('AI 예측이 완료되었습니다!', 'success');
            } else {
                throw new Error(response.error || '예측 생성에 실패했습니다.');
            }
            
        } catch (error) {
            console.error('Prediction failed:', error);
            this.displayError(error.message);
            window.lottoPro.utils.showToast('예측 생성 중 오류가 발생했습니다: ' + error.message, 'danger');
        } finally {
            this.hideLoadingState();
            this.isGenerating = false;
        }
    },
    
    /**
     * 사용자 번호 수집
     */
    collectUserNumbers: function() {
        const userNumbers = [];
        for (let i = 1; i <= 6; i++) {
            const input = document.getElementById(`num${i}`);
            if (input && input.value) {
                const num = parseInt(input.value);
                if (num >= 1 && num <= 45) {
                    userNumbers.push(num);
                }
            }
        }
        
        // 중복 검사
        if (userNumbers.length > 0) {
            const validation = window.lottoPro.utils.validateNumbers(userNumbers.length === 6 ? userNumbers : [1,2,3,4,5,6]);
            if (userNumbers.length === 6 && !validation.valid) {
                throw new Error(validation.error);
            }
        }
        
        return userNumbers;
    },
    
    /**
     * 로딩 상태 표시
     */
    showLoadingState: function() {
        const resultsElement = document.getElementById('results');
        const loadingElement = document.getElementById('loading');
        
        if (resultsElement) resultsElement.style.display = 'none';
        if (loadingElement) {
            loadingElement.style.display = 'block';
            loadingElement.innerHTML = `
                <div class="text-center p-4">
                    <div class="spinner-border mb-3" role="status"></div>
                    <p class="text-muted">AI가 고유한 번호 조합을 생성하고 있습니다...</p>
                    <small class="text-muted">랜덤성 개선 시스템 활성화</small>
                </div>
            `;
        }
        
        // 생성 버튼 비활성화
        const generateBtn = document.getElementById('generate-btn');
        if (generateBtn) {
            generateBtn.disabled = true;
            generateBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>생성 중...';
        }
    },
    
    /**
     * 로딩 상태 숨김
     */
    hideLoadingState: function() {
        const loadingElement = document.getElementById('loading');
        if (loadingElement) loadingElement.style.display = 'none';
        
        // 생성 버튼 활성화
        const generateBtn = document.getElementById('generate-btn');
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="fas fa-magic me-2"></i>AI 예측 생성';
        }
    },
    
    /**
     * 예측 결과 표시
     */
    displayResults: function(data) {
        const resultsElement = document.getElementById('results');
        if (!resultsElement) return;
        
        let html = '<div class="prediction-results">';
        
        // 헤더
        html += `
            <div class="results-header mb-4">
                <h4><i class="fas fa-magic me-2"></i>AI 예측 결과</h4>
                <div class="d-flex justify-content-between align-items-center">
                    <small class="text-muted">생성시간: ${new Date().toLocaleTimeString()}</small>
                    <div class="d-flex gap-2">
                        <button class="btn btn-sm btn-outline-primary" onclick="window.lottoPro.modules.prediction.forceRefresh()">
                            <i class="fas fa-sync me-1"></i>강제 새로고침
                        </button>
                        <button class="btn btn-sm btn-outline-info" onclick="window.lottoPro.modules.prediction.showRandomnessInfo()">
                            <i class="fas fa-info-circle me-1"></i>랜덤성 정보
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // 알고리즘별 결과
        if (data.data) {
            const algorithms = Object.entries(data.data);
            
            algorithms.forEach(([key, algorithm]) => {
                const isProblematic = window.lottoPro.config.problematicAlgorithms.some(
                    prob => algorithm.name && algorithm.name.includes(prob.replace('_analysis', '').replace('_', ''))
                );
                
                html += `
                    <div class="algorithm-result mb-3 ${isProblematic ? 'border-warning' : ''}">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <h6 class="mb-0">
                                <i class="fas fa-robot me-2"></i>${algorithm.name || key}
                                ${isProblematic ? '<span class="badge bg-warning text-dark ms-2">개선됨</span>' : ''}
                            </h6>
                            <div class="d-flex gap-2">
                                <span class="badge bg-primary">${algorithm.confidence}%</span>
                                <button class="btn btn-sm btn-outline-success" onclick="window.lottoPro.modules.savedNumbers.quickSave([${algorithm.priority_numbers.join(',')}], '${algorithm.name}')">
                                    <i class="fas fa-heart me-1"></i>저장
                                </button>
                            </div>
                        </div>
                        
                        <div class="number-display mb-2">
                            ${algorithm.priority_numbers.map(num => `<span class="number-ball">${num}</span>`).join('')}
                        </div>
                        
                        <small class="text-muted">${algorithm.description || ''}</small>
                    </div>
                `;
            });
        }
        
        html += '</div>';
        
        resultsElement.innerHTML = html;
        resultsElement.style.display = 'block';
        
        // 결과로 스크롤
        window.lottoPro.utils.scrollToElement(resultsElement, 100);
    },
    
    /**
     * 에러 표시
     */
    displayError: function(message) {
        const resultsElement = document.getElementById('results');
        if (!resultsElement) return;
        
        resultsElement.innerHTML = `
            <div class="alert alert-danger">
                <h5><i class="fas fa-exclamation-triangle me-2"></i>예측 생성 실패</h5>
                <p class="mb-2">${message}</p>
                <div class="d-flex gap-2">
                    <button class="btn btn-sm btn-outline-danger" onclick="window.lottoPro.modules.prediction.generate()">
                        <i class="fas fa-redo me-1"></i>다시 시도
                    </button>
                    <button class="btn btn-sm btn-outline-secondary" onclick="window.lottoPro.api.checkHealth().then(r => console.log(r))">
                        <i class="fas fa-stethoscope me-1"></i>시스템 상태 확인
                    </button>
                </div>
            </div>
        `;
        resultsElement.style.display = 'block';
    },
    
    /**
     * 랜덤성 통계 표시
     */
    displayRandomnessStats: function(response) {
        const stats = window.lottoPro.state.randomnessStats;
        const responseInfo = response.randomness_info || {};
        
        console.log(`📊 랜덤성 통계:`, {
            totalRequests: stats.totalRequests,
            forcedRefreshes: stats.forcedRefreshes,
            duplicateDetections: stats.duplicateDetections,
            uniqueResults: responseInfo.unique_results || 'N/A',
            duplicateResults: responseInfo.duplicate_results || 'N/A'
        });
    },
    
    /**
     * 강제 새로고침
     */
    forceRefresh: async function() {
        if (this.isGenerating) return;
        
        try {
            this.isGenerating = true;
            this.showLoadingState();
            
            const userNumbers = this.collectUserNumbers();
            const response = await window.lottoPro.api.forceRefreshPrediction(userNumbers);
            
            if (response.success) {
                this.displayResults(response);
                window.lottoPro.state.lastPrediction = response;
            }
            
        } catch (error) {
            this.displayError(error.message);
        } finally {
            this.hideLoadingState();
            this.isGenerating = false;
        }
    },
    
    /**
     * 랜덤성 정보 모달 표시
     */
    showRandomnessInfo: function() {
        const stats = window.lottoPro.state.randomnessStats;
        const successRate = stats.totalRequests > 0 ? 
            ((stats.totalRequests - stats.duplicateDetections) / stats.totalRequests * 100).toFixed(1) : 100;
        
        const modalHtml = `
            <div class="modal fade" id="randomnessModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-info text-white">
                            <h5 class="modal-title">
                                <i class="fas fa-dice me-2"></i>랜덤성 시스템 정보
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <h6>시스템 상태</h6>
                            <div class="row mb-3">
                                <div class="col-6">
                                    <div class="text-center p-2 bg-light rounded">
                                        <div class="fw-bold text-success">${successRate}%</div>
                                        <small>고유 결과율</small>
                                    </div>
                                </div>
                                <div class="col-6">
                                    <div class="text-center p-2 bg-light rounded">
                                        <div class="fw-bold text-primary">${stats.forcedRefreshes}</div>
                                        <small>강제 새로고침</small>
                                    </div>
                                </div>
                            </div>
                            
                            <h6>요청 통계</h6>
                            <ul class="list-unstyled">
                                <li><strong>총 요청:</strong> ${stats.totalRequests}회</li>
                                <li><strong>중복 감지:</strong> ${stats.duplicateDetections}회</li>
                                <li><strong>강제 새로고침:</strong> ${stats.forcedRefreshes}회</li>
                            </ul>
                            
                            <h6>개선된 알고리즘</h6>
                            <div class="d-flex flex-wrap gap-1">
                                ${window.lottoPro.config.problematicAlgorithms.map(alg => 
                                    `<span class="badge bg-warning text-dark">${alg.replace('_', ' ')}</span>`
                                ).join('')}
                            </div>
                            
                            <div class="mt-3 p-2 bg-light rounded">
                                <small class="text-muted">
                                    <strong>랜덤성 개선 기능:</strong><br>
                                    • 동적 시드 시스템<br>
                                    • 캐시 버스팅<br>
                                    • 중복 결과 감지 및 재생성<br>
                                    • 알고리즘별 개별 시드 적용
                                </small>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">닫기</button>
                            <button type="button" class="btn btn-info" onclick="window.lottoPro.modules.prediction.resetRandomnessStats()">
                                통계 리셋
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 기존 모달 제거
        const existingModal = document.getElementById('randomnessModal');
        if (existingModal) existingModal.remove();
        
        // 새 모달 추가
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // 모달 표시
        const modal = new bootstrap.Modal(document.getElementById('randomnessModal'));
        modal.show();
    },
    
    /**
     * 랜덤성 통계 리셋
     */
    resetRandomnessStats: function() {
        window.lottoPro.state.randomnessStats = {
            totalRequests: 0,
            forcedRefreshes: 0,
            uniqueResults: 0,
            duplicateDetections: 0
        };
        
        window.lottoPro.utils.showToast('랜덤성 통계가 리셋되었습니다.', 'info');
        
        // 모달 닫기
        const modal = bootstrap.Modal.getInstance(document.getElementById('randomnessModal'));
        if (modal) modal.hide();
    }
};

// ===== Enhanced Saved Numbers Module =====
window.lottoPro.modules.savedNumbers = {
    
    /**
     * 빠른 저장
     */
    quickSave: async function(numbers, label) {
        try {
            // 간단한 저장 (API 없이 로컬 상태만)
            const savedItem = {
                id: window.lottoPro.utils.generateId(),
                numbers: numbers,
                label: label || `AI 추천 ${new Date().toLocaleTimeString()}`,
                saved_at: new Date().toISOString(),
                analysis: this.analyzeNumbers(numbers)
            };
            
            window.lottoPro.state.savedNumbers.push(savedItem);
            this.updateDisplay();
            
            window.lottoPro.utils.showToast('번호가 저장되었습니다!', 'success');
            
        } catch (error) {
            console.error('Quick save failed:', error);
            window.lottoPro.utils.showToast('저장 실패: ' + error.message, 'danger');
        }
    },
    
    /**
     * 번호 분석
     */
    analyzeNumbers: function(numbers) {
        const sum = numbers.reduce((a, b) => a + b, 0);
        const oddCount = numbers.filter(n => n % 2 === 1).length;
        const evenCount = 6 - oddCount;
        const range = Math.max(...numbers) - Math.min(...numbers);
        
        // 연속 번호 검사
        let consecutive = 0;
        const sortedNumbers = [...numbers].sort((a, b) => a - b);
        for (let i = 0; i < sortedNumbers.length - 1; i++) {
            if (sortedNumbers[i + 1] - sortedNumbers[i] === 1) {
                consecutive++;
            }
        }
        
        return {
            sum,
            odd_count: oddCount,
            even_count: evenCount,
            range,
            consecutive
        };
    },
    
    /**
     * 표시 업데이트
     */
    updateDisplay: function() {
        const container = document.getElementById('saved-numbers-list');
        if (!container) return;
        
        const numbers = window.lottoPro.state.savedNumbers;
        
        if (numbers.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-inbox fa-2x mb-2"></i>
                    <p>저장된 번호가 없습니다</p>
                    <small>소중한 번호들을 저장해보세요!</small>
                </div>
            `;
            return;
        }
        
        let html = '';
        numbers.slice(-10).reverse().forEach(item => {  // 최근 10개만 표시
            html += `
                <div class="saved-number-item mb-3 p-3 border rounded">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h6 class="mb-0">${item.label}</h6>
                        <small class="text-muted">${new Date(item.saved_at).toLocaleString()}</small>
                    </div>
                    
                    <div class="number-display mb-2">
                        ${item.numbers.map(num => `<span class="number-ball">${num}</span>`).join('')}
                    </div>
                    
                    <div class="d-flex justify-content-between">
                        <small class="text-muted">
                            합계: ${item.analysis.sum} | 홀짝: ${item.analysis.odd_count}:${item.analysis.even_count}
                        </small>
                        <button class="btn btn-sm btn-outline-danger" onclick="window.lottoPro.modules.savedNumbers.remove('${item.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    },
    
    /**
     * 번호 제거
     */
    remove: function(id) {
        window.lottoPro.state.savedNumbers = window.lottoPro.state.savedNumbers.filter(item => item.id !== id);
        this.updateDisplay();
        window.lottoPro.utils.showToast('번호가 삭제되었습니다.', 'info');
    }
};

// ===== Global Functions =====

/**
 * 메인 예측 생성 함수
 */
window.generatePrediction = function() {
    window.lottoPro.modules.prediction.generate();
};

/**
 * 강제 새로고침 함수
 */
window.forceRefresh = function() {
    window.lottoPro.modules.prediction.forceRefresh();
};

/**
 * 캐시 클리어 함수
 */
window.clearCache = async function() {
    try {
        await window.lottoPro.api.request('/api/clear-cache', { method: 'POST' });
        window.lottoPro.utils.showToast('캐시가 클리어되었습니다.', 'success');
    } catch (error) {
        window.lottoPro.utils.showToast('캐시 클리어 실패: ' + error.message, 'danger');
    }
};

/**
 * 시스템 상태 확인 함수
 */
window.checkSystemHealth = async function() {
    try {
        const health = await window.lottoPro.api.checkHealth();
        console.log('시스템 상태:', health);
        
        const status = health.status === 'healthy' ? 'success' : 'warning';
        window.lottoPro.utils.showToast(`시스템 상태: ${health.status}`, status);
        
    } catch (error) {
        window.lottoPro.utils.showToast('상태 확인 실패: ' + error.message, 'danger');
    }
};

// ===== Application Initialization =====
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 LottoPro AI v2.0 초기화 중... (랜덤성 개선 버전)');
    
    // 초기 상태 설정
    window.lottoPro.state.lastRefreshTime = Date.now();
    
    // 자동 새로고침 (30초마다, 단 중복 감지 시에만)
    setInterval(() => {
        const stats = window.lottoPro.state.randomnessStats;
        if (stats.duplicateDetections > stats.forcedRefreshes && 
            !window.lottoPro.modules.prediction.isGenerating) {
            console.log('🔄 자동 새로고침 실행 (중복 감지로 인한)');
            window.lottoPro.modules.prediction.forceRefresh();
        }
    }, 30000);
    
    // 저장된 번호 표시 업데이트
    window.lottoPro.modules.savedNumbers.updateDisplay();
    
    console.log('✅ LottoPro AI v2.0 초기화 완료! (랜덤성 시스템 활성화)');
    console.log('🎯 개선사항: 동적 시드, 캐시 버스팅, 중복 감지, 강제 새로고침');
});

// ===== Error Handling =====
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    window.lottoPro.utils.showToast('시스템 오류가 발생했습니다.', 'danger');
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    event.preventDefault();
});

console.log('🎲 LottoPro AI v2.0 JavaScript 완전 로드 완료! (랜덤성 개선 버전)');
