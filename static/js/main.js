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

        // 모달 이벤트
        document.querySelector('.close').addEventListener('click', () => {
            this.closeModal();
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
    }

    async loadInitialData() {
        try {
            // 통계 데이터 로드
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
        document.getElementById('totalDraws').textContent = data.total_draws.toLocaleString();
        document.getElementById('lastDraw').textContent = `${data.last_draw_info.round}회`;
        document.getElementById('lastUpdate').textContent = new Date().toLocaleDateString('ko-KR');
    }

    async generatePredictions() {
        const loadingIndicator = document.getElementById('loadingIndicator');
        const predictionsContainer = document.getElementById('predictionsContainer');
        const generateBtn = document.getElementById('generateBtn');

        try {
            // UI 상태 변경
            loadingIndicator.style.display = 'block';
            predictionsContainer.style.display = 'none';
            generateBtn.disabled = true;

            // API 호출
            const response = await fetch('/api/predictions');
            const data = await response.json();

            if (data.success) {
                this.algorithms = data.data;
                this.renderPredictions();
                predictionsContainer.style.display = 'block';
                
                // 성공 메시지
                this.showSuccess('AI 예측 번호가 생성되었습니다!');
            } else {
                throw new Error(data.error || '예측 생성에 실패했습니다.');
            }
        } catch (error) {
            console.error('예측 생성 실패:', error);
            this.showError('예측 생성에 실패했습니다. 다시 시도해주세요.');
        } finally {
            loadingIndicator.style.display = 'none';
            generateBtn.disabled = false;
        }
    }

    renderPredictions() {
        const container = document.getElementById('algorithmsGrid');
        container.innerHTML = '';

        const algorithmColors = {
            'frequency': '#FF6B6B',
            'hot_cold': '#4ECDC4',
            'pattern': '#45B7D1',
            'statistical': '#96CEB4',
            'machine_learning': '#FFEAA7'
        };

        const algorithmIcons = {
            'frequency': 'fas fa-chart-bar',
            'hot_cold': 'fas fa-thermometer-half',
            'pattern': 'fas fa-puzzle-piece',
            'statistical': 'fas fa-calculator',
            'machine_learning': 'fas fa-robot'
        };

        for (const [key, algorithm] of Object.entries(this.algorithms)) {
            const algorithmCard = this.createAlgorithmCard(
                key, 
                algorithm, 
                algorithmColors[key], 
                algorithmIcons[key]
            );
            container.appendChild(algorithmCard);
        }
    }

    createAlgorithmCard(key, algorithm, color, icon) {
        const card = document.createElement('div');
        card.className = 'algorithm-card';
        card.style.borderLeftColor = color;

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

        card.innerHTML = `
            <div class="algorithm-header">
                <div class="algorithm-info">
                    <i class="${icon}" style="color: ${color}"></i>
                    <div>
                        <h3>${algorithm.name}</h3>
                        <p>${algorithm.description}</p>
                    </div>
                </div>
                <div class="algorithm-badge" style="background-color: ${color}">
                    ${algorithm.predictions.length}세트
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
                
                // 통계 섹션으로 스크롤
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
            index: index
        };

        document.getElementById('modalTitle').textContent = 
            `${algorithm.name} - 세트 ${index + 1}`;
        
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
        
        // 클립보드 API 사용
        if (navigator.clipboard) {
            navigator.clipboard.writeText(numbersText).then(() => {
                this.showSuccess('번호가 클립보드에 복사되었습니다!');
            }).catch(() => {
                this.fallbackCopy(numbersText);
            });
        } else {
            this.fallbackCopy(numbersText);
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
            numbers: this.currentModalData.numbers,
            timestamp: new Date().toISOString(),
            round: this.statistics.last_draw_info?.round + 1 || '미확인'
        };

        // 로컬 스토리지에 저장
        let savedNumbers = JSON.parse(localStorage.getItem('savedLottoNumbers') || '[]');
        savedNumbers.push(saveData);
        
        // 최근 20개만 유지
        if (savedNumbers.length > 20) {
            savedNumbers = savedNumbers.slice(-20);
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
        // 기존 알림 제거
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

        // 3초 후 제거
        setTimeout(() => {
            notification.classList.add('notification-fade');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    // 유틸리티 메서드들
    formatNumber(num) {
        return num.toString().padStart(2, '0');
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('ko-KR');
    }

    animateNumbers(element) {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            element.style.transition = 'all 0.5s ease';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, 100);
    }
}

// 앱 초기화
document.addEventListener('DOMContentLoaded', () => {
    window.lottoApp = new LottoApp();
});

// 서비스 워커 등록 (PWA 지원)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}
