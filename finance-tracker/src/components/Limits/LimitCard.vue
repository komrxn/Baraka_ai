<template>
    <div class="limit-card">
        <div class="limit-card__header">
            <div class="limit-card__category">
                <h3 class="limit-card__category-name">{{ categoryName }}</h3>
            </div>
            <div v-if="props.hideMenu !== true" class="limit-card__menu-wrapper">
                <Button @click="toggleMenu" :icon="menuDots" text class="limit-card__menu-button" />
                <TieredMenu ref="menu" :model="menuItems" popup />
            </div>
        </div>

        <div class="limit-card__progress" :class="progressBarClass">
            <ProgressBar :value="progressPercentage" :show-value="false" />
        </div>

        <div class="limit-card__content">
            <div class="limit-card__budget">
                <span class="limit-card__budget-value">{{ formattedBudget }}</span>
                <span class="limit-card__budget-currency">UZS</span>
            </div>
            <div class="limit-card__spent-info">
                <span class="limit-card__spent-label">{{ t('limits.spent') }}:</span>
                <span class="limit-card__spent-value" :class="{ 'limit-card__spent-value--exceeded': isExceeded }">
                    {{ formattedSpent }}
                </span>
                <span v-if="isExceeded" class="limit-card__exceeded">
                    (+{{ formattedExceeded }})
                </span>
            </div>
            <p class="limit-card__period">{{ period }}</p>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { Button, ProgressBar, TieredMenu } from 'primevue';
import type { MenuItem } from 'primevue/menuitem';
import { menuDots } from '@/assets/icons';
import type { Limit } from '@/composables/Limits/types';
import { formatAmount } from '@/utils';
import { MONTHS_FULL } from '@/composables/data';

const { t } = useI18n();

const props = defineProps<{
    limit: Limit;
    hideMenu?: boolean;
}>();

const emit = defineEmits<{
    (e: 'remove'): void;
    (e: 'edit'): void;
}>();

const menu = ref();

const toggleMenu = (event: Event) => {
    menu.value.toggle(event);
};

const menuItems = computed<MenuItem[]>(() => [
    {
        label: t('common.edit'),
        command: () => {
            emit('edit');
        },
    },
    {
        label: t('common.delete'),
        command: () => {
            emit('remove');
        },
    },
]);

import { storeToRefs } from 'pinia';
import { useCategoriesStore } from '@/store/categoriesStore';

const categoriesStore = useCategoriesStore();
const { categories } = storeToRefs(categoriesStore);

const categoryName = computed(() => {
    if (props.limit.category_id) {
        const category = categories.value.find((c: any) => c.id === props.limit.category_id);
        if (category && category.slug) {
            return t(`categoryList.${category.slug}`);
        }
    }
    return props.limit.category_name || t('limits.notSelected');
});

const formattedBudget = computed(() => {
    return formatAmount(props.limit.amount);
});

const period = computed(() => {
    const startDate = new Date(props.limit.period_start);
    const endDate = new Date(props.limit.period_end);

    const startMonth = MONTHS_FULL[startDate.getMonth()];
    const startYear = startDate.getFullYear();
    const endMonth = MONTHS_FULL[endDate.getMonth()];
    const endYear = endDate.getFullYear();

    if (startMonth === endMonth && startYear === endYear) {
        return `${startMonth} ${startYear} г.`;
    }

    return `${startMonth} ${startYear} - ${endMonth} ${endYear} г.`;
});

const progressPercentage = computed(() => {
    // Если превысили, показываем 100%, чтобы прогресс-бар был полностью заполнен
    return props.limit.is_exceeded ? 100 : Math.min(props.limit.percentage || 0, 100);
});

const isExceeded = computed(() => {
    return props.limit.is_exceeded;
});

const formattedSpent = computed(() => {
    return formatAmount(props.limit.spent);
});

const formattedExceeded = computed(() => {
    if (!props.limit.is_exceeded) return '0';
    const exceeded = parseFloat(props.limit.spent) - parseFloat(props.limit.amount);
    return formatAmount(exceeded.toString());
});

const progressBarClass = computed(() => {
    if (props.limit.is_exceeded) {
        return 'limit-card__progress-bar--danger';
    } else if (props.limit.percentage >= 90) {
        return 'limit-card__progress-bar--warning';
    } else if (props.limit.percentage >= 70) {
        return 'limit-card__progress-bar--caution';
    } else {
        return 'limit-card__progress-bar--success';
    }
});
</script>

<style scoped lang="scss">
.limit-card {
    background: var(--gold-card-bg);
    border-radius: var(--radius-l);
    padding: 1.6rem;
    display: flex;
    flex-direction: column;
    gap: 1.2rem;
    border: 1px solid var(--gold-border);
    box-shadow: var(--gold-shadow);
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;

    &::before {
        content: '';
        position: absolute;
        inset: 0;
        border-radius: var(--radius-l);
        background: var(--gold-card-radial);
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    &:hover {
        border-color: var(--gold-border-hover);
        box-shadow: var(--gold-shadow-hover);

        &::before {
            opacity: 1;
        }
    }

    &__header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        position: relative;
        z-index: 1;
    }

    &__category-name {
        font: var(--font-16-b);
        margin: 0;
        color: var(--text-color);
        position: relative;
        z-index: 1;
    }

    &__progress {
        width: 100%;
        margin-top: 0.4rem;

        :deep(.p-progressbar) {
            height: 0.8rem;
            border-radius: 0.4rem;
            overflow: hidden;
            background-color: var(--border-light);
        }

        :deep(.p-progressbar-value) {
            transition: background-color 0.3s ease;
        }
    }

    &__progress-bar {
        &--success {
            :deep(.p-progressbar-value) {
                background: linear-gradient(90deg, #10b981 0%, #059669 100%);
            }
        }

        &--caution {
            :deep(.p-progressbar-value) {
                background: linear-gradient(90deg, #f59e0b 0%, #d97706 100%);
            }
        }

        &--warning {
            :deep(.p-progressbar-value) {
                background: linear-gradient(90deg, #f97316 0%, #ea580c 100%);
            }
        }

        &--danger {
            :deep(.p-progressbar-value) {
                background: linear-gradient(90deg, #ef4444 0%, #dc2626 100%);
            }
        }
    }

    &__content {
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
        position: relative;
        z-index: 1;
    }

    &__budget {
        display: flex;
        align-items: baseline;
        gap: 0.4rem;
    }

    &__budget-value {
        font: var(--font-20-b);
        color: var(--text-color);
        position: relative;
        z-index: 1;
    }

    &__budget-currency {
        font: var(--font-14-r);
        color: var(--text-color-secondary);
    }

    &__spent-info {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        margin-top: 0.4rem;
    }

    &__spent-label {
        font: var(--font-12-r);
        color: var(--text-color-secondary);
    }

    &__spent-value {
        font: var(--font-14-b);
        color: var(--text-color);

        &--exceeded {
            color: #ef4444;
        }
    }

    &__exceeded {
        font: var(--font-12-r);
        color: #ef4444;
    }

    &__period {
        font: var(--font-12-r);
        color: var(--text-color-secondary);
        margin: 0.4rem 0 0 0;
    }

    &__menu-wrapper {
        position: relative;
        z-index: 1;
    }

    &__menu-button {
        width: 2.4rem;
        height: 2.4rem;
    }
}
</style>
