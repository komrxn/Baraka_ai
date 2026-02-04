<template>
    <div class="main-chart">
        <div class="main-chart__header">
            <h1 class="font-20-b ">{{ t('main.categories') }}</h1>
            <Button :label="t('main.categoriesViewAll')" text size="small" @click="handleViewAll" />
        </div>
        <div ref="chartWrapperRef" class="main-chart__container-wrapper">
            <VChart ref="chartRef" :option="chartOption" class="main-chart__container" autoresize
                @click="handleChartClick" />
            <div class="main-chart__center">
                <div class="main-chart__center-content">
                    <p class="main-chart__center-label font-14-r">{{ selectedCategory ? centerLabel :
                        t('main.currentBalance') }}</p>
                    <h2 class="main-chart__center-value font-30-b ">{{ selectedCategory ? formattedCenterValue
                        : formattedBalance }}</h2>
                    <Button v-if="selectedCategory" :label="t('main.viewTransactions')" size="small" severity="primary"
                        class="main-chart__center-button" outlined @click="handleViewTransactions" />
                </div>
            </div>
        </div>
        <div class="main-chart__categories">
            <div v-for="category in displayedCategories" :key="category.name" class="main-chart__category"
                :class="{ 'main-chart__category--active': selectedCategory === category.name }"
                @click="handleCategoryClick(category)">
                <div class="main-chart__category-icon" :style="{ backgroundColor: category.color }"></div>
                <p class="main-chart__category-name font-12-r">{{ category.name }}</p>
                <span class="main-chart__category-percent font-10-r">{{ category.percentage }}%</span>
            </div>
        </div>
    </div>

    <!-- Модальное окно с полным графиком -->
    <MainChartFullModal :model-value="showFullChart" @update:model-value="showFullChart = $event" :categories="expensesData" :balance="balance"
        :formatted-balance="formattedBalance" />
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { onClickOutside } from '@vueuse/core';
import { Button } from 'primevue';

import VChart from 'vue-echarts';
import type { EChartsOption } from 'echarts';
import { formatAmountShort, formatDateToAPIDatetime, formatDateToAPI } from '@/utils';
import { useBalanceStore } from '@/store/balanceStore';
import { useCategoriesChartStore } from '@/store/categoriesChartStore';
import { useTransactionsStore } from '@/store/transactionsStore';
import MainChartFullModal from './MainChartFullModal.vue';

const { t, te } = useI18n();
const router = useRouter();

const balanceStore = useBalanceStore();
const { balance: balanceData } = storeToRefs(balanceStore);
const { loadBalance } = balanceStore;

const categoriesChartStore = useCategoriesChartStore();
const { categoryBreakdown, isLoaded } = storeToRefs(categoriesChartStore);
const { loadCategories } = categoriesChartStore;

const transactionsStore = useTransactionsStore();
const { applyFilters } = transactionsStore;

const chartRef = ref<InstanceType<typeof VChart> | null>(null);
const chartWrapperRef = ref<HTMLElement | null>(null);
const selectedCategory = ref<string | null>(null);
const showFullChart = ref(false);

const MAX_DISPLAYED_CATEGORIES = 6;

// Сброс выбора при клике вне графика
onClickOutside(chartWrapperRef, () => {
    if (selectedCategory.value) {
        selectedCategory.value = null;
    }
});

// Данные
const balance = computed(() => {
    return balanceData.value ? parseFloat(balanceData.value.balance) : 0;
});

const expensesData = computed(() => {
    if (!categoryBreakdown.value) {
        return [];
    }
    return categoryBreakdown.value.categories.map((cat: any) => {
        const slug = cat.category_slug;
        const nameKey = `categoryList.${slug}`;
        // If translation exists, use it. Otherwise use the backend name.
        const displayName = (slug && te(nameKey)) ? t(nameKey) : cat.category_name;

        return {
            name: displayName,
            value: parseFloat(cat.amount),
            percentage: cat.percentage.toString(),
            color: cat.color || 'rgb(149, 165, 166)',
            category_id: cat.category_id,
        };
    });
});

// Тип для категории
export type CategoryItem = {
    name: string;
    value: number;
    percentage: string;
    color: string;
    category_id: string | null;
    isOthers?: boolean;
    othersCategories?: CategoryItem[];
};

// Отображаемые категории (первые 8 + "Другое" если есть)
const displayedCategories = computed<CategoryItem[]>(() => {
    const allCategories = expensesData.value;
    if (allCategories.length <= MAX_DISPLAYED_CATEGORIES) {
        return allCategories;
    }

    const displayed: CategoryItem[] = allCategories.slice(0, MAX_DISPLAYED_CATEGORIES);
    const others = allCategories.slice(MAX_DISPLAYED_CATEGORIES);

    // Суммируем остальные категории
    const othersTotal = others.reduce((sum, cat) => sum + cat.value, 0);
    const othersPercentage = others.reduce((sum, cat) => sum + parseFloat(cat.percentage), 0).toFixed(1);

    // Добавляем категорию "Показать все"
    displayed.push({
        name: t('main.showAllCategories'),
        value: othersTotal,
        percentage: othersPercentage,
        color: 'rgb(149, 165, 166)',
        category_id: null,
        isOthers: true,
        othersCategories: others,
    });

    return displayed;
});

// Форматированный баланс
const formattedBalance = computed(() => {
    return formatAmountShort(balance.value);
});

// Выбор категории
const selectCategory = (categoryName: string) => {
    if (selectedCategory.value === categoryName) {
        selectedCategory.value = null;
    } else {
        selectedCategory.value = categoryName;
    }
};

// Обработка клика на категорию
const handleCategoryClick = (category: CategoryItem) => {
    if (category.isOthers) {
        // Открываем модальное окно с полным графиком
        showFullChart.value = true;
    } else {
        selectCategory(category.name);
    }
};

// Переход на страницу категорий
const handleViewAll = () => {
    router.push({ name: 'categories' });
};

// Получение дат начала и конца текущего месяца
const getMonthDates = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth();

    const startDate = new Date(year, month, 1);
    const endDate = new Date(year, month + 1, 0);

    return {
        start: formatDateToAPIDatetime(formatDateToAPI(startDate), false),
        end: formatDateToAPIDatetime(formatDateToAPI(endDate), true),
    };
};

// Переход на страницу транзакций с фильтрами
const handleViewTransactions = async () => {
    if (!selectedCategory.value) return;

    const category = expensesData.value.find(c => c.name === selectedCategory.value);
    if (!category || !category.category_id) return;

    const { start, end } = getMonthDates();

    // Применяем фильтры через store
    await applyFilters({
        category_id: category.category_id,
        start_date: start,
        end_date: end,
        type: 'expense',
    });

    // Переходим на страницу транзакций
    router.push({ name: 'transactions' });
};

const handleChartClick = (params: any) => {
    if (params.componentType === 'series' && params.name) {
        const category = displayedCategories.value.find(c => c.name === params.name);
        if (category?.isOthers) {
            showFullChart.value = true;
        } else {
            selectCategory(params.name);
        }
    }
};

// Текст и значение для центра
const centerLabel = computed(() => {
    if (selectedCategory.value) {
        const category = displayedCategories.value.find(c => c.name === selectedCategory.value);
        return category?.name || t('main.currentBalance');
    }
    return t('main.currentBalance');
});

const formattedCenterValue = computed(() => {
    if (selectedCategory.value) {
        const category = displayedCategories.value.find(c => c.name === selectedCategory.value);
        if (category) {
            return formatAmountShort(category.value);
        }
    }
    return formattedBalance.value;
});


// Инициализация обработчика клика на график и перерисовка графика
const initChartClickHandler = async () => {
    await nextTick();
    setTimeout(() => {
        if (chartRef.value?.chart) {
            chartRef.value.chart.off('click', handleChartClick);
            chartRef.value.chart.on('click', handleChartClick);
            // Принудительно перерисовываем график для правильного центрирования
            chartRef.value.chart.resize();
        }
    }, 100);
};

// Загружаем данные при монтировании
onMounted(async () => {
    try {
        await Promise.all([
            loadBalance({ period: 'month' }), // Используем store, чтобы избежать дублирования запроса
            loadCategories({ period: 'month', type: 'expense' }), // Используем store для кеширования
        ]);

        // Ждем следующего тика для правильной инициализации DOM
        await nextTick();

        // Инициализируем обработчик клика и перерисовываем график
        if (categoryBreakdown.value) {
            await initChartClickHandler();
        }

        // Дополнительная перерисовка через небольшую задержку для гарантии правильного центрирования
        setTimeout(() => {
            if (chartRef.value?.chart) {
                chartRef.value.chart.resize();
            }
        }, 300);
    } catch (error) {
        console.error('Failed to load chart data:', error);
    }
});

// Следим за изменениями данных и обновляем обработчик клика
watch(
    () => expensesData.value.length,
    async (newLength) => {
        if (isLoaded.value && newLength > 0) {
            await initChartClickHandler();
        }
    },
    { immediate: true }
);

// Также следим за изменениями categoryBreakdown
watch(
    () => categoryBreakdown.value,
    async () => {
        if (categoryBreakdown.value && isLoaded.value) {
            await initChartClickHandler();
        }
    }
);


const chartOption = computed<EChartsOption>(() => ({
    tooltip: {
        show: false,
    },
    // Отключаем анимацию если данные уже были загружены (повторное монтирование)
    // Это предотвращает перерисовку графика при возврате на страницу
    animation: !isLoaded.value,
    animationType: 'scale',
    animationDuration: 1000,
    animationEasing: 'cubicOut',
    animationDelay: (idx: number) => idx * 100,
    series: [
        {
            type: 'pie',
            radius: ['80%', '90%'],
            avoidLabelOverlap: false,
            itemStyle: {
                borderRadius: 30,
                borderColor: 'rgb(30, 30, 30)',
                borderWidth: 2,
            },
            label: {
                show: false,
            },
            emphasis: {
                itemStyle: {
                    shadowBlur: 15,
                    shadowOffsetX: 0,
                    shadowOffsetY: 5,
                    shadowColor: 'rgba(0, 0, 0, 0.6)',
                    borderWidth: 4,
                },
                scale: true,
                scaleSize: 5,
            },
            labelLine: {
                show: false,
            },
            data: displayedCategories.value.length > 0
                ? displayedCategories.value.map((item) => ({
                    value: item.value,
                    name: item.name,
                    itemStyle: {
                        color: item.color,
                        opacity: selectedCategory.value && selectedCategory.value !== item.name ? 0.3 : 1,
                    },
                }))
                : [],
        },
    ],
}));
</script>

<style scoped lang="scss">
.main-chart {
    width: 100%;
    margin-top: 1.2rem;
    padding: 1.6rem 1.2rem;
    border-radius: 1.6rem;
    background-color: var(--card-default);
    border: 1px solid var(--border-medium);
    box-shadow: none;
    position: relative;
    overflow: hidden;

    &::before {
        content: '';
        position: absolute;
        inset: 0;
        border-radius: 1.6rem;
        background: transparent;
        pointer-events: none;
    }

    &__header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.6rem;
    }

    &__container-wrapper {
        position: relative;
        width: 100%;
        margin-bottom: 1.6rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    &__container {
        width: 100%;
        height: 300px;
        min-width: 0;
        min-height: 300px;
    }

    &__center {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        pointer-events: none;
        z-index: 10;
        width: 100%;
    }

    &__center-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        position: relative;
    }

    &__center-label {
        color: var(--text-color);
        opacity: 0.7;
        transition: opacity 0.3s ease;
    }

    &__center-value {
        color: var(--text-color);
        transition: transform 0.3s ease, color 0.3s ease;
    }

    &__center-button {
        pointer-events: auto;
        min-width: 12rem;
    }

    &__categories {
        display: flex;
        flex-wrap: wrap;
        gap: 0.2rem;
        justify-content: center;
    }

    &__category {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.6rem;
        padding: 0.4rem 0.8rem;
        border-radius: var(--radius-m);
        cursor: pointer;
        transition: all 0.3s ease;
        background: transparent;
        border: 1px solid transparent;

        &:hover {
            background: var(--card-hover);
            border-color: var(--border-light);
        }

        &--active {
            background: var(--card-accent);
            border-color: var(--border-medium);
        }
    }

    &__category-icon {
        width: 1.2rem;
        height: 1.2rem;
        border-radius: 50%;
        transition: transform 0.3s ease;
        flex-shrink: 0;
    }

    &__category-name {
        transition: color 0.3s ease;
    }

    &__category-percent {
        color: var(--text-color);
        opacity: 0.6;
        font-size: 1rem;
    }

    &__category:hover &__category-icon {
        transform: scale(1.2);
    }

    &__category--active &__category-icon {
        transform: scale(1.3);
        box-shadow: 0 0 8px currentColor;
    }
}

.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
    transform: translate(-50%, -60%);
}
</style>
