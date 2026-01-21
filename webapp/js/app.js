/**
 * AI投资新闻 H5 应用 - 主页逻辑
 * 文章列表页
 */

const { createApp, ref, computed, onMounted } = Vue;

const app = createApp({
    setup() {
        // 状态
        const loading = ref(true);
        const refreshing = ref(false);
        const showSearch = ref(false);
        const searchKeyword = ref('');
        const dateList = ref([]);

        // 周几映射
        const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];

        // 计算属性：根据搜索过滤
        const filteredDateList = computed(() => {
            if (!searchKeyword.value) {
                return dateList.value;
            }
            const keyword = searchKeyword.value.toLowerCase();
            return dateList.value.filter(item => {
                // 搜索事件标题
                return item.topEvents.some(event =>
                    event.title.toLowerCase().includes(keyword)
                );
            });
        });

        // 格式化日期
        const formatDate = (dateStr) => {
            if (!dateStr) return '';
            const parts = dateStr.split('-');
            if (parts.length === 3) {
                return `${parts[0]}年${parts[1]}月${parts[2]}日`;
            }
            return dateStr;
        };

        // 获取周几
        const getWeekday = (dateStr) => {
            if (!dateStr) return '';
            const date = new Date(dateStr);
            return weekdays[date.getDay()];
        };

        // 获取信号图标
        const getSignalIcon = (signal) => {
            switch (signal) {
                case 'positive':
                    return 'arrow-up';
                case 'risk':
                    return 'warning-o';
                default:
                    return 'minus';
            }
        };

        // 截断文本
        const truncateText = (text, maxLength) => {
            if (!text) return '';
            if (text.length <= maxLength) return text;
            return text.substring(0, maxLength) + '...';
        };

        // 加载数据
        const loadData = async () => {
            loading.value = true;
            try {
                // 加载索引文件
                const response = await fetch('data/index.json');
                if (!response.ok) {
                    throw new Error('加载数据失败');
                }
                const data = await response.json();
                dateList.value = data.articles || [];
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

        // 下拉刷新
        const onRefresh = async () => {
            await loadData();
            refreshing.value = false;
            vant.showToast('刷新成功');
        };

        // 搜索
        const onSearch = () => {
            showSearch.value = false;
        };

        // 清除搜索
        const onClearSearch = () => {
            searchKeyword.value = '';
        };

        // 跳转到详情页
        const goToDetail = (date) => {
            window.location.href = `detail.html?date=${date}`;
        };

        // 生命周期
        onMounted(() => {
            loadData();
        });

        return {
            loading,
            refreshing,
            showSearch,
            searchKeyword,
            dateList,
            filteredDateList,
            formatDate,
            getWeekday,
            getSignalIcon,
            truncateText,
            loadData,
            onRefresh,
            onSearch,
            onClearSearch,
            goToDetail
        };
    }
});

// 注册 Vant 组件
app.use(vant);

// 挂载应用
app.mount('#app');
