class LottoApp {
    constructor() {
        this.algorithms = {};
        this.statistics = {};
        this.currentModalData = null;
        this.isLoading = false;
        this.retryCount = 0;
        this.maxRetries = 3;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadInitialDataWithRetry();
        this.checkForWeeklyUpdate();
        console.log('🎰 로또프로 AI v2.0 초기화 완료 (메모리 최적화)');
    }

    bindEvents() {
        // 메인 버튼 이벤트
        document.getElementById('generateBtn').addEventListener('click', () => {
            if (!this.isLoading) {
                this.generatePredictions();
            }
        });

        document.getElementById('statisticsBtn').addEventListener('click', () => {
            if (!this.isLoading) {
                this.toggleStatistics();
            }
        });

        // 카테고리 필터 버튼 이벤트
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('category-filter')) {
                this.filterAlgorithms(e.target.dataset.category);
            }
        });

        // 모달 이벤트
        const closeButtons = document.querySelectorAll('.close');
        closeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                this.closeModal();
            });
        });

        document.getElementById('copyNumbers').addEventListener('click', () => {
            this.copyNumbers();
        });

        document.getElementById('saveNumbers').addEventListener('click', () => {
            this.saveNumbers();
        });

        // 모달 외부 클릭시 닫기
        window.addEventListener('click', (event) => {
            const modal = document.getElementById('numbersModal');
            if (event.target === modal) {
                this.closeModal();
            }
        });

        // 네트워크 상태 모니터링
        window.addEventListener('online', () => {
            this.showSuccess('네트워크 연결이 복구되었습니다.');
        });

        window.addEventListener('offline', () => {
            this.showError('네트워크 연결이 끊어졌습니다.');
        });
    }

    // 향상된 fetch 함수 (타임아웃 및 재시도 로직 포함)
    async fetchWithTimeout(url, options = {}) {
        const timeout = options.timeout || 30000; // 30초 타임아웃
        
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
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            
            if (error.name === 'AbortError') {
                throw new Error('요청 시간이 초과되었습니다. 서버가 과부하 상태일 수 있습니다.');
            }
            
            throw error;
        }
    }

    async loadInitialDataWithRetry() {
        for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
            try {
                console.log(`📡 데이터 로드 시도 ${attempt}/${this.maxRetries}`);
                
                const response = await this.fetchWithTimeout('/api/statistics', { timeout: 20000 });
                const data = await response.json();
                
                if (data.success) {
                    this.updateDataInfo(data.data);
                    console.log('✅ 초기 데이터 로드 성공');
                    return;
                } else {
                    throw new Error(data.error || '서버에서 에러를 반환했습니다.');
                }
            } catch (error) {
                console.error(`❌ 데이터 로드 시도 ${attempt} 실패:`, error.message);
                
                if (attempt === this.maxRetries) {
                    this.showError(`초기 데이터 로드에 실패했습니다: ${error.message}`);
                    this.showFallbackData();
                } else {
                    // 재시도 전 대기 (지수 백오프)
                    const delay = Math.min(1000 * Math.pow(2, attempt - 1), 5000);
                    console.log(`⏳ ${delay}ms 후 재시도...`);
                    await new Promise(resolve => setTimeout(resolve, delay));
                }
            }
        }
    }

    showFallbackData() {
        // 네트워크 실패 시 기본 데이터 표시
        const fallbackData = {
            total_draws: 1187,
            last_draw_info: {
                round: 1187,
                date: '알 수 없음',
                numbers: [1, 2, 3, 4, 5, 6],
                bonus: 7
            }
        };
        
        this.updateDataInfo(fallbackData);
        this.showError('서버 연결 실패로 기본 정보를 표시합니다.');
    }

    updateDataInfo(data) {
        try {
            document.getElementById('totalDraws').textContent = 
                data.total_draws ? data.total_draws.toLocaleString() : '알 수 없음';
            document.getElementById('lastDraw').textContent = 
                data.last_draw_info ? `${data.last_draw_info.round}회` : '알 수 없음';
            
            this.displayRecentWinningNumbers(data);
            this.displayDataUpdateInfo(data);
        } catch (error) {
            console.error('데이터 표시 중 오류:', error);
        }
    }

    displayRecentWinningNumbers(data) {
        try {
            const recentRoundText = document.getElementById('recentRoundText');
            const recentRoundDate = document.getElementById('recentRoundDate');
            const recentWinningNumbers = document.getElementById('recentWinningNumbers');
            
            if (data.last_draw_info && recentWinningNumbers) {
                const { round, date, numbers, bonus } = data.last_draw_info;
                
                if (recentRoundText) {
                    recentRoundText.textContent = `${round}회차`;
                }
                if (recentRoundDate) {
                    recentRoundDate.textContent = this.formatDate(date);
                }
                
                // 당첨번호 표시 (애니메이션 간소화)
                recentWinningNumbers.innerHTML = '';
                
                // 일반 번호 6개
                numbers.forEach((num) => {
                    const numberElement = document.createElement('span');
                    numberElement.className = 'recent-number';
                    numberElement.textContent = num;
                    recentWinningNumbers.appendChild(numberElement);
                });
                
                // 보너스 번호
                const bonusElement = document.createElement('span');
                bonusElement.className = 'recent-number recent-bonus';
                bonusElement.textContent = bonus;
                recentWinningNumbers.appendChild(bonusElement);
            }
        } catch (error) {
            console.error('당첨번호 표시 오류:', error);
        }
    }

    displayDataUpdateInfo(data) {
        try {
            const dataUpdateTime = document.getElementById('dataUpdateTime');
            if (dataUpdateTime) {
                const updateTime = data.last_updated || new Date().toLocaleDateString('ko-KR');
                dataUpdateTime.textContent = updateTime;
            }
        } catch (error) {
            console.error('업데이트 시간 표시 오류:', error);
        }
    }

    formatDate(dateString) {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('ko-KR', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        } catch (e) {
            return dateString || '알 수 없음';
        }
    }

    checkForWeeklyUpdate() {
        try {
            const now = new Date();
            const isMonday = now.getDay() === 1;
            const hour = now.getHours();
            
            if (isMonday && hour >= 9) {
                const lastUpdateCheck = localStorage.getItem('lastUpdateCheck');
                const today = now.toDateString();
                
                if (lastUpdateCheck !== today) {
                    console.log('🔄 주간 업데이트 체크 실행');
                    this.loadInitialDataWithRetry();
                    localStorage.setItem('lastUpdateCheck', today);
                    this.showSuccess('주간 회차 정보가 업데이트되었습니다!');
                }
            }
        } catch (error) {
            console.error('주간 업데이트 체크 오류:', error);
        }
    }

    async generatePredictions() {
        if (this.isLoading) return;
        
        const loadingIndicator = document.getElementById('loadingIndicator');
        const predictionsContainer = document.getElementById('predictionsContainer');
        const generateBtn = document.getElementById('generateBtn');

        try {
            this.isLoading = true;
            loadingIndicator.style.display = 'block';
            predictionsContainer.style.display = 'none';
            generateBtn.disabled = true;
            generateBtn.textContent = '분석 중...';
            
            this.updateProgress(0, '5개 AI 알고리즘 초기화 중...');
            
            const startTime = performance.now();
            
            // 최적화된 API 호출 (타임아웃 60초)
            const response = await this.fetchWithTimeout('/api/predictions', { timeout: 60000 });
            const data = await response.json();

            if (data.success && data.data) {
                this.algorithms = data.data;
                
                const algorithmCount = Object.keys(data.data).length;
                this.updateProgress(100, '분석 완료!');
                
                const processingTime = ((performance.now() - startTime) / 1000).toFixed(2);
                this.updatePerformanceIndicators(processingTime, data);
                
                this.renderPredictions();
                predictionsContainer.style.display = 'block';
                
                this.showSuccess(`✅ ${algorithmCount}개 AI 알고리즘이 분석을 완료했습니다!`);
            } else {
                throw new Error(data.error || '예측 생성에 실패했습니다.');
            }
        } catch (error) {
            console.error('예측 생성 실패:', error);
            this.showError(`예측 생성 실패: ${error.message}`);
            this.updateProgress(0, '분석 실패');
        } finally {
            this.isLoading = false;
            loadingIndicator.style.display = 'none';
            generateBtn.disabled = false;
            generateBtn.textContent = '🎲 AI 예측 생성';
        }
    }

    updateProgress(percentage, message) {
        try {
            const progressFill = document.getElementById('progressFill');
            const progressText = document.getElementById('progressText');
            
            if (progressFill) {
                progressFill.style.width = `${percentage}%`;
            }
            
            if (progressText) {
                progressText.textContent = message;
            }
        } catch (error) {
            console.error('진행 상황 업데이트 오류:', error);
        }
    }

    updatePerformanceIndicators(processingTime, data) {
        try {
            const processingTimeElement = document.getElementById('processingTime');
            const dataPointsElement = document.getElementById('dataPoints');
            
            if (processingTimeElement) {
                processingTimeElement.textContent = `${processingTime}초`;
            }
            
            if (dataPointsElement && data.total_draws) {
                dataPointsElement.textContent = `${data.total_draws.toLocaleString()}회차`;
            }
        } catch (error) {
            console.error('성능 지표 업데이트 오류:', error);
        }
    }

    renderPredictions() {
        try {
            const container = document.getElementById('algorithmsGrid');
            container.innerHTML = '';

            // 카테고리 필터 (5개 알고리즘으로 수정)
            this.addCategoryFilters(container);

            const algorithmColors = {
                'frequency': '#FF6B6B',
                'hot_cold': '#4ECDC4', 
                'pattern': '#45B7D1',
                'statistical': '#96CEB4',
                'co_occurrence': '#E17055'
            };

            const algorithmIcons = {
                'frequency': 'fas fa-chart-bar',
                'hot_cold': 'fas fa-thermometer-half',
                'pattern': 'fas fa-puzzle-piece',
                'statistical': 'fas fa-calculator',
                'co_occurrence': 'fas fa-link'
            };

            // 카테고리별로 정렬
            const basicAlgorithms = {};
            const advancedAlgorithms = {};

            for (const [key, algorithm] of Object.entries(this.algorithms)) {
                if (algorithm.category === 'basic') {
                    basicAlgorithms[key] = algorithm;
                } else {
                    advancedAlgorithms[key] = algorithm;
                }
            }

            // 기본 알고리즘 섹션
            if (Object.keys(basicAlgorithms).length > 0) {
                const basicSection = this.createAlgorithmSection('기본 AI 알고리즘', 'basic-algorithms');
                container.appendChild(basicSection);

                for (const [key, algorithm] of Object.entries(basicAlgorithms)) {
                    const algorithmCard = this.createAlgorithmCard(
                        key, 
                        algorithm, 
                        algorithmColors[key] || '#999999', 
                        algorithmIcons[key] || 'fas fa-cog'
                    );
                    basicSection.appendChild(algorithmCard);
                }
            }

            // 고급 알고리즘 섹션
            if (Object.keys(advancedAlgorithms).length > 0) {
                const advancedSection = this.createAlgorithmSection('고급 AI 알고리즘', 'advanced-algorithms');
                container.appendChild(advancedSection);

                for (const [key, algorithm] of Object.entries(advancedAlgorithms)) {
                    const algorithmCard = this.createAlgorithmCard(
                        key, 
                        algorithm, 
                        algorithmColors[key] || '#999999', 
                        algorithmIcons[key] || 'fas fa-cog'
                    );
                    advancedSection.appendChild(algorithmCard);
                }
            }
        } catch (error) {
            console.error('예측 결과 렌더링 오류:', error);
            this.showError('예측 결과를 표시하는 중 오류가 발생했습니다.');
        }
    }

    addCategoryFilters(container) {
        try {
            const totalAlgorithms = Object.keys(this.algorithms).length;
            const basicCount = Object.values(this.algorithms).filter(alg => alg.category === 'basic').length;
            const advancedCount = totalAlgorithms - basicCount;

            const filterContainer = document.createElement('div');
            filterContainer.className = 'category-filters';
            filterContainer.innerHTML = `
                <h3><i class="fas fa-filter"></i> 알고리즘 필터</h3>
                <div class="filter-buttons">
                    <button class="category-filter active" data-category="all">
                        <i class="fas fa-th"></i> 전체 (${totalAlgorithms}개)
                    </button>
                    ${basicCount > 0 ? `
                    <button class="category-filter" data-category="basic">
                        <i class="fas fa-star"></i> 기본 (${basicCount}개)
                    </button>` : ''}
                    ${advancedCount > 0 ? `
                    <button class="category-filter" data-category="advanced">
                        <i class="fas fa-rocket"></i> 고급 (${advancedCount}개)
                    </button>` : ''}
                </div>
            `;
            container.appendChild(filterContainer);
        } catch (error) {
            console.error('필터 생성 오류:', error);
        }
    }

    createAlgorithmSection(title, id) {
        const section = document.createElement('div');
        section.className = 'algorithm-section';
        section.id = id;
        
        const sectionHeader = document.createElement('div');
        sectionHeader.className = 'section-header';
        sectionHeader.innerHTML = `<h3>${title}</h3>`;
        
        section.appendChild(sectionHeader);
        return section;
    }

    createAlgorithmCard(key, algorithm, color, icon) {
        try {
            const card = document.createElement('div');
            card.className = 'algorithm-card';
            card.style.borderLeftColor = color;
            card.dataset.category = algorithm.category;

            const predictionsHTML = algorithm.predictions.map((prediction, index) => {
                return `
                    <div class="number-set" data-algorithm="${key}" data-index="${index}">
                        <div class="set-label">세트 ${index + 1}</div>
                        <div class="numbers">
                            ${prediction.map(num => `<span class="number">${num}</span>`).join('')}
                        </div>
                    </div>
                `;
            }).join('');

            const categoryBadge = algorithm.category === 'advanced' ? 
                `<span class="category-badge advanced">HIGH-TECH</span>` : 
                `<span class="category-badge basic">CLASSIC</span>`;

            card.innerHTML = `
                <div class="algorithm-header">
                    <div class="algorithm-info">
                        <i class="${icon}" style="color: ${color}"></i>
                        <div>
                            <h3>${algorithm.name}</h3>
                            <p>${algorithm.description}</p>
                        </div>
                    </div>
                    <div class="algorithm-badges">
                        ${categoryBadge}
                        <div class="algorithm-badge" style="background-color: ${color}">
                            ${algorithm.predictions.length}세트
                        </div>
                    </div>
                </div>
                <div class="predictions-list">
                    ${predictionsHTML}
                </div>
            `;

            // 번호 세트 클릭 이벤트 추가
            card.addEventListener('click', (e) => {
                const numberSet = e.target.closest('.number-set');
                if (numberSet) {
                    const algorithmKey = numberSet.dataset.algorithm;
                    const index = parseInt(numberSet.dataset.index);
                    this.showNumbersModal(algorithmKey, index);
                }
            });

            return card;
        } catch (error) {
            console.error('알고리즘 카드 생성 오류:', error);
            return document.createElement('div'); // 빈 div 반환
        }
    }

    filterAlgorithms(category) {
        try {
            // 필터 버튼 활성화 상태 업데이트
            document.querySelectorAll('.category-filter').forEach(btn => {
                btn.classList.remove('active');
            });
            document.querySelector(`[data-category="${category}"]`).classList.add('active');

            // 알고리즘 카드 필터링 (애니메이션 간소화)
            const cards = document.querySelectorAll('.algorithm-card');
            const sections = document.querySelectorAll('.algorithm-section');

            if (category === 'all') {
                cards.forEach(card => card.style.display = 'block');
                sections.forEach(section => section.style.display = 'block');
            } else {
                cards.forEach(card => {
                    card.style.display = card.dataset.category === category ? 'block' : 'none';
                });

                sections.forEach(section => {
                    const visibleCards = section.querySelectorAll(`.algorithm-card[data-category="${category}"]`);
                    section.style.display = visibleCards.length > 0 ? 'block' : 'none';
                });
            }
        } catch (error) {
            console.error('필터링 오류:', error);
        }
    }

    async toggleStatistics() {
        if (this.isLoading) return;
        
        const statisticsSection = document.getElementById('statisticsSection');
        const isVisible = statisticsSection.style.display !== 'none';

        if (isVisible) {
            statisticsSection.style.display = 'none';
            return;
        }

        try {
            this.isLoading = true;
            this.showNotification('통계 데이터 로드 중...', 'info');
            
            const response = await this.fetchWithTimeout('/api/statistics', { timeout: 30000 });
            const data = await response.json();

            if (data.success) {
                this.statistics = data.data;
                this.renderStatistics();
                statisticsSection.style.display = 'block';
                
                statisticsSection.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start' 
                });
                
                this.showSuccess('통계 데이터를 성공적으로 로드했습니다.');
            } else {
                throw new Error(data.error || '통계 로드에 실패했습니다.');
            }
        } catch (error) {
            console.error('통계 로드 실패:', error);
            this.showError(`통계 데이터 로드 실패: ${error.message}`);
        } finally {
            this.isLoading = false;
        }
    }

    renderStatistics() {
        try {
            // 최근 당첨 정보
            const recentNumbers = document.getElementById('recentNumbers');
            const recentDetails = document.getElementById('recentDetails');
            
            if (this.statistics.last_draw_info && recentNumbers) {
                const lastDraw = this.statistics.last_draw_info;
                recentNumbers.innerHTML = lastDraw.numbers.map(num => 
                    `<span class="number">${num}</span>`
                ).join('') + `<span class="bonus-number">${lastDraw.bonus}</span>`;
                
                if (recentDetails) {
                    recentDetails.innerHTML = `
                        <div class="detail-item">
                            <span class="label">회차:</span>
                            <span class="value">${lastDraw.round}회</span>
                        </div>
                        <div class="detail-item">
                            <span class="label">추첨일:</span>
                            <span class="value">${lastDraw.date}</span>
                        </div>
                    `;
                }
            }

            // 빈도 통계 렌더링
            if (this.statistics.most_frequent) {
                this.renderFrequencyList('mostFrequent', this.statistics.most_frequent);
            }
            if (this.statistics.least_frequent) {
                this.renderFrequencyList('leastFrequent', this.statistics.least_frequent);
            }
            if (this.statistics.recent_hot) {
                this.renderFrequencyList('recentHot', this.statistics.recent_hot);
            }
        } catch (error) {
            console.error('통계 렌더링 오류:', error);
        }
    }

    renderFrequencyList(containerId, data) {
        try {
            const container = document.getElementById(containerId);
            if (container && data) {
                container.innerHTML = data.map((item, index) => `
                    <div class="frequency-item">
                        <span class="rank">${index + 1}</span>
                        <span class="number">${item.number}</span>
                        <span class="count">${item.count}회</span>
                    </div>
                `).join('');
            }
        } catch (error) {
            console.error('빈도 목록 렌더링 오류:', error);
        }
    }

    showNumbersModal(algorithmKey, index) {
        try {
            const algorithm = this.algorithms[algorithmKey];
            if (!algorithm || !algorithm.predictions[index]) return;
            
            const numbers = algorithm.predictions[index];
            
            this.currentModalData = {
                algorithm: algorithm.name,
                numbers: numbers,
                algorithmKey: algorithmKey,
                index: index,
                category: algorithm.category
            };

            const categoryText = algorithm.category === 'advanced' ? ' (고급 AI)' : ' (기본 AI)';
            document.getElementById('modalTitle').textContent = 
                `${algorithm.name}${categoryText} - 세트 ${index + 1}`;
            
            const modalNumbers = document.getElementById('modalNumbers');
            modalNumbers.innerHTML = numbers.map(num => 
                `<span class="modal-number">${num}</span>`
            ).join('');

            document.getElementById('numbersModal').style.display = 'block';
        } catch (error) {
            console.error('모달 표시 오류:', error);
        }
    }

    closeModal() {
        try {
            document.getElementById('numbersModal').style.display = 'none';
            this.currentModalData = null;
        } catch (error) {
            console.error('모달 닫기 오류:', error);
        }
    }

    copyNumbers() {
        if (!this.currentModalData) return;

        try {
            const numbersText = this.currentModalData.numbers.join(', ');
            const fullText = `${this.currentModalData.algorithm} 예측번호: ${numbersText}`;
            
            if (navigator.clipboard) {
                navigator.clipboard.writeText(fullText).then(() => {
                    this.showSuccess('번호가 클립보드에 복사되었습니다!');
                }).catch(() => {
                    this.fallbackCopy(fullText);
                });
            } else {
                this.fallbackCopy(fullText);
            }
        } catch (error) {
            console.error('복사 오류:', error);
            this.showError('복사에 실패했습니다.');
        }
    }

    fallbackCopy(text) {
        try {
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            this.showSuccess('번호가 복사되었습니다!');
        } catch (error) {
            console.error('백업 복사 실패:', error);
            this.showError('복사 기능을 사용할 수 없습니다.');
        }
    }

    saveNumbers() {
        if (!this.currentModalData) return;

        try {
            const saveData = {
                algorithm: this.currentModalData.algorithm,
                category: this.currentModalData.category,
                numbers: this.currentModalData.numbers,
                timestamp: new Date().toISOString(),
                round: this.statistics.last_draw_info?.round + 1 || '미확인'
            };

            let savedNumbers = JSON.parse(localStorage.getItem('savedLottoNumbers') || '[]');
            savedNumbers.push(saveData);
            
            if (savedNumbers.length > 50) {
                savedNumbers = savedNumbers.slice(-50);
            }
            
            localStorage.setItem('savedLottoNumbers', JSON.stringify(savedNumbers));
            this.showSuccess('번호가 저장되었습니다!');
        } catch (error) {
            console.error('저장 오류:', error);
            this.showError('저장에 실패했습니다.');
        }
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type) {
        try {
            const existingNotification = document.querySelector('.notification');
            if (existingNotification) {
                existingNotification.remove();
            }

            const notification = document.createElement('div');
            notification.className = `notification notification-${type}`;
            
            const iconClass = type === 'success' ? 'fa-check-circle' : 
                            type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle';
            
            notification.innerHTML = `
                <i class="fas ${iconClass}"></i>
                <span>${message}</span>
            `;

            document.body.appendChild(notification);

            setTimeout(() => {
                notification.classList.add('notification-fade');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            }, 3000);
        } catch (error) {
            console.error('알림 표시 오류:', error);
        }
    }
}

// 앱 초기화 (메모리 최적화)
document.addEventListener('DOMContentLoaded', () => {
    try {
        window.lottoApp = new LottoApp();
        console.log('✅ 로또 앱 초기화 완료');
    } catch (error) {
        console.error('❌ 앱 초기화 실패:', error);
    }
});

// 서비스 워커 등록 (조건부 실행으로 404 오류 방지)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', async () => {
        try {
            const swResponse = await fetch('/static/js/sw.js', { 
                method: 'HEAD',
                cache: 'no-cache'
            });
            
            if (swResponse.ok) {
                const registration = await navigator.serviceWorker.register('/static/js/sw.js');
                console.log('✅ Service Worker 등록 성공');
            } else {
                console.log('ℹ️ Service Worker 파일이 없습니다.');
            }
        } catch (error) {
            console.log('ℹ️ Service Worker 등록을 건너뜁니다.');
        }
    });
}
