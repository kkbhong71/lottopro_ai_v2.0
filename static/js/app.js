/**
 * LottoPro AI v2.0 - Main JavaScript Application
 * 15가지 기능을 지원하는 완전한 클라이언트 사이드 애플리케이션
 */

// ===== Global Application Object =====
window.lottoPro = {
    // Configuration
    config: {
        apiBaseUrl: '',
        version: '2.0.0',
        maxSavedNumbers: 50,
        maxSimulationRounds: 10000,
        debounceDelay: 300,
        animationDuration: 300
    },
    
    // State management
    state: {
        currentUser: null,
        savedNumbers: [],
        lastPrediction: null,
        systemHealth: null,
        statsData: null,
        isLoading: false
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

// ===== Utility Functions =====
window.lottoPro.utils = {
    
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
     * Format currency
     */
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('ko-KR', {
            style: 'currency',
            currency: 'KRW',
            minimumFractionDigits: 0
        }).format(amount);
    },
    
    /**
     * Format number with commas
     */
    formatNumber: function(num) {
        return new Intl.NumberFormat('ko-KR').format(num);
    },
    
    /**
     * Format date
     */
    formatDate: function(dateString) {
        return new Date(dateString).toLocaleString('ko-KR');
    },
    
    /**
     * Show toast notification
     */
    showToast: function(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} toast`;
        toast.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <span>${message}</span>
                <button type="button" class="btn-close btn-close-${type === 'warning' ? 'dark' : 'white'}" onclick="this.parentElement.parentElement.remove()"></button>
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
        spinner.className = 'loading';
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
    },
    
    /**
     * Animate number counting
     */
    animateNumber: function(element, start, end, duration = 1000) {
        const startTime = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const current = Math.floor(start + (end - start) * progress);
            element.textContent = this.formatNumber(current);
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    },
    
    /**
     * Smooth scroll to element
     */
    scrollToElement: function(element, offset = 0) {
        const targetPosition = element.offsetTop - offset;
        window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
        });
    },
    
    /**
     * Get user's location
     */
    getUserLocation: function() {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject(new Error('위치 서비스가 지원되지 않습니다.'));
                return;
            }
            
            navigator.geolocation.getCurrentPosition(
                position => resolve({
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                }),
                error => reject(error),
                { timeout: 10000 }
            );
        });
    }
};

// ===== API Client =====
window.lottoPro.api = {
    
    /**
     * Generic API request
     */
    request: async function(url, options = {}) {
        try {
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            };
            
            const config = { ...defaultOptions, ...options };
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
     * 1. AI 예측 API
     */
    predict: async function(userNumbers = []) {
        return await this.request('/api/predict', {
            method: 'POST',
            body: JSON.stringify({ user_numbers: userNumbers })
        });
    },
    
    /**
     * 2. 통계 분석 API
     */
    getStats: async function() {
        return await this.request('/api/stats');
    },
    
    /**
     * 3. 번호 저장 API
     */
    saveNumbers: async function(numbers, label) {
        return await this.request('/api/save-numbers', {
            method: 'POST',
            body: JSON.stringify({ numbers, label })
        });
    },
    
    /**
     * 4. 저장된 번호 조회 API
     */
    getSavedNumbers: async function() {
        return await this.request('/api/saved-numbers');
    },
    
    /**
     * 5. 번호 삭제 API
     */
    deleteSavedNumber: async function(id) {
        return await this.request('/api/delete-saved-number', {
            method: 'POST',
            body: JSON.stringify({ id })
        });
    },
    
    /**
     * 6. 당첨 확인 API
     */
    checkWinning: async function(numbers) {
        return await this.request('/api/check-winning', {
            method: 'POST',
            body: JSON.stringify({ numbers })
        });
    },
    
    /**
     * 7. QR 코드 생성 API
     */
    generateQR: async function(numbers) {
        return await this.request('/api/generate-qr', {
            method: 'POST',
            body: JSON.stringify({ numbers })
        });
    },
    
    /**
     * 8. 세금 계산기 API
     */
    calculateTax: async function(prizeAmount) {
        return await this.request('/api/tax-calculator', {
            method: 'POST',
            body: JSON.stringify({ prize_amount: prizeAmount })
        });
    },
    
    /**
     * 9. 시뮬레이션 API
     */
    runSimulation: async function(numbers, rounds) {
        return await this.request('/api/simulation', {
            method: 'POST',
            body: JSON.stringify({ numbers, rounds })
        });
    },
    
    /**
     * 10. 판매점 검색 API
     */
    searchStores: async function(query, lat = null, lng = null) {
        const params = new URLSearchParams();
        if (query) params.append('query', query);
        if (lat) params.append('lat', lat);
        if (lng) params.append('lng', lng);
        
        return await this.request(`/api/lottery-stores?${params}`);
    },
    
    /**
     * 11. 랜덤 번호 생성 API
     */
    generateRandom: async function(count = 1) {
        return await this.request('/api/generate-random', {
            method: 'POST',
            body: JSON.stringify({ count })
        });
    },
    
    /**
     * 12. AI 모델 정보 API
     */
    getAIModels: async function() {
        return await this.request('/api/ai-models');
    },
    
    /**
     * 13. 예측 히스토리 API
     */
    getPredictionHistory: async function() {
        return await this.request('/api/prediction-history');
    },
    
    /**
     * 14. 시스템 상태 API
     */
    checkHealth: async function() {
        return await this.request('/api/health');
    }
};

// ===== Feature Modules =====

/**
 * AI 예측 모듈
 */
window.lottoPro.modules.prediction = {
    
    /**
     * 예측 생성
     */
    generate: async function() {
        try {
            // 사용자 입력 수집
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
            const validation = window.lottoPro.utils.validateNumbers(userNumbers.length === 0 ? [1,2,3,4,5,6] : userNumbers);
            if (userNumbers.length > 0 && !validation.valid) {
                window.lottoPro.utils.showToast(validation.error, 'warning');
                return;
            }
            
            // 로딩 표시
            const resultsElement = document.getElementById('results');
            const loadingElement = document.getElementById('loading');
            
            if (resultsElement) resultsElement.style.display = 'none';
            if (loadingElement) loadingElement.style.display = 'block';
            
            // API 호출
            const response = await window.lottoPro.api.predict(userNumbers);
            
            if (response.success) {
                this.displayResults(response);
                window.lottoPro.state.lastPrediction = response;
                window.lottoPro.utils.showToast('AI 예측이 완료되었습니다!', 'success');
            } else {
                throw new Error(response.error || '예측 생성에 실패했습니다.');
            }
            
        } catch (error) {
            console.error('Prediction failed:', error);
            window.lottoPro.utils.showToast('예측 생성 중 오류가 발생했습니다: ' + error.message, 'danger');
        } finally {
            const loadingElement = document.getElementById('loading');
            if (loadingElement) loadingElement.style.display = 'none';
        }
    },
    
    /**
     * 예측 결과 표시
     */
    displayResults: function(data) {
        const resultsElement = document.getElementById('results');
        const topRecommendationsElement = document.getElementById('top-recommendations');
        const modelResultsElement = document.getElementById('model-results');
        
        if (!resultsElement) return;
        
        // TOP 추천 표시
        if (topRecommendationsElement && data.top_recommendations) {
            let topHtml = '';
            data.top_recommendations.slice(0, 5).forEach((numbers, index) => {
                topHtml += `
                    <div class="col-md-6 mb-3">
                        <div class="prediction-result ${index === 0 ? 'prediction-result-top' : ''}">
                            <h6 class="fw-bold d-flex justify-content-between align-items-center">
                                <span><i class="fas fa-star text-warning me-2"></i>추천 ${index + 1}</span>
                                <button class="btn btn-sm btn-outline-primary" onclick="window.lottoPro.modules.savedNumbers.quickSave([${numbers.join(',')}], 'AI 추천 ${index + 1}')">
                                    <i class="fas fa-heart me-1"></i>저장
                                </button>
                            </h6>
                            <div class="number-display">
                                ${numbers.map(num => `<span class="number-ball">${num}</span>`).join('')}
                            </div>
                            <div class="mt-2">
                                <small class="text-muted">
                                    합계: ${numbers.reduce((a, b) => a + b, 0)} | 
                                    홀짝: ${numbers.filter(n => n % 2 === 1).length}:${numbers.filter(n => n % 2 === 0).length}
                                </small>
                            </div>
                        </div>
                    </div>
                `;
            });
            topRecommendationsElement.innerHTML = topHtml;
        }
        
        // 모델별 결과 표시
        if (modelResultsElement && data.models) {
            let modelHtml = '';
            Object.entries(data.models).forEach(([modelName, modelData]) => {
                modelHtml += `
                    <div class="col-lg-6 mb-4">
                        <div class="card h-100">
                            <div class="card-header bg-primary text-white">
                                <h6 class="mb-0 d-flex justify-content-between align-items-center">
                                    <span><i class="fas fa-robot me-2"></i>${modelName}</span>
                                    <span class="badge bg-light text-dark">${modelData.accuracy}% 정확도</span>
                                </h6>
                            </div>
                            <div class="card-body">
                                <p class="text-muted small">${modelData.description}</p>
                                
                                <!-- 정확도 바 -->
                                <div class="model-accuracy-bar">
                                    <div class="model-accuracy-fill" style="width: ${modelData.accuracy}%"></div>
                                </div>
                                <small class="text-muted">정확도: ${modelData.accuracy}%</small>
                                
                                <!-- 예측 번호들 -->
                                <div class="mt-3">
                                    <h6>예측 번호 (상위 3개)</h6>
                                    ${modelData.predictions.slice(0, 3).map((numbers, idx) => `
                                        <div class="prediction-result mb-2">
                                            <div class="d-flex justify-content-between align-items-center mb-2">
                                                <span class="small fw-bold">예측 ${idx + 1}</span>
                                                <button class="btn btn-sm btn-outline-success" onclick="window.lottoPro.modules.savedNumbers.quickSave([${numbers.join(',')}], '${modelName} 예측')">
                                                    <i class="fas fa-heart me-1"></i>저장
                                                </button>
                                            </div>
                                            <div class="number-display justify-content-start">
                                                ${numbers.map(num => `<span class="number-ball">${num}</span>`).join('')}
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            modelResultsElement.innerHTML = modelHtml;
        }
        
        // 결과 섹션 표시
        resultsElement.style.display = 'block';
        
        // 결과로 스크롤
        window.lottoPro.utils.scrollToElement(resultsElement, 100);
    }
};

/**
 * 저장된 번호 관리 모듈
 */
window.lottoPro.modules.savedNumbers = {
    
    /**
     * 저장된 번호 로드
     */
    load: async function() {
        try {
            const response = await window.lottoPro.api.getSavedNumbers();
            if (response.success) {
                window.lottoPro.state.savedNumbers = response.saved_numbers;
                this.display();
                this.updateCount();
            }
        } catch (error) {
            console.error('Failed to load saved numbers:', error);
        }
    },
    
    /**
     * 번호 저장
     */
    save: async function() {
        try {
            const numbers = [];
            const label = document.getElementById('save-label')?.value || `저장된 번호 ${new Date().toLocaleString()}`;
            
            for (let i = 1; i <= 6; i++) {
                const input = document.getElementById(`save-num${i}`);
                if (input && input.value) {
                    numbers.push(parseInt(input.value));
                }
            }
            
            const validation = window.lottoPro.utils.validateNumbers(numbers);
            if (!validation.valid) {
                window.lottoPro.utils.showToast(validation.error, 'warning');
                return;
            }
            
            const response = await window.lottoPro.api.saveNumbers(numbers, label);
            if (response.success) {
                await this.load();
                this.clearInputs();
                window.lottoPro.utils.showToast('번호가 저장되었습니다!', 'success');
            } else {
                throw new Error(response.error);
            }
            
        } catch (error) {
            console.error('Save failed:', error);
            window.lottoPro.utils.showToast('저장 중 오류가 발생했습니다: ' + error.message, 'danger');
        }
    },
    
    /**
     * 빠른 저장
     */
    quickSave: async function(numbers, label) {
        try {
            const response = await window.lottoPro.api.saveNumbers(numbers, label);
            if (response.success) {
                await this.load();
                window.lottoPro.utils.showToast('번호가 저장되었습니다!', 'success');
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            console.error('Quick save failed:', error);
            window.lottoPro.utils.showToast('저장 실패: ' + error.message, 'danger');
        }
    },
    
    /**
     * 번호 삭제
     */
    delete: async function(id) {
        if (!confirm('정말 삭제하시겠습니까?')) return;
        
        try {
            const response = await window.lottoPro.api.deleteSavedNumber(id);
            if (response.success) {
                await this.load();
                window.lottoPro.utils.showToast('번호가 삭제되었습니다.', 'success');
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            console.error('Delete failed:', error);
            window.lottoPro.utils.showToast('삭제 실패: ' + error.message, 'danger');
        }
    },
    
    /**
     * 저장된 번호 표시
     */
    display: function() {
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
        numbers.forEach(item => {
            html += `
                <div class="saved-number-item" data-id="${item.id}">
                    <div class="saved-number-actions">
                        <button class="btn btn-sm btn-outline-primary me-1" onclick="window.lottoPro.modules.tools.checkWinning([${item.numbers.join(',')}])">
                            <i class="fas fa-search"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="window.lottoPro.modules.savedNumbers.delete('${item.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                    
                    <div class="saved-number-label">${item.label}</div>
                    
                    <div class="number-display justify-content-start mb-2">
                        ${item.numbers.map(num => `<span class="number-ball">${num}</span>`).join('')}
                    </div>
                    
                    <div class="saved-number-date">${window.lottoPro.utils.formatDate(item.saved_at)}</div>
                    
                    ${item.analysis ? `
                        <div class="saved-number-analysis">
                            <div class="analysis-item">
                                <div class="analysis-value">${item.analysis.sum}</div>
                                <div>합계</div>
                            </div>
                            <div class="analysis-item">
                                <div class="analysis-value">${item.analysis.odd_count}:${item.analysis.even_count}</div>
                                <div>홀짝</div>
                            </div>
                            <div class="analysis-item">
                                <div class="analysis-value">${item.analysis.range}</div>
                                <div>범위</div>
                            </div>
                            <div class="analysis-item">
                                <div class="analysis-value">${item.analysis.consecutive}</div>
                                <div>연속</div>
                            </div>
                        </div>
                    ` : ''}
                </div>
            `;
        });
        
        container.innerHTML = html;
    },
    
    /**
     * 카운트 업데이트
     */
    updateCount: function() {
        const countElements = document.querySelectorAll('#saved-count-badge, #nav-saved-count, #total-saved');
        const count = window.lottoPro.state.savedNumbers.length;
        
        countElements.forEach(element => {
            if (element) {
                element.textContent = count;
            }
        });
    },
    
    /**
     * 입력 필드 초기화
     */
    clearInputs: function() {
        const labelInput = document.getElementById('save-label');
        if (labelInput) labelInput.value = '';
        
        for (let i = 1; i <= 6; i++) {
            const input = document.getElementById(`save-num${i}`);
            if (input) input.value = '';
        }
    }
};

/**
 * 통계 분석 모듈
 */
window.lottoPro.modules.stats = {
    
    /**
     * 통계 데이터 로드
     */
    load: async function() {
        try {
            const response = await window.lottoPro.api.getStats();
            if (response.success) {
                window.lottoPro.state.statsData = response;
                this.display();
            }
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    },
    
    /**
     * 통계 데이터 표시
     */
    display: function() {
        const data = window.lottoPro.state.statsData;
        if (!data) return;
        
        // 핫 넘버 표시
        const hotNumbersElement = document.getElementById('hotNumbers');
        if (hotNumbersElement && data.hot_numbers) {
            const hotHtml = data.hot_numbers.map(([num, freq]) => 
                `<span class="number-ball number-ball-hot" title="출현 ${freq}회">${num}</span>`
            ).join('');
            hotNumbersElement.innerHTML = hotHtml;
        }
        
        // 콜드 넘버 표시
        const coldNumbersElement = document.getElementById('coldNumbers');
        if (coldNumbersElement && data.cold_numbers) {
            const coldHtml = data.cold_numbers.map(([num, freq]) => 
                `<span class="number-ball number-ball-cold" title="출현 ${freq}회">${num}</span>`
            ).join('');
            coldNumbersElement.innerHTML = coldHtml;
        }
        
        // 이월수 분석 표시
        this.displayCarryOverAnalysis(data.carry_over_analysis);
        
        // 궁합수 분석 표시
        this.displayCompanionAnalysis(data.companion_analysis);
        
        // 패턴 분석 표시
        this.displayPatternAnalysis(data.pattern_analysis);
    },
    
    displayCarryOverAnalysis: function(data) {
        const element = document.getElementById('carryOverAnalysis');
        if (!element || !data) return;
        
        let html = '<div class="small mb-3">최근 20회차 이월수 현황</div>';
        
        if (data.length > 0) {
            html += data.slice(0, 10).map(item => `
                <div class="d-flex justify-content-between align-items-center mb-2 p-2 bg-light rounded">
                    <span class="fw-bold">${item.round}회차</span>
                    <div>
                        ${item.carry_over_numbers.length > 0 ? 
                            item.carry_over_numbers.map(num => `<span class="badge bg-warning text-dark me-1">${num}</span>`).join('') :
                            '<span class="text-muted">없음</span>'
                        }
                    </div>
                    <span class="badge bg-primary">${item.count}개</span>
                </div>
            `).join('');
        } else {
            html += '<p class="text-muted">데이터를 불러오는 중...</p>';
        }
        
        element.innerHTML = html;
    },
    
    displayCompanionAnalysis: function(data) {
        const element = document.getElementById('companionAnalysis');
        if (!element || !data) return;
        
        let html = '<div class="small mb-3">자주 함께 나오는 번호 조합</div>';
        
        if (data.length > 0) {
            html += data.slice(0, 5).map(([[num1, num2], freq]) => `
                <div class="d-flex justify-content-between align-items-center mb-2 p-2 bg-light rounded">
                    <div>
                        <span class="number-ball me-1" style="width: 30px; height: 30px; line-height: 30px; font-size: 0.8rem;">${num1}</span>
                        <span class="number-ball" style="width: 30px; height: 30px; line-height: 30px; font-size: 0.8rem;">${num2}</span>
                    </div>
                    <span class="badge bg-success">${freq}회</span>
                </div>
            `).join('');
        } else {
            html += '<p class="text-muted">데이터를 분석하는 중...</p>';
        }
        
        element.innerHTML = html;
    },
    
    displayPatternAnalysis: function(data) {
        const element = document.getElementById('patternAnalysis');
        if (!element || !data) return;
        
        let html = '<div class="small mb-3">최근 패턴 분석</div>';
        
        if (data.consecutive_count && data.odd_even_ratio) {
            const avgConsecutive = data.consecutive_count.reduce((a, b) => a + b, 0) / data.consecutive_count.length;
            const oddEvenCounts = {};
            data.odd_even_ratio.forEach(ratio => {
                oddEvenCounts[ratio] = (oddEvenCounts[ratio] || 0) + 1;
            });
            const mostCommonRatio = Object.keys(oddEvenCounts).reduce((a, b) => 
                oddEvenCounts[a] > oddEvenCounts[b] ? a : b
            );
            
            html += `
                <div class="row">
                    <div class="col-6">
                        <div class="text-center p-2 bg-light rounded mb-2">
                            <div class="fw-bold text-primary">${avgConsecutive.toFixed(1)}</div>
                            <small>평균 연속번호</small>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="text-center p-2 bg-light rounded mb-2">
                            <div class="fw-bold text-success">${mostCommonRatio}</div>
                            <small>가장 흔한 홀짝비</small>
                        </div>
                    </div>
                </div>
            `;
        } else {
            html += '<p class="text-muted">패턴을 분석하는 중...</p>';
        }
        
        element.innerHTML = html;
    }
};

/**
 * 도구 기능 모듈
 */
window.lottoPro.modules.tools = {
    
    /**
     * 세금 계산
     */
    calculateTax: async function() {
        const amountInput = document.getElementById('tax-amount');
        if (!amountInput || !amountInput.value) {
            window.lottoPro.utils.showToast('당첨금액을 입력해주세요.', 'warning');
            return;
        }
        
        try {
            const amount = parseInt(amountInput.value.replace(/[^0-9]/g, ''));
            const response = await window.lottoPro.api.calculateTax(amount);
            
            if (response.success) {
                this.displayTaxResult(response);
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            console.error('Tax calculation failed:', error);
            window.lottoPro.utils.showToast('세금 계산 실패: ' + error.message, 'danger');
        }
    },
    
    /**
     * 세금 계산 결과 표시
     */
    displayTaxResult: function(data) {
        const resultElement = document.getElementById('tax-result');
        if (!resultElement) return;
        
        const html = `
            <div class="calculator-result">
                <h6 class="fw-bold mb-3">세금 계산 결과</h6>
                
                <div class="row">
                    <div class="col-sm-6">
                        <div class="text-center p-2 bg-primary text-white rounded mb-2">
                            <div class="fw-bold">${window.lottoPro.utils.formatCurrency(data.prize_amount)}</div>
                            <small>당첨금액</small>
                        </div>
                    </div>
                    <div class="col-sm-6">
                        <div class="text-center p-2 bg-danger text-white rounded mb-2">
                            <div class="fw-bold">${window.lottoPro.utils.formatCurrency(data.tax_amount)}</div>
                            <small>세금 (${data.effective_tax_rate}%)</small>
                        </div>
                    </div>
                </div>
                
                <div class="text-center p-3 bg-success text-white rounded">
                    <div class="h5 fw-bold mb-1">${window.lottoPro.utils.formatCurrency(data.net_amount)}</div>
                    <small>실수령액</small>
                </div>
                
                <div class="mt-3">
                    <small class="text-muted">
                        <strong>과세 구간:</strong> ${data.tax_brackets}<br>
                        <strong>비과세 금액:</strong> ${window.lottoPro.utils.formatCurrency(data.tax_free_amount)}
                    </small>
                </div>
            </div>
        `;
        
        resultElement.innerHTML = html;
        resultElement.classList.remove('d-none');
    },
    
    /**
     * 당첨 확인
     */
    checkWinning: async function(numbers) {
        try {
            const response = await window.lottoPro.api.checkWinning(numbers);
            
            if (response.success) {
                this.displayWinningResult(response);
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            console.error('Winning check failed:', error);
            window.lottoPro.utils.showToast('당첨 확인 실패: ' + error.message, 'danger');
        }
    },
    
    /**
     * 당첨 확인 결과 표시
     */
    displayWinningResult: function(data) {
        const prizeClass = data.prize === '낙첨' ? 'danger' : 
                          ['1등', '2등'].includes(data.prize) ? 'success' : 'warning';
        
        const modalHtml = `
            <div class="modal fade" id="winningModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-${prizeClass} text-white">
                            <h5 class="modal-title">
                                <i class="fas fa-trophy me-2"></i>${data.round}회차 당첨 결과
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="text-center mb-4">
                                <div class="h2 text-${prizeClass} fw-bold">${data.prize}</div>
                                <div class="h4">${data.prize_money}</div>
                            </div>
                            
                            <div class="row mb-3">
                                <div class="col-6">
                                    <div class="text-center">
                                        <div class="small text-muted mb-2">내 번호</div>
                                        <div class="number-display justify-content-center">
                                            ${data.user_numbers.map(num => `<span class="number-ball">${num}</span>`).join('')}
                                        </div>
                                    </div>
                                </div>
                                <div class="col-6">
                                    <div class="text-center">
                                        <div class="small text-muted mb-2">당첨 번호</div>
                                        <div class="number-display justify-content-center">
                                            ${data.winning_numbers.map(num => `<span class="number-ball ${data.user_numbers.includes(num) ? 'number-ball-hot' : ''}">${num}</span>`).join('')}
                                        </div>
                                        <div class="mt-2">
                                            <span class="small">보너스: </span>
                                            <span class="number-ball ${data.bonus_match ? 'number-ball-hot' : ''}" style="width: 30px; height: 30px; line-height: 30px;">${data.bonus_number}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="alert alert-info">
                                <div class="row text-center">
                                    <div class="col-6">
                                        <div class="fw-bold">${data.matches}개</div>
                                        <small>번호 일치</small>
                                    </div>
                                    <div class="col-6">
                                        <div class="fw-bold">${data.bonus_match ? 'O' : 'X'}</div>
                                        <small>보너스 일치</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">닫기</button>
                            ${data.prize !== '낙첨' ? `
                                <button type="button" class="btn btn-success" onclick="window.lottoPro.modules.tools.calculateTaxForWinning(${data.prize_money.replace(/[^0-9]/g, '')})">
                                    <i class="fas fa-calculator me-1"></i>세금 계산
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 기존 모달 제거
        const existingModal = document.getElementById('winningModal');
        if (existingModal) existingModal.remove();
        
        // 새 모달 추가
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // 모달 표시
        const modal = new bootstrap.Modal(document.getElementById('winningModal'));
        modal.show();
    },
    
    /**
     * 당첨금 세금 계산
     */
    calculateTaxForWinning: function(amount) {
        const taxAmountInput = document.getElementById('tax-amount');
        if (taxAmountInput) {
            taxAmountInput.value = amount;
            this.calculateTax();
            
            // 모달 닫고 세금 계산기로 스크롤
            const modal = bootstrap.Modal.getInstance(document.getElementById('winningModal'));
            if (modal) modal.hide();
            
            const toolsSection = document.getElementById('tools');
            if (toolsSection) {
                window.lottoPro.utils.scrollToElement(toolsSection, 100);
            }
        }
    }
};

// ===== Event Handlers =====
window.lottoPro.events = {
    
    /**
     * DOM 로드 완료 후 초기화
     */
    onDOMContentLoaded: function() {
        console.log('🎯 LottoPro AI v2.0 초기화 중...');
        
        // 기본 이벤트 리스너 등록
        this.registerEventListeners();
        
        // 초기 데이터 로드
        this.loadInitialData();
        
        // 키보드 단축키 등록
        this.registerKeyboardShortcuts();
        
        // PWA 설치 이벤트 등록
        this.registerPWAEvents();
        
        console.log('✅ LottoPro AI v2.0 초기화 완료!');
    },
    
    /**
     * 이벤트 리스너 등록
     */
    registerEventListeners: function() {
        // 예측 폼 제출
        const predictionForm = document.getElementById('predictionForm');
        if (predictionForm) {
            predictionForm.addEventListener('submit', (e) => {
                e.preventDefault();
                window.lottoPro.modules.prediction.generate();
            });
        }
        
        // 번호 저장 폼
        const saveForm = document.querySelector('[onclick*="saveNumbers"]');
        if (saveForm) {
            saveForm.addEventListener('click', (e) => {
                e.preventDefault();
                window.lottoPro.modules.savedNumbers.save();
            });
        }
        
        // 세금 계산
        const taxButton = document.querySelector('[onclick*="calculateTax"]');
        if (taxButton) {
            taxButton.addEventListener('click', (e) => {
                e.preventDefault();
                window.lottoPro.modules.tools.calculateTax();
            });
        }
        
        // 번호 입력 검증
        document.querySelectorAll('.number-input').forEach(input => {
            input.addEventListener('input', this.validateNumberInput);
            input.addEventListener('keypress', this.handleNumberKeyPress);
        });
        
        // 스크롤 이벤트 (네비게이션 상태 변경)
        window.addEventListener('scroll', this.handleScroll);
        
        // 뒤로 가기 버튼
        const backToTopBtn = document.getElementById('back-to-top');
        if (backToTopBtn) {
            backToTopBtn.addEventListener('click', () => {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        }
    },
    
    /**
     * 초기 데이터 로드
     */
    loadInitialData: async function() {
        try {
            // 시스템 상태 확인
            await this.checkSystemHealth();
            
            // 저장된 번호 로드
            await window.lottoPro.modules.savedNumbers.load();
            
            // 통계 데이터 로드
            await window.lottoPro.modules.stats.load();
            
        } catch (error) {
            console.error('Initial data load failed:', error);
        }
    },
    
    /**
     * 시스템 상태 확인
     */
    checkSystemHealth: async function() {
        try {
            const response = await window.lottoPro.api.checkHealth();
            window.lottoPro.state.systemHealth = response;
            
            // 상태 표시 업데이트
            this.updateHealthStatus(response);
            
        } catch (error) {
            console.error('Health check failed:', error);
        }
    },
    
    /**
     * 상태 표시 업데이트
     */
    updateHealthStatus: function(health) {
        const statusElements = document.querySelectorAll('#status-text, #nav-data-source');
        statusElements.forEach(element => {
            if (element && element.id === 'status-text') {
                element.textContent = health.status === 'healthy' ? '정상 운영' : '서비스 점검';
                element.className = health.status === 'healthy' ? 'text-success fw-bold' : 'text-warning fw-bold';
            }
            if (element && element.id === 'nav-data-source') {
                element.textContent = health.data_source || '데이터 로딩 중';
            }
        });
    },
    
    /**
     * 번호 입력 검증
     */
    validateNumberInput: function(event) {
        const input = event.target;
        const value = parseInt(input.value);
        
        if (input.value === '') {
            input.setCustomValidity('');
            return;
        }
        
        if (isNaN(value) || value < 1 || value > 45) {
            input.setCustomValidity('1-45 사이의 번호를 입력해주세요.');
            input.classList.add('is-invalid');
        } else {
            input.setCustomValidity('');
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
        }
    },
    
    /**
     * 번호 입력 키 처리
     */
    handleNumberKeyPress: function(event) {
        // Enter 키로 다음 입력으로 이동
        if (event.key === 'Enter') {
            event.preventDefault();
            const inputs = document.querySelectorAll('.number-input');
            const currentIndex = Array.from(inputs).indexOf(event.target);
            
            if (currentIndex < inputs.length - 1) {
                inputs[currentIndex + 1].focus();
            } else {
                // 마지막 입력이면 예측 생성
                window.lottoPro.modules.prediction.generate();
            }
        }
    },
    
    /**
     * 스크롤 처리
     */
    handleScroll: function() {
        const navbar = document.querySelector('.navbar');
        const backToTopBtn = document.getElementById('back-to-top');
        
        // 네비게이션 스타일 변경
        if (navbar) {
            if (window.scrollY > 100) {
                navbar.classList.add('navbar-scrolled');
            } else {
                navbar.classList.remove('navbar-scrolled');
            }
        }
        
        // 뒤로 가기 버튼 표시/숨김
        if (backToTopBtn) {
            if (window.scrollY > 300) {
                backToTopBtn.style.display = 'flex';
                backToTopBtn.classList.add('visible');
            } else {
                backToTopBtn.classList.remove('visible');
                setTimeout(() => {
                    if (window.scrollY <= 300) {
                        backToTopBtn.style.display = 'none';
                    }
                }, 300);
            }
        }
    },
    
    /**
     * 키보드 단축키 등록
     */
    registerKeyboardShortcuts: function() {
        document.addEventListener('keydown', (event) => {
            // Ctrl+P: AI 예측
            if (event.ctrlKey && event.key === 'p') {
                event.preventDefault();
                window.lottoPro.modules.prediction.generate();
            }
            
            // Ctrl+S: 빠른 저장 모달
            if (event.ctrlKey && event.key === 's') {
                event.preventDefault();
                this.openQuickSaveModal();
            }
            
            // Home: 맨 위로
            if (event.key === 'Home') {
                event.preventDefault();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
            
            // F5: 새로고침 대신 데이터 갱신
            if (event.key === 'F5') {
                event.preventDefault();
                this.refreshData();
            }
        });
    },
    
    /**
     * PWA 설치 이벤트
     */
    registerPWAEvents: function() {
        let deferredPrompt;
        const installButton = document.getElementById('install-pwa');
        
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            if (installButton) {
                installButton.classList.remove('d-none');
            }
        });
        
        if (installButton) {
            installButton.addEventListener('click', async () => {
                if (deferredPrompt) {
                    deferredPrompt.prompt();
                    const { outcome } = await deferredPrompt.userChoice;
                    console.log(`PWA 설치 결과: ${outcome}`);
                    deferredPrompt = null;
                    installButton.classList.add('d-none');
                }
            });
        }
    },
    
    /**
     * 빠른 저장 모달 열기
     */
    openQuickSaveModal: function() {
        // 모달이 없다면 생성
        let modal = document.getElementById('quickSaveModal');
        if (!modal) {
            const modalHtml = `
                <div class="modal fade" id="quickSaveModal" tabindex="-1">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header bg-primary text-white">
                                <h5 class="modal-title">
                                    <i class="fas fa-lightning-bolt me-2"></i>빠른 저장
                                </h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="mb-3">
                                    <label class="form-label">라벨</label>
                                    <input type="text" class="form-control" id="quick-save-label" placeholder="예: AI 추천 번호">
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">번호 (쉼표로 구분)</label>
                                    <input type="text" class="form-control" id="quick-save-numbers" 
                                           placeholder="예: 1, 7, 13, 25, 31, 42">
                                    <div class="form-text">번호를 쉼표(,)로 구분하여 입력하세요</div>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">취소</button>
                                <button type="button" class="btn btn-primary" onclick="window.lottoPro.events.quickSave()">저장</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            modal = document.getElementById('quickSaveModal');
        }
        
        // 모달 표시
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
    },
    
    /**
     * 빠른 저장 실행
     */
    quickSave: function() {
        const label = document.getElementById('quick-save-label').value.trim();
        const numbersInput = document.getElementById('quick-save-numbers').value.trim();
        
        if (!label) {
            window.lottoPro.utils.showToast('라벨을 입력해주세요.', 'warning');
            return;
        }
        
        if (!numbersInput) {
            window.lottoPro.utils.showToast('번호를 입력해주세요.', 'warning');
            return;
        }
        
        // 번호 파싱
        const numbers = numbersInput.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n) && n >= 1 && n <= 45);
        
        const validation = window.lottoPro.utils.validateNumbers(numbers);
        if (!validation.valid) {
            window.lottoPro.utils.showToast(validation.error, 'warning');
            return;
        }
        
        // 저장 실행
        window.lottoPro.modules.savedNumbers.quickSave(numbers, label).then(() => {
            // 모달 닫기
            const modal = bootstrap.Modal.getInstance(document.getElementById('quickSaveModal'));
            if (modal) modal.hide();
            
            // 입력 필드 초기화
            document.getElementById('quick-save-label').value = '';
            document.getElementById('quick-save-numbers').value = '';
        });
    },
    
    /**
     * 데이터 새로고침
     */
    refreshData: async function() {
        window.lottoPro.utils.showToast('데이터를 새로고침합니다...', 'info');
        
        try {
            await this.loadInitialData();
            window.lottoPro.utils.showToast('데이터 새로고침 완료!', 'success');
        } catch (error) {
            window.lottoPro.utils.showToast('데이터 새로고침 실패: ' + error.message, 'danger');
        }
    }
};

// ===== Global Functions (for backward compatibility) =====
window.generatePrediction = () => window.lottoPro.modules.prediction.generate();
window.checkHealth = () => window.lottoPro.events.checkSystemHealth();
window.loadSavedNumbers = () => window.lottoPro.modules.savedNumbers.load();
window.loadStats = () => window.lottoPro.modules.stats.load();
window.saveNumbers = () => window.lottoPro.modules.savedNumbers.save();
window.calculateTax = () => window.lottoPro.modules.tools.calculateTax();

// ===== Application Initialization =====
document.addEventListener('DOMContentLoaded', () => {
    window.lottoPro.events.onDOMContentLoaded();
});

// ===== Error Handling =====
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    // 선택적으로 에러 추적 서비스로 전송
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    event.preventDefault();
});

// ===== Performance Monitoring =====
window.addEventListener('load', () => {
    const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
    console.log(`페이지 로드 시간: ${loadTime}ms`);
    
    if (loadTime > 3000) {
        console.warn('페이지 로드가 느립니다.');
    }
});

console.log('🚀 LottoPro AI v2.0 JavaScript 로드 완료!');
