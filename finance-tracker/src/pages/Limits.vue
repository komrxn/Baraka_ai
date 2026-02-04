<template>
    <div class="limits-page">
        <div class="limits-page__header">
            <Button :icon="arrowLeft" severity="secondary" @click="router.back()" class="limits-page__header-button" />
            <h1 class="">{{ t('limits.title') }}</h1>
            <div class="limits-page__header-empty" />
        </div>

        <div class="limits-page__content">
            <div v-if="loading" class="limits-page__loading">
                <ProgressSpinner />
            </div>
            <div v-else-if="limits.length === 0" class="limits-page__empty">
                <div class="limits-page__empty-icon">
                    <VIcon :icon="warning" />
                </div>
                <p class="limits-page__empty-text">{{ t('limits.noLimits') }}</p>
                <p class="limits-page__empty-hint">{{ t('limits.addFirst') }}</p>
            </div>
            <div v-else class="limits-page__list">
                <LimitCard v-for="limit in sortedLimits" :key="limit.id" :limit="limit"
                    @remove="() => removeLimit(limit.id)" @edit="() => editLimit(limit)" />
            </div>
        </div>

        <div class="limits-page__footer">
            <Button :label="t('limits.addLimit')" fluid :icon="plus" @click="drawerVisible = true" />
        </div>
        <LimitForm v-model:visible="drawerVisible" :edit-data="formEditData" @submit="handleSubmit"
            @update:visible="handleDrawerVisibilityChange" />


    </div>
</template>

<script setup lang="ts">
import { computed, onBeforeMount } from 'vue';
import { storeToRefs } from 'pinia';
import { useI18n } from 'vue-i18n';
import { arrowLeft, plus, warning } from '@/assets/icons';
import router from '@/router/router';
import { Button, ProgressSpinner } from 'primevue';

const { t } = useI18n();
import LimitForm from '@/components/Limits/LimitForm.vue';
import LimitCard from '@/components/Limits/LimitCard.vue';
import VIcon from '@/components/UI/VIcon.vue';
import type { LimitFormData } from '@/composables/Limits/types';
import { useLimitsStore } from '@/store/limitsStore';
import { useCategoriesStore } from '@/store/categoriesStore';

const limitsStore = useLimitsStore();
const { limits, loading, drawerVisible, editingLimit, sortedLimits } = storeToRefs(limitsStore);
const { loadLimits, removeLimit, editLimit, handleSubmit: handleSubmitStore, closeForm } = limitsStore;

const categoriesStore = useCategoriesStore();
const { categories } = storeToRefs(categoriesStore);
const { loadCategories } = categoriesStore;

const formEditData = computed(() => {
    if (!editingLimit.value) return null;
    const category = categories.value.find((cat: any) => cat.id === editingLimit.value?.category_id);

    return {
        category: category?.name || editingLimit.value.category_name,
        budget: parseFloat(editingLimit.value.amount) || 0,
    };
});

const handleDrawerVisibilityChange = (value: boolean) => {
    if (!value) {
        closeForm();
    }
};

const handleSubmit = async (formData: LimitFormData | null) => {
    if (!formData) return;

    const category = categories.value.find((cat: any) => cat.name === formData.category);

    if (!category) {
        console.error(t('limits.categoryNotFound'));
        return;
    }

    try {
        await handleSubmitStore(formData, category.id);
    } catch (error) {
        console.error('Failed to save limit:', error);
    }
};

onBeforeMount(async () => {
    await Promise.all([
        loadLimits(),
        loadCategories()
    ]);
});
</script>

<style scoped lang="scss">
.limits-page {
    position: relative;
    padding: 2.4rem;
    padding-bottom: 10rem;

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

    &__header-empty {
        width: 3.6rem;
        height: 3.6rem;
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
        background: var(--card-default);
        border-radius: 1.6rem;
        border: 1px solid var(--border-medium);
        box-shadow: none;
        position: relative;
        overflow: hidden;

        &::before {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: 1.6rem;
            background: transparent;
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