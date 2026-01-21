/**
 * AI投资新闻 H5 应用 - 详情页逻辑
 * 文章详情页（事件列表）
 */

console.log('[Detail] Script loaded');

const { createApp, ref, computed, onMounted, watch, nextTick } = Vue;

console.log('[Detail] Vue imported:', { createApp, ref, computed, onMounted, watch, nextTick });

const app = createApp({
    setup() {
        console.log('[Detail] Setup function called');

        // 状态
        const loading = ref(true);
        const articleData = ref(null);
        const activeTab = ref(0);  // 使用数字索引: 0=全部, 1=利好, 2=风险, 3=中性
        const currentDate = ref('');

        // 信号类型映射
        const signalTypes = ['all', 'positive', 'risk', 'neutral'];

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
                    return '利好';
                case 'risk':
                    return '风险';
                default:
                    return '中性';
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

        // 页面标题
        const pageTitle = computed(() => {
            console.log('[Detail] Computing pageTitle, articleData:', articleData.value);
            if (articleData.value && articleData.value.date) {
                return formatDate(articleData.value.date);
            }
            return 'AI投资新闻';
        });

        // 利好数量
        const positiveCount = computed(() => {
            if (!articleData.value || !articleData.value.events) return 0;
            return articleData.value.events.filter(
                e => e.decision && e.decision.signal === 'positive'
            ).length;
        });

        // 风险数量
        const riskCount = computed(() => {
            if (!articleData.value || !articleData.value.events) return 0;
            return articleData.value.events.filter(
                e => e.decision && e.decision.signal === 'risk'
            ).length;
        });

        // 过滤后的事件（带原始索引）
        const filteredEvents = computed(() => {
            console.log('[Detail] ====== Computing filteredEvents START ======');
            console.log('[Detail] articleData.value:', articleData.value);
            console.log('[Detail] activeTab.value:', activeTab.value);

            if (!articleData.value) {
                console.log('[Detail] articleData.value is null/undefined');
                return [];
            }

            if (!articleData.value.events) {
                console.log('[Detail] articleData.value.events is null/undefined');
                return [];
            }

            console.log('[Detail] articleData.value.events:', articleData.value.events);
            console.log('[Detail] events length:', articleData.value.events.length);

            // 给每个事件添加原始索引
            const eventsWithIndex = articleData.value.events.map((e, idx) => {
                console.log('[Detail] Processing event', idx, ':', e.representative_title);
                return {
                    ...e,
                    _originalIndex: idx
                };
            });

            const currentSignal = signalTypes[activeTab.value];
            console.log('[Detail] currentSignal:', currentSignal);

            if (currentSignal === 'all') {
                console.log('[Detail] Returning all events:', eventsWithIndex.length);
                console.log('[Detail] ====== Computing filteredEvents END ======');
                return eventsWithIndex;
            }

            const filtered = eventsWithIndex.filter(
                e => e.decision && e.decision.signal === currentSignal
            );
            console.log('[Detail] Returning filtered events:', filtered.length);
            console.log('[Detail] ====== Computing filteredEvents END ======');
            return filtered;
        });

        // 监听数据变化
        watch(articleData, (newVal, oldVal) => {
            console.log('[Detail] articleData changed:', { oldVal, newVal });
            if (newVal) {
                nextTick(() => {
                    console.log('[Detail] nextTick after articleData change');
                    console.log('[Detail] filteredEvents.value:', filteredEvents.value);
                    console.log('[Detail] DOM check - event-list:', document.querySelector('.event-list'));
                    console.log('[Detail] DOM check - event-cards:', document.querySelectorAll('.event-card').length);
                });
            }
        });

        // 监听 filteredEvents 变化
        watch(filteredEvents, (newVal, oldVal) => {
            console.log('[Detail] filteredEvents changed:', { 
                oldLength: oldVal ? oldVal.length : 0, 
                newLength: newVal ? newVal.length : 0 
            });
        });

        watch(loading, (newVal, oldVal) => {
            console.log('[Detail] loading changed:', { oldVal, newVal });
        });

        watch(activeTab, (newVal, oldVal) => {
            console.log('[Detail] activeTab changed:', { oldVal, newVal });
        });

        // Tab 切换
        const onTabChange = (index) => {
            console.log('[Detail] Tab changed to:', index, signalTypes[index]);
            activeTab.value = index;
        };

        // 返回上一页
        const goBack = () => {
            window.location.href = 'index.html';
        };

        // 跳转到事件详情
        const goToEvent = (event) => {
            const date = currentDate.value;
            const index = event._originalIndex;
            console.log('[Detail] Going to event:', { date, index });
            window.location.href = `event.html?date=${date}&index=${index}`;
        };

        // 加载数据
        const loadData = async () => {
            console.log('[Detail] loadData called');
            loading.value = true;
            currentDate.value = getUrlParam('date');
            console.log('[Detail] Loading data for date:', currentDate.value);

            if (!currentDate.value) {
                console.error('[Detail] No date parameter');
                vant.showToast({
                    message: '参数错误',
                    type: 'fail'
                });
                loading.value = false;
                return;
            }

            try {
                const dateStr = currentDate.value.replace(/-/g, '');
                const url = `data/${dateStr}.json`;
                console.log('[Detail] Fetching:', url);
                const response = await fetch(url);
                console.log('[Detail] Response status:', response.status);

                if (!response.ok) {
                    throw new Error('加载数据失败');
                }
                const data = await response.json();
                console.log('[Detail] Data loaded successfully:', data);
                console.log('[Detail] Events count:', data.events ? data.events.length : 0);

                // 设置数据前打印
                console.log('[Detail] About to set articleData.value');
                articleData.value = data;
                console.log('[Detail] articleData.value has been set');

                // 等待 DOM 更新
                await nextTick();
                console.log('[Detail] After nextTick');
                console.log('[Detail] filteredEvents computed:', filteredEvents.value);
                console.log('[Detail] filteredEvents length:', filteredEvents.value.length);

                // 检查 DOM
                setTimeout(() => {
                    console.log('[Detail] setTimeout check:');
                    console.log('[Detail] .detail-content visible:', document.querySelector('.detail-content'));
                    console.log('[Detail] .event-list visible:', document.querySelector('.event-list'));
                    console.log('[Detail] .event-card count:', document.querySelectorAll('.event-card').length);
                    console.log('[Detail] loading.value:', loading.value);
                    console.log('[Detail] articleData.value:', articleData.value ? 'exists' : 'null');
                }, 100);

            } catch (error) {
                console.error('[Detail] 加载数据失败:', error);
                vant.showToast({
                    message: '加载数据失败',
                    type: 'fail'
                });
            } finally {
                loading.value = false;
                console.log('[Detail] loadData finished, loading:', loading.value);
            }
        };

        // 生命周期
        onMounted(() => {
            console.log('[Detail] Component mounted');
            loadData();
        });

        console.log('[Detail] Setup returning...');

        return {
            loading,
            articleData,
            activeTab,
            currentDate,
            pageTitle,
            positiveCount,
            riskCount,
            filteredEvents,
            formatDate,
            truncateText,
            getSignalTagType,
            getSignalText,
            getImportanceTagType,
            getImportanceText,
            onTabChange,
            goBack,
            goToEvent,
            loadData
        };
    }
});

// 添加全局错误处理
app.config.errorHandler = (err, vm, info) => {
    console.error('[Detail] Vue Error:', err);
    console.error('[Detail] Error Info:', info);
    console.error('[Detail] Component:', vm);
    // 显示错误在页面上
    document.body.innerHTML += `<div style="color:red;padding:20px;background:#fff;">Vue Error: ${err.message}</div>`;
};

app.config.warnHandler = (msg, vm, trace) => {
    console.warn('[Detail] Vue Warning:', msg);
    console.warn('[Detail] Trace:', trace);
};

// 添加编译错误处理
app.config.compilerOptions = {
    onError: (err) => {
        console.error('[Detail] Compile Error:', err);
    },
    onWarn: (msg) => {
        console.warn('[Detail] Compile Warning:', msg);
    }
};

console.log('[Detail] Registering Vant components...');
console.log('[Detail] vant object:', vant);
console.log('[Detail] vant.NavBar:', vant.NavBar);
console.log('[Detail] vant.Tabs:', vant.Tabs);
console.log('[Detail] vant.Tab:', vant.Tab);

// 注册 Vant 组件
app.use(vant);

console.log('[Detail] Vant registered');

// 打印 app 挂载前的状态
console.log('[Detail] App before mount:', app);
console.log('[Detail] Target element:', document.getElementById('app'));
console.log('[Detail] Target element innerHTML:', document.getElementById('app').innerHTML.substring(0, 200));

console.log('[Detail] Mounting app to #app...');

// 挂载应用
try {
    const mountedApp = app.mount('#app');
    console.log('[Detail] App mounted successfully');
    console.log('[Detail] Mounted app:', mountedApp);
    console.log('[Detail] Mounted app $el:', mountedApp.$el);
    
    // 延迟检查 DOM
    setTimeout(() => {
        console.log('[Detail] Final DOM check:');
        console.log('[Detail] #app innerHTML:', document.getElementById('app').innerHTML.substring(0, 500));
    }, 500);
} catch (error) {
    console.error('[Detail] Mount error:', error);
    console.error('[Detail] Mount error stack:', error.stack);
}
