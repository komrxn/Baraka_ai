<template>
    <div class="transactions-page">
        <div class="transactions-page__header">
            <Button :icon="arrowLeft" severity="secondary" @click="router.back()"
                class="transactions-page__header-button" />
            <h1 class="gold-text">{{ t('transactions.title') }}</h1>
            <Button :icon="filter" severity="secondary" @click="filterDrawerVisible = true"
                class="transactions-page__header-button" />
        </div>

        <div class="transactions-page__content">
            <div v-if="loading" class="transactions-page__loading">
                <ProgressSpinner />
            </div>
            <template v-else>
                <div v-if="groupedTransactions.length === 0" class="transactions-page__empty">
                    <div class="transactions-page__empty-icon">
                        <VIcon :icon="warning" />
                    </div>
                    <p class="transactions-page__empty-text">{{ t('transactions.noTransactions') }}</p>
                    <p class="transactions-page__empty-hint">{{ t('transactions.tryFilters') }}</p>
                </div>
                <template v-else>
                    <div class="transactions-page__list">
                        <TransactionGroup v-for="group in groupedTransactions" :key="group.date" :group="group"
                            @transaction-click="handleTransactionClick" />
                    </div>
                    <div v-if="hasMore" class="transactions-page__load-more">
                        <Button :label="t('common.loadMore')" severity="secondary" outlined
                            @click="loadMoreTransactions" />
                    </div>
                </template>
            </template>
        </div>

        <TransactionFilterForm v-model:visible="filterDrawerVisible" :current-filters="currentFilters"
            @apply="handleApplyFilters" @reset="handleResetFilters" />

        <VDrawer v-model:visible="detailsDrawerVisible">
            <template #header>
                <h2 class="transaction-details-drawer__title">{{ t('transactions.details') }}</h2>
            </template>
            <TransactionDetails v-if="selectedTransaction" :transaction="selectedTransaction"
                @edit="handleEditTransaction" @remove="handleRemoveTransaction" />
        </VDrawer>

        <TransactionForm v-model:visible="formDrawerVisible" :edit-data="formEditData"
            @submit="handleSubmitTransaction" />
    </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useI18n } from 'vue-i18n';
import { arrowLeft, filter, warning } from '@/assets/icons';
import router from '@/router/router';
import { Button, ProgressSpinner } from 'primevue';

const { t } = useI18n();
import VIcon from '@/components/UI/VIcon.vue';
import VDrawer from '@/components/UI/VDrawer.vue';
import TransactionGroup from '@/components/Transactions/TransactionGroup.vue';
import TransactionFilterForm from '@/components/Transactions/TransactionFilterForm.vue';
import TransactionDetails from '@/components/Transactions/TransactionDetails.vue';
import TransactionForm from '@/components/Transactions/TransactionForm.vue';
import type { GetTransactionsParams, Transaction, TransactionFormData, TransactionUpdateData } from '@/composables/Transactions/types';
import { useTransactionsStore } from '@/store/transactionsStore';
import { useCategoriesStore } from '@/store/categoriesStore';
import { useToastStore } from '@/store/toastsStore';

const transactionsStore = useTransactionsStore();
const categoriesStore = useCategoriesStore();
const $toast = useToastStore();

const { groupedTransactions, loading, hasMore, currentFilters, filterDrawerVisible, editingTransaction } = storeToRefs(transactionsStore);
const { loadTransactions, loadMoreTransactions, applyFilters, resetFilters, updateTransaction, removeTransaction, editTransaction, refreshTransactions } = transactionsStore;
const { loadCategories } = categoriesStore;

const handleApplyFilters = async (filters: GetTransactionsParams) => {
    await applyFilters(filters);
};

const handleResetFilters = async () => {
    await resetFilters();
};

const detailsDrawerVisible = ref(false);
const selectedTransaction = ref<Transaction | null>(null);
const formDrawerVisible = ref(false);

const formEditData = computed(() => {
    return editingTransaction.value;
});

const handleTransactionClick = (transaction: Transaction) => {
    selectedTransaction.value = transaction;
    detailsDrawerVisible.value = true;
};

const handleEditTransaction = () => {
    if (selectedTransaction.value) {
        editTransaction(selectedTransaction.value);
        detailsDrawerVisible.value = false;
        formDrawerVisible.value = true;
    }
};

const handleRemoveTransaction = async () => {
    if (!selectedTransaction.value) return;

    try {
        await removeTransaction(selectedTransaction.value.id);
        detailsDrawerVisible.value = false;
        selectedTransaction.value = null;
        await refreshTransactions();
        $toast.success(t('common.success'), t('transactions.deleteSuccess'));
    } catch (error) {
        $toast.error(t('common.error'), t('transactions.deleteError'));
    }
};

const convertFormDataToUpdateData = (formData: TransactionFormData): TransactionUpdateData => {
    const updateData: TransactionUpdateData = {
        type: formData.type,
        amount: formData.amount.toString(),
        currency: formData.currency,
        description: formData.description,
        transaction_date: formData.transaction_date,
    };

    // Добавляем category_id только если он выбран
    if (formData.category_id && formData.category_id.trim() !== '') {
        updateData.category_id = formData.category_id;
    }

    return updateData;
};

const handleSubmitTransaction = async (formData: TransactionFormData) => {
    if (!editingTransaction.value) return;

    try {
        const updateData = convertFormDataToUpdateData(formData);
        await updateTransaction(editingTransaction.value.id, updateData);
        formDrawerVisible.value = false;
        await refreshTransactions();
        $toast.success(t('common.success'), t('transactions.updateSuccess'));
    } catch (error) {
        $toast.error(t('common.error'), t('transactions.updateError'));
    }
};

onMounted(async () => {
    transactionsStore.currentFilters = undefined;
    transactionsStore.isLoaded = false;
    transactionsStore.transactions = [];
    transactionsStore.page = 1;
    transactionsStore.hasMore = true;

    await Promise.all([
        loadCategories(),
        loadTransactions({}, false, true)
    ]);
});

// onBeforeUnmount(() => {
//     // При уходе со страницы не сбрасываем данные, чтобы они остались в кеше
//     // Но сбрасываем флаг инициализации для возможности повторной загрузки при возврате
// });
</script>

<style scoped lang="scss">
.transactions-page {
    padding: 2.4rem;

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

    &__content {
        display: flex;
        flex-direction: column;
    }

    &__empty {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 4rem 2rem;
        background: var(--gold-card-bg);
        border-radius: 1.6rem;
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

        &-icon {
            width: 6.4rem;
            height: 6.4rem;
            color: var(--primary-500);
            margin-bottom: 1.6rem;
            position: relative;
            z-index: 1;
            opacity: 0.5;
        }

        &-text {
            font: var(--font-18-b);
            color: var(--text-color);
            margin: 0 0 0.4rem 0;
            position: relative;
            z-index: 1;
        }

        &-hint {
            font: var(--font-14-r);
            color: var(--text-color-secondary);
            margin: 0;
            position: relative;
            z-index: 1;
        }
    }

    &__list {
        display: flex;
        flex-direction: column;
    }

    &__loading {
        display: flex;
        justify-content: center;
        padding: 2rem;
    }

    &__load-more {
        display: flex;
        justify-content: center;
        padding: 2rem 0;
    }
}

.transaction-details-drawer {
    &__title {
        font: var(--font-20-b);
        margin: 0;
    }
}
</style>
