<template>
    <div class="analytics-page">
        <div class="analytics-page__header">
            <Button :icon="arrowLeft" severity="secondary" @click="router.back()"
                class="analytics-page__header-button" />
            <h1 class="gold-text">{{ t('analytics.title') }}</h1>
            <div class="analytics-page__header-empty" />
        </div>

        <div class="analytics-page__filters">
            <SelectButton v-model="selectedPeriod" :options="periodOptions" option-label="label" option-value="value"
                :allow-empty="false" />
        </div>

        <div v-if="loading" class="analytics-page__loading">
            <ProgressSpinner />
        </div>
        <template v-else>
            <div class="analytics-page__stats">
                <div class="analytics-page__stat-card">
                    <div class="analytics-page__stat-card-header">
                        <VIcon :icon="arrowUpRight" class="analytics-page__stat-card-icon income" />
                        <span class="analytics-page__stat-card-label">{{ t('analytics.income') }}</span>
                    </div>
                    <p class="analytics-page__stat-card-value gold-text">{{ formatAmount(stats.income) }} UZS</p>
                    <div class="analytics-page__stat-card-change" :class="{ positive: stats.incomeChange > 0 }">
                        <VIcon :icon="stats.incomeChange > 0 ? arrowUpRight : arrowDownLeft"
                            class="analytics-page__stat-card-change-icon" />
                        <span>{{ Math.abs(stats.incomeChange) }}%</span>
                    </div>
                </div>

                <div class="analytics-page__stat-card">
                    <div class="analytics-page__stat-card-header">
                        <VIcon :icon="arrowDownLeft" class="analytics-page__stat-card-icon expense" />
                        <span class="analytics-page__stat-card-label">{{ t('analytics.expenses') }}</span>
                    </div>
                    <p class="analytics-page__stat-card-value gold-text">{{ formatAmount(stats.expense) }} UZS</p>
                    <div class="analytics-page__stat-card-change" :class="{ positive: stats.expenseChange < 0 }">
                        <VIcon :icon="stats.expenseChange < 0 ? arrowDownLeft : arrowUpRight"
                            class="analytics-page__stat-card-change-icon" />
                        <span>{{ Math.abs(stats.expenseChange) }}%</span>
                    </div>
                </div>

                <div class="analytics-page__stat-card">
                    <div class="analytics-page__stat-card-header">
                        <VIcon :icon="dollar" class="analytics-page__stat-card-icon balance" />
                        <span class="analytics-page__stat-card-label">{{ t('analytics.balance') }}</span>
                    </div>
                    <p class="analytics-page__stat-card-value gold-text">{{ formatAmount(stats.balance) }} UZS</p>
                    <div class="analytics-page__stat-card-change" :class="{ positive: stats.balanceChange > 0 }">
                        <VIcon :icon="stats.balanceChange > 0 ? arrowUpRight : arrowDownLeft"
                            class="analytics-page__stat-card-change-icon" />
                        <span>{{ Math.abs(stats.balanceChange) }}%</span>
                    </div>
                </div>

                <div class="analytics-page__stat-card">
                    <div class="analytics-page__stat-card-header">
                        <VIcon :icon="analitcs" class="analytics-page__stat-card-icon average" />
                        <span class="analytics-page__stat-card-label">{{ t('analytics.averageExpense') }}</span>
                    </div>
                    <p class="analytics-page__stat-card-value gold-text">{{ formatAmount(stats.averageExpense) }} UZS
                    </p>
                    <div class="analytics-page__stat-card-change" :class="{ positive: stats.averageChange < 0 }">
                        <VIcon :icon="stats.averageChange < 0 ? arrowDownLeft : arrowUpRight"
                            class="analytics-page__stat-card-change-icon" />
                        <span>{{ Math.abs(stats.averageChange) }}%</span>
                    </div>
                </div>
            </div>

            <div class="analytics-page__content">
                <div class="analytics-page__chart-card">
                    <div class="analytics-page__chart-card-header">
                        <h2 class="font-18-b gold-text">{{ t('analytics.dynamics') }}</h2>
                    </div>
                    <div class="analytics-page__chart-wrapper">
                        <VChart :option="lineChartOption" class="analytics-page__chart" />
                    </div>
                </div>

                <div class="analytics-page__chart-card">
                    <div class="analytics-page__chart-card-header">
                        <h2 class="font-18-b gold-text">{{ t('analytics.averageTrend') }}</h2>
                    </div>
                    <div class="analytics-page__chart-wrapper">
                        <VChart :option="trendChartOption" class="analytics-page__chart" />
                    </div>
                </div>

                <div class="analytics-page__chart-card">
                    <div class="analytics-page__chart-card-header">
                        <h2 class="font-18-b gold-text">{{ t('analytics.expensesByCategory') }}</h2>
                    </div>
                    <div ref="pieChartWrapperRef" class="analytics-page__chart-wrapper pie">
                        <VChart ref="pieChartRef" :option="pieChartOption" class="analytics-page__chart" />
                        <Transition name="fade">
                            <div v-if="selectedCategory" class="analytics-page__chart-center">
                                <p class="analytics-page__chart-center-label font-14-r">{{ selectedCategory }}</p>
                                <h2 class="analytics-page__chart-center-value font-30-b gold-text">
                                    {{ formatAmount(getCategoryAmount(selectedCategory)) }}
                                </h2>
                            </div>
                            <div v-else class="analytics-page__chart-center">
                                <p class="analytics-page__chart-center-label font-14-r">{{ t('main.totalExpenses') }}</p>
                                <h2 class="analytics-page__chart-center-value font-30-b gold-text">
                                    {{ formatAmount(stats.expense) }}
                                </h2>
                            </div>
                        </Transition>
                    </div>
                    <div class="analytics-page__categories">
                        <div v-for="category in categoryData" :key="category.name" class="analytics-page__category"
                            :class="{ 'analytics-page__category--active': selectedCategory === category.name }"
                            @click="selectCategory(category.name)">
                            <div class="analytics-page__category-icon" :style="{ backgroundColor: category.color }">
                            </div>
                            <p class="analytics-page__category-name font-12-r">{{ category.name }}</p>
                            <span class="analytics-page__category-percent font-10-r">{{ category.percentage }}%</span>
                        </div>
                    </div>
                </div>

                <div class="analytics-page__top-categories">
                    <div class="analytics-page__top-categories-header">
                        <h2 class="font-18-b gold-text">{{ t('analytics.topCategories') }}</h2>
                    </div>
                    <div v-if="topCategories.length === 0" class="analytics-page__empty">
                        <div class="analytics-page__empty-icon">
                            <VIcon :icon="warning" />
                        </div>
                        <p class="analytics-page__empty-text">{{ t('analytics.noData') }}</p>
                        <p class="analytics-page__empty-hint">{{ t('analytics.addTransactions') }}</p>
                    </div>
                    <div v-else class="analytics-page__top-categories-list">
                        <div v-for="(category, index) in topCategories" :key="category.name"
                            class="analytics-page__top-category">
                            <div class="analytics-page__top-category-rank">{{ index + 1 }}</div>
                            <div class="analytics-page__top-category-icon" :style="{ backgroundColor: category.color }">
                            </div>
                            <div class="analytics-page__top-category-info">
                                <p class="analytics-page__top-category-name font-14-r">{{ category.name }}</p>
                                <p class="analytics-page__top-category-amount font-12-r">
                                    {{ formatAmount(category.value) }} UZS
                                </p>
                            </div>
                            <div class="analytics-page__top-category-percent">
                                <span class="font-14-b">{{ category.percentage }}%</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </template>

    </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { onClickOutside } from '@vueuse/core';
import { Button, SelectButton, ProgressSpinner } from 'primevue';
import VChart from 'vue-echarts';
import { arrowLeft, arrowUpRight, arrowDownLeft, dollar, analitcs, warning } from '@/assets/icons';
import router from '@/router/router';
import VIcon from '@/components/UI/VIcon.vue';
import { useAnalytics } from '@/composables/Analytics/useAnalytics';
import type { Period } from '@/composables/Analytics/types';

const { t } = useI18n();

const {
    selectedPeriod,
    selectedCategory,
    stats,
    categoryData,
    topCategories,
    lineChartOption,
    pieChartOption,
    trendChartOption,
    formatAmount,
    getCategoryAmount,
    selectCategory,
    loading,
} = useAnalytics();



const pieChartRef = ref<InstanceType<typeof VChart> | null>(null);
const pieChartWrapperRef = ref<HTMLElement | null>(null);

const periodOptions = computed(() => [
    { label: t('analytics.day'), value: 'day' as Period },
    { label: t('analytics.week'), value: 'week' as Period },
    { label: t('analytics.month'), value: 'month' as Period },
    { label: t('analytics.year'), value: 'year' as Period },
]);

// Сброс выбора при клике вне графика
onClickOutside(pieChartWrapperRef, () => {
    if (selectedCategory.value) {
        selectCategory(selectedCategory.value);
    }
});

const handlePieChartClick = (params: any) => {
    if (params.componentType === 'series' && params.name) {
        selectCategory(params.name);
    }
};

onMounted(() => {
    setTimeout(() => {
        if (pieChartRef.value?.chart) {
            pieChartRef.value.chart.on('click', handlePieChartClick);
        }
    }, 100);
});
</script>

<style scoped lang="scss">
.analytics-page {
    padding: 2.4rem;
    padding-bottom: 2rem;

    &__header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 2rem;
    }

    &__header-button {
        width: 3.6rem;
        height: 3.6rem;
    }

    &__header-empty {
        width: 3.6rem;
        height: 3.6rem;
    }

    &__filters {
        margin-bottom: 2rem;

        :deep(.p-selectbutton) {
            width: 100%;

            .p-togglebutton {
                width: 100%;
            }
        }
    }

    &__stats {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1.2rem;
        margin-bottom: 2rem;
    }

    &__stat-card {
        padding: 1.6rem;
        border-radius: 1.6rem;
        background: var(--gold-card-bg);
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

        &-header {
            display: flex;
            align-items: center;
            gap: 0.8rem;
            margin-bottom: 1rem;
            position: relative;
            z-index: 1;
        }

        &-icon {
            width: 2.4rem;
            height: 2.4rem;
            padding: 0.4rem;
            border-radius: 0.8rem;
            background: rgba(255, 215, 0, 0.1);

            &.income {
                color: rgb(46, 213, 115);
            }

            &.expense {
                color: rgb(255, 107, 107);
            }

            &.balance {
                color: var(--primary-500);
            }

            &.average {
                color: rgb(74, 144, 226);
            }
        }

        &-label {
            font: var(--font-12-r);
            color: var(--text-color-secondary);
        }

        &-value {
            font: var(--font-20-b);
            margin: 0 0 0.8rem 0;
            position: relative;
            z-index: 1;
        }

        &-change {
            display: flex;
            align-items: center;
            gap: 0.4rem;
            font: var(--font-12-r);
            color: rgb(255, 107, 107);
            position: relative;
            z-index: 1;

            &.positive {
                color: rgb(46, 213, 115);
            }

            &-icon {
                width: 1.2rem;
                height: 1.2rem;
            }
        }
    }

    &__loading {
        display: flex;
        justify-content: center;
        padding: 4rem 2rem;
    }

    &__content {
        display: flex;
        flex-direction: column;
        gap: 1.6rem;
    }

    &__chart-card {
        padding: 1.6rem;
        border-radius: 1.6rem;
        background: var(--gold-card-bg);
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

        &-header {
            margin-bottom: 1.6rem;
            position: relative;
            z-index: 1;
        }
    }

    &__chart-wrapper {
        position: relative;
        width: 100%;
        margin-bottom: 1.6rem;

        &.pie {
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 1.6rem;
        }
    }

    &__chart {
        width: 100%;
        height: 300px;
    }

    &__chart-center {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 0.8rem;
        pointer-events: none;
        z-index: 10;
    }

    &__chart-center-label {
        color: var(--text-color);
        opacity: 0.7;
        transition: opacity 0.3s ease;
    }

    &__chart-center-value {
        color: var(--text-color);
        transition: transform 0.3s ease, color 0.3s ease;
    }

    &__categories {
        display: flex;
        flex-wrap: wrap;
        gap: 0.2rem;
        justify-content: center;
        position: relative;
        z-index: 1;
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

        &-icon {
            width: 1.2rem;
            height: 1.2rem;
            border-radius: 50%;
            transition: transform 0.3s ease;
            flex-shrink: 0;
        }

        &-name {
            transition: color 0.3s ease;
        }

        &-percent {
            color: var(--text-color);
            opacity: 0.6;
            font-size: 1rem;
        }

        &:hover &-icon {
            transform: scale(1.2);
        }

        &--active &-icon {
            transform: scale(1.3);
            box-shadow: 0 0 8px currentColor;
        }
    }

    &__top-categories {
        padding: 1.6rem;
        border-radius: 1.6rem;
        background: var(--gold-card-bg);
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

        &-header {
            margin-bottom: 1.6rem;
            position: relative;
            z-index: 1;
        }

        &-list {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            position: relative;
            z-index: 1;
        }
    }

    &__top-category {
        display: flex;
        align-items: center;
        gap: 1.2rem;
        padding: 1rem;
        border-radius: 1.2rem;
        background: var(--card-accent);
        border: 1px solid var(--border-light);
        transition: all 0.3s ease;

        &:hover {
            background: var(--card-hover);
            border-color: var(--border-medium);
            transform: translateX(4px);
        }

        &-rank {
            width: 2.4rem;
            height: 2.4rem;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            background: var(--primary-500);
            color: var(--black);
            font: var(--font-14-b);
            flex-shrink: 0;
        }

        &-icon {
            width: 3.2rem;
            height: 3.2rem;
            border-radius: 50%;
            flex-shrink: 0;
        }

        &-info {
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
        }

        &-name {
            color: var(--text-color);
        }

        &-amount {
            color: var(--text-color-secondary);
        }

        &-percent {
            color: var(--primary-500);
        }
    }

    &__empty {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 4rem 2rem;
        position: relative;
        z-index: 1;

        &-icon {
            width: 6.4rem;
            height: 6.4rem;
            color: var(--primary-500);
            margin-bottom: 1.6rem;
            opacity: 0.5;
        }

        &-text {
            font: var(--font-18-b);
            color: var(--text-color);
            margin: 0 0 0.4rem 0;
        }

        &-hint {
            font: var(--font-14-r);
            color: var(--text-color-secondary);
            margin: 0;
        }
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
