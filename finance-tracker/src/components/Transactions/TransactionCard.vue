<template>
    <div class="transaction-card" @click="handleClick">
        <div class="transaction-card__content">
            <div class="transaction-card__icon" :style="{ backgroundColor: categoryColor }">
                <span class="transaction-card__emoji">{{ categoryIcon }}</span>
            </div>
            <div class="transaction-card__info">
                <h3 class="transaction-card__description">{{ transaction.description }}</h3>
                <div class="transaction-card__meta">
                    <span class="transaction-card__category">{{ categoryName }}</span>
                    <span class="transaction-card__time">{{ formatTime(transaction.transaction_date) }}</span>
                </div>
            </div>
        </div>
        <div class="transaction-card__amount" :class="`transaction-card__amount--${transaction.type}`">
            <span>{{ transaction.type === 'expense' ? '-' : '+' }}{{ formatAmount(transaction.amount) }}</span>
            <span class="transaction-card__currency">{{ transaction.currency.toUpperCase() }}</span>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { storeToRefs } from 'pinia';
import type { Transaction } from '@/composables/Transactions/types';
import { useCategoriesStore } from '@/store/categoriesStore';
import { formatAmount } from '@/utils';
import { formatTime } from '@/composables/Transactions/utils';

const props = defineProps<{
    transaction: Transaction;
}>();

const { t } = useI18n();
const { categories } = storeToRefs(useCategoriesStore());

const category = computed(() => {
    return categories.value.find(cat => cat.id === props.transaction.category_id);
});

const categoryName = computed(() => {
    if (category.value?.slug) {
        return t(`categoryList.${category.value.slug}`);
    }
    return category.value?.name || t('transactions.noCategory');
});

const categoryIcon = computed(() => {
    return category.value?.icon || '💰';
});

const categoryColor = computed(() => {
    const color = category.value?.color || '#FFD700';
    // Конвертируем hex в rgba с прозрачностью
    const hex = color.replace('#', '');
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, 0.2)`;
});

const emit = defineEmits<{
    (e: 'click', transaction: Transaction): void;
}>();

const handleClick = () => {
    emit('click', props.transaction);
};
</script>

<style scoped lang="scss">
.transaction-card {
    background: var(--gold-card-bg);
    border-radius: var(--radius-l);
    padding: 1.2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1.2rem;
    border: 1px solid var(--gold-border);
    box-shadow: var(--gold-shadow);
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
    cursor: pointer;

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

    &__content {
        display: flex;
        align-items: center;
        gap: 1.2rem;
        flex: 1;
        min-width: 0;
        position: relative;
        z-index: 1;
    }

    &__icon {
        width: 4.4rem;
        height: 4.4rem;
        display: flex;
        justify-content: center;
        align-items: center;
        border-radius: 1.2rem;
        flex-shrink: 0;
        border: 1px solid rgba(255, 215, 0, 0.3);
        box-shadow: 0 2px 8px rgba(255, 215, 0, 0.2);
    }

    &__emoji {
        font-size: 2rem;
        line-height: 1;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    &__info {
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
        flex: 1;
        min-width: 0;
    }

    &__description {
        font: var(--font-16-b);
        margin: 0;
        color: var(--text-color);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    &__meta {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        flex-wrap: wrap;
    }

    &__category {
        font: var(--font-12-r);
        color: var(--text-color-secondary);
    }

    &__time {
        font: var(--font-12-r);
        color: var(--text-color-secondary);
    }

    &__amount {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 0.2rem;
        font: var(--font-16-b);
        position: relative;
        z-index: 1;
        flex-shrink: 0;

        &--expense {
            color: rgb(255, 65, 43);
        }

        &--income {
            color: rgb(90, 204, 62);
        }
    }

    &__currency {
        font: var(--font-12-r);
        color: var(--text-color-secondary);
    }
}
</style>
