<template>
    <div class="debts-page">
        <div class="debts-page__header">
            <Button :icon="arrowLeft" severity="secondary" @click="router.back()" class="debts-page__header-button" />
            <h1 class="gold-text">{{ t('debts.title') }}</h1>
            <Button :icon="filter" severity="secondary" @click="filterDrawerVisible = true"
                class="debts-page__header-button" />
        </div>

        <div class="debts-page__balance">
            <div class="debts-page__balance-item">
                <VIcon :icon="arrowDownLeft" class="debts-page__balance-icon" />
                <div class="debts-page__balance-content">
                    <h5 class="font-14-r">{{ t('debts.iOwe') }}</h5>
                    <p class="font-16-r gold-text">{{ formatAmount(totalBorrowed) }} UZS</p>
                </div>
            </div>
            <div class="debts-page__balance-item">
                <VIcon :icon="arrowUpRight" class="debts-page__balance-icon" />
                <div class="debts-page__balance-content">
                    <h5 class="font-14-r">{{ t('debts.oweMe') }}</h5>
                    <p class="font-16-r gold-text">{{ formatAmount(totalLent) }} UZS</p>
                </div>
            </div>
        </div>

        <div class="debts-page__content">
            <div v-if="loading" class="debts-page__loading">
                <ProgressSpinner />
            </div>
            <div v-else-if="filteredDebts.length === 0" class="debts-page__empty">
                <div class="debts-page__empty-icon">
                    <VIcon :icon="warning" />
                </div>
                <p class="debts-page__empty-text">{{ t('debts.noDebts') }}</p>
                <p class="debts-page__empty-hint">{{ t('debts.tryOtherFilters') }}</p>
            </div>
            <div v-else class="debts-page__list">
                <DebtCard v-for="debt in filteredDebts" :key="debt.id" :debt="debt" @remove="removeDebtHandler(debt.id)"
                    @edit="editDebt(debt)" @mark-paid="markAsPaid(debt.id)" />
            </div>
        </div>

        <div class="debts-page__footer">
            <Button :label="t('debts.addDebt')" fluid :icon="plus" @click="drawerVisible = true" />
        </div>
        <DebtForm v-model:visible="drawerVisible" :edit-data="formEditData" @submit="handleSubmitWrapper"
            @update:visible="handleDrawerVisibilityChange" />

        <DebtFilterForm v-model:visible="filterDrawerVisible" :current-filters="currentFilters"
            @apply="handleApplyFilters" @reset="handleResetFilters" />
    </div>
</template>

<script setup lang="ts">
import { computed, ref, onBeforeMount } from 'vue';
import { storeToRefs } from 'pinia';
import { useI18n } from 'vue-i18n';
import { Button, ProgressSpinner } from 'primevue';

const { t } = useI18n();
import DebtForm from '@/components/Debts/DebtForm.vue';
import DebtCard from '@/components/Debts/DebtCard.vue';
import DebtFilterForm from '@/components/Debts/DebtFilterForm.vue';
import VIcon from '@/components/UI/VIcon.vue';
import type { Debt, DebtFormData, DebtCreateData, DebtUpdateData } from '@/composables/Debts/types';
import type { DebtFilters } from '@/components/Debts/DebtFilterForm.vue';
import { DebtStatus } from '@/composables/Debts/types';
import { useDebtsRequests } from '@/composables/Debts/requests';
import { useToastStore } from '@/store/toastsStore';
import { useCategoriesStore } from '@/store/categoriesStore';
import { useDebtsBalanceStore } from '@/store/debtsBalanceStore';
import { arrowDownLeft, arrowUpRight, plus, arrowLeft, warning, filter } from '@/assets/icons';
import router from '@/router/router';
import { formatAmount } from '@/utils';

const { getDebts, addDebt: addDebtRequest, updateDebt: updateDebtRequest, deleteDebt: deleteDebtRequest, markDebtAsPaid: markDebtAsPaidRequest } = useDebtsRequests();
const $toast = useToastStore();
const { loadCategories } = useCategoriesStore();
const debtsBalanceStore = useDebtsBalanceStore();
const { balance } = storeToRefs(debtsBalanceStore);
const { loadDebtBalance } = debtsBalanceStore;

const debts = ref<Debt[]>([]);
const drawerVisible = ref(false);
const editingDebt = ref<Debt | null>(null);
const loading = ref(false);

const filterDrawerVisible = ref(false);
const currentFilters = ref<DebtFilters | undefined>(undefined);

const totalBorrowed = computed(() => {
    return balance.value ? parseFloat(balance.value.i_owe_total) : 0;
});

const totalLent = computed(() => {
    return balance.value ? parseFloat(balance.value.owe_me_total) : 0;
});

const sortedDebts = computed(() => {
    return [...debts.value].sort((a, b) => {
        const dateA = new Date(a.created_at).getTime();
        const dateB = new Date(b.created_at).getTime();
        return dateB - dateA;
    });
});

const filteredDebts = computed(() => {
    let filtered = sortedDebts.value;

    const type = currentFilters.value?.type;
    const status = currentFilters.value?.status;

    if (type && type !== 'all') {
        filtered = filtered.filter(debt => debt.type === type);
    }

    if (status && status !== 'all') {
        filtered = filtered.filter(debt => debt.status === status);
    }

    return filtered;
});

const formEditData = computed(() => {
    if (!editingDebt.value) return null;
    return {
        type: editingDebt.value.type,
        person_name: editingDebt.value.person_name,
        amount: parseFloat(editingDebt.value.amount),
        currency: editingDebt.value.currency,
        description: editingDebt.value.description,
        due_date: editingDebt.value.due_date,
    };
});

const convertFormDataToCreateData = (formData: DebtFormData): DebtCreateData => {
    return {
        type: formData.type,
        person_name: formData.person_name,
        amount: formData.amount,
        currency: formData.currency,
        description: formData.description,
        due_date: formData.due_date || null,
    };
};

const convertFormDataToUpdateData = (formData: DebtFormData): DebtUpdateData => {
    return {
        person_name: formData.person_name,
        amount: formData.amount,
        description: formData.description,
        status: editingDebt.value?.status || DebtStatus.OPEN,
        due_date: formData.due_date || null,
        settled_at: editingDebt.value?.settled_at || null,
    };
};

const loadDebts = async () => {
    try {
        loading.value = true;
        debts.value = await getDebts();
    } catch (error) {
        console.error('Failed to load debts:', error);
    } finally {
        loading.value = false;
    }
};

const editDebt = (debt: Debt) => {
    editingDebt.value = debt;
    drawerVisible.value = true;
};

const removeDebtHandler = async (id: string) => {
    try {
        loading.value = true;
        await deleteDebtRequest(id);
        debts.value = debts.value.filter(debt => debt.id !== id);
        await loadDebtBalance(true); // Принудительно обновляем баланс после удаления
    } catch (error) {
        $toast.error(t('toast.error'), t('debts.deleteError'));
    } finally {
        loading.value = false;
    }
};

const markAsPaid = async (id: string) => {
    try {
        loading.value = true;
        await markDebtAsPaidRequest(id);
        await loadDebts();
        await loadDebtBalance(true); // Принудительно обновляем баланс после погашения
    } catch (error) {
        $toast.error(t('toast.error'), t('debts.markPaidError'));
    } finally {
        loading.value = false;
    }
};

const handleApplyFilters = (filters: DebtFilters) => {
    currentFilters.value = filters;
};

const handleResetFilters = () => {
    currentFilters.value = undefined;
};

const handleSubmitWrapper = async (data: DebtFormData) => {
    try {
        loading.value = true;
        if (editingDebt.value) {
            const updateData = convertFormDataToUpdateData(data);
            await updateDebtRequest(editingDebt.value.id, updateData);
            editingDebt.value = null;
        } else {
            const createData = convertFormDataToCreateData(data);
            await addDebtRequest(createData);
        }
        drawerVisible.value = false;
        await loadDebts();
        await loadDebtBalance(true); // Принудительно обновляем баланс после создания/обновления
    } catch (error) {
        $toast.error(t('toast.error'), t('debts.saveError'));
    } finally {
        loading.value = false;
    }
};

const handleDrawerVisibilityChange = (value: boolean) => {
    if (!value) {
        drawerVisible.value = false;
        editingDebt.value = null;
    }
};

onBeforeMount(async () => {
    await Promise.all([
        loadDebts(),
        loadDebtBalance(), // Использует store, не будет дублировать запрос если уже загружен
        loadCategories()
    ]);
});

</script>

<style scoped lang="scss">
.debts-page {
    padding: 2.4rem;
    padding-bottom: 10rem;

    &__header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 2rem;
        gap: 1rem;
    }

    &__header-button {
        width: 3.6rem;
        height: 3.6rem;
        flex-shrink: 0;
    }


    &__balance {
        display: flex;
        gap: 1.2rem;
        margin-bottom: 2rem;

        &-item {
            flex: 1;
            padding: 1.6rem;
            border-radius: 1.6rem;
            background: var(--gold-card-bg);
            border: 1px solid var(--gold-border);
            box-shadow: var(--gold-shadow);
            display: flex;
            align-items: center;
            gap: 1.2rem;
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
        }

        &-icon {
            width: 3.6rem;
            height: 3.6rem;
            color: var(--primary-500);
            position: relative;
            z-index: 1;
            flex-shrink: 0;
        }

        &-content {
            display: flex;
            flex-direction: column;
            gap: 0.6rem;
            position: relative;
            z-index: 1;

            h5 {
                color: var(--text-color-secondary);
            }
        }
    }

    &__content {
        display: flex;
        flex-direction: column;
        gap: 1.2rem;
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
        gap: 1.2rem;
    }

    &__loading {
        display: flex;
        justify-content: center;
        padding: 4rem 2rem;
    }

    &__footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 2rem 2.4rem;
        background-color: var(--card-default);
        border-radius: 1.6rem 1.6rem 0 0;
        box-shadow: 0 0 10px 0 rgba(0, 0, 0, 0.25);
        z-index: 10;
    }
}
</style>
