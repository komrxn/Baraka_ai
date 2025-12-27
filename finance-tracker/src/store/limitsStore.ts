import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Limit, LimitFormData, LimitCreateData, LimitUpdateData, GetLimitsParams } from '@/composables/Limits/types';
import { useLimitsRequests } from '@/composables/Limits/requests';

export const useLimitsStore = defineStore('limits', () => {
    const limits = ref<Limit[]>([]);
    const loading = ref<boolean>(false);
    const isLoaded = ref<boolean>(false);
    const currentFilter = ref<GetLimitsParams | undefined>(undefined);
    const drawerVisible = ref(false);
    const editingLimit = ref<Limit | null>(null);
    const { getLimits: fetchLimits, addLimit: addLimitRequest, removeLimit: removeLimitRequest, updateLimit: updateLimitRequest } = useLimitsRequests();

    const sortedLimits = computed(() => {
        return [...limits.value].sort((a, b) => {
            const dateA = new Date(a.created_at).getTime();
            const dateB = new Date(b.created_at).getTime();
            return dateB - dateA;
        });
    });

    const convertFormDataToCreateData = (formData: LimitFormData, categoryId: string): LimitCreateData => {
        const now = new Date();
        const year = now.getFullYear();
        const month = now.getMonth();

        const periodStart = new Date(year, month, 1);
        const periodEnd = new Date(year, month + 1, 0);

        return {
            category_id: categoryId,
            amount: formData.budget,
            period_start: periodStart.toISOString().split('T')[0],
            period_end: periodEnd.toISOString().split('T')[0],
        };
    };

    const convertFormDataToUpdateData = (formData: LimitFormData): LimitUpdateData => {
        const now = new Date();
        const year = now.getFullYear();
        const month = now.getMonth();

        const periodStart = new Date(year, month, 1);
        const periodEnd = new Date(year, month + 1, 0);

        return {
            amount: formData.budget,
            period_start: periodStart.toISOString().split('T')[0],
            period_end: periodEnd.toISOString().split('T')[0],
        };
    };

    const loadLimits = async (params?: GetLimitsParams, force = false) => {
        // Проверяем, изменился ли фильтр
        const filterChanged = JSON.stringify(currentFilter.value) !== JSON.stringify(params);

        // Если данные уже загружены, фильтр не изменился и не требуется принудительная загрузка, не загружаем заново
        if (!force && isLoaded.value && !filterChanged) {
            return;
        }

        if (loading.value) return;
        try {
            loading.value = true;
            currentFilter.value = params;
            limits.value = await fetchLimits(params);
            isLoaded.value = true;
        } catch (error) {
            console.error('Failed to load limits:', error);
        } finally {
            loading.value = false;
        }
    };

    const addLimit = async (limitData: LimitCreateData) => {
        try {
            loading.value = true;
            await addLimitRequest(limitData);
            // Перезагружаем список с текущим фильтром, чтобы получить полные данные с сервера
            limits.value = await fetchLimits(currentFilter.value);
        } catch (error) {
            console.error('Failed to create limit:', error);
            throw error;
        } finally {
            loading.value = false;
        }
    };

    const updateLimit = async (id: string, limitData: LimitUpdateData) => {
        try {
            loading.value = true;
            await updateLimitRequest(id, limitData);
            // Перезагружаем список с текущим фильтром, чтобы получить полные данные с сервера
            limits.value = await fetchLimits(currentFilter.value);
        } catch (error) {
            console.error('Failed to update limit:', error);
            throw error;
        } finally {
            loading.value = false;
        }
    };

    const removeLimit = async (id: string) => {
        try {
            loading.value = true;
            await removeLimitRequest(id);
            // Перезагружаем список с текущим фильтром
            limits.value = await fetchLimits(currentFilter.value);
        } catch (error) {
            console.error('Failed to delete limit:', error);
            throw error;
        } finally {
            loading.value = false;
        }
    };

    const editLimit = (limit: Limit) => {
        editingLimit.value = limit;
        drawerVisible.value = true;
    };

    const handleSubmit = async (formData: LimitFormData, categoryId: string) => {
        if (editingLimit.value) {
            const updateData = convertFormDataToUpdateData(formData);
            await updateLimit(editingLimit.value.id, updateData);
            editingLimit.value = null;
        } else {
            const createData = convertFormDataToCreateData(formData, categoryId);
            await addLimit(createData);
        }
        drawerVisible.value = false;
    };

    const closeForm = () => {
        drawerVisible.value = false;
        editingLimit.value = null;
    };

    const refreshLimits = async () => {
        await loadLimits(currentFilter.value, true);
    };

    return {
        limits,
        loading,
        isLoaded,
        drawerVisible,
        editingLimit,
        sortedLimits,
        loadLimits,
        addLimit,
        removeLimit,
        updateLimit,
        editLimit,
        handleSubmit,
        closeForm,
        convertFormDataToCreateData,
        convertFormDataToUpdateData,
        refreshLimits,
    };
});

