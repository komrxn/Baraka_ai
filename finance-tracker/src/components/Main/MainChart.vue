<template>
    <div class="main-chart">
        <div class="main-chart__header">
            <h1 class="font-20-b gold-text">{{ t('main.categories') }}</h1>
            <Button label="Посмотреть все" text size="small" @click="handleViewAll" />
        </div>
        <div ref="chartWrapperRef" class="main-chart__container-wrapper">
            <VChart ref="chartRef" :option="chartOption" class="main-chart__container" @click="handleChartClick" />
            <Transition name="fade">
                <div v-if="selectedCategory" class="main-chart__center">
                    <p class="main-chart__center-label font-14-r">{{ centerLabel }}</p>
                    <h2 class="main-chart__center-value font-30-b gold-text">{{ formattedCenterValue }}</h2>
                </div>
                <div v-else class="main-chart__center">
                    <p class="main-chart__center-label font-14-r">{{ t('main.currentBalance') }}</p>
                    <h2 class="main-chart__center-value font-30-b gold-text">{{ formattedBalance }}</h2>
                </div>
            </Transition>
        </div>
        <div class="main-chart__categories">
            <div v-for="category in expensesData" :key="category.name" class="main-chart__category"
                :class="{ 'main-chart__category--active': selectedCategory === category.name }"
                @click="selectCategory(category.name)">
                <div class="main-chart__category-icon" :style="{ backgroundColor: category.color }"></div>
                <p class="main-chart__category-name font-12-r">{{ category.name }}</p>
                <span class="main-chart__category-percent font-10-r">{{ category.percentage }}%</span>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { onClickOutside } from '@vueuse/core';
import { Button } from 'primevue';

import VChart from 'vue-echarts';
import type { EChartsOption } from 'echarts';
import { formatAmountShort } from '@/utils';
import { useBalanceStore } from '@/store/balanceStore';
import { useCategoriesChartStore } from '@/store/categoriesChartStore';

const { t, te } = useI18n();
const router = useRouter();

const balanceStore = useBalanceStore();
const { balance: balanceData } = storeToRefs(balanceStore);
const { loadBalance } = balanceStore;

const categoriesChartStore = useCategoriesChartStore();
const { categoryBreakdown, isLoaded } = storeToRefs(categoriesChartStore);
const { loadCategories } = categoriesChartStore;

const chartRef = ref<InstanceType<typeof VChart> | null>(null);
const chartWrapperRef = ref<HTMLElement | null>(null);
const selectedCategory = ref<string | null>(null);

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
        };
    });
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

// Переход на страницу категорий
const handleViewAll = () => {
    router.push({ name: 'categories' });
};

// Обработчик клика на график
const handleChartClick = (params: any) => {
    if (params.componentType === 'series' && params.name) {
        selectCategory(params.name);
    }
};

// Текст и значение для центра
const centerLabel = computed(() => {
    if (selectedCategory.value) {
        const category = expensesData.value.find(c => c.name === selectedCategory.value);
        return category?.name || t('main.currentBalance');
    }
    return t('main.currentBalance');
});

const formattedCenterValue = computed(() => {
    if (selectedCategory.value) {
        const category = expensesData.value.find(c => c.name === selectedCategory.value);
        if (category) {
            return formatAmountShort(category.value);
        }
    }
    return formattedBalance.value;
});

// Инициализация обработчика клика на график
const initChartClickHandler = () => {
    setTimeout(() => {
        if (chartRef.value?.chart) {
            chartRef.value.chart.off('click', handleChartClick);
            chartRef.value.chart.on('click', handleChartClick);
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

        // Инициализируем обработчик клика
        if (categoryBreakdown.value) {
            initChartClickHandler();
        }
    } catch (error) {
        console.error('Failed to load chart data:', error);
    }
});

// Следим за изменениями данных и обновляем обработчик клика
watch(
    () => expensesData.value.length,
    (newLength) => {
        if (isLoaded.value && newLength > 0) {
            initChartClickHandler();
        }
    },
    { immediate: true }
);

// Также следим за изменениями categoryBreakdown
watch(
    () => categoryBreakdown.value,
    () => {
        if (categoryBreakdown.value && isLoaded.value) {
            initChartClickHandler();
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
            data: expensesData.value.length > 0
                ? expensesData.value.map((item) => ({
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
    border: 1px solid var(--gold-border);
    box-shadow: var(--gold-shadow);
    position: relative;
    overflow: hidden;

    &::before {
        content: '';
        position: absolute;
        inset: 0;
        border-radius: 1.6rem;
        background: var(--gold-card-radial);
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
        gap: 1rem;
        pointer-events: none;
        z-index: 10;
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
