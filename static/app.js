function appData() {
            return {
                captureForm: {
                    content: '',
                    tags: []
                },
                tagInput: '',
                status: {
                    total_star: 0,
                    today_count: 0,
                    streak_days: 0,
                    medals: [],
                    monthly_medals: 0,
                    gray_medal: false,
                    fund_bonus: 0,
                    weekly_review_done: false,
                    monthly_report_done: false
                },
                config: {
                    base_star: 10,
                    daily_multipliers: [1.0, 1.5, 2.0, 0.2],
                    weekly_review_reward: 200,
                    monthly_report_reward: 500,
                    content_output_reward_min: 750,
                    content_output_reward_max: 1000,
                    content_output_max_times: 5,
                    coupon_rate: 1.0,
                    fund_base_rate: 1.0,
                    fund_base_bonus: 0.5,
                    fund: {
                        base_rate: 1.0,
                        base_bonus: 0.5,
                        lock_days: 30,
                        min_withdraw: 500
                    },
                    custom_fund_name: "我的投资账户",
                    exchange_enabled: false
                },
                showNotification: false,
                notificationMessage: '',
                notificationType: 'success',
                notificationIcon: '✅',
                showExchangeModal: false,
                exchangeType: 'coupon',
                exchangeAmount: '',
                showIncomeModal: false,
                incomeRecords: [],
                showEarned: false,
                ui: {
                    editing: {
                        baseStar: false,
                        weeklyReward: false,
                        monthlyReward: false,
                        couponRate: false,
                        fundRate: false,
                        fundName: false,
                        multipliers: [false, false, false, false]
                    }
                },
                editValue: {
                    baseStar: '',
                    weeklyReward: '',
                    monthlyReward: '',
                    couponRate: '',
                    fundRate: '',
                    fundName: '',
                    multipliers: ['', '', '', '']
                },
                publishUrl: '',
                // 回顾弹窗状态
                showReviewModal: false,
                reviewType: '',
                reviewData: {},
                reviewInsight: '',
                copySuccess: false,
                renderedContent: '',
                reviewRawContent: '',
                // ===== 消费记录（v0.4 新增） =====
                showConsumptionModal: false,
                consumptionContent: '',
                consumptionAmount: null,
                consumptionData: {
                    consumed_amount: 0,
                    coupon_pool: 0,
                    remaining: 0,
                    records: []
                },
                allMedals: [
                    { name: '灵光乍现', emoji: '💡' },
                    { name: '周常猎人', emoji: '🏹' },
                    { name: '连线大师', emoji: '🔗' }
                ],
                // ===== 采集成功弹窗 =====
                captureSuccessData: null,
                showCaptureSuccessModal: false,
                expandedNote: null,
                closeCaptureSuccessModal() {
                    this.showCaptureSuccessModal = false;
                    this.captureSuccessData = null;
                    this.expandedNote = null;
                },
                // ===== 重复提交警告 =====
                duplicateWarningData: null,
                showDuplicateWarningModal: false,
                closeDuplicateWarningModal() {
                    this.showDuplicateWarningModal = false;
                    this.duplicateWarningData = null;
                },
                // ===== 长期推演数据 =====
                projection: null,
                showProjectionModal: false,
                async loadProjection() {
                    try {
                        const response = await fetch('/api/projection');
                        if (response.ok) {
                            this.projection = await response.json();
                        }
                    } catch (error) {
                        console.error('Failed to load projection:', error);
                    }
                },
                openProjectionModal() {
                    this.loadProjection();
                    this.showProjectionModal = true;
                },
                closeProjectionModal() {
                    this.showProjectionModal = false;
                },
                // ===== 赛季结算 =====
                seasonSettlementData: null,
                showSeasonSettlementModal: false,
                async checkSeasonEnd() {
                    try {
                        const response = await fetch('/api/season/check', { method: 'POST' });
                        const data = await response.json();
                        
                        if (data.season_changed) {
                            this.seasonSettlementData = data;
                            this.showSeasonSettlementModal = true;
                            await this.loadStatus();
                        } else {
                            this.showNotificationMessage('当前赛季尚未结束', 'info', '📅');
                        }
                    } catch (error) {
                        console.error('Failed to check season end:', error);
                    }
                },
                closeSeasonSettlementModal() {
                    this.showSeasonSettlementModal = false;
                    this.seasonSettlementData = null;
                },
                getSeasonMessage(activeDays) {
                    if (activeDays >= 60) {
                        return '你保持了惊人的专注力，连续活跃超过60天。这份坚持终将开花结果。';
                    } else if (activeDays >= 30) {
                        return '你建立了稳定的采集习惯，这是成长的基石。继续保持。';
                    } else if (activeDays >= 10) {
                        return '你开始了这段旅程。每一个开始都值得尊敬。';
                    } else {
                        return '新的赛季，新的开始。无论过去如何，此刻都是重新出发的机会。';
                    }
                },
                // ===== 标签相关 =====
                tagViewMode: 'cloud',
                tagCloudData: {},
                tagNotes: [],
                selectedTag: '',
                showTagModal: false,
                tagDetailLoading: false,
                tagDetailError: '',
                async loadTags() {
                    try {
                        const response = await fetch('/api/tags');
                        if (response.ok) {
                            const data = await response.json();
                            this.tagCloudData = data.nodes || {};
                        }
                    } catch (error) {
                        console.error('Failed to load tags:', error);
                    }
                },
                // ===== 获取记录 =====
                showIncomeModal: false,
                incomeRecords: [],
                async openIncomeHistory() {
                    try {
                        const response = await fetch('/api/income/history');
                        if (response.ok) {
                            const data = await response.json();
                            this.incomeRecords = data.records || [];
                            this.showIncomeModal = true;
                        }
                    } catch (error) {
                        console.error('Failed to load income records:', error);
                    }
                },
                closeIncomeModal() {
                    this.showIncomeModal = false;
                },
                get tagCloudData() {
                    return this._tagCloudData || {};
                },
                set tagCloudData(value) {
                    this._tagCloudData = value;
                },
                getTagSize(count) {
                    // 按团队建议：基准 11px，log 映射，最大 20px
                    return Math.min(11 + Math.log(count + 1) * 3, 20);
                },
                getTagColor(count) {
                    const colors = [
                        'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                        'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                        'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
                        'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'
                    ];
                    const index = Math.min(count - 1, colors.length - 1);
                    return colors[index];
                },
                get sortedTags() {
                    // 排行榜：只显示 count >= 2 的标签，最多 50 个
                    return Object.entries(this.tagCloudData)
                        .filter(([_, data]) => data.count >= 2)
                        .sort((a, b) => b[1].count - a[1].count)
                        .slice(0, 50);
                },
                get filteredTagCloudEntries() {
                    // 标签云：只显示 count >= 2 的标签，最多 50 个
                    return Object.entries(this.tagCloudData)
                        .filter(([_, data]) => data.count >= 2)
                        .sort((a, b) => b[1].count - a[1].count)
                        .slice(0, 50);
                },
                getSeasonEndDate() {
                    if (this.status.current_season?.end_date) {
                        return this.status.current_season.end_date;
                    }
                    if (!this.status.current_season?.start_date) {
                        return '-';
                    }
                    const start = new Date(this.status.current_season.start_date);
                    start.setDate(start.getDate() + 15);
                    return start.toISOString().split('T')[0];
                },
                async openTagDetail(tag) {
                    this.selectedTag = tag;
                    this.tagNotes = [];
                    this.tagDetailError = '';
                    this.tagDetailLoading = true;
                    this.showTagModal = true;
                    
                    try {
                        const response = await fetch(`/api/notes/by-tag?tag=${encodeURIComponent(tag)}`);
                        if (response.ok) {
                            this.tagNotes = await response.json();
                        } else {
                            this.tagDetailError = '加载失败，请重试';
                        }
                    } catch (error) {
                        console.error('Failed to load tag notes:', error);
                        this.tagDetailError = '网络错误，请检查连接';
                    } finally {
                        this.tagDetailLoading = false;
                    }
                },
                closeTagModal() {
                    this.showTagModal = false;
                    this.tagNotes = [];
                    this.selectedTag = '';
                },
                addTag() {
                    if (this.tagInput.trim() && !this.captureForm.tags.includes(this.tagInput.trim())) {
                        this.captureForm.tags.push(this.tagInput.trim());
                        this.tagInput = '';
                    }
                },
                removeTag(index) {
                    this.captureForm.tags.splice(index, 1);
                },
                extractTags() {
                    const content = this.captureForm.content.trim();
                    if (!content) return;
                    
                    // 匹配 #标签 格式：以#开头，后跟非空格、非标点的中文/英文/数字/斜杠
                    // 排除 Markdown 标题格式（## ### 等）和 # 后面直接是空格的情况
                    const tagPattern = /#([^\s.,;:!?，。；：！？、\n#][^\s.,;:!?，。；：！？、\n]*)/g;
                    const matches = content.match(tagPattern) || [];
                    const extracted = matches
                        .map(t => t.replace(/^#/, '').trim())
                        .filter(t => t.length > 0 && t !== '#');
                    
                    // 去重 + 合并到现有标签（不替换，只追加）
                    const allTags = new Set([...this.captureForm.tags, ...extracted]);
                    this.captureForm.tags = [...allTags];
                },
                async submitCapture() {
                    if (!this.captureForm.content.trim()) return;
                    
                    try {
                        const response = await fetch('/api/capture', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                content: this.captureForm.content,
                                tags: this.captureForm.tags,
                                folder: 'Inbox'
                            })
                        });
                        
                        const data = await response.json();
                        
                        if (response.ok) {
                            this.showEarned = true;
                            setTimeout(() => { this.showEarned = false; }, 500);
                            
                            // 保存采集成功数据用于弹窗展示
                            this.captureSuccessData = data;
                            this.showCaptureSuccessModal = true;
                            
                            this.captureForm.content = '';
                            this.captureForm.tags = [];
                            this.tagInput = '';
                            await this.loadStatus();
                            await this.loadTags();
                            this.playSound();
                        } else {
                            // 检测是否是重复提交错误
                            if (data.error && (data.error.includes('相同内容') || data.error.includes('高度相似'))) {
                                this.duplicateWarningData = {
                                    error: data.error,
                                    detail: data.detail
                                };
                                this.showDuplicateWarningModal = true;
                            } else {
                                this.showNotificationMessage(data.detail || '捕获失败', 'error', '❌');
                            }
                        }
                    } catch (error) {
                        this.showNotificationMessage('网络错误', 'error', '❌');
                    }
                },
                async loadStatus() {
                    try {
                        const response = await fetch('/api/status');
                        if (response.ok) {
                            this.status = await response.json();
                        }
                    } catch (error) {
                        console.error('Failed to load status:', error);
                    }
                },
                
                // 初始化时加载消费记录数据（v0.4 新增）
                async init() {
                    await this.loadStatus();
                    await this.loadConfig();
                    await this.loadConsumptionData();  // 加载消费记录
                },
                async loadConfig() {
                    try {
                        const response = await fetch('/api/config');
                        if (response.ok) {
                            this.config = await response.json();
                            this.configForm = { ...this.config };
                            this.multipliersInput = this.config.daily_multipliers.join(',');
                        }
                    } catch (error) {
                        console.error('Failed to load config:', error);
                    }
                },
                openExchangeModal(type) {
                    this.cancelAllEdits();
                    this.exchangeType = type;
                    this.exchangeAmount = '';
                    this.showExchangeModal = true;
                },
                closeExchangeModal() {
                    this.showExchangeModal = false;
                    this.exchangeAmount = '';
                },
                async openIncomeModal() {
                    try {
                        const response = await fetch('/api/income/history');
                        if (response.ok) {
                            const data = await response.json();
                            this.incomeRecords = data.records || [];
                            this.showIncomeModal = true;
                        }
                    } catch (error) {
                        console.error('Failed to load income records:', error);
                    }
                },
                closeIncomeModal() {
                    this.showIncomeModal = false;
                },
                calculateRealValue() {
                    if (!this.exchangeAmount) return 0;
                    
                    if (this.exchangeType === 'coupon') {
                        return (this.exchangeAmount * this.config.coupon_rate).toFixed(2);
                    } else {
                        const bonus = this.status.fund_bonus / 100;
                        return (this.exchangeAmount * (this.config.fund_base_rate + (this.config.fund_base_bonus || 0) + bonus)).toFixed(2);
                    }
                },
                async submitPublish() {
                    if (!this.publishUrl.trim()) {
                        this.showNotificationMessage('请输入发布链接', 'error', '❌');
                        return;
                    }
                    
                    if (this.status.published_count >= 5) {
                        this.showNotificationMessage('已达到最大发布次数（5次）', 'error', '❌');
                        return;
                    }
                    
                    try {
                        const response = await fetch('/api/content/verify', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ url: this.publishUrl })
                        });
                        
                        const data = await response.json();
                        
                        if (response.ok) {
                            this.showNotificationMessage(`发布成功！获得 ${data.reward} 星点`, 'success', '🎉');
                            this.publishUrl = '';
                            await this.loadStatus();
                        } else {
                            this.showNotificationMessage(data.detail || '发布失败', 'error', '❌');
                        }
                    } catch (error) {
                        console.error('Publish error:', error);
                        this.showNotificationMessage('网络错误', 'error', '❌');
                    }
                },
                async submitExchange() {
                    if (!this.exchangeAmount || this.exchangeAmount <= 0) {
                        this.showNotificationMessage('请输入有效的星点数量', 'error', '❌');
                        return;
                    }
                    
                    if (this.exchangeAmount > this.status.total_star) {
                        this.showNotificationMessage('星点不足', 'error', '❌');
                        return;
                    }
                    
                    try {
                        const endpoint = this.exchangeType === 'fund' ? '/api/exchange/fund' : '/api/exchange/coupon';
                        const response = await fetch(endpoint, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                amount: this.exchangeAmount
                            })
                        });
                        
                        const data = await response.json();
                        
                        if (response.ok) {
                            this.showNotificationMessage(
                                `兑换成功！扣除 ${data.deducted_star} 星点，实际价值 ${data.real_value.toFixed(2)}`, 
                                'success', 
                                '✅'
                            );
                            this.closeExchangeModal();
                            await this.loadStatus();
                        } else {
                            this.showNotificationMessage(data.detail || '兑换失败', 'error', '❌');
                        }
                    } catch (error) {
                        this.showNotificationMessage('网络错误', 'error', '❌');
                    }
                },
                // ===== 回顾与战报：两步流程 =====

                async openReview(type) {
                    const endpoint = type === 'weekly' ? '/api/review/weekly' : '/api/report/monthly';
                    
                    try {
                        const response = await fetch(endpoint, { method: 'POST' });
                        const data = await response.json();
                        
                        if (response.ok) {
                            this.reviewType = type;
                            this.reviewData = data;
                            this.reviewInsight = '';
                            this.copySuccess = false;
                            this.reviewRawContent = data.content;
                            this.renderedContent = this.parseMaterialContent(data.content);
                            this.showReviewModal = true;
                        } else {
                            this.showNotificationMessage(data.detail || '生成素材失败', 'error', '❌');
                        }
                    } catch (error) {
                        this.showNotificationMessage('网络错误', 'error', '❌');
                    }
                },

                parseMaterialContent(md) {
                    // 将素材 Markdown 转为带层级的 HTML（过滤 frontmatter 由后端保证）
                    let html = '';
                    const lines = md.split('\n');
                    let inCodeBlock = false;
                    
                    for (let i = 0; i < lines.length; i++) {
                        let line = lines[i];
                        
                        // 跳过 YAML frontmatter 标记
                        if (line.trim() === '---') {
                            inCodeBlock = !inCodeBlock;
                            continue;
                        }
                        if (inCodeBlock) continue;
                        
                        // 空行
                        if (line.trim() === '') {
                            html += '<br>';
                            continue;
                        }
                        
                        // h1
                        if (line.startsWith('# ') && !line.startsWith('## ')) {
                            html += '<h1 class="review-h1">' + this.escapeHtml(line.slice(2)) + '</h1>';
                            continue;
                        }
                        
                        // h2
                        if (line.startsWith('## ') && !line.startsWith('### ')) {
                            html += '<h2 class="review-h2">' + this.escapeHtml(line.slice(3)) + '</h2>';
                            continue;
                        }
                        
                        // h3 → 日期行（主题色底纹）
                        if (line.startsWith('### ')) {
                            html += '<h3 class="review-date">' + this.escapeHtml(line.slice(4)) + '</h3>';
                            continue;
                        }
                        
                        // blockquote
                        if (line.startsWith('> ')) {
                            html += '<div class="review-blockquote">' + this.formatBold(this.escapeHtml(line.slice(2))) + '</div>';
                            continue;
                        }
                        
                        // divider
                        if (line.trim() === '---') {
                            html += '<hr class="review-divider">';
                            continue;
                        }
                        
                        // title+tags line: **标题** #tag1 #tag2 ...
                        let titleMatch = line.match(/^\*\*(.+?)\*\*\s*(.*)$/);
                        if (titleMatch) {
                            let title = this.escapeHtml(titleMatch[1].trim());
                            let tagPart = this.formatTags(this.escapeHtml(titleMatch[2].trim()));
                            html += '<p style="margin:4px 0 6px 0;"><span class="review-note-title">' + title + '</span> ' + tagPart + '</p>';
                            continue;
                        }

                        // bold + tags in regular lines
                        let processed = this.formatTags(this.formatBold(this.escapeHtml(line.trim())));
                        html += '<p class="review-body">' + processed + '</p>';
                    }

                    return html;
                },

                formatBold(text) {
                    return text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
                },

                formatTags(text) {
                    return text.replace(/#([\u4e00-\u9fa5\w\u3130-\u318F\uAC00-\uD7AF-]+)/g, '<span class="review-tag">#$1</span>');
                },

                escapeHtml(text) {
                    const div = document.createElement('div');
                    div.textContent = text;
                    return div.innerHTML;
                },

                copyReviewContent() {
                    const text = this.reviewRawContent;
                    // 优先使用 Clipboard API
                    if (navigator.clipboard && navigator.clipboard.writeText) {
                        navigator.clipboard.writeText(text).then(() => {
                            this.copySuccess = true;
                            setTimeout(() => { this.copySuccess = false; }, 2000);
                        }).catch(() => {
                            this._fallbackCopy(text);
                        });
                    } else {
                        this._fallbackCopy(text);
                    }
                },

                _fallbackCopy(text) {
                    const ta = document.createElement('textarea');
                    ta.value = text;
                    ta.style.position = 'fixed';
                    ta.style.left = '-9999px';
                    ta.style.top = '-9999px';
                    document.body.appendChild(ta);
                    ta.focus();
                    ta.select();
                    try {
                        document.execCommand('copy');
                        this.copySuccess = true;
                        setTimeout(() => { this.copySuccess = false; }, 2000);
                    } catch (e) {
                        this.showNotificationMessage('复制失败', 'error', '❌');
                    }
                    document.body.removeChild(ta);
                },

                closeReviewModal() {
                    this.showReviewModal = false;
                    this.reviewInsight = '';
                    this.reviewRawContent = '';
                    this.renderedContent = '';
                },

                async submitReviewInsight() {
                    if (!this.reviewInsight.trim()) return;
                    
                    const endpoint = this.reviewType === 'weekly' 
                        ? '/api/review/weekly/submit' 
                        : '/api/report/monthly/submit';
                    const title = this.reviewType === 'weekly' ? '周回顾' : '月度战报';
                    
                    try {
                        const response = await fetch(endpoint, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                file_path: this.reviewData.file_path,
                                insight: this.reviewInsight
                            })
                        });
                        
                        const data = await response.json();
                        
                        if (response.ok) {
                            this.showNotificationMessage(`${title}完成！+${data.reward} 星点`, 'success', '🎉');
                            this.closeReviewModal();
                            await this.loadStatus();
                        } else {
                            this.showNotificationMessage(data.detail || `${title}提交失败`, 'error', '❌');
                        }
                    } catch (error) {
                        this.showNotificationMessage('网络错误', 'error', '❌');
                    }
                },
                
                // ===== 消费记录（v0.4 新增） =====
                async loadConsumptionData() {
                    try {
                        const response = await fetch('/api/consume/history');
                        if (response.ok) {
                            const data = await response.json();
                            this.consumptionData = data;
                        }
                    } catch (error) {
                        console.error('加载消费记录失败:', error);
                    }
                },
                
                async submitConsumption() {
                    if (!this.consumptionContent.trim() || !this.consumptionAmount || this.consumptionAmount <= 0) {
                        return;
                    }
                    
                    try {
                        const response = await fetch('/api/consume', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                content: this.consumptionContent,
                                amount: parseFloat(this.consumptionAmount)
                            })
                        });
                        
                        const data = await response.json();
                        
                        if (response.ok && data.success) {
                            this.showNotificationMessage('消费记录成功', 'success', '✅');
                            this.consumptionContent = '';
                            this.consumptionAmount = null;
                            this.showConsumptionModal = false;
                            await this.loadConsumptionData();
                            await this.loadStatus();
                        } else {
                            const errorMessage = data.error || data.detail || '记录失败';
                            this.showNotificationMessage(errorMessage, 'error', '❌');
                        }
                    } catch (error) {
                        this.showNotificationMessage('网络错误', 'error', '❌');
                    }
                },
                showNotificationMessage(message, type = 'success', icon = '✅') {
                    this.notificationMessage = message;
                    this.notificationType = type;
                    this.notificationIcon = icon;
                    this.showNotification = true;
                    
                    setTimeout(() => {
                        this.showNotification = false;
                    }, 3000);
                },
                getMedalClass(name) {
                    if (this.status.medals.includes(name)) {
                        return '';
                    }
                    return 'locked';
                },
                formatNumber(num) {
                    return num.toFixed(1);
                },
                playSound() {
                    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    const oscillator = audioContext.createOscillator();
                    const gainNode = audioContext.createGain();
                    
                    oscillator.connect(gainNode);
                    gainNode.connect(audioContext.destination);
                    
                    oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
                    oscillator.frequency.setValueAtTime(1000, audioContext.currentTime + 0.1);
                    
                    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
                    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
                    
                    oscillator.start(audioContext.currentTime);
                    oscillator.stop(audioContext.currentTime + 0.3);
                },
                startEditBaseStar() {
                    this.ui.editing.baseStar = true;
                    this.editValue.baseStar = this.config.base_star.toString();
                },
                saveEditBaseStar() {
                    const value = parseInt(this.editValue.baseStar);
                    if (value > 0) {
                        this.saveConfigPartial('base_star', value);
                    }
                    this.ui.editing.baseStar = false;
                },
                startEditWeeklyReward() {
                    this.ui.editing.weeklyReward = true;
                    this.editValue.weeklyReward = this.config.weekly_review_reward.toString();
                },
                saveEditWeeklyReward() {
                    const value = parseInt(this.editValue.weeklyReward);
                    if (value >= 0) {
                        this.saveConfigPartial('weekly_review_reward', value);
                    }
                    this.ui.editing.weeklyReward = false;
                },
                startEditMonthlyReward() {
                    this.ui.editing.monthlyReward = true;
                    this.editValue.monthlyReward = this.config.monthly_report_reward.toString();
                },
                saveEditMonthlyReward() {
                    const value = parseInt(this.editValue.monthlyReward);
                    if (value >= 0) {
                        this.saveConfigPartial('monthly_report_reward', value);
                    }
                    this.ui.editing.monthlyReward = false;
                },
                startEditCouponRate() {
                    this.ui.editing.couponRate = true;
                    this.editValue.couponRate = this.config.coupon_rate.toString();
                },
                saveEditCouponRate() {
                    const value = parseFloat(this.editValue.couponRate);
                    if (value >= 0) {
                        this.saveConfigPartial('coupon_rate', value);
                    }
                    this.ui.editing.couponRate = false;
                },
                startEditFundRate() {
                    this.ui.editing.fundRate = true;
                    this.editValue.fundRate = this.config.fund_base_rate.toString();
                },
                saveEditFundRate() {
                    const value = parseFloat(this.editValue.fundRate);
                    if (value >= 0) {
                        this.saveConfigPartial('fund_base_rate', value);
                    }
                    this.ui.editing.fundRate = false;
                },
                startEditFundName() {
                    this.ui.editing.fundName = true;
                    this.editValue.fundName = this.config.custom_fund_name;
                },
                saveEditFundName() {
                    const value = this.editValue.fundName.trim();
                    if (value) {
                        this.saveConfigPartial('custom_fund_name', value);
                    }
                    this.ui.editing.fundName = false;
                },
                
                startEditMultiplier(index) {
                    this.ui.editing.multipliers = [false, false, false, false];
                    this.ui.editing.multipliers[index] = true;
                    this.editValue.multipliers = [...this.config.daily_multipliers.map(m => m.toString())];
                },
                saveEditMultiplier(index) {
                    const value = parseFloat(this.editValue.multipliers[index]);
                    if (!isNaN && value >= 0) {
                        const newMultipliers = [...this.config.daily_multipliers];
                        newMultipliers[index] = value;
                        this.saveConfigPartial('daily_multipliers', newMultipliers);
                    }
                    this.ui.editing.multipliers[index] = false;
                },
                cancelEditMultiplier() {
                    this.ui.editing.multiplier = false;
                },
                cancelAllEdits() {
                    this.ui.editing.baseStar = false;
                    this.ui.editing.weeklyReward = false;
                    this.ui.editing.monthlyReward = false;
                    this.ui.editing.couponRate = false;
                    this.ui.editing.fundRate = false;
                    this.ui.editing.fundName = false;
                    this.ui.editing.multipliers = [false, false, false, false];
                },
                async saveConfigPartial(field, value) {
                    try {
                        const configData = { ...this.config };
                        configData[field] = value;
                        
                        const response = await fetch('/api/config', {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(configData)
                        });
                        
                        if (response.ok) {
                            const result = await response.json();
                            this.config = { ...result };
                            this.showNotificationMessage('配置已更新', 'success', '✅');
                        } else {
                            const result = await response.json();
                            this.showNotificationMessage(result.detail || '更新失败', 'error', '❌');
                        }
                    } catch (error) {
                        console.error('Save config error:', error);
                        this.showNotificationMessage('网络错误', 'error', '❌');
                    }
                },
                async loadMedals() {
                    try {
                        const response = await fetch('/api/medals');
                        if (response.ok) {
                            const data = await response.json();
                            this.allMedals = data.medals || [];
                        }
                    } catch (error) {
                        console.error('Failed to load medals:', error);
                    }
                },
                init() {
                    this.loadStatus();
                    this.loadConfig();
                    this.loadMedals();
                    this.loadTags();
                    this.loadProjection();
                    setInterval(() => {
                        this.loadStatus();
                    }, 10000);
                },
                async resetState() {
                    console.log('[resetState] 按钮被点击');
                    if (!confirm('确定要重置吗？所有星点、勋章、连续天数将归零，回顾素材文件将被删除。')) {
                        console.log('[resetState] 用户取消了重置');
                        return;
                    }
                    console.log('[resetState] 用户确认，开始重置...');
                    
                    try {
                        const response = await fetch('/api/reset', { method: 'POST' });
                        const data = await response.json();
                        if (response.ok) {
                            await this.loadStatus();
                            this.showNotificationMessage(data.message || '已重置', 'success', '🔄');
                        } else {
                            this.showNotificationMessage(data.detail || '重置失败', 'error', '❌');
                        }
                    } catch (error) {
                        this.showNotificationMessage('网络错误', 'error', '❌');
                    }
                }
            }
        }