<template>
    <Dialog :visible="modelValue" modal
        :style="{ width: '100vw', height: '100vh', maxWidth: '100vw', maxHeight: '100vh', borderRadius: '0', margin: '0' }"
        :closable="true" :show-header="true" class="full-chart-dialog" @update:visible="handleUpdate">
        <template #header>
            <h2 class="full-chart-dialog__title">{{ t('main.allCategories') }}</h2>
        </template>
        <div class="full-chart">
            <div class="full-chart__container-wrapper">
                <VChart ref="fullChartRef" :option="fullChartOption" class="full-chart__container" autoresize
                    @click="handleFullChartClick" />
                <div class="full-chart__center">
                    <div class="full-chart__center-content">
                        <p class="full-chart__center-label font-14-r">{{ selectedCategory ? centerLabel :
                            t('main.currentBalance') }}</p>
                        <h2 class="full-chart__center-value font-30-b ">{{ selectedCategory ? formattedCenterValue
                            : formattedBalance }}</h2>
                        <Button v-if="selectedCategory" :label="t('main.viewTransactions')" size="small" severity="primary"
                            class="full-chart__center-button" outlined @click="handleViewTransactions" />
                    </div>
                </div>
            </div>
            <div v-if="categories.length > 0" class="full-chart__categories">
                <div v-for="category in categories" :key="category.name" class="full-chart__category"
                    :class="{ 'full-chart__category--active': selectedCategory === category.name }"
                    @click="selectCategory(category.name)">
                    <div class="full-chart__category-icon" :style="{ backgroundColor: category.color }"></div>
                    <p class="full-chart__category-name font-12-r">{{ category.name }}</p>
                    <span class="full-chart__category-percent font-10-r">{{ category.percentage }}%</span>
                </div>
            </div>
            <div v-else class="full-chart__empty">
                <p>{{ t('common.noData') }}</p>
            </div>
        </div>
    </Dialog>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { Button, Dialog } from 'primevue';
import VChart from 'vue-echarts';
import type { EChartsOption } from 'echarts';
import { formatAmountShort, formatDateToAPIDatetime, formatDateToAPI } from '@/utils';
import { useTransactionsStore } from '@/store/transactionsStore';

export type CategoryItem = {
    name: string;
    value: number;
    percentage: string;
    color: string;
    category_id: string | null;
};

const props = defineProps<{
    modelValue: boolean;
    categories: CategoryItem[];
    balance: number;
    formattedBalance: string;
}>();

const emit = defineEmits<{
    (e: 'update:modelValue', value: boolean): void;
}>();

const { t } = useI18n();
const router = useRouter();
const transactionsStore = useTransactionsStore();
const { applyFilters } = transactionsStore;

const fullChartRef = ref<InstanceType<typeof VChart> | null>(null);
const selectedCategory = ref<string | null>(null);

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

// Выбор категории
const selectCategory = (categoryName: string) => {
    if (selectedCategory.value === categoryName) {
        selectedCategory.value = null;
    } else {
        selectedCategory.value = categoryName;
    }
};

// Переход на страницу транзакций
const handleViewTransactions = async () => {
    if (!selectedCategory.value) return;

    const category = props.categories.find(c => c.name === selectedCategory.value);
    if (!category || !category.category_id) return;

    const { start, end } = getMonthDates();

    // Применяем фильтры через store
    await applyFilters({
        category_id: category.category_id,
        start_date: start,
        end_date: end,
        type: 'expense',
    });

    // Закрываем модальное окно
    emit('update:modelValue', false);
    selectedCategory.value = null;

    // Переходим на страницу транзакций
    router.push({ name: 'transactions' });
};

const handleFullChartClick = (params: any) => {
    if (params.componentType === 'series' && params.name) {
        selectCategory(params.name);
    }
};

// Текст и значение для центра
const centerLabel = computed(() => {
    if (selectedCategory.value) {
        const category = props.categories.find(c => c.name === selectedCategory.value);
        return category?.name || t('main.currentBalance');
    }
    return t('main.currentBalance');
});

const formattedCenterValue = computed(() => {
    if (selectedCategory.value) {
        const category = props.categories.find(c => c.name === selectedCategory.value);
        if (category) {
            return formatAmountShort(category.value);
        }
    }
    return props.formattedBalance;
});

// Инициализация полного графика
const initFullChartClickHandler = async () => {
    await nextTick();
    setTimeout(() => {
        if (fullChartRef.value?.chart) {
            fullChartRef.value.chart.off('click', handleFullChartClick);
            fullChartRef.value.chart.on('click', handleFullChartClick);
            fullChartRef.value.chart.resize();
            fullChartRef.value.chart.setOption(fullChartOption.value, true);
        }
    }, 100);
};

// Следим за открытием модального окна
watch(() => props.modelValue, async (isOpen) => {
    if (isOpen) {
        selectedCategory.value = null;
        await nextTick();
        setTimeout(() => {
            initFullChartClickHandler();
            setTimeout(() => {
                if (fullChartRef.value?.chart) {
                    fullChartRef.value.chart.resize();
                }
            }, 200);
        }, 300);
    }
});

const handleUpdate = (value: boolean) => {
    emit('update:modelValue', value);
};

// Опции для полного графика
const fullChartOption = computed<EChartsOption>(() => ({
    tooltip: {
        show: false,
    },
    animation: true,
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
            data: props.categories.length > 0
                ? props.categories.map((item) => ({
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
.full-chart {
    display: flex;
    flex-direction: column;
    gap: 2rem;
    padding: 1rem 0;
    height: 100%;
    overflow: hidden;

    &__container-wrapper {
        position: relative;
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 300px;
        flex-shrink: 0;
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
        gap: 0.5rem;
        position: relative;
    }

    &__center-button {
        pointer-events: auto;
        min-width: 12rem;
        margin-top: 0.5rem;
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
        flex-direction: column;
        gap: 0.8rem;
        overflow-y: auto;
        flex: 1;
        padding-right: 0.4rem;

        &::-webkit-scrollbar {
            width: 4px;
        }

        &::-webkit-scrollbar-track {
            background: transparent;
        }

        &::-webkit-scrollbar-thumb {
            background: var(--border-medium);
            border-radius: 2px;
        }
    }

    &__category {
        display: flex;
        align-items: center;
        gap: 1.2rem;
        padding: 1.2rem 1.6rem;
        border-radius: var(--radius-l);
        cursor: pointer;
        transition: all 0.3s ease;
        background: var(--card-default);
        border: 1px solid var(--border-medium);
        width: 100%;
        flex-shrink: 0;

        &:hover {
            background: var(--card-hover);
            border-color: var(--border-light);
        }

        &--active {
            background: var(--card-accent);
            border-color: var(--primary-500);
        }
    }

    &__category-icon {
        width: 2rem;
        height: 2rem;
        border-radius: 50%;
        transition: transform 0.3s ease;
        flex-shrink: 0;
    }

    &__category-name {
        transition: color 0.3s ease;
        color: var(--text-color);
        flex: 1;
        text-align: left;
    }

    &__category-percent {
        color: var(--text-color);
        opacity: 0.7;
        font-size: 1.2rem;
        font-weight: 600;
    }

    &__category:hover &__category-icon {
        transform: scale(1.2);
    }

    &__category--active &__category-icon {
        transform: scale(1.3);
        box-shadow: 0 0 8px currentColor;
    }

    &__empty {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        color: var(--text-color-secondary);
        font: var(--font-16-r);
    }
}

:deep(.full-chart-dialog) {
    color: var(--text-color);

    .p-dialog {
        width: 100vw !important;
        height: 100vh !important;
        max-width: 100vw !important;
        max-height: 100vh !important;
        margin: 0;
        border-radius: 0;
        top: 0 !important;
        left: 0 !important;
    }

    .p-dialog-content {
        padding: 1.6rem;
        height: calc(100vh - 60px);
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }

    .p-dialog-header {
        padding: 1.6rem !important;
    }

    .p-dialog-header .p-dialog-title {
        color: var(--text-color) !important;
        font: var(--font-20-b) !important;
        font-size: 2.0rem !important;
        font-weight: 600 !important;
        line-height: 1 !important;
    }
}

.full-chart-dialog__title {
    color: var(--text-color) !important;
    font: var(--font-20-b) !important;
    font-size: 2.0rem !important;
    font-weight: 600 !important;
    margin: 0;
    padding: 0;
}
</style>
