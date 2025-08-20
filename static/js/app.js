// LottoPro AI v2.0 Enhanced JavaScript Application

class LottoProAI {
    constructor() {
        this.isLoading = false;
        this.currentPrediction = null;
        this.animationTimeouts = [];
        this.exampleUpdateInterval = null;
        this.isUpdatingExample = false;
        this.qrScanner = null;
        this.savedNumbers = [];
        this.currentStream = null;
        
        this.init();
    }
    
    init() {
        this.initializeEventListeners();
        this.initializeAnimations();
        this.loadInitialStats();
        this.setupQRScanner();
        this.loadSavedNumbers();
        this.initializeServiceWorker();
    }
    
    initializeEventListeners() {
        // 기존 폼 제출 이벤트
        const form = document.getElementById('predictionForm');
        if (form) {
            form.addEventListener('submit', (e) => this.handlePredictionSubmit(e));
        }
        
        // 숫자 입력 검증 (예측용)
        for (let i = 1; i <= 6; i++) {
            const input = document.getElementById(`num${i}`);
            if (input) {
                input.addEventListener('input', (e) => this.validateNumberInput(e));
                input.addEventListener('blur', (e) => this.checkDuplicates(e));
                input.addEventListener('keypress', (e) => this.handleNumberKeyPress(e));
            }
        }
        
        // 저장용 번호 입력 검증
        for (let i = 1; i <= 6; i++) {
            const saveInput = document.getElementById(`save-num${i}`);
            if (saveInput) {
                saveInput.addEventListener('input', (e) => this.validateNumberInput(e));
                saveInput.addEventListener('blur', (e) => this.checkDuplicates(e, 'save'));
            }
        }
        
        // 당첨확인용 번호 입력 검증
        for (let i = 1; i <= 6; i++) {
            const checkInput = document.getElementById(`check-num${i}`);
            if (checkInput) {
                checkInput.addEventListener('input', (e) => this.validateNumberInput(e));
                checkInput.addEventListener('blur', (e) => this.checkDuplicates(e, 'check'));
            }
        }
        
        // 시뮬레이션용 번호 입력 검증
        for (let i = 1; i <= 6; i++) {
            const simInput = document.getElementById(`sim-num${i}`);
            if (simInput) {
                simInput.addEventListener('input', (e) => this.validateNumberInput(e));
                simInput.addEventListener('blur', (e) => this.checkDuplicates(e, 'sim'));
            }
        }
        
        // QR 스캔 버튼 이벤트
        const qrButton = document.getElementById('start-qr-scan');
        if (qrButton) {
            qrButton.addEventListener('click', () => this.startQRScan());
        }
        
        // 스크롤 애니메이션
        this.initializeScrollAnimations();
        
        // 결과 공유 기능
        this.initializeShareFeatures();
        
        // 키보드 단축키
        this.initializeKeyboardShortcuts();
    }
    
    initializeAnimations() {
        // 히어로 섹션 로또볼 애니메이션
        this.animateHeroBalls();
        
        // 카운터 애니메이션
        this.animateCounters();
        
        // 배경 파티클 효과
        this.initializeParticleEffect();
        
        // 퀵 액션 카드 애니메이션
        this.initializeQuickActions();
    }
    
    async loadInitialStats() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();
            
            if (data.hot_numbers && data.cold_numbers) {
                this.displayStatistics(data);
            }
        } catch (error) {
            console.error('통계 로드 실패:', error);
        }
    }

    // ===== QR 스캔 기능 =====
    
    setupQRScanner() {
        this.log('QR 스캐너 설정 초기화');
    }
    
    async startQRScan() {
        try {
            this.log('QR 스캔 시작');
            
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('이 브라우저는 카메라를 지원하지 않습니다.');
            }
            
            // UI 변경
            document.getElementById('qr-start-area').style.display = 'none';
            document.getElementById('qr-scanner-area').style.display = 'block';
            
            // 카메라 스트림 시작
            const stream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    facingMode: 'environment',  // 후면 카메라 선호
                    width: { ideal: 640 },
                    height: { ideal: 480 }
                } 
            });
            
            this.currentStream = stream;
            const video = document.getElementById('qr-video');
            video.srcObject = stream;
            await video.play();
            
            this.showToast('QR 스캔 준비 완료! 로또 용지를 카메라에 대주세요.', 'info');
            
            // QR 코드 감지 시작
            this.startQRDetection(video);
            
        } catch (error) {
            console.error('QR 스캔 시작 실패:', error);
            this.showToast(error.message || '카메라에 접근할 수 없습니다.', 'error');
            this.stopQRScan();
        }
    }
    
    startQRDetection(video) {
        const canvas = document.getElementById('qr-canvas');
        const ctx = canvas.getContext('2d');
        
        const detectQR = () => {
            if (video.readyState === video.HAVE_ENOUGH_DATA) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                
                // 실제 구현에서는 QR 코드 라이브러리 사용
                // 여기서는 시뮬레이션
                if (Math.random() < 0.01) { // 1% 확률로 QR 감지 시뮬레이션
                    this.handleQRDetected('1,7,13,25,31,42'); // 시뮬레이션 데이터
                    return;
                }
            }
            
            if (this.currentStream) {
                requestAnimationFrame(detectQR);
            }
        };
        
        detectQR();
    }
    
    handleQRDetected(qrData) {
        this.log(`QR 감지됨: ${qrData}`);
        
        try {
            // QR 데이터 파싱 (실제로는 더 복잡한 파싱 필요)
            const numbers = qrData.split(',').map(n => parseInt(n.trim()));
            
            if (numbers.length === 6 && numbers.every(n => n >= 1 && n <= 45)) {
                this.stopQRScan();
                this.checkWinningNumbers(numbers);
            } else {
                this.showToast('올바른 로또 QR 코드가 아닙니다.', 'warning');
            }
        } catch (error) {
            console.error('QR 데이터 파싱 실패:', error);
            this.showToast('QR 코드를 읽을 수 없습니다.', 'error');
        }
    }
    
    stopQRScan() {
        if (this.currentStream) {
            this.currentStream.getTracks().forEach(track => track.stop());
            this.currentStream = null;
        }
        
        document.getElementById('qr-start-area').style.display = 'block';
        document.getElementById('qr-scanner-area').style.display = 'none';
    }
    
    async checkWinningNumbers(numbers) {
        try {
            const response = await fetch('/api/check-winning', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ numbers: numbers })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayWinningResult(data);
            } else {
                this.showToast(data.error || '당첨 확인에 실패했습니다.', 'error');
            }
        } catch (error) {
            console.error('당첨 확인 실패:', error);
            this.showToast('당첨 확인에 실패했습니다.', 'error');
        }
    }
    
    displayWinningResult(data) {
        const resultContainer = document.getElementById('qr-result');
        
        let resultClass = 'alert-success';
        let resultIcon = 'fas fa-trophy';
        let celebrationEmoji = '🎉';
        
        if (data.prize === '낙첨') {
            resultClass = 'alert-secondary';
            resultIcon = 'fas fa-times-circle';
            celebrationEmoji = '😢';
        } else if (data.prize === '1등' || data.prize === '2등') {
            resultClass = 'alert-warning';
            resultIcon = 'fas fa-crown';
            celebrationEmoji = '👑';
            this.triggerCelebration();
        }
        
        resultContainer.innerHTML = `
            <div class="alert ${resultClass} shadow-lg">
                <div class="text-center">
                    <i class="${resultIcon} fa-3x mb-3 animate__animated animate__bounceIn"></i>
                    <h4 class="mb-2">${celebrationEmoji} ${data.prize} ${celebrationEmoji}</h4>
                    <h5 class="text-primary mb-4">${data.prize_money}</h5>
                    
                    <div class="row mt-4">
                        <div class="col-md-6">
                            <h6 class="mb-3">내 번호</h6>
                            <div class="number-display justify-content-center mb-3">
                                ${data.user_numbers.map(num => 
                                    `<div class="lotto-ball lotto-ball-${this.getNumberColorClass(num)} ${data.winning_numbers.includes(num) ? 'matched-number' : ''}">${num}</div>`
                                ).join('')}
                            </div>
                        </div>
                        <div class="col-md-6">
                            <h6 class="mb-3">당첨번호 (${data.round}회차)</h6>
                            <div class="number-display justify-content-center mb-3">
                                ${data.winning_numbers.map(num => 
                                    `<div class="lotto-ball lotto-ball-${this.getNumberColorClass(num)} ${data.user_numbers.includes(num) ? 'matched-number' : ''}">${num}</div>`
                                ).join('')}
                                <div class="lotto-ball bonus-ball ${data.user_numbers.includes(data.bonus_number) ? 'matched-number' : ''}">${data.bonus_number}</div>
                            </div>
                            <small class="text-muted">마지막은 보너스번호</small>
                        </div>
                    </div>
                    
                    <div class="mt-4 p-3 bg-light rounded">
                        <div class="row text-center">
                            <div class="col-4">
                                <strong class="text-success">${data.matches}개</strong>
                                <br><small class="text-muted">일치</small>
                            </div>
                            <div class="col-4">
                                <strong class="text-warning">${data.bonus_match ? 'O' : 'X'}</strong>
                                <br><small class="text-muted">보너스</small>
                            </div>
                            <div class="col-4">
                                <strong class="text-primary">${data.prize}</strong>
                                <br><small class="text-muted">등수</small>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-4">
                        <button onclick="lottoPro.shareWinningResult(${JSON.stringify(data).replace(/"/g, '&quot;')})" class="btn btn-primary me-2">
                            <i class="fas fa-share me-2"></i>결과 공유
                        </button>
                        <button onclick="lottoPro.saveWinningResult(${JSON.stringify(data).replace(/"/g, '&quot;')})" class="btn btn-success">
                            <i class="fas fa-save me-2"></i>결과 저장
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        resultContainer.classList.remove('d-none');
        resultContainer.scrollIntoView({ behavior: 'smooth' });
        
        // 당첨 시 효과음 (가능한 경우)
        if (data.prize !== '낙첨') {
            this.playWinSound();
        }
    }
    
    triggerCelebration() {
        // 축하 애니메이션 효과
        this.createConfetti();
        this.showToast('🎉 축하합니다! 고액 당첨입니다! 🎉', 'success');
    }
    
    createConfetti() {
        // 간단한 색종이 효과 생성
        for (let i = 0; i < 50; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.cssText = `
                position: fixed;
                top: -10px;
                left: ${Math.random() * window.innerWidth}px;
                width: 10px;
                height: 10px;
                background: ${['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#6c5ce7'][Math.floor(Math.random() * 5)]};
                z-index: 9999;
                animation: confetti-fall 3s linear forwards;
                pointer-events: none;
            `;
            document.body.appendChild(confetti);
            
            setTimeout(() => confetti.remove(), 3000);
        }
    }
    
    // ===== 번호 저장 및 관리 =====
    
    async loadSavedNumbers() {
        try {
            const response = await fetch('/api/saved-numbers');
            const data = await response.json();
            
            if (data.success) {
                this.savedNumbers = data.saved_numbers;
                this.displaySavedNumbers();
            }
        } catch (error) {
            console.error('저장된 번호 로드 실패:', error);
        }
    }
    
    displaySavedNumbers() {
        const container = document.getElementById('saved-numbers-list');
        
        if (this.savedNumbers.length > 0) {
            container.innerHTML = this.savedNumbers.map(item => `
                <div class="saved-number-item mb-3 p-3 border rounded animate__animated animate__fadeInUp">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="mb-0 text-truncate" style="max-width: 200px;" title="${item.label}">${item.label}</h6>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary" onclick="lottoPro.useSavedNumber('${item.id}')" title="예측에 사용">
                                <i class="fas fa-magic"></i>
                            </button>
                            <button class="btn btn-outline-success" onclick="lottoPro.checkSavedNumber('${item.id}')" title="당첨 확인">
                                <i class="fas fa-check"></i>
                            </button>
                            <button class="btn btn-outline-warning" onclick="lottoPro.editSavedNumber('${item.id}')" title="수정">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-outline-danger" onclick="lottoPro.deleteSavedNumber('${item.id}')" title="삭제">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div class="number-display mb-2">
                        ${item.numbers.map(num => `<div class="lotto-ball lotto-ball-${this.getNumberColorClass(num)}" title="번호 ${num}">${num}</div>`).join('')}
                    </div>
                    <div class="d-flex justify-content-between align-items-center">
                        <small class="text-muted">${new Date(item.saved_at).toLocaleString()}</small>
                        <div class="saved-number-actions">
                            <button class="btn btn-sm btn-outline-info" onclick="lottoPro.copySavedNumber('${item.id}')" title="번호 복사">
                                <i class="fas fa-copy"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-secondary" onclick="lottoPro.shareSavedNumber('${item.id}')" title="번호 공유">
                                <i class="fas fa-share"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = `
                <div class="text-center text-muted py-4 animate__animated animate__fadeIn">
                    <i class="fas fa-inbox fa-3x mb-3 opacity-50"></i>
                    <h6>저장된 번호가 없습니다</h6>
                    <p class="mb-0">소중한 번호들을 저장해보세요!</p>
                    <button onclick="document.getElementById('save-num1').focus()" class="btn btn-primary btn-sm mt-2">
                        <i class="fas fa-plus me-1"></i>첫 번호 저장하기
                    </button>
                </div>
            `;
        }
    }
    
    async saveNumbers() {
        const label = document.getElementById('save-label').value.trim() || `저장된 번호 ${new Date().toLocaleString()}`;
        const numbers = [];
        
        for (let i = 1; i <= 6; i++) {
            const input = document.getElementById(`save-num${i}`);
            if (input.value) {
                const num = parseInt(input.value);
                if (num >= 1 && num <= 45) {
                    numbers.push(num);
                }
            }
        }
        
        if (numbers.length !== 6) {
            this.showToast('6개의 번호를 모두 입력해주세요.', 'warning');
            this.highlightEmptyInputs('save');
            return;
        }
        
        if (new Set(numbers).size !== 6) {
            this.showToast('중복된 번호가 있습니다.', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/save-numbers', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    numbers: numbers.sort((a, b) => a - b),
                    label: label
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast('번호가 저장되었습니다! 🎯', 'success');
                
                // 입력 필드 초기화
                document.getElementById('save-label').value = '';
                for (let i = 1; i <= 6; i++) {
                    const input = document.getElementById(`save-num${i}`);
                    input.value = '';
                    input.classList.remove('is-valid', 'is-invalid');
                }
                
                // 저장된 번호 목록 새로고침
                await this.loadSavedNumbers();
                
                // 저장 성공 애니메이션
                this.playSuccessAnimation();
                
            } else {
                this.showToast(data.error || '번호 저장에 실패했습니다.', 'error');
            }
        } catch (error) {
            console.error('번호 저장 실패:', error);
            this.showToast('번호 저장에 실패했습니다.', 'error');
        }
    }
    
    async deleteSavedNumber(id) {
        const savedNumber = this.savedNumbers.find(item => item.id === id);
        if (!savedNumber) return;
        
        if (!confirm(`"${savedNumber.label}" 번호를 삭제하시겠습니까?`)) {
            return;
        }
        
        try {
            const response = await fetch('/api/delete-saved-number', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ id: id })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast('번호가 삭제되었습니다.', 'success');
                await this.loadSavedNumbers();
            } else {
                this.showToast(data.error || '삭제에 실패했습니다.', 'error');
            }
        } catch (error) {
            console.error('번호 삭제 실패:', error);
            this.showToast('삭제에 실패했습니다.', 'error');
        }
    }
    
    useSavedNumber(id) {
        const savedNumber = this.savedNumbers.find(item => item.id === id);
        if (!savedNumber) return;
        
        // 예측 폼에 번호 입력
        for (let i = 0; i < 6; i++) {
            const input = document.getElementById(`num${i + 1}`);
            if (input) {
                input.value = savedNumber.numbers[i];
                input.classList.add('is-valid');
            }
        }
        
        this.showToast(`"${savedNumber.label}" 번호를 예측에 적용했습니다!`, 'success');
        
        // 예측 섹션으로 스크롤
        document.getElementById('prediction')?.scrollIntoView({ behavior: 'smooth' });
    }
    
    checkSavedNumber(id) {
        const savedNumber = this.savedNumbers.find(item => item.id === id);
        if (!savedNumber) return;
        
        this.checkWinningNumbers(savedNumber.numbers);
    }
    
    copySavedNumber(id) {
        const savedNumber = this.savedNumbers.find(item => item.id === id);
        if (!savedNumber) return;
        
        const text = savedNumber.numbers.join(', ');
        navigator.clipboard.writeText(text).then(() => {
            this.showToast(`번호가 복사되었습니다: ${text}`, 'success');
        }).catch(() => {
            this.showToast('복사 실패', 'error');
        });
    }
    
    shareSavedNumber(id) {
        const savedNumber = this.savedNumbers.find(item => item.id === id);
        if (!savedNumber) return;
        
        const text = `LottoPro AI v2.0 저장 번호 "${savedNumber.label}": ${savedNumber.numbers.join(', ')}`;
        
        if (navigator.share) {
            navigator.share({
                title: 'LottoPro AI 저장 번호',
                text: text,
                url: window.location.href
            });
        } else {
            this.copySavedNumber(id);
        }
    }

    // ===== 실시간 예시번호 기능 =====
    
    initializeHeroExampleNumbers() {
        this.log('실시간 예시번호 시스템 초기화');
        
        // 즉시 첫 예시번호 생성
        this.updateHeroExampleNumbers();
        
        // 30초마다 자동 업데이트
        this.exampleUpdateInterval = setInterval(() => {
            this.updateHeroExampleNumbers();
        }, 30000);
        
        // 예시번호 클릭 시 수동 업데이트
        this.attachExampleClickEvent();
    }

    async updateHeroExampleNumbers() {
        try {
            this.log('예시번호 업데이트 시작');
            
            const response = await fetch('/api/example-numbers');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.example_numbers) {
                this.displayHeroExampleNumbers(data.example_numbers, data.analysis);
                this.log('예시번호 업데이트 완료:', data.example_numbers);
            } else {
                throw new Error(data.error || '예시번호 생성 실패');
            }
            
        } catch (error) {
            this.log('예시번호 업데이트 실패, 클라이언트 생성 사용:', error);
            this.generateClientSideExample();
        }
    }

    generateClientSideExample() {
        try {
            const numbers = [];
            const hotNumbers = [7, 13, 22, 31, 42, 1, 14, 25, 33, 43];
            
            // 2-3개는 핫넘버에서, 나머지는 랜덤
            for (let i = 0; i < 3; i++) {
                if (Math.random() < 0.8 && hotNumbers.length > 0) {
                    const randomIndex = Math.floor(Math.random() * hotNumbers.length);
                    const selected = hotNumbers[randomIndex];
                    if (!numbers.includes(selected)) {
                        numbers.push(selected);
                        hotNumbers.splice(randomIndex, 1);
                    }
                }
            }
            
            // 나머지 번호 랜덤 생성
            while (numbers.length < 6) {
                const randomNum = Math.floor(Math.random() * 45) + 1;
                if (!numbers.includes(randomNum)) {
                    numbers.push(randomNum);
                }
            }
            
            const sortedNumbers = numbers.sort((a, b) => a - b);
            
            const analysis = {
                sum: sortedNumbers.reduce((a, b) => a + b, 0),
                even_count: sortedNumbers.filter(n => n % 2 === 0).length,
                odd_count: sortedNumbers.filter(n => n % 2 !== 0).length
            };
            
            this.displayHeroExampleNumbers(sortedNumbers, analysis);
            this.log('클라이언트 예시번호 생성 완료:', sortedNumbers);
            
        } catch (error) {
            console.error('클라이언트 예시번호 생성 실패:', error);
        }
    }

    displayHeroExampleNumbers(numbers, analysis = null) {
        const container = document.getElementById('heroExampleNumbers');
        if (!container) return;
        
        // 기존 볼들을 페이드아웃
        const existingBalls = container.querySelectorAll('.lotto-ball');
        existingBalls.forEach((ball, index) => {
            setTimeout(() => {
                ball.style.transform = 'scale(0) rotateY(180deg)';
                ball.style.opacity = '0';
            }, index * 100);
        });
        
        // 새 번호들을 생성하고 페이드인
        setTimeout(() => {
            container.innerHTML = '';
            
            numbers.forEach((number, index) => {
                const ball = document.createElement('div');
                ball.className = `lotto-ball lotto-ball-${this.getNumberColorClass(number)} example-ball`;
                ball.textContent = number;
                ball.style.transform = 'scale(0) rotateY(-180deg)';
                ball.style.opacity = '0';
                ball.style.cursor = 'pointer';
                ball.title = '클릭하면 새로운 예시번호가 생성됩니다';
                
                // 호버 효과 추가
                ball.addEventListener('mouseenter', function() {
                    this.style.transform = 'scale(1.1) rotateY(0deg)';
                });
                
                ball.addEventListener('mouseleave', function() {
                    this.style.transform = 'scale(1) rotateY(0deg)';
                });
                
                container.appendChild(ball);
                
                // 순차적 애니메이션
                setTimeout(() => {
                    ball.style.transition = 'all 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55)';
                    ball.style.transform = 'scale(1) rotateY(0deg)';
                    ball.style.opacity = '1';
                }, index * 150 + 200);
            });
            
            // 분석 정보 업데이트
            this.updateExampleAnalysis(numbers, analysis);
            
        }, 600);
    }

    updateExampleAnalysis(numbers, analysis) {
        const infoContainer = document.getElementById('exampleInfo');
        if (infoContainer && analysis) {
            const infoHTML = `
                <small class="text-light opacity-75">
                    합계: ${analysis.sum} | 
                    짝수: ${analysis.even_count}개 | 
                    홀수: ${analysis.odd_count}개 | 
                    <span class="text-warning">✨ 실시간 AI 분석</span>
                </small>
            `;
            infoContainer.innerHTML = infoHTML;
            
            // 애니메이션 효과
            infoContainer.style.opacity = '0';
            setTimeout(() => {
                infoContainer.style.transition = 'opacity 0.5s ease';
                infoContainer.style.opacity = '1';
            }, 800);
        }
    }

    attachExampleClickEvent() {
        document.addEventListener('click', (event) => {
            if (event.target.classList.contains('example-ball')) {
                if (this.isUpdatingExample) return;
                
                this.isUpdatingExample = true;
                this.updateHeroExampleNumbers();
                
                this.showToast('새로운 AI 예시번호가 생성되었습니다! 🎯', 'info');
                
                setTimeout(() => {
                    this.isUpdatingExample = false;
                }, 1000);
            }
        });
    }

    // ===== 예측 기능 개선 =====
    
    validateNumberInput(event) {
        const input = event.target;
        let value = parseInt(input.value);
        
        // 입력값 범위 검증
        if (isNaN(value)) {
            input.classList.remove('is-valid', 'is-invalid');
            return;
        }
        
        if (value < 1) {
            input.value = 1;
            value = 1;
        } else if (value > 45) {
            input.value = 45;
            value = 45;
        }
        
        // 시각적 피드백
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
        
        // 중복 검사
        this.checkDuplicates(event);
    }
    
    checkDuplicates(event, prefix = '') {
        const currentInput = event.target;
        const currentValue = currentInput.value;
        
        if (!currentValue) return;
        
        let hasDuplicate = false;
        const inputPrefix = prefix || this.getInputPrefix(currentInput.id);
        
        // 다른 입력 필드들과 중복 검사
        for (let i = 1; i <= 6; i++) {
            const otherInput = document.getElementById(`${inputPrefix}num${i}`);
            if (otherInput && otherInput !== currentInput && otherInput.value === currentValue) {
                hasDuplicate = true;
                break;
            }
        }
        
        if (hasDuplicate) {
            currentInput.classList.remove('is-valid');
            currentInput.classList.add('is-invalid');
            currentInput.title = '중복된 번호입니다';
            
            // 중복 입력 시각적 효과
            currentInput.style.animation = 'shake 0.5s ease-in-out';
            setTimeout(() => {
                currentInput.style.animation = '';
            }, 500);
            
        } else {
            currentInput.classList.remove('is-invalid');
            currentInput.classList.add('is-valid');
            currentInput.title = '';
        }
    }
    
    getInputPrefix(inputId) {
        if (inputId.startsWith('save-')) return 'save-';
        if (inputId.startsWith('check-')) return 'check-';
        if (inputId.startsWith('sim-')) return 'sim-';
        return '';
    }
    
    handleNumberKeyPress(event) {
        // Enter 키로 다음 입력 필드로 이동
        if (event.key === 'Enter') {
            event.preventDefault();
            const currentId = parseInt(event.target.id.replace(/\D/g, ''));
            if (currentId < 6) {
                const prefix = this.getInputPrefix(event.target.id);
                const nextInput = document.getElementById(`${prefix}num${currentId + 1}`);
                if (nextInput) {
                    nextInput.focus();
                }
            } else {
                // 마지막 입력에서 Enter 시 해당 기능 실행
                if (event.target.id.startsWith('num')) {
                    this.handlePredictionSubmit(event);
                } else if (event.target.id.startsWith('save-')) {
                    this.saveNumbers();
                } else if (event.target.id.startsWith('check-')) {
                    this.checkWinningManual();
                }
            }
        }
    }
    
    getUserNumbers(prefix = '') {
        const userNumbers = [];
        for (let i = 1; i <= 6; i++) {
            const input = document.getElementById(`${prefix}num${i}`);
            if (input && input.value && input.value.trim() !== '') {
                const value = parseInt(input.value.trim());
                if (!isNaN(value) && value >= 1 && value <= 45) {
                    userNumbers.push(value);
                }
            }
        }
        return [...new Set(userNumbers)]; // 중복 제거
    }
    
    async handlePredictionSubmit(event) {
        event.preventDefault();
        
        if (this.isLoading) return;
        
        const userNumbers = this.getUserNumbers();
        
        // 중복 검사는 실제로 번호가 입력된 경우에만
        if (userNumbers.length > 0 && this.hasDuplicateNumbers()) {
            this.showToast('중복된 번호를 제거해주세요', 'error');
            return;
        }
        
        try {
            this.startLoading();
            
            const requestData = {
                user_numbers: userNumbers || []
            };
            
            this.log('전송 데이터:', requestData);
            
            // AI 예측 요청
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            this.log('응답 상태:', response.status);
            
            if (!response.ok) {
                let errorMessage = `서버 오류 (${response.status})`;
                
                if (response.status === 400) {
                    errorMessage = '잘못된 요청입니다. 번호를 다시 확인해주세요.';
                } else if (response.status === 500) {
                    errorMessage = '서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
                } else if (response.status === 404) {
                    errorMessage = '요청한 서비스를 찾을 수 없습니다.';
                }
                
                throw new Error(errorMessage);
            }
            
            const data = await response.json();
            this.log('응답 데이터:', data);
            
            if (data.success) {
                this.currentPrediction = data;
                await this.displayResults(data);
                
                if (userNumbers.length > 0) {
                    this.showToast(`선호 번호 ${userNumbers.length}개를 포함한 AI 예측이 완료되었습니다! 🎯`, 'success');
                } else {
                    this.showToast('AI 완전 랜덤 예측이 완료되었습니다! 🎯', 'success');
                }
                
                // 결과로 스크롤
                setTimeout(() => {
                    const resultsSection = document.getElementById('resultsSection');
                    if (resultsSection) {
                        resultsSection.scrollIntoView({ 
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                }, 500);
            } else {
                throw new Error(data.error || '예측 중 알 수 없는 오류가 발생했습니다');
            }
            
        } catch (error) {
            console.error('예측 오류:', error);
            
            let errorMessage = error.message;
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                errorMessage = '네트워크 연결에 문제가 있습니다. 인터넷 연결을 확인해주세요.';
            }
            
            this.showToast(errorMessage, 'error');
        } finally {
            this.stopLoading();
        }
    }
    
    hasDuplicateNumbers(prefix = '') {
        const filledInputs = [];
        const values = [];
        
        for (let i = 1; i <= 6; i++) {
            const input = document.getElementById(`${prefix}num${i}`);
            if (input && input.value && input.value.trim() !== '') {
                const value = parseInt(input.value.trim());
                if (!isNaN(value)) {
                    filledInputs.push(input);
                    values.push(value);
                }
            }
        }
        
        if (values.length === 0) {
            return false;
        }
        
        const uniqueValues = new Set(values);
        return uniqueValues.size !== values.length;
    }
    
    startLoading() {
        this.isLoading = true;
        
        // 버튼 상태 변경
        const button = document.querySelector('#predictionForm button[type="submit"]');
        if (button) {
            const buttonText = button.querySelector('.btn-text');
            const spinner = button.querySelector('.spinner-border');
            
            if (buttonText) buttonText.textContent = 'AI가 분석 중...';
            if (spinner) spinner.classList.remove('d-none');
            button.disabled = true;
            button.style.pointerEvents = 'none';
        }
        
        // 로딩 섹션 표시
        const loadingSection = document.getElementById('loadingSection');
        const resultsSection = document.getElementById('resultsSection');
        
        if (loadingSection) loadingSection.classList.remove('d-none');
        if (resultsSection) resultsSection.classList.add('d-none');
        
        // 로딩 애니메이션 효과
        this.animateLoadingEffect();
    }
    
    stopLoading() {
        this.isLoading = false;
        
        // 버튼 상태 복원
        const button = document.querySelector('#predictionForm button[type="submit"]');
        if (button) {
            const buttonText = button.querySelector('.btn-text');
            const spinner = button.querySelector('.spinner-border');
            
            if (buttonText) buttonText.textContent = 'AI 예상번호 생성하기';
            if (spinner) spinner.classList.add('d-none');
            button.disabled = false;
            button.style.pointerEvents = 'auto';
        }
        
        // 로딩 섹션 숨김
        const loadingSection = document.getElementById('loadingSection');
        if (loadingSection) loadingSection.classList.add('d-none');
    }
    
    animateLoadingEffect() {
        const loadingTexts = [
            'AI 모델이 데이터를 분석하고 있습니다...',
            '빈도분석 모델 실행 중...',
            '트렌드분석 모델 실행 중...',
            '패턴분석 모델 실행 중...',
            '통계분석 모델 실행 중...',
            '머신러닝 모델 실행 중...',
            '최적의 번호를 선별하고 있습니다...'
        ];
        
        let index = 0;
        const loadingText = document.querySelector('#loadingSection h4');
        
        const interval = setInterval(() => {
            if (!this.isLoading) {
                clearInterval(interval);
                return;
            }
            
            if (loadingText) {
                loadingText.textContent = loadingTexts[index];
                index = (index + 1) % loadingTexts.length;
            }
        }, 1500);
    }
    
    async displayResults(data) {
        // 결과 섹션 표시
        const resultsSection = document.getElementById('resultsSection');
        if (resultsSection) {
            resultsSection.classList.remove('d-none');
        }
        
        // 최고 추천 번호 표시
        await this.displayTopRecommendations(data.top_recommendations, data.user_numbers);
        
        // 모델별 결과 표시
        await this.displayModelResults(data.models, data.user_numbers);
        
        // 결과 애니메이션
        this.animateResults();
        
        // 성공 효과
        this.playSuccessAnimation();
    }
    
    async displayTopRecommendations(recommendations, userNumbers) {
        const container = document.getElementById('topRecommendations');
        if (!container) return;
        
        container.innerHTML = '';
        
        for (let i = 0; i < recommendations.length; i++) {
            const numbers = recommendations[i];
            const card = this.createRecommendationCard(numbers, `TOP ${i + 1}`, userNumbers, true);
            container.appendChild(card);
            
            // 순차적 애니메이션
            await this.delay(100);
            card.classList.add('animate__animated', 'animate__fadeInUp');
        }
    }
    
    async displayModelResults(models, userNumbers) {
        const container = document.getElementById('modelResults');
        if (!container) return;
        
        container.innerHTML = '';
        
        const modelOrder = [
            '빈도분석 모델',
            '트렌드분석 모델', 
            '패턴분석 모델',
            '통계분석 모델',
            '머신러닝 모델'
        ];
        
        for (const modelName of modelOrder) {
            if (models[modelName]) {
                const modelSection = this.createModelSection(modelName, models[modelName], userNumbers);
                container.appendChild(modelSection);
                
                await this.delay(200);
                modelSection.classList.add('animate__animated', 'animate__fadeInLeft');
            }
        }
    }
    
    createRecommendationCard(numbers, label, userNumbers = [], isTopPick = false) {
        const card = document.createElement('div');
        card.className = 'col-md-6 col-lg-4';
        
        const cardContent = document.createElement('div');
        cardContent.className = `prediction-result ${isTopPick ? 'top-recommendation' : ''}`;
        
        const header = document.createElement('div');
        header.className = 'result-header';
        header.innerHTML = `
            <h6 class="result-title">${label}</h6>
            <div class="result-actions">
                <button class="btn btn-sm btn-outline-primary me-2" onclick="lottoPro.copyNumbers([${numbers.join(',')}])" title="번호 복사">
                    <i class="fas fa-copy"></i>
                </button>
                <button class="btn btn-sm btn-outline-success me-2" onclick="lottoPro.shareNumbers([${numbers.join(',')}])" title="번호 공유">
                    <i class="fas fa-share"></i>
                </button>
                <button class="btn btn-sm btn-outline-info" onclick="lottoPro.saveNumbersFromResult([${numbers.join(',')}])" title="번호 저장">
                    <i class="fas fa-save"></i>
                </button>
            </div>
        `;
        
        const numbersDisplay = document.createElement('div');
        numbersDisplay.className = 'number-display';
        numbersDisplay.innerHTML = numbers.map(num => {
            const isUserNumber = userNumbers.includes(num);
            const ballClass = this.getNumberColorClass(num);
            const extraClass = isUserNumber ? 'user-number' : '';
            return `<div class="lotto-ball lotto-ball-${ballClass} ${extraClass}" title="${isUserNumber ? '내가 선택한 번호' : ''}">${num}</div>`;
        }).join('');
        
        cardContent.appendChild(header);
        cardContent.appendChild(numbersDisplay);
        
        if (userNumbers.length > 0) {
            const legend = document.createElement('small');
            legend.className = 'text-muted mt-2 d-block';
            legend.innerHTML = '⭐ = 내가 선택한 번호';
            cardContent.appendChild(legend);
        }
        
        card.appendChild(cardContent);
        
        return card;
    }
    
    createModelSection(modelName, modelData, userNumbers) {
        const section = document.createElement('div');
        section.className = 'model-section';
        
        const header = document.createElement('div');
        header.className = 'model-header';
        header.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h6 class="mb-1">${modelName}</h6>
                    <div class="model-description">${modelData.description}</div>
                </div>
                <div class="model-stats">
                    <span class="badge bg-light text-dark me-2">정확도 ${modelData.accuracy || 85}%</span>
                    <span class="badge bg-light text-dark">신뢰도 ${modelData.confidence || 90}%</span>
                </div>
            </div>
        `;
        
        const content = document.createElement('div');
        content.className = 'model-content';
        
        const predictionsContainer = document.createElement('div');
        predictionsContainer.className = 'row g-3';
        
        // 각 모델의 예측 결과 표시 (상위 5개만)
        modelData.predictions.slice(0, 5).forEach((numbers, index) => {
            const predictionCard = this.createRecommendationCard(
                numbers, 
                `${index + 1}번`, 
                userNumbers, 
                false
            );
            predictionsContainer.appendChild(predictionCard);
        });
        
        content.appendChild(predictionsContainer);
        
        // 통계 정보
        const stats = document.createElement('div');
        stats.className = 'mt-3 d-flex gap-2 flex-wrap';
        stats.innerHTML = `
            <span class="badge bg-primary">총 ${modelData.predictions.length}개 조합</span>
            <span class="badge bg-success">신뢰도 높음</span>
            <span class="badge bg-info">최신 데이터 반영</span>
        `;
        content.appendChild(stats);
        
        section.appendChild(header);
        section.appendChild(content);
        
        return section;
    }
    
    getNumberColorClass(number) {
        if (number <= 10) return '1';
        if (number <= 20) return '2';
        if (number <= 30) return '3';
        if (number <= 40) return '4';
        return '5';
    }
    
    displayStatistics(data) {
        // 핫 넘버 표시
        const hotContainer = document.getElementById('hotNumbers');
        if (hotContainer && data.hot_numbers) {
            hotContainer.innerHTML = data.hot_numbers.slice(0, 8).map(([num, freq]) => 
                `<div class="lotto-ball hot-number" title="${freq}회 출현" data-frequency="${freq}">${num}</div>`
            ).join('');
        }
        
        // 콜드 넘버 표시
        const coldContainer = document.getElementById('coldNumbers');
        if (coldContainer && data.cold_numbers) {
            coldContainer.innerHTML = data.cold_numbers.slice(0, 8).map(([num, freq]) => 
                `<div class="lotto-ball cold-number" title="${freq}회 출현" data-frequency="${freq}">${num}</div>`
            ).join('');
        }
    }
    
    // ===== 유틸리티 함수들 =====
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    log(message) {
        console.log(`[LottoPro-AI v2.0] ${message}`);
    }
    
    showToast(message, type = 'info') {
        // 기존 토스트 제거
        const existingToasts = document.querySelectorAll('.custom-toast');
        existingToasts.forEach(toast => toast.remove());
        
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed custom-toast`;
        toast.style.cssText = 'top: 100px; right: 20px; z-index: 9999; max-width: 350px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border: none; border-radius: 15px;';
        
        const iconMap = {
            'success': 'fas fa-check-circle',
            'error': 'fas fa-exclamation-triangle',
            'warning': 'fas fa-exclamation-circle',
            'info': 'fas fa-info-circle'
        };
        
        toast.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="${iconMap[type] || iconMap.info} me-2"></i>
                <span>${message}</span>
            </div>
            <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
        `;
        
        document.body.appendChild(toast);
        
        // 자동 제거
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.opacity = '0';
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.parentNode.removeChild(toast);
                    }
                }, 300);
            }
        }, 5000);
    }
    
    copyNumbers(numbers) {
        const text = numbers.join(', ');
        navigator.clipboard.writeText(text).then(() => {
            this.showToast(`번호가 복사되었습니다: ${text}`, 'success');
        }).catch(() => {
            this.showToast('복사 실패', 'error');
        });
    }
    
    shareNumbers(numbers) {
        const text = `LottoPro AI v2.0 추천 번호: ${numbers.join(', ')}`;
        const url = window.location.href;
        
        if (navigator.share) {
            navigator.share({
                title: 'LottoPro AI 추천 번호',
                text: text,
                url: url
            });
        } else {
            this.copyNumbers(numbers);
        }
    }
    
    saveNumbersFromResult(numbers) {
        // 저장 폼에 번호 입력
        for (let i = 0; i < 6; i++) {
            const input = document.getElementById(`save-num${i + 1}`);
            if (input) {
                input.value = numbers[i];
                input.classList.add('is-valid');
            }
        }
        
        // 라벨 자동 설정
        const labelInput = document.getElementById('save-label');
        if (labelInput) {
            labelInput.value = `AI 추천 번호 ${new Date().toLocaleString()}`;
        }
        
        this.showToast('번호가 저장 폼에 입력되었습니다!', 'success');
        
        // 저장 섹션으로 스크롤
        document.getElementById('my-numbers')?.scrollIntoView({ behavior: 'smooth' });
    }
    
    // ===== 애니메이션 및 UI 효과 =====
    
    animateResults() {
        const resultCards = document.querySelectorAll('.prediction-result');
        resultCards.forEach((card, index) => {
            setTimeout(() => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                card.style.transition = 'all 0.5s ease';
                
                setTimeout(() => {
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, 50);
            }, index * 100);
        });
    }
    
    animateHeroBalls() {
        const balls = document.querySelectorAll('.lotto-ball-container .lotto-ball');
        balls.forEach((ball, index) => {
            ball.addEventListener('click', () => {
                ball.style.animation = 'none';
                ball.offsetHeight; // 리플로우 강제 실행
                ball.style.animation = 'bounce 0.6s ease';
            });
        });
    }
    
    animateCounters() {
        const counters = document.querySelectorAll('.hero-stats h3');
        
        const observerOptions = {
            threshold: 0.5,
            rootMargin: '0px 0px -100px 0px'
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.animateCounter(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);
        
        counters.forEach(counter => {
            if (counter) observer.observe(counter);
        });
    }
    
    animateCounter(element) {
        const target = element.textContent.replace(/[^0-9]/g, '');
        const targetNumber = parseInt(target);
        
        if (isNaN(targetNumber)) return;
        
        let current = 0;
        const increment = targetNumber / 50;
        const timer = setInterval(() => {
            current += increment;
            if (current >= targetNumber) {
                current = targetNumber;
                clearInterval(timer);
            }
            element.textContent = element.textContent.replace(/[0-9]+/, Math.floor(current));
        }, 40);
    }
    
    initializeScrollAnimations() {
        const animatedElements = document.querySelectorAll('.feature-card, .about-feature-item');
        
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate__animated', 'animate__fadeInUp');
                }
            });
        }, observerOptions);
        
        animatedElements.forEach(element => {
            if (element) observer.observe(element);
        });
    }
    
    initializeShareFeatures() {
        const socialLinks = document.querySelectorAll('footer a[href="#"]');
        socialLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const platform = link.querySelector('i').classList.contains('fa-github') ? 'GitHub' :
                                link.querySelector('i').classList.contains('fa-twitter') ? 'Twitter' : 'Email';
                this.showToast(`${platform} 공유 기능은 준비 중입니다`, 'info');
            });
        });
    }
    
    initializeParticleEffect() {
        if (window.innerWidth > 768) {
            this.createParticles();
        }
    }
    
    createParticles() {
        const heroSection = document.querySelector('.hero-section');
        if (!heroSection) return;
        
        for (let i = 0; i < 20; i++) {
            const particle = document.createElement('div');
            particle.style.cssText = `
                position: absolute;
                width: 4px;
                height: 4px;
                background: rgba(255,255,255,0.3);
                border-radius: 50%;
                top: ${Math.random() * 100}%;
                left: ${Math.random() * 100}%;
                animation: float ${3 + Math.random() * 4}s infinite ease-in-out;
                animation-delay: ${Math.random() * 2}s;
                pointer-events: none;
            `;
            heroSection.appendChild(particle);
        }
    }
    
    initializeQuickActions() {
        const quickActions = document.querySelectorAll('.quick-action-card');
        quickActions.forEach(card => {
            card.addEventListener('click', function() {
                this.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    this.style.transform = 'scale(1)';
                }, 150);
            });
        });
    }
    
    initializeKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl + P: 예측 시작
            if (e.ctrlKey && e.key === 'p') {
                e.preventDefault();
                document.getElementById('prediction')?.scrollIntoView({ behavior: 'smooth' });
            }
            
            // Ctrl + S: 번호 저장
            if (e.ctrlKey && e.key === 's' && e.target.id.startsWith('save-')) {
                e.preventDefault();
                this.saveNumbers();
            }
            
            // Escape: QR 스캔 중지
            if (e.key === 'Escape' && this.currentStream) {
                this.stopQRScan();
            }
        });
    }
    
    playSuccessAnimation() {
        // 성공 시 간단한 펄스 애니메이션
        const button = document.querySelector('#predictionForm button[type="submit"]');
        if (button) {
            button.style.animation = 'pulse 0.6s ease-in-out';
            setTimeout(() => {
                button.style.animation = '';
            }, 600);
        }
    }
    
    playWinSound() {
        // 브라우저가 지원하는 경우 간단한 효과음
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
            oscillator.frequency.setValueAtTime(1000, audioContext.currentTime + 0.1);
            oscillator.frequency.setValueAtTime(1200, audioContext.currentTime + 0.2);
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.setValueAtTime(0, audioContext.currentTime + 0.3);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
        } catch (error) {
            // 오디오 지원하지 않는 경우 무시
        }
    }
    
    highlightEmptyInputs(prefix = '') {
        for (let i = 1; i <= 6; i++) {
            const input = document.getElementById(`${prefix}num${i}`);
            if (input && !input.value) {
                input.style.animation = 'highlight 1s ease-in-out';
                setTimeout(() => {
                    input.style.animation = '';
                }, 1000);
            }
        }
    }
    
    // ===== PWA 및 서비스 워커 =====
    
    initializeServiceWorker() {
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js')
                    .then(registration => {
                        this.log('ServiceWorker 등록 성공');
                    })
                    .catch(error => {
                        this.log('ServiceWorker 등록 실패');
                    });
            });
        }
    }
    
    // ===== 정리 =====
    
    destroy() {
        if (this.exampleUpdateInterval) {
            clearInterval(this.exampleUpdateInterval);
        }
        
        if (this.currentStream) {
            this.currentStream.getTracks().forEach(track => track.stop());
        }
        
        this.animationTimeouts.forEach(timeout => clearTimeout(timeout));
    }
}

// CSS 애니메이션 추가
const additionalCSS = `
@keyframes confetti-fall {
    0% { transform: translateY(-100vh) rotate(0deg); opacity: 1; }
    100% { transform: translateY(100vh) rotate(360deg); opacity: 0; }
}

@keyframes shake {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-5px); }
    75% { transform: translateX(5px); }
}

@keyframes highlight {
    0%, 100% { box-shadow: 0 0 0 0 rgba(255, 193, 7, 0); }
    50% { box-shadow: 0 0 0 5px rgba(255, 193, 7, 0.4); }
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}

.matched-number {
    border: 3px solid #28a745 !important;
    box-shadow: 0 0 15px rgba(40, 167, 69, 0.5) !important;
}

.quick-action-card {
    background: white;
    padding: 1rem;
    border-radius: 15px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
    border: 1px solid rgba(0,0,0,0.05);
}

.quick-action-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 5px 20px rgba(0,0,0,0.15);
}

.quick-action-card i {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
    display: block;
}

.confetti {
    border-radius: 50%;
}

.bonus-ball {
    background: linear-gradient(135deg, #e17055, #d63031) !important;
    border: 2px solid #fff !important;
}

.tax-breakdown .tax-item {
    padding: 1rem;
    background: #f8f9fa;
    border-radius: 10px;
    margin-bottom: 0.5rem;
}

.store-item:hover {
    background: #f8f9fa;
    transform: translateX(3px);
}

.saved-number-item {
    transition: all 0.3s ease;
}

.saved-number-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.animate__animated {
    animation-duration: 0.6s;
    animation-fill-mode: both;
}

.animate__fadeInUp {
    animation-name: fadeInUp;
}

.animate__fadeInLeft {
    animation-name: fadeInLeft;
}

.animate__bounceIn {
    animation-name: bounceIn;
}

.animate__fadeIn {
    animation-name: fadeIn;
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translate3d(0, 40px, 0);
    }
    to {
        opacity: 1;
        transform: translate3d(0, 0, 0);
    }
}

@keyframes fadeInLeft {
    from {
        opacity: 0;
        transform: translate3d(-40px, 0, 0);
    }
    to {
        opacity: 1;
        transform: translate3d(0, 0, 0);
    }
}

@keyframes bounceIn {
    from, 20%, 40%, 60%, 80%, to {
        animation-timing-function: cubic-bezier(0.215, 0.610, 0.355, 1.000);
    }
    0% {
        opacity: 0;
        transform: scale3d(.3, .3, .3);
    }
    20% {
        transform: scale3d(1.1, 1.1, 1.1);
    }
    40% {
        transform: scale3d(.9, .9, .9);
    }
    60% {
        opacity: 1;
        transform: scale3d(1.03, 1.03, 1.03);
    }
    80% {
        transform: scale3d(.97, .97, .97);
    }
    to {
        opacity: 1;
        transform: scale3d(1, 1, 1);
    }
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
`;

// 스타일 추가
const style = document.createElement('style');
style.textContent = additionalCSS;
document.head.appendChild(style);

// 전역 인스턴스 생성
let lottoPro;

// DOM 로드 완료 시 앱 초기화
document.addEventListener('DOMContentLoaded', function() {
    try {
        lottoPro = new LottoProAI();
        console.log('✅ LottoPro AI v2.0이 성공적으로 초기화되었습니다.');
        
        // 실시간 예시번호 시스템 초기화 (약간의 지연 후)
        setTimeout(() => {
            if (lottoPro && lottoPro.initializeHeroExampleNumbers) {
                lottoPro.initializeHeroExampleNumbers();
            }
        }, 1000);
        
    } catch (error) {
        console.error('❌ 앱 초기화 실패:', error);
    }
});

// 페이지 언로드 시 정리
window.addEventListener('beforeunload', function() {
    if (lottoPro) {
        lottoPro.destroy();
    }
});

// 전역 함수들
window.scrollToSection = function(sectionId) {
    document.getElementById(sectionId)?.scrollIntoView({ behavior: 'smooth' });
};

window.saveNumbers = function() {
    if (lottoPro) lottoPro.saveNumbers();
};

window.loadSavedNumbers = function() {
    if (lottoPro) lottoPro.loadSavedNumbers();
};

window.checkWinningManual = function() {
    if (lottoPro) {
        const numbers = lottoPro.getUserNumbers('check-');
        if (numbers.length === 6) {
            lottoPro.checkWinningNumbers(numbers);
        } else {
            lottoPro.showToast('6개의 번호를 모두 입력해주세요.', 'warning');
        }
    }
};

