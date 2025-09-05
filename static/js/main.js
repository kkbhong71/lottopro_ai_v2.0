class LottoApp {
    constructor() {
        this.algorithms = {};
        this.statistics = {};
        this.currentModalData = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadInitialData();
        this.checkForWeeklyUpdate(); // 주간 업데이트 체크 추가
        console.log('🎰 로또프로 AI v2.0 초기화 완료');
    }

    bindEvents() {
        // 메인 버튼 이벤트
        document.getElementById('generateBtn').addEventListener('click', () => {
            this.generatePredictions();
        });

        document.getElementById('statisticsBtn').addEventListener('click', () => {
            this.toggleStatistics();
        });

        // 카테고리 필터 버튼 이벤트
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('category-filter')) {
                this.filterAlgorithms(e.target.dataset.category);
            }
        });

        // 알고리즘 설명 탭 이벤트
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('tab-btn')) {
                this.switchTab(e.target.dataset.tab);
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

        // 상세 분석 버튼 이벤트 (있는 경우)
        const analyzeBtn = document.getElementById('analyzeNumbers');
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => {
                this.showDetailedAnalysis();
            });
        }

        // 모달 외부 클릭시 닫기
        window.addEventListener('click', (event) => {
            const modal = document.getElementById('numbersModal');
            if (event.target === modal) {
                this.closeModal();
            }
        });
    }

    async loadInitialData() {
        try {
            const statsResponse = await fetch('/api/statistics');
            if (statsResponse.ok) {
                const statsData = await statsResponse.json();
                if (statsData.success) {
                    this.updateDataInfo(statsData.data);
                }
            }
        } catch (error) {
            console.error('초기 데이터 로드 실패:', error);
            this.showError('데이터 로드에 실패했습니다.');
        }
    }

    updateDataInfo(data) {
        // 기본 정보 업데이트
        document.getElementById('totalDraws').textContent = data.current_expected_round ? 
            data.current_expected_round.toLocaleString() : data.total_draws.toLocaleString();
        document.getElementById('lastDraw').textContent = `${data.last_draw_info.round}회`;
        
        // 다음 추첨 정보
        if (data.next_draw) {
            document.getElementById('nextDraw').textContent = `${data.next_draw.days_left}일 후`;
        }
        
        // 최근 당첨번호 표시
        this.displayRecentWinningNumbers(data);
        
        // 데이터 업데이트 시간 표시
        this.displayDataUpdateInfo(data);
    }

    displayRecentWinningNumbers(data) {
        const recentRoundText = document.getElementById('recentRoundText');
        const recentRoundDate = document.getElementById('recentRoundDate');
        const recentWinningNumbers = document.getElementById('recentWinningNumbers');
        
        if (data.recent_draw) {
            const { round, date, numbers, bonus } = data.recent_draw;
            
            // 회차 및 날짜 정보
            if (recentRoundText) {
                recentRoundText.textContent = `${round}회차`;
            }
            if (recentRoundDate) {
                recentRoundDate.textContent = this.formatDate(date);
            }
            
            // 당첨번호 표시
            if (recentWinningNumbers) {
                recentWinningNumbers.innerHTML = '';
                
                // 일반 번호 6개
                numbers.forEach((num, index) => {
                    const numberElement = document.createElement('span');
                    numberElement.className = 'recent-number';
                    numberElement.textContent = num;
                    numberElement.style.animationDelay = `${index * 0.1}s`;
                    recentWinningNumbers.appendChild(numberElement);
                });
                
                // 보너스 번호
                const bonusElement = document.createElement('span');
                bonusElement.className = 'recent-number recent-bonus';
                bonusElement.textContent = bonus;
                bonusElement.style.animationDelay = '0.6s';
                recentWinningNumbers.appendChild(bonusElement);
            }
        }
        
        // 다음 추첨까지 남은 일수
        const daysUntilDraw = document.getElementById('daysUntilDraw');
        if (daysUntilDraw && data.next_draw) {
            daysUntilDraw.textContent = `${data.next_draw.days_left}일`;
            
            // 당일이면 특별 표시
            if (data.next_draw.days_left === 0) {
                daysUntilDraw.textContent = '오늘!';
                daysUntilDraw.style.color = '#FF6B6B';
                daysUntilDraw.style.fontWeight = 'bold';
            }
        }
    }

    displayDataUpdateInfo(data) {
        const dataUpdateTime = document.getElementById('dataUpdateTime');
        if (dataUpdateTime) {
            if (data.last_updated) {
                dataUpdateTime.textContent = data.last_updated;
            } else {
                dataUpdateTime.textContent = new Date().toLocaleDateString('ko-KR');
            }
        }
    }

    formatDate(dateString) {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('ko-KR', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                weekday: 'short'
            });
        } catch (e) {
            return dateString;
        }
    }

    // 자동 회차 업데이트 체크 (매주 월요일)
    checkForWeeklyUpdate() {
        const now = new Date();
        const isMonday = now.getDay() === 1; // 월요일 = 1
        const hour = now.getHours();
        
        // 월요일 오전 9시 이후에만 업데이트 체크
        if (isMonday && hour >= 9) {
            const lastUpdateCheck = localStorage.getItem('lastUpdateCheck');
            const today = now.toDateString();
            
            if (lastUpdateCheck !== today) {
                console.log('🔄 주간 업데이트 체크 실행 (월요일)');
                this.loadInitialData(); // 데이터 새로고침
                localStorage.setItem('lastUpdateCheck', today);
                
                this.showNotification('📅 주간 회차 정보가 업데이트되었습니다!', 'success');
            }
        }
    }

    async generatePredictions() {
        const loadingIndicator = document.getElementById('loadingIndicator');
        const predictionsContainer = document.getElementById('predictionsContainer');
        const generateBtn = document.getElementById('generateBtn');
        const performanceSection = document.getElementById('performanceSection');

        try {
            loadingIndicator.style.display = 'block';
            predictionsContainer.style.display = 'none';
            generateBtn.disabled = true;
            
            // 진행 상황 표시
            this.updateProgress(0, '10개 AI 알고리즘 초기화 중...');
            
            const startTime = performance.now();
            
            // API 호출
            const response = await fetch('/api/predictions');
            const data = await response.json();

            if (data.success) {
                this.algorithms = data.data;
                
                // 데이터 소스 검증 정보 표시
                if (data.data_source) {
                    console.log('✅ CSV 데이터 검증 정보:', data.data_source);
                    this.showDataVerification(data.data_source);
                }
                
                this.updateProgress(100, '분석 완료!');
                
                // 성능 지표 업데이트
                const processingTime = ((performance.now() - startTime) / 1000).toFixed(2);
                this.updatePerformanceIndicators(processingTime, data);
                
                this.renderPredictions();
                predictionsContainer.style.display = 'block';
                
                if (performanceSection) {
                    performanceSection.style.display = 'block';
                }
                
                this.showSuccess(`✅ ${data.algorithms_count}개 AI 알고리즘이 실제 CSV 데이터를 분석하여 ${data.total_prediction_sets}개 예측 세트를 생성했습니다!`);
            } else {
                throw new Error(data.error || '예측 생성에 실패했습니다.');
            }
        } catch (error) {
            console.error('예측 생성 실패:', error);
            this.showError('예측 생성에 실패했습니다. CSV 파일이 올바르게 업로드되었는지 확인해주세요.');
        } finally {
            loadingIndicator.style.display = 'none';
            generateBtn.disabled = false;
        }
    }

    updateProgress(percentage, message) {
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        if (progressFill) {
            progressFill.style.width = `${percentage}%`;
        }
        
        if (progressText) {
            progressText.textContent = message;
        }
    }

    showDataVerification(dataSource) {
        // 데이터 검증 정보를 UI에 표시
        const verificationElement = document.createElement('div');
        verificationElement.className = 'data-verification-info';
        verificationElement.innerHTML = `
            <div class="verification-card">
                <h4><i class="fas fa-check-circle"></i> CSV 데이터 검증 완료</h4>
                <div class="verification-details">
                    <div class="detail-row">
                        <span class="label">분석 파일:</span>
                        <span class="value">${dataSource.file_name}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">분석 회차:</span>
                        <span class="value">${dataSource.total_rounds.toLocaleString()}개</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">최신 회차:</span>
                        <span class="value">${dataSource.last_round}회</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">기간:</span>
                        <span class="value">${dataSource.date_range}</span>
                    </div>
                    <div class="verification-status">
                        ${dataSource.verification}
                    </div>
                </div>
            </div>
        `;

        // 기존 검증 정보 제거
        const existingVerification = document.querySelector('.data-verification-info');
        if (existingVerification) {
            existingVerification.remove();
        }

        // 예측 컨테이너 위에 삽입
        const predictionsContainer = document.getElementById('predictionsContainer');
        if (predictionsContainer) {
            predictionsContainer.insertBefore(verificationElement, predictionsContainer.firstChild);
        }
    }

    updatePerformanceIndicators(processingTime, data) {
        const processingTimeElement = document.getElementById('processingTime');
        const dataPointsElement = document.getElementById('dataPoints');
        
        if (processingTimeElement) {
            processingTimeElement.textContent = `${processingTime}초`;
        }
        
        if (dataPointsElement && data.data_source) {
            dataPointsElement.textContent = `${data.data_source.total_rounds.toLocaleString()}회차`;
        }
    }

    renderPredictions() {
        const container = document.getElementById('algorithmsGrid');
        container.innerHTML = '';

        // 카테고리 필터 버튼 추가
        this.addCategoryFilters(container);

        const algorithmColors = {
            // 기본 알고리즘 (Basic)
            'frequency': '#FF6B6B',
            'hot_cold': '#4ECDC4', 
            'pattern': '#45B7D1',
            'statistical': '#96CEB4',
            'machine_learning': '#FFEAA7',
            // 고급 알고리즘 (Advanced)
            'neural_network': '#A29BFE',
            'markov_chain': '#FD79A8',
            'genetic': '#00B894',
            'co_occurrence': '#E17055',
            'time_series': '#6C5CE7'
        };

        const algorithmIcons = {
            // 기본 알고리즘
            'frequency': 'fas fa-chart-bar',
            'hot_cold': 'fas fa-thermometer-half',
            'pattern': 'fas fa-puzzle-piece',
            'statistical': 'fas fa-calculator',
            'machine_learning': 'fas fa-robot',
            // 고급 알고리즘
            'neural_network': 'fas fa-brain',
            'markov_chain': 'fas fa-project-diagram',
            'genetic': 'fas fa-dna',
            'co_occurrence': 'fas fa-link',
            'time_series': 'fas fa-chart-line'
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
        const basicSection = this.createAlgorithmSection('기본 AI 알고리즘', 'basic-algorithms');
        container.appendChild(basicSection);

        for (const [key, algorithm] of Object.entries(basicAlgorithms)) {
            const algorithmCard = this.createAlgorithmCard(
                key, 
                algorithm, 
                algorithmColors[key], 
                algorithmIcons[key]
            );
            basicSection.appendChild(algorithmCard);
        }

        // 고급 알고리즘 섹션
        const advancedSection = this.createAlgorithmSection('고급 AI 알고리즘', 'advanced-algorithms');
        container.appendChild(advancedSection);

        for (const [key, algorithm] of Object.entries(advancedAlgorithms)) {
            const algorithmCard = this.createAlgorithmCard(
                key, 
                algorithm, 
                algorithmColors[key], 
                algorithmIcons[key]
            );
            advancedSection.appendChild(algorithmCard);
        }
    }

    addCategoryFilters(container) {
        const filterContainer = document.createElement('div');
        filterContainer.className = 'category-filters';
        filterContainer.innerHTML = `
            <h3><i class="fas fa-filter"></i> 알고리즘 필터</h3>
            <div class="filter-buttons">
                <button class="category-filter active" data-category="all">
                    <i class="fas fa-th"></i> 전체 (10개)
                </button>
                <button class="category-filter" data-category="basic">
                    <i class="fas fa-star"></i> 기본 (5개)
                </button>
                <button class="category-filter" data-category="advanced">
                    <i class="fas fa-rocket"></i> 고급 (5개)
                </button>
            </div>
        `;
        container.appendChild(filterContainer);
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
    }

    filterAlgorithms(category) {
        // 필터 버튼 활성화 상태 업데이트
        document.querySelectorAll('.category-filter').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-category="${category}"]`).classList.add('active');

        // 알고리즘 카드 필터링
        const cards = document.querySelectorAll('.algorithm-card');
        const sections = document.querySelectorAll('.algorithm-section');

        if (category === 'all') {
            cards.forEach(card => {
                card.style.display = 'block';
                this.animateCard(card);
            });
            sections.forEach(section => section.style.display = 'block');
        } else {
            cards.forEach(card => {
                if (card.dataset.category === category) {
                    card.style.display = 'block';
                    this.animateCard(card);
                } else {
                    card.style.display = 'none';
                }
            });

            // 섹션 표시/숨김
            sections.forEach(section => {
                const visibleCards = section.querySelectorAll(`.algorithm-card[data-category="${category}"]`);
                if (visibleCards.length > 0) {
                    section.style.display = 'block';
                } else {
                    section.style.display = 'none';
                }
            });
        }
    }

    animateCard(card) {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        requestAnimationFrame(() => {
            card.style.transition = 'all 0.3s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        });
    }

    switchTab(tabName) {
        // 모든 탭 버튼에서 active 클래스 제거
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // 모든 탭 콘텐츠 숨기기
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });

        // 선택된 탭 버튼에 active 클래스 추가
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // 선택된 탭 콘텐츠 표시
        const targetTab = tabName === 'basic' ? 'basic-algorithms' : 'advanced-algorithms';
        document.getElementById(targetTab).classList.add('active');

        // 애니메이션 효과
        this.animateTabContent(targetTab);
    }

    animateTabContent(tabId) {
        const tabContent = document.getElementById(tabId);
        const cards = tabContent.querySelectorAll('.algo-explanation-card');
        
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(30px)';
            
            setTimeout(() => {
                card.style.transition = 'all 0.5s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }

    async toggleStatistics() {
        const statisticsSection = document.getElementById('statisticsSection');
        const isVisible = statisticsSection.style.display !== 'none';

        if (isVisible) {
            statisticsSection.style.display = 'none';
            return;
        }

        try {
            const response = await fetch('/api/statistics');
            const data = await response.json();

            if (data.success) {
                this.statistics = data.data;
                this.renderStatistics();
                statisticsSection.style.display = 'block';
                
                statisticsSection.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start' 
                });
            } else {
                throw new Error(data.error || '통계 로드에 실패했습니다.');
            }
        } catch (error) {
            console.error('통계 로드 실패:', error);
            this.showError('통계 데이터 로드에 실패했습니다.');
        }
    }

    renderStatistics() {
        // 최근 당첨 정보
        const recentNumbers = document.getElementById('recentNumbers');
        const recentDetails = document.getElementById('recentDetails');
        
        const lastDraw = this.statistics.last_draw_info;
        recentNumbers.innerHTML = lastDraw.numbers.map(num => 
            `<span class="number">${num}</span>`
        ).join('') + `<span class="bonus-number">${lastDraw.bonus}</span>`;
        
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

        // 빈도 통계 렌더링
        this.renderFrequencyList('mostFrequent', this.statistics.most_frequent);
        this.renderFrequencyList('leastFrequent', this.statistics.least_frequent);
        this.renderFrequencyList('recentHot', this.statistics.recent_hot);
    }

    renderFrequencyList(containerId, data) {
        const container = document.getElementById(containerId);
        container.innerHTML = data.map((item, index) => `
            <div class="frequency-item">
                <span class="rank">${index + 1}</span>
                <span class="number">${item.number}</span>
                <span class="count">${item.count}회</span>
            </div>
        `).join('');
    }

    showNumbersModal(algorithmKey, index) {
        const algorithm = this.algorithms[algorithmKey];
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
    }

    closeModal() {
        document.getElementById('numbersModal').style.display = 'none';
        this.currentModalData = null;
    }

    copyNumbers() {
        if (!this.currentModalData) return;

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
    }

    fallbackCopy(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        this.showSuccess('번호가 복사되었습니다!');
    }

    saveNumbers() {
        if (!this.currentModalData) return;

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
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type) {
        const existingNotification = document.querySelector('.notification');
        if (existingNotification) {
            existingNotification.remove();
        }

        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
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
    }

    exportPredictions() {
        if (!this.algorithms) return;

        const exportData = {
            timestamp: new Date().toISOString(),
            totalAlgorithms: Object.keys(this.algorithms).length,
            algorithms: this.algorithms
        };

        const dataStr = JSON.stringify(exportData, null, 2);
        const dataBlob = new Blob([dataStr], {type: 'application/json'});
        
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `lotto_predictions_${new Date().toISOString().split('T')[0]}.json`;
        link.click();
        
        URL.revokeObjectURL(url);
        this.showSuccess('예측 결과가 다운로드되었습니다!');
    }
}

// 앱 초기화
document.addEventListener('DOMContentLoaded', () => {
    window.lottoApp = new LottoApp();
    
    // 추가 기능 버튼들
    const exportBtn = document.createElement('button');
    exportBtn.innerHTML = '<i class="fas fa-download"></i> 결과 내보내기';
    exportBtn.className = 'export-btn';
    exportBtn.onclick = () => window.lottoApp.exportPredictions();
    
    const controlsContainer = document.querySelector('.main-controls');
    if (controlsContainer) {
        controlsContainer.appendChild(exportBtn);
    }
});

// 서비스 워커 등록 (PWA 지원) - 조건부 실행으로 404 오류 방지
if ('serviceWorker' in navigator) {
    window.addEventListener('load', async () => {
        try {
            // sw.js 파일 존재 여부 확인
            const swResponse = await fetch('/static/js/sw.js', { 
                method: 'HEAD',
                cache: 'no-cache'
            });
            
            if (swResponse.ok) {
                const registration = await navigator.serviceWorker.register('/static/js/sw.js');
                console.log('✅ Service Worker 등록 성공:', registration);
            } else {
                console.log('ℹ️ Service Worker 파일이 없습니다. PWA 기능을 건너뜁니다.');
            }
        } catch (error) {
            console.log('ℹ️ Service Worker 등록을 건너뜁니다:', error.message);
        }
    });
}
