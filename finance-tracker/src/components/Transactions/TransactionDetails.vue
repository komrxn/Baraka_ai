<template>
    <div class="transaction-details">
        <div class="transaction-details__header">
            <div class="transaction-details__icon" :style="{ backgroundColor: categoryColor }">
                <span class="transaction-details__emoji">{{ categoryIcon }}</span>
            </div>
            <div class="transaction-details__header-info">
                <h2 class="transaction-details__description">{{ transaction.description }}</h2>
                <p class="transaction-details__category">{{ categoryName }}</p>
            </div>
        </div>

        <div class="transaction-details__amount-section">
            <div class="transaction-details__amount" :class="`transaction-details__amount--${transaction.type}`">
                <span class="transaction-details__amount-value font-32-b">
                    {{ transaction.type === 'expense' ? '-' : '+' }}{{ formatAmount(transaction.amount) }}
                </span>
                <span class="transaction-details__currency font-16-r">{{ transaction.currency.toUpperCase() }}</span>
            </div>
        </div>

        <div class="transaction-details__info">
            <div class="transaction-details__info-item">
                <span class="transaction-details__info-label">{{ t('transactions.type') }}</span>
                <span class="transaction-details__info-value">
                    {{ transaction.type === 'income' ? t('transactions.income') : t('transactions.expense') }}
                </span>
            </div>
            <div class="transaction-details__info-item">
                <span class="transaction-details__info-label">{{ t('transactions.date') }}</span>
                <span class="transaction-details__info-value">{{ formatDate(transaction.transaction_date) }}</span>
            </div>
            <div class="transaction-details__info-item">
                <span class="transaction-details__info-label">{{ t('transactions.time') }}</span>
                <span class="transaction-details__info-value">{{ formatTime(transaction.transaction_date) }}</span>
            </div>
            <div v-if="transaction.created_at" class="transaction-details__info-item">
                <span class="transaction-details__info-label">{{ t('transactions.created') }}</span>
                <span class="transaction-details__info-value">{{ formatDateTime(transaction.created_at) }}</span>
            </div>
            <div v-if="transaction.updated_at && transaction.updated_at !== transaction.created_at"
                class="transaction-details__info-item">
                <span class="transaction-details__info-label">{{ t('transactions.updated') }}</span>
                <span class="transaction-details__info-value">{{ formatDateTime(transaction.updated_at) }}</span>
            </div>
        </div>

        <div class="transaction-details__actions">
            <Button :label="t('common.edit')" severity="secondary" outlined fluid @click="$emit('edit')"
                class="transaction-details__action-button" />
            <Button :label="t('common.delete')" severity="danger" outlined fluid @click="$emit('remove')"
                class="transaction-details__action-button" />
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { storeToRefs } from 'pinia';
import { Button } from 'primevue';
import type { Transaction } from '@/composables/Transactions/types';
import { useCategoriesStore } from '@/store/categoriesStore';
import { formatAmount, formatDate, formatDateTime } from '@/utils';
import { formatTime } from '@/composables/Transactions/utils';

const { t } = useI18n();

const props = defineProps<{
    transaction: Transaction;
}>();

defineEmits<{
    (e: 'edit'): void;
    (e: 'remove'): void;
}>();

const { categories } = storeToRefs(useCategoriesStore());

const category = computed(() => {
    return categories.value.find(cat => cat.id === props.transaction.category_id);
});

const categoryName = computed(() => {
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
</script>

<style scoped lang="scss">
.transaction-details {
    display: flex;
    flex-direction: column;
    gap: 2.4rem;
    padding: 0 2rem 2rem 2rem;

    &__header {
        display: flex;
        align-items: center;
        gap: 1.6rem;
    }

    &__icon {
        width: 6.4rem;
        height: 6.4rem;
        display: flex;
        justify-content: center;
        align-items: center;
        border-radius: 1.6rem;
        flex-shrink: 0;
        border: 1px solid rgba(255, 215, 0, 0.3);
        box-shadow: 0 2px 8px rgba(255, 215, 0, 0.2);
    }

    &__emoji {
        font-size: 3rem;
        line-height: 1;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    &__header-info {
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
        flex: 1;
        min-width: 0;
    }

    &__description {
        font: var(--font-20-b);
        margin: 0;
        color: var(--text-color);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    &__category {
        font: var(--font-14-r);
        color: var(--text-color-secondary);
        margin: 0;
    }

    &__amount-section {
        display: flex;
        justify-content: center;
        padding: 2rem 0;
        border-top: 1px solid var(--border-light);
        border-bottom: 1px solid var(--border-light);
    }

    &__amount {
        display: flex;
        align-items: center;
        gap: 0.4rem;

        &--expense {
            color: rgb(255, 65, 43);
        }

        &--income {
            color: rgb(90, 204, 62);
        }
    }

    &__amount-value {
        font: var(--font-34-b);
    }

    &__currency {
        font: var(--font-20-r);
        color: var(--text-color-secondary);
    }

    &__info {
        display: flex;
        flex-direction: column;
        gap: 1.6rem;
    }

    &__info-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1.2rem;
    }

    &__info-label {
        font: var(--font-14-r);
        color: var(--text-color-secondary);
    }

    &__info-value {
        font: var(--font-14-b);
        color: var(--text-color);
        text-align: right;
    }

    &__actions {
        display: flex;
        flex-direction: column;
        gap: 1.2rem;
        padding-top: 2rem;
        border-top: 1px solid var(--border-light);
    }

    &__action-button {
        width: 100%;
    }
}
</style>
