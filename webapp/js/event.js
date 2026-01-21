/**
 * AI投资新闻 H5 应用 - 事件详情页逻辑
 */

const { createApp, ref, computed, onMounted } = Vue;

const app = createApp({
    setup() {
        // 状态
        const loading = ref(true);
        const eventData = ref(null);
        const articleData = ref(null);
        const currentDate = ref('');
        const eventIndex = ref(0);
        const showShare = ref(false);
        const activeCollapse = ref(['core']);

        // 分享选项
        const shareOptions = [
            { name: '复制链接', icon: 'link' },
            { name: '微信', icon: 'wechat' },
            { name: '微博', icon: 'weibo' }
        ];

        // 获取 URL 参数
        const getUrlParam = (name) => {
            const urlParams = new URLSearchParams(window.location.search);
            return urlParams.get(name);
        };

        // 格式化日期
        const formatDate = (dateStr) => {
            if (!dateStr) return '';
            const parts = dateStr.split('-');
            if (parts.length === 3) {
                return `${parts[0]}年${parts[1]}月${parts[2]}日`;
            }
            return dateStr;
        };

        // 格式化时间
        const formatTime = (timeStr) => {
            if (!timeStr) return '';
            const date = new Date(timeStr);
            const month = date.getMonth() + 1;
            const day = date.getDate();
            const hour = date.getHours();
            const minute = date.getMinutes().toString().padStart(2, '0');
            return `${month}/${day} ${hour}:${minute}`;
        };

        // 截断文本
        const truncateText = (text, maxLength) => {
            if (!text) return '';
            if (text.length <= maxLength) return text;
            return text.substring(0, maxLength) + '...';
        };

        // 获取信号标签类型
        const getSignalTagType = (signal) => {
            switch (signal) {
                case 'positive':
                    return 'success';
                case 'risk':
                    return 'danger';
                default:
                    return 'default';
            }
        };

        // 获取信号文本
        const getSignalText = (signal) => {
            switch (signal) {
                case 'positive':
                    return '利好信号';
                case 'risk':
                    return '风险提示';
                default:
                    return '中性信号';
            }
        };

        // 获取重要性标签类型
        const getImportanceTagType = (importance) => {
            switch (importance) {
                case 'high':
                    return 'danger';
                case 'medium':
                    return 'warning';
                default:
                    return 'default';
            }
        };

        // 获取重要性文本
        const getImportanceText = (importance) => {
            switch (importance) {
                case 'high':
                    return '高重要性';
                case 'medium':
                    return '中等';
                default:
                    return '一般';
            }
        };

        // 获取动作标签类型
        const getActionTagType = (action) => {
            switch (action) {
                case 'buy':
                case 'increase':
                    return 'success';
                case 'sell':
                case 'decrease':
                    return 'danger';
                case 'hold':
                    return 'warning';
                default:
                    return 'default';
            }
        };

        // 获取动作文本
        const getActionText = (action) => {
            const actionMap = {
                'buy': '建议买入',
                'increase': '建议加仓',
                'hold': '持有观望',
                'decrease': '建议减仓',
                'sell': '建议卖出',
                'watch': '持续关注',
                'avoid': '建议规避'
            };
            return actionMap[action] || '持续关注';
        };

        // 相关新闻列表
        const relatedNews = computed(() => {
            if (!eventData.value || !articleData.value) return [];

            // 获取事件关联的新闻索引
            const newsIndices = eventData.value.news_indices || [];
            const allNews = articleData.value.news || [];

            // 如果有索引，使用索引获取新闻
            if (newsIndices.length > 0) {
                return newsIndices
                    .filter(idx => idx >= 0 && idx < allNews.length)
                    .map(idx => allNews[idx]);
            }

            // 否则返回全部新闻的前5条
            return allNews.slice(0, 5);
        });

        // 是否有投资信息
        const hasInvestmentInfo = computed(() => {
            if (!relatedNews.value || relatedNews.value.length === 0) return false;
            return relatedNews.value.some(news => news.investment_info);
        });

        // 合并的投资信息
        const investmentInfo = computed(() => {
            if (!hasInvestmentInfo.value) return {};

            // 从第一个有投资信息的新闻中获取
            const newsWithInfo = relatedNews.value.find(news => news.investment_info);
            return newsWithInfo ? newsWithInfo.investment_info : {};
        });

        // 返回上一页
        const goBack = () => {
            window.location.href = `detail.html?date=${currentDate.value}`;
        };

        // 打开新闻链接
        const openNews = (url) => {
            if (url) {
                window.open(url, '_blank');
            }
        };

        // 分享事件
        const shareEvent = () => {
            showShare.value = true;
        };

        // 分享选择
        const onShareSelect = (option) => {
            if (option.name === '复制链接') {
                const url = window.location.href;
                navigator.clipboard.writeText(url).then(() => {
                    vant.showToast('链接已复制');
                }).catch(() => {
                    vant.showToast('复制失败');
                });
            } else {
                vant.showToast(`${option.name}分享功能开发中`);
            }
            showShare.value = false;
        };

        // 加载数据
        const loadData = async () => {
            loading.value = true;
            currentDate.value = getUrlParam('date');
            eventIndex.value = parseInt(getUrlParam('index') || '0', 10);

            if (!currentDate.value) {
                vant.showToast({
                    message: '参数错误',
                    type: 'fail'
                });
                loading.value = false;
                return;
            }

            try {
                // 根据日期加载数据文件
                const dateStr = currentDate.value.replace(/-/g, '');
                const response = await fetch(`data/${dateStr}.json`);
                if (!response.ok) {
                    throw new Error('加载数据失败');
                }

                articleData.value = await response.json();

                // 获取指定索引的事件
                if (articleData.value.events && articleData.value.events.length > eventIndex.value) {
                    eventData.value = articleData.value.events[eventIndex.value];
                } else {
                    throw new Error('事件不存在');
                }
            } catch (error) {
                console.error('加载数据失败:', error);
                vant.showToast({
                    message: '加载数据失败',
                    type: 'fail'
                });
            } finally {
                loading.value = false;
            }
        };

        // 生命周期
        onMounted(() => {
            loadData();
        });

        return {
            loading,
            eventData,
            articleData,
            currentDate,
            showShare,
            activeCollapse,
            shareOptions,
            relatedNews,
            hasInvestmentInfo,
            investmentInfo,
            formatDate,
            formatTime,
            truncateText,
            getSignalTagType,
            getSignalText,
            getImportanceTagType,
            getImportanceText,
            getActionTagType,
            getActionText,
            goBack,
            openNews,
            shareEvent,
            onShareSelect,
            loadData
        };
    }
});

// 注册 Vant 组件
app.use(vant);

// 挂载应用
app.mount('#app');
