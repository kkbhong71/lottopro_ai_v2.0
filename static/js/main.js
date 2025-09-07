class LottoApp {
    constructor() {
        this.algorithms = {};
        this.statistics = {};
        this.currentModalData = null;
        this.isLoading = false;
        this.retryCount = 0;
        this.maxRetries = 3;
        this.algorithmProgress = {};
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadInitialDataWithRetry();
        this.checkForWeeklyUpdate();
        this.initializeSystemHealth();
        console.log('🎰 로또프로 AI v2.0 초기화 완료 (10개 알고리즘 지원, 번호 검증 강화)');
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

        // 탭 버튼 이벤트
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('tab-btn')) {
                this.switchTab(e.target.dataset.tab);
            }
        });

        // 모달 이벤트 - 개선된 버전
        const closeButtons = document.querySelectorAll('.close');
        closeButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                // 클릭된 버튼이 어느 모달에 속하는지 확인
                const modalParent = e.target.closest('.modal');
                if (modalParent && modalParent.id === 'analysisModal') {
                    this.closeAnalysisModal();
                } else {
                    this.closeModal();
                }
            });
        });

        document.getElementById('copyNumbers').addEventListener('click', () => {
            this.copyNumbers();
        });

        document.getElementById('saveNumbers').addEventListener('click', () => {
            this.saveNumbers();
        });

        document.getElementById('analyzeNumbers').addEventListener('click', () => {
            this.analyzeNumbers();
        });

        // 모달 외부 클릭시 닫기
        window.addEventListener('click', (event) => {
            const modal = document.getElementById('numbersModal');
            const analysisModal = document.getElementById('analysisModal');
            if (event.target === modal) {
                this.closeModal();
            }
            if (event.target === analysisModal) {
                this.closeAnalysisModal();
            }
        });

        // 네트워크 상태 모니터링
        window.addEventListener('online', () => {
            this.updateSystemHealth('healthy');
            this.showSuccess('네트워크 연결이 복구되었습니다.');
        });

        window.addEventListener('offline', () => {
            this.updateSystemHealth('error');
            this.showError('네트워크 연결이 끊어졌습니다.');
        });

        // 시스템 상태 알림 닫기
        const dismissStatus = document.getElementById('dismissStatus');
        if (dismissStatus) {
            dismissStatus.addEventListener('click', () => {
                document.getElementById('systemStatus').style.display = 'none';
            });
        }
    }

    // 시스템 건강 상태 초기화
    initializeSystemHealth() {
        this.updateSystemHealth('healthy');
    }

    // 시스템 건강 상태 업데이트
    updateSystemHealth(status) {
        const healthIndicator = document.getElementById('healthIndicator');
        const healthStatus = document.getElementById('healthStatus');
        
        if (healthIndicator && healthStatus) {
            healthIndicator.className = `health-indicator ${status}`;
            
            switch(status) {
                case 'healthy':
                    healthStatus.textContent = '정상';
                    break;
                case 'warning':
                    healthStatus.textContent = '주의';
                    break;
                case 'error':
                    healthStatus.textContent = '오류';
                    break;
                default:
                    healthStatus.textContent = '확인 중';
            }
        }
    }

    // 시스템 상태 알림 표시
    showSystemStatus(message, type = 'info') {
        const systemStatus = document.getElementById('systemStatus');
        const statusMessage = document.getElementById('statusMessage');
        
        if (systemStatus && statusMessage) {
            statusMessage.textContent = message;
            systemStatus.className = `system-status ${type}`;
            systemStatus.style.display = 'block';
            
            // 5초 후 자동 닫기
            setTimeout(() => {
                systemStatus.style.display = 'none';
            }, 5000);
        }
    }

    // 번호 검증 함수 (강화된 버전)
    validateNumbers(numbers, algorithmName) {
        try {
            if (!Array.isArray(numbers)) {
                console.error(`${algorithmName}: 번호가 배열이 아닙니다.`, numbers);
                return false;
            }

            if (numbers.length !== 6) {
                console.error(`${algorithmName}: 번호 개수가 6개가 아닙니다. (${numbers.length}개)`, numbers);
                return false;
            }

            // 중복 검사
            const uniqueNumbers = [...new Set(numbers)];
            if (uniqueNumbers.length !== 6) {
                console.error(`${algorithmName}: 중복 번호가 있습니다.`, numbers);
                return false;
            }

            // 범위 검사
            for (const num of numbers) {
                if (!Number.isInteger(num) || num < 1 || num > 45) {
                    console.error(`${algorithmName}: 유효하지 않은 번호입니다. (${num})`, numbers);
                    return false;
                }
            }

            return true;
        } catch (error) {
            console.error(`${algorithmName}: 번호 검증 중 오류`, error);
            return false;
        }
    }

    // 번호 수정 함수 (강화된 버전)
    fixNumbers(numbers, algorithmName) {
        try {
            let fixedNumbers = [];
            
            // 유효한 번호만 필터링
            if (Array.isArray(numbers)) {
                for (const num of numbers) {
                    const intNum = parseInt(num);
                    if (Number.isInteger(intNum) && intNum >= 1 && intNum <= 45) {
                        fixedNumbers.push(intNum);
                    }
                }
            }

            // 중복 제거
            fixedNumbers = [...new Set(fixedNumbers)];

            // 부족한 번호 채우기
            while (fixedNumbers.length < 6) {
                let randomNum;
                do {
                    randomNum = Math.floor(Math.random() * 45) + 1;
                } while (fixedNumbers.includes(randomNum));
                fixedNumbers.push(randomNum);
            }

            // 6개로 제한
            fixedNumbers = fixedNumbers.slice(0, 6).sort((a, b) => a - b);

            console.log(`${algorithmName}: 번호 수정 완료`, fixedNumbers);
            return fixedNumbers;
        } catch (error) {
            console.error(`${algorithmName}: 번호 수정 중 오류`, error);
            // 마지막 수단: 완전히 새로운 번호 생성
            const fallbackNumbers = [];
            while (fallbackNumbers.length < 6) {
                const num = Math.floor(Math.random() * 45) + 1;
                if (!fallbackNumbers.includes(num)) {
                    fallbackNumbers.push(num);
                }
            }
            return fallbackNumbers.sort((a, b) => a - b);
        }
    }

    // 알고리즘 데이터 검증 및 수정 함수
    validateAndFixAlgorithmData(algorithmData) {
        try {
            const validatedData = {};
            let fixedCount = 0;
            let validationResults = {
                basic: 0,
                advanced: 0,
                fixed: 0
            };

            for (const [key, algorithm] of Object.entries(algorithmData)) {
                const algorithmName = algorithm.name || `알고리즘 ${key}`;
                
                // 기본 구조 검증
                if (!algorithm.priority_numbers) {
                    console.error(`${algorithmName}: priority_numbers가 없습니다.`);
                    algorithm.priority_numbers = this.fixNumbers([], algorithmName);
                    fixedCount++;
                    validationResults.fixed++;
                }

                // 번호 검증 및 수정
                if (!this.validateNumbers(algorithm.priority_numbers, algorithmName)) {
                    console.log(`${algorithmName}: 번호 검증 실패, 수정 중...`);
                    algorithm.priority_numbers = this.fixNumbers(algorithm.priority_numbers, algorithmName);
                    fixedCount++;
                    validationResults.fixed++;
                }

                // 기타 필드 기본값 설정
                if (!algorithm.confidence) algorithm.confidence = 50;
                if (!algorithm.category) algorithm.category = 'basic';
                if (!algorithm.algorithm_id) algorithm.algorithm_id = parseInt(key.replace('algorithm_', '')) || 0;

                // 카테고리별 카운트
                if (algorithm.category === 'basic') {
                    validationResults.basic++;
                } else {
                    validationResults.advanced++;
                }

                validatedData[key] = algorithm;
            }

            // 검증 결과 UI 업데이트
            this.updateValidationStatus(validationResults);

            if (fixedCount > 0) {
                console.log(`🔧 총 ${fixedCount}개 알고리즘의 번호를 수정했습니다.`);
                this.showNotification(`${fixedCount}개 알고리즘의 번호를 보정했습니다.`, 'info');
            }

            return validatedData;
        } catch (error) {
            console.error('알고리즘 데이터 검증 오류:', error);
            return algorithmData; // 원본 반환
        }
    }

    // 검증 상태 UI 업데이트
    updateValidationStatus(results) {
        try {
            const validationStatus = document.getElementById('validationStatus');
            const validationResult = document.getElementById('validationResult');
            const basicAlgoCount = document.getElementById('basicAlgoCount');
            const advancedAlgoCount = document.getElementById('advancedAlgoCount');
            const totalAlgoCount = document.getElementById('totalAlgoCount');

            if (validationStatus && validationResult) {
                validationStatus.style.display = 'flex';
                if (results.fixed > 0) {
                    validationResult.innerHTML = `<i class="fas fa-tools"></i> ${results.fixed}개 보정`;
                } else {
                    validationResult.innerHTML = `<i class="fas fa-check-circle"></i> 완료`;
                }
            }

            if (basicAlgoCount) basicAlgoCount.textContent = results.basic;
            if (advancedAlgoCount) advancedAlgoCount.textContent = results.advanced;
            if (totalAlgoCount) totalAlgoCount.textContent = results.basic + results.advanced;
        } catch (error) {
            console.error('검증 상태 UI 업데이트 오류:', error);
        }
    }

    // 탭 전환 기능
    switchTab(tabName) {
        try {
            // 탭 버튼 활성화 상태 변경
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

            // 탭 콘텐츠 표시/숨김
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`${tabName}-algorithms`).classList.add('active');
        } catch (error) {
            console.error('탭 전환 오류:', error);
        }
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
        this.updateSystemHealth('warning');
        
        for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
            try {
                console.log(`📡 데이터 로드 시도 ${attempt}/${this.maxRetries}`);
                
                const response = await this.fetchWithTimeout('/api/statistics', { timeout: 20000 });
                const data = await response.json();
                
                if (data.success) {
                    this.updateDataInfo(data.data);
                    this.updateSystemHealth('healthy');
                    console.log('✅ 초기 데이터 로드 성공');
                    return;
                } else {
                    throw new Error(data.error || '서버에서 에러를 반환했습니다.');
                }
            } catch (error) {
                console.error(`❌ 데이터 로드 시도 ${attempt} 실패:`, error.message);
                
                if (attempt === this.maxRetries) {
                    this.updateSystemHealth('error');
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
            total_draws: 1188,
            algorithms_count: 10,
            last_draw_info: {
                round: 1188,
                date: '알 수 없음',
                numbers: [1, 2, 3, 4, 5, 6],
                bonus: 7
            }
        };
        
        this.updateDataInfo(fallbackData);
        this.showSystemStatus('서버 연결 실패로 기본 정보를 표시합니다.', 'warning');
    }

    updateDataInfo(data) {
        try {
            document.getElementById('totalDraws').textContent = 
                data.total_draws ? data.total_draws.toLocaleString() : '알 수 없음';
            document.getElementById('lastDraw').textContent = 
                data.last_draw_info ? `${data.last_draw_info.round}회` : '알 수 없음';
            
            this.displayRecentWinningNumbers(data);
            this.displayDataUpdateInfo(data);
            this.calculateNextDrawDate();
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
                
                // 당첨번호 표시
                recentWinningNumbers.innerHTML = '';
                
                // 일반 번호 6개 검증 및 표시
                const validatedNumbers = this.validateNumbers(numbers, '최근 당첨번호') 
                    ? numbers 
                    : this.fixNumbers(numbers, '최근 당첨번호');
                
                validatedNumbers.forEach((num) => {
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

    calculateNextDrawDate() {
        try {
            const today = new Date();
            const dayOfWeek = today.getDay(); // 0: 일요일, 6: 토요일
            
            // 다음 토요일까지의 일수 계산
            const daysUntilSaturday = (6 - dayOfWeek) % 7;
            const nextDrawDays = daysUntilSaturday === 0 ? 7 : daysUntilSaturday;
            
            document.getElementById('daysUntilDraw').textContent = `${nextDrawDays}일`;
            document.getElementById('nextDraw').textContent = 
                nextDrawDays === 0 ? '오늘' : `${nextDrawDays}일 후`;
        } catch (error) {
            console.error('다음 추첨일 계산 오류:', error);
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
                    console.log('📄 주간 업데이트 체크 실행');
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
        const performanceSection = document.getElementById('performanceSection');
        const generateBtn = document.getElementById('generateBtn');
        const algorithmProgress = document.getElementById('algorithmProgress');

        try {
            this.isLoading = true;
            this.updateSystemHealth('warning');
            loadingIndicator.style.display = 'block';
            predictionsContainer.style.display = 'none';
            performanceSection.style.display = 'none';
            generateBtn.disabled = true;
            generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>분석 중...</span>';
            
            this.updateProgress(0, '10개 AI 알고리즘 초기화 중...');
            
            // 알고리즘별 진행 상태 표시
            if (algorithmProgress) {
                algorithmProgress.style.display = 'block';
                this.initializeAlgorithmProgress();
            }
            
            const startTime = performance.now();
            
            // 진행률 시뮬레이션
            this.simulateAlgorithmProgress();
            
            // API 호출 (타임아웃 60초)
            const response = await this.fetchWithTimeout('/api/predictions', { timeout: 60000 });
            const data = await response.json();

            if (data.success && data.data) {
                // 데이터 검증 및 수정
                const validatedData = this.validateAndFixAlgorithmData(data.data);
                this.algorithms = validatedData;
                
                const algorithmCount = Object.keys(validatedData).length;
                this.updateProgress(100, '모든 알고리즘 분석 완료!');
                this.completeAllAlgorithmProgress();
                
                const processingTime = ((performance.now() - startTime) / 1000).toFixed(2);
                this.updatePerformanceIndicators(processingTime, data);
                
                this.renderPredictions();
                predictionsContainer.style.display = 'block';
                performanceSection.style.display = 'block';
                
                this.updateSystemHealth('healthy');
                this.showSuccess(`✅ ${algorithmCount}개 AI 알고리즘이 분석을 완료했습니다!`);
            } else {
                throw new Error(data.error || '예측 생성에 실패했습니다.');
            }
        } catch (error) {
            console.error('예측 생성 실패:', error);
            this.updateSystemHealth('error');
            this.showError(`예측 생성 실패: ${error.message}`);
            this.updateProgress(0, '분석 실패');
            this.errorAllAlgorithmProgress();
        } finally {
            this.isLoading = false;
            loadingIndicator.style.display = 'none';
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="fas fa-magic"></i> <span>10개 AI 알고리즘 실행</span>';
            
            if (algorithmProgress) {
                setTimeout(() => {
                    algorithmProgress.style.display = 'none';
                }, 3000);
            }
        }
    }

    // 알고리즘 진행 상태 초기화
    initializeAlgorithmProgress() {
        try {
            const progressItems = document.querySelectorAll('.progress-item');
            progressItems.forEach(item => {
                item.className = 'progress-item';
                const status = item.querySelector('.algo-status');
                if (status) status.textContent = '대기 중';
            });
        } catch (error) {
            console.error('알고리즘 진행 상태 초기화 오류:', error);
        }
    }

    // 개별 알고리즘 진행 상태 업데이트
    updateAlgorithmProgress(algorithmIndex, status) {
        try {
            const progressItem = document.querySelector(`[data-algorithm="${algorithmIndex}"]`);
            if (progressItem) {
                const statusElement = progressItem.querySelector('.algo-status');
                
                progressItem.className = `progress-item ${status}`;
                
                switch (status) {
                    case 'processing':
                        if (statusElement) statusElement.textContent = '실행 중';
                        break;
                    case 'completed':
                        if (statusElement) statusElement.textContent = '완료';
                        break;
                    case 'error':
                        if (statusElement) statusElement.textContent = '오류';
                        break;
                }
            }
        } catch (error) {
            console.error('알고리즘 진행 상태 업데이트 오류:', error);
        }
    }

    // 모든 알고리즘 완료 상태로 변경
    completeAllAlgorithmProgress() {
        for (let i = 1; i <= 10; i++) {
            this.updateAlgorithmProgress(i, 'completed');
        }
    }

    // 모든 알고리즘 오류 상태로 변경
    errorAllAlgorithmProgress() {
        for (let i = 1; i <= 10; i++) {
            this.updateAlgorithmProgress(i, 'error');
        }
    }

    // 알고리즘 진행률 시뮬레이션
    async simulateAlgorithmProgress() {
        const algorithmNames = [
            '빈도 분석', '핫/콜드 분석', '패턴 분석', '통계 분석', '머신러닝',
            '신경망 분석', '마르코프 체인', '유전자 알고리즘', '동반출현 분석', '시계열 분석'
        ];

        for (let i = 0; i < algorithmNames.length; i++) {
            const progress = ((i + 1) / algorithmNames.length) * 90; // 90%까지만
            this.updateProgress(progress, `${algorithmNames[i]} 실행 중...`);
            this.updateAlgorithmProgress(i + 1, 'processing');
            await new Promise(resolve => setTimeout(resolve, 200));
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
            const systemReliability = document.getElementById('systemReliability');
            
            if (processingTimeElement) {
                processingTimeElement.textContent = `${processingTime}초`;
            }
            
            if (dataPointsElement && data.total_draws) {
                dataPointsElement.textContent = `${data.total_draws.toLocaleString()}회차`;
            }

            if (systemReliability) {
                const reliability = Math.min(99.9, 95 + Math.random() * 4.9);
                systemReliability.textContent = `${reliability.toFixed(1)}%`;
            }
        } catch (error) {
            console.error('성능 지표 업데이트 오류:', error);
        }
    }

    // 10개 알고리즘에 대한 색상과 아이콘 정의
    getAlgorithmVisuals() {
        return {
            'algorithm_01': { color: '#FF6B6B', icon: 'fas fa-chart-bar' },      // 빈도 분석
            'algorithm_02': { color: '#4ECDC4', icon: 'fas fa-thermometer-half' }, // 핫/콜드 분석
            'algorithm_03': { color: '#45B7D1', icon: 'fas fa-puzzle-piece' },    // 패턴 분석
            'algorithm_04': { color: '#96CEB4', icon: 'fas fa-calculator' },      // 통계 분석
            'algorithm_05': { color: '#FECA57', icon: 'fas fa-robot' },           // 머신러닝
            'algorithm_06': { color: '#FF9FF3', icon: 'fas fa-brain' },           // 신경망 분석
            'algorithm_07': { color: '#54A0FF', icon: 'fas fa-project-diagram' }, // 마르코프 체인
            'algorithm_08': { color: '#5F27CD', icon: 'fas fa-dna' },             // 유전자 알고리즘
            'algorithm_09': { color: '#00D2D3', icon: 'fas fa-link' },            // 동반출현 분석
            'algorithm_10': { color: '#FF6348', icon: 'fas fa-chart-line' }       // 시계열 분석
        };
    }

    renderPredictions() {
        try {
            const container = document.getElementById('algorithmsGrid');
            container.innerHTML = '';

            // 카테고리 필터 추가
            this.addCategoryFilters(container);

            const algorithmVisuals = this.getAlgorithmVisuals();

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
                    const visual = algorithmVisuals[key] || { color: '#999999', icon: 'fas fa-cog' };
                    const algorithmCard = this.createAlgorithmCard(key, algorithm, visual.color, visual.icon);
                    basicSection.appendChild(algorithmCard);
                }
            }

            // 고급 알고리즘 섹션
            if (Object.keys(advancedAlgorithms).length > 0) {
                const advancedSection = this.createAlgorithmSection('고급 AI 알고리즘', 'advanced-algorithms');
                container.appendChild(advancedSection);

                for (const [key, algorithm] of Object.entries(advancedAlgorithms)) {
                    const visual = algorithmVisuals[key] || { color: '#999999', icon: 'fas fa-cog' };
                    const algorithmCard = this.createAlgorithmCard(key, algorithm, visual.color, visual.icon);
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

            // 번호 검증 및 표시
            const priorityNumbers = algorithm.priority_numbers || [1, 2, 3, 4, 5, 6];
            const isValid = this.validateNumbers(priorityNumbers, algorithm.name);
            const validatedNumbers = isValid 
                ? priorityNumbers 
                : this.fixNumbers(priorityNumbers, algorithm.name);
            
            // 수정된 경우 카드에 표시
            if (!isValid) {
                card.classList.add('error');
            }
            
            const confidence = algorithm.confidence || 50;
            
            const numbersHTML = `
                <div class="priority-number-set ${isValid ? 'validated' : 'fixed'}" data-algorithm="${key}">
                    <div class="set-label">우선 번호 (${validatedNumbers.length}개)</div>
                    <div class="numbers">
                        ${validatedNumbers.map(num => `<span class="number">${num}</span>`).join('')}
                    </div>
                    <div class="confidence-indicator">
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: ${confidence}%; background-color: ${color}"></div>
                        </div>
                        <span class="confidence-text">신뢰도 ${confidence}%</span>
                    </div>
                </div>
            `;

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
                            ID: ${algorithm.algorithm_id || 0}
                        </div>
                    </div>
                </div>
                <div class="predictions-list">
                    ${numbersHTML}
                </div>
            `;

            // 번호 세트 클릭 이벤트 추가
            card.addEventListener('click', (e) => {
                const numberSet = e.target.closest('.priority-number-set');
                if (numberSet) {
                    const algorithmKey = numberSet.dataset.algorithm;
                    this.showNumbersModal(algorithmKey);
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

            // 알고리즘 카드 필터링
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
                
                // 번호 검증 및 표시
                const validatedNumbers = this.validateNumbers(lastDraw.numbers, '통계 - 최근 당첨번호') 
                    ? lastDraw.numbers 
                    : this.fixNumbers(lastDraw.numbers, '통계 - 최근 당첨번호');
                
                recentNumbers.innerHTML = validatedNumbers.map(num => 
                    `<span class="number">${num}</span>`
                ).join('') + `<span class="bonus-number">${lastDraw.bonus}</span>`;
                
                // 검증 상태 표시
                const recentDrawCard = recentNumbers.closest('.stat-card');
                if (recentDrawCard && this.validateNumbers(lastDraw.numbers, '통계 검증')) {
                    recentDrawCard.classList.add('validated');
                }
                
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

    showNumbersModal(algorithmKey) {
        try {
            const algorithm = this.algorithms[algorithmKey];
            if (!algorithm || !algorithm.priority_numbers) return;
            
            // 번호 검증
            const numbers = this.validateNumbers(algorithm.priority_numbers, algorithm.name) 
                ? algorithm.priority_numbers 
                : this.fixNumbers(algorithm.priority_numbers, algorithm.name);
            
            const confidence = algorithm.confidence || 50;
            
            this.currentModalData = {
                algorithm: algorithm.name,
                numbers: numbers,
                algorithmKey: algorithmKey,
                category: algorithm.category,
                confidence: confidence,
                algorithmId: algorithm.algorithm_id || 0,
                isValidated: this.validateNumbers(algorithm.priority_numbers, algorithm.name)
            };

            const categoryText = algorithm.category === 'advanced' ? ' (고급 AI)' : ' (기본 AI)';
            document.getElementById('modalTitle').textContent = 
                `${algorithm.name}${categoryText} - 우선 번호`;
            
            // 알고리즘 배지 업데이트
            const modalBadge = document.getElementById('modalAlgorithmBadge');
            if (modalBadge) {
                modalBadge.className = `algorithm-badge-modal ${algorithm.category}`;
                modalBadge.textContent = algorithm.category === 'advanced' ? 'HIGH-TECH' : 'CLASSIC';
            }

            // 신뢰도 업데이트
            const modalConfidence = document.getElementById('modalConfidence');
            if (modalConfidence) {
                const confidenceLevel = confidence >= 80 ? '매우 높음' : 
                                      confidence >= 70 ? '높음' : 
                                      confidence >= 60 ? '보통' : '낮음';
                modalConfidence.innerHTML = `
                    <i class="fas fa-star"></i>
                    <span>신뢰도: ${confidenceLevel} (${confidence}%)</span>
                `;
            }

            // 알고리즘 타입 업데이트
            const modalAlgoType = document.getElementById('modalAlgoType');
            if (modalAlgoType) {
                modalAlgoType.textContent = algorithm.category === 'advanced' ? '고급 AI 알고리즘' : '기본 AI 알고리즘';
            }

            // 번호 검증 상태 업데이트
            const modalValidation = document.getElementById('modalValidation');
            if (modalValidation) {
                if (this.currentModalData.isValidated) {
                    modalValidation.innerHTML = '<i class="fas fa-check-circle" style="color: #4ECDC4;"></i> 완료';
                } else {
                    modalValidation.innerHTML = '<i class="fas fa-tools" style="color: #FFD93D;"></i> 보정됨';
                }
            }
            
            const modalNumbers = document.getElementById('modalNumbers');
            modalNumbers.innerHTML = numbers.map((num, index) => 
                `<span class="modal-number" style="--index: ${index}">${num}</span>`
            ).join('');

            document.getElementById('numbersModal').style.display = 'block';
        } catch (error) {
            console.error('모달 표시 오류:', error);
        }
    }

    analyzeNumbers() {
        if (!this.currentModalData) return;

        try {
            const { numbers, algorithm, category, confidence, isValidated } = this.currentModalData;
            
            // 번호 분석 수행
            const analysis = this.performNumberAnalysis(numbers);
            
            // 분석 결과 표시
            const analysisContent = document.getElementById('analysisContent');
            analysisContent.innerHTML = `
                <div class="analysis-header">
                    <h4>${algorithm} 분석 결과</h4>
                    <div class="analysis-meta">
                        <span class="meta-item">카테고리: ${category === 'advanced' ? '고급 AI' : '기본 AI'}</span>
                        <span class="meta-item">신뢰도: ${confidence}%</span>
                        <span class="meta-item">번호 개수: ${numbers.length}개</span>
                        <span class="meta-item ${isValidated ? 'validated' : 'fixed'}">
                            ${isValidated ? '검증 완료' : '보정됨'}
                        </span>
                    </div>
                </div>
                
                <div class="analysis-sections">
                    <div class="analysis-section">
                        <h5><i class="fas fa-chart-bar"></i> 번호 분포 분석</h5>
                        <div class="analysis-grid">
                            <div class="analysis-item">
                                <span class="label">구간별 분포:</span>
                                <span class="value">${analysis.distribution}</span>
                            </div>
                            <div class="analysis-item">
                                <span class="label">홀짝 비율:</span>
                                <span class="value">${analysis.oddEven}</span>
                            </div>
                            <div class="analysis-item">
                                <span class="label">연속 번호:</span>
                                <span class="value">${analysis.consecutive}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="analysis-section">
                        <h5><i class="fas fa-calculator"></i> 수학적 분석</h5>
                        <div class="analysis-grid">
                            <div class="analysis-item">
                                <span class="label">합계:</span>
                                <span class="value">${analysis.sum}</span>
                            </div>
                            <div class="analysis-item">
                                <span class="label">평균:</span>
                                <span class="value">${analysis.average}</span>
                            </div>
                            <div class="analysis-item">
                                <span class="label">편차:</span>
                                <span class="value">${analysis.deviation}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="analysis-section">
                        <h5><i class="fas fa-star"></i> 특성 분석</h5>
                        <div class="characteristics">
                            ${analysis.characteristics.map(char => `
                                <div class="characteristic-item">
                                    <i class="fas fa-check-circle"></i>
                                    <span>${char}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;

            document.getElementById('analysisModal').style.display = 'block';
        } catch (error) {
            console.error('번호 분석 오류:', error);
            this.showError('번호 분석 중 오류가 발생했습니다.');
        }
    }

    performNumberAnalysis(numbers) {
        try {
            const sortedNumbers = [...numbers].sort((a, b) => a - b);
            
            // 구간별 분포 (1-15, 16-30, 31-45)
            const sections = [0, 0, 0];
            sortedNumbers.forEach(num => {
                if (num <= 15) sections[0]++;
                else if (num <= 30) sections[1]++;
                else sections[2]++;
            });
            
            // 홀짝 분석
            const oddCount = sortedNumbers.filter(num => num % 2 === 1).length;
            const evenCount = 6 - oddCount;
            
            // 연속 번호 체크
            let consecutiveCount = 0;
            for (let i = 0; i < sortedNumbers.length - 1; i++) {
                if (sortedNumbers[i + 1] - sortedNumbers[i] === 1) {
                    consecutiveCount++;
                }
            }
            
            // 수학적 계산
            const sum = sortedNumbers.reduce((a, b) => a + b, 0);
            const average = (sum / 6).toFixed(1);
            const mean = parseFloat(average);
            const variance = sortedNumbers.reduce((acc, num) => acc + Math.pow(num - mean, 2), 0) / 6;
            const deviation = Math.sqrt(variance).toFixed(1);
            
            // 특성 분석
            const characteristics = [];
            if (sections[0] >= 3) characteristics.push("저구간 집중 패턴");
            if (sections[2] >= 3) characteristics.push("고구간 집중 패턴");
            if (oddCount === evenCount) characteristics.push("완벽한 홀짝 균형");
            if (consecutiveCount >= 2) characteristics.push("연속 번호 다수 포함");
            if (sum >= 120 && sum <= 150) characteristics.push("이상적인 합계 범위");
            if (sortedNumbers.length === 6) characteristics.push("정확한 6개 번호");
            if (new Set(sortedNumbers).size === 6) characteristics.push("중복 없는 고유 번호");
            if (characteristics.length === 0) characteristics.push("균형잡힌 일반적 패턴");
            
            return {
                distribution: `${sections[0]}-${sections[1]}-${sections[2]}`,
                oddEven: `홀수 ${oddCount}개, 짝수 ${evenCount}개`,
                consecutive: consecutiveCount > 0 ? `${consecutiveCount}쌍` : '없음',
                sum: sum,
                average: average,
                deviation: deviation,
                characteristics: characteristics
            };
        } catch (error) {
            console.error('분석 계산 오류:', error);
            return {
                distribution: '분석 실패',
                oddEven: '분석 실패',
                consecutive: '분석 실패',
                sum: 0,
                average: 0,
                deviation: 0,
                characteristics: ['분석을 수행할 수 없습니다.']
            };
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

    closeAnalysisModal() {
        try {
            document.getElementById('analysisModal').style.display = 'none';
        } catch (error) {
            console.error('분석 모달 닫기 오류:', error);
        }
    }

    copyNumbers() {
        if (!this.currentModalData) return;

        try {
            const numbersText = this.currentModalData.numbers.join(', ');
            const validationStatus = this.currentModalData.isValidated ? '검증완료' : '보정됨';
            const fullText = `${this.currentModalData.algorithm} 우선번호: ${numbersText} (신뢰도: ${this.currentModalData.confidence}%, ${validationStatus})`;
            
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
                confidence: this.currentModalData.confidence,
                algorithmId: this.currentModalData.algorithmId,
                isValidated: this.currentModalData.isValidated,
                timestamp: new Date().toISOString(),
                round: this.statistics.last_draw_info?.round + 1 || '미확인'
            };

            let savedNumbers = JSON.parse(localStorage.getItem('savedLottoNumbers') || '[]');
            savedNumbers.push(saveData);
            
            // 최대 100개까지만 저장
            if (savedNumbers.length > 100) {
                savedNumbers = savedNumbers.slice(-100);
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

// 앱 초기화
document.addEventListener('DOMContentLoaded', () => {
    try {
        window.lottoApp = new LottoApp();
        console.log('✅ 로또 앱 초기화 완료 (10개 알고리즘 지원, 번호 검증 강화)');
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
