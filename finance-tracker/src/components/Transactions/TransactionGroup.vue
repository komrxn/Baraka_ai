<template>
    <div class="transaction-group">
        <div class="transaction-group__header">
            <h3 class="transaction-group__date">{{ group.dateLabel }}</h3>
            <div class="transaction-group__totals">
                <span v-if="group.totalIncome > 0" class="transaction-group__total transaction-group__total--income">
                    +{{ formatAmount(group.totalIncome) }}
                </span>
                <span v-if="group.totalExpense > 0" class="transaction-group__total transaction-group__total--expense">
                    -{{ formatAmount(group.totalExpense) }}
                </span>
            </div>
        </div>
        <div class="transaction-group__transactions">
            <TransactionCard v-for="transaction in group.transactions" :key="transaction.id"
                :transaction="transaction" :selection-mode="selectionMode" :selected="selectedIds.includes(transaction.id)"
                @click="handleTransactionClick" @select="handleSelect" />
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { TransactionGroup, Transaction } from '@/composables/Transactions/types';
import TransactionCard from './TransactionCard.vue';
import { formatAmount } from '@/utils';

const props = defineProps<{
    group: TransactionGroup;
    selectionMode?: boolean;
    selectedIds?: string[];
}>();

const emit = defineEmits<{
    (e: 'transaction-click', transaction: Transaction): void;
    (e: 'select', transaction: Transaction, selected: boolean): void;
}>();

const selectedIds = computed(() => props.selectedIds ?? []);

const handleTransactionClick = (transaction: Transaction) => {
    if (!props.selectionMode) {
        emit('transaction-click', transaction);
    }
};

const handleSelect = (transaction: Transaction, selected: boolean) => {
    emit('select', transaction, selected);
};
</script>

<style scoped lang="scss">
.transaction-group {
    margin-bottom: 2.4rem;

    &__header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.2rem;
        padding: 0 0.4rem;
    }

    &__date {
        font: var(--font-18-b);
        margin: 0;
        color: var(--text-color);
    }

    &__totals {
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }

    &__total {
        font: var(--font-14-b);

        &--income {
            color: rgb(90, 204, 62);
        }

        &--expense {
            color: rgb(255, 65, 43);
        }
    }

    &__transactions {
        display: flex;
        flex-direction: column;
        gap: 0.8rem;
    }
}
</style>
