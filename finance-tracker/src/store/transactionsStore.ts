import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Transaction, GetTransactionsParams, TransactionGroup, TransactionUpdateData } from '@/composables/Transactions/types';
import { useTransactionsRequests } from '@/composables/Transactions/requests';
import { groupTransactionsByDay } from '@/composables/Transactions/utils';

export const useTransactionsStore = defineStore('transactions', () => {
    const transactions = ref<Transaction[]>([]);
    const loading = ref<boolean>(false);
    const isLoaded = ref<boolean>(false);
    const isLoadingRequest = ref<boolean>(false); // Дополнительный флаг для защиты от параллельных запросов
    const total = ref<number>(0);
    const page = ref<number>(1);
    const pageSize = ref<number>(50);
    const hasMore = ref<boolean>(true);
    const currentFilters = ref<GetTransactionsParams | undefined>(undefined);
    const drawerVisible = ref(false);
    const filterDrawerVisible = ref(false);
    const editingTransaction = ref<Transaction | null>(null);

    const { getTransactions: fetchTransactions, updateTransaction: updateTransactionRequest, deleteTransaction: deleteTransactionRequest } = useTransactionsRequests();

    const groupedTransactions = computed<TransactionGroup[]>(() => {
        return groupTransactionsByDay(transactions.value);
    });

    const loadTransactions = async (params?: GetTransactionsParams, append = false, force = false) => {
        // Защита от параллельных запросов - всегда проверяем
        if (loading.value || isLoadingRequest.value) {
            return;
        }

        // Если force = true, пропускаем все проверки и загружаем принудительно
        if (!force) {
            // Нормализуем параметры: если params не передан, используем пустой объект (без фильтров)
            const normalizedParams: GetTransactionsParams = params || {};

            // Упрощенная проверка изменения фильтров
            // Сравниваем только ключи фильтров (игнорируя page и page_size)
            const getFilterKeys = (filters: GetTransactionsParams | undefined) => {
                if (!filters || Object.keys(filters).length === 0) return '';
                const { page, page_size, ...rest } = filters;
                return JSON.stringify(rest);
            };

            const currentFilterKeys = getFilterKeys(currentFilters.value);
            const newFilterKeys = getFilterKeys(normalizedParams);
            const filtersChanged = currentFilterKeys !== newFilterKeys;

            // Если данные уже загружены, фильтры не изменились и не требуется принудительная загрузка, не загружаем заново
            if (!append && isLoaded.value && !filtersChanged && transactions.value.length > 0) {
                return;
            }
        }

        try {
            loading.value = true;
            isLoadingRequest.value = true;

            // Нормализуем параметры для запроса
            const normalizedParams: GetTransactionsParams = params || {};

            // Формируем параметры запроса
            const requestParams: GetTransactionsParams = {
                ...normalizedParams,
                page: append ? page.value : (normalizedParams.page || 1),
                page_size: normalizedParams.page_size || pageSize.value,
            };

            const response = await fetchTransactions(requestParams);

            if (append) {
                // Добавляем к существующим транзакциям
                transactions.value = [...transactions.value, ...response.items];
            } else {
                // Заменяем транзакции новыми
                transactions.value = response.items;
                page.value = response.page;
                isLoaded.value = true;
            }

            total.value = response.total;
            page.value = response.page;
            pageSize.value = response.page_size;
            hasMore.value = response.items.length === response.page_size && transactions.value.length < response.total;

            // Сохраняем текущие фильтры только если это не append
            if (!append) {
                // Если params пустой объект или undefined, сбрасываем фильтры
                if (!params || Object.keys(params).length === 0) {
                    currentFilters.value = undefined;
                } else {
                    currentFilters.value = normalizedParams;
                }
            }
        } catch (error) {
            console.error('Failed to load transactions:', error);
            isLoaded.value = false;
            throw error;
        } finally {
            loading.value = false;
            isLoadingRequest.value = false;
        }
    };

    const loadMoreTransactions = async () => {
        if (!hasMore.value || loading.value) return;

        page.value += 1;
        await loadTransactions({ page: page.value }, true);
    };

    const applyFilters = async (filters: GetTransactionsParams) => {
        page.value = 1;
        currentFilters.value = filters;
        isLoaded.value = false;
        transactions.value = []; // Очищаем транзакции перед загрузкой с новыми фильтрами
        await loadTransactions(filters, false, true);
        filterDrawerVisible.value = false;
    };

    const resetFilters = async () => {
        page.value = 1;
        currentFilters.value = undefined;
        isLoaded.value = false;
        transactions.value = []; // Очищаем транзакции перед загрузкой
        await loadTransactions({}, false, true);
        filterDrawerVisible.value = false;
    };

    const refreshTransactions = async () => {
        await loadTransactions(currentFilters.value, false, true);
    };

    const updateTransaction = async (id: string, transactionData: TransactionUpdateData) => {
        try {
            loading.value = true;
            const updatedTransaction = await updateTransactionRequest(id, transactionData);
            // Обновляем транзакцию в списке
            const index = transactions.value.findIndex(tx => tx.id === id);
            if (index !== -1) {
                transactions.value[index] = updatedTransaction;
            }
            return updatedTransaction;
        } catch (error) {
            console.error('Failed to update transaction:', error);
            throw error;
        } finally {
            loading.value = false;
        }
    };

    const removeTransaction = async (id: string) => {
        try {
            loading.value = true;
            await deleteTransactionRequest(id);
            // Удаляем транзакцию из списка
            transactions.value = transactions.value.filter(tx => tx.id !== id);
            // Обновляем total
            total.value = Math.max(0, total.value - 1);
        } catch (error) {
            console.error('Failed to delete transaction:', error);
            throw error;
        } finally {
            loading.value = false;
        }
    };

    const editTransaction = (transaction: Transaction) => {
        editingTransaction.value = transaction;
        drawerVisible.value = true;
    };

    return {
        transactions,
        groupedTransactions,
        loading,
        isLoaded,
        total,
        page,
        pageSize,
        hasMore,
        currentFilters,
        drawerVisible,
        filterDrawerVisible,
        editingTransaction,
        loadTransactions,
        loadMoreTransactions,
        applyFilters,
        resetFilters,
        refreshTransactions,
        updateTransaction,
        removeTransaction,
        editTransaction,
    };
});
