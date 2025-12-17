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

        <div class="limit-card__progress">
            <ProgressBar :value="progressPercentage" :show-value="false" />
        </div>

        <div class="limit-card__content">
            <div class="limit-card__budget">
                <span class="limit-card__budget-value">{{ formattedBudget }}</span>
                <span class="limit-card__budget-currency">UZS</span>
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

const categoryName = computed(() => {
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
    return props.limit.percentage || 0;
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

    &__period {
        font: var(--font-12-r);
        color: var(--text-color-secondary);
        margin: 0;
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
