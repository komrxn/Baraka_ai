import { onMounted, onBeforeUnmount } from 'vue';
import { storeToRefs } from 'pinia';
import { useTransactionsStore } from '@/store/transactionsStore';
import { useCategoriesStore } from '@/store/categoriesStore';
import { useLimitsStore } from '@/store/limitsStore';
import { useBalanceStore } from '@/store/balanceStore';
import { useDebtsBalanceStore } from '@/store/debtsBalanceStore';
import { useCategoriesChartStore } from '@/store/categoriesChartStore';

const REFRESH_INTERVAL = 60 * 1000; // 1 минута в миллисекундах

export const useAutoRefresh = () => {
    let refreshInterval: ReturnType<typeof setInterval> | null = null;

    const refreshAllStores = async () => {
        try {
            const transactionsStore = useTransactionsStore();
            const categoriesStore = useCategoriesStore();
            const limitsStore = useLimitsStore();
            const balanceStore = useBalanceStore();
            const debtsBalanceStore = useDebtsBalanceStore();
            const categoriesChartStore = useCategoriesChartStore();

            // Получаем текущие фильтры и состояние через storeToRefs
            const { currentFilters } = storeToRefs(transactionsStore);
            const { isLoaded: chartIsLoaded } = storeToRefs(categoriesChartStore);

            // Обновляем все сторы параллельно
            await Promise.allSettled([
                // Обновляем транзакции с текущими фильтрами
                transactionsStore.loadTransactions(currentFilters.value, false, true).catch(() => { }),
                // Обновляем категории с текущим фильтром
                categoriesStore.refreshCategories().catch(() => { }),
                // Обновляем лимиты с текущим фильтром
                limitsStore.refreshLimits().catch(() => { }),
                // Обновляем баланс
                balanceStore.loadBalance({ period: 'month' }, true).catch(() => { }),
                // Обновляем баланс долгов
                debtsBalanceStore.loadDebtBalance(true).catch(() => { }),
                // Обновляем график категорий, если он был загружен
                chartIsLoaded.value
                    ? categoriesChartStore.loadCategories({ period: 'month', type: 'expense' }, true).catch(() => { })
                    : Promise.resolve(),
            ]);
        } catch (error) {
            console.error('Failed to refresh stores:', error);
        }
    };

    const startAutoRefresh = () => {
        // Очищаем предыдущий интервал, если он существует
        if (refreshInterval) {
            clearInterval(refreshInterval);
        }

        console.log('startAutoRefresh');

        // Запускаем обновление каждую минуту
        refreshInterval = setInterval(() => {
            refreshAllStores();
        }, REFRESH_INTERVAL);
    };

    const stopAutoRefresh = () => {
        if (refreshInterval) {
            clearInterval(refreshInterval);
            refreshInterval = null;
        }
    };

    onMounted(() => {
        startAutoRefresh();
    });

    onBeforeUnmount(() => {
        stopAutoRefresh();
    });

    return {
        refreshAllStores,
        startAutoRefresh,
        stopAutoRefresh,
    };
};

