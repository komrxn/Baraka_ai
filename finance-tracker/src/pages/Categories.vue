<template>
    <div class="categories-page">
        <div class="categories-page__header">
            <Button :icon="arrowLeft" severity="secondary" @click="router.back()"
                class="categories-page__header-button" />
            <h1 class="">{{ t('categories.title') }}</h1>
            <div class="categories-page__header-empty" />
        </div>

        <div class="categories-page__filters">
            <SelectButton v-model="selectedType" :options="filterOptions" option-label="label" option-value="value"
                @update:model-value="handleTypeChange" :allow-empty="false" />
        </div>

        <div class="categories-page__content">
            <div v-if="loading" class="categories-page__loading">
                <ProgressSpinner />
            </div>
            <div v-else-if="filteredCategories.length === 0" class="categories-page__empty">
                <div class="categories-page__empty-icon">
                    <VIcon :icon="warning" />
                </div>
                <p class="categories-page__empty-text">
                    {{ selectedType !== 'all' ? t('categories.noCategoriesOfType') : t('categories.noCategories') }}
                </p>
                <p class="categories-page__empty-hint">
                    {{ selectedType !== 'all' ? t('categories.tryOtherType') : t('categories.addFirst') }}
                </p>
            </div>
            <div v-else class="categories-page__list">
                <CategoryCard v-for="category in filteredCategories" :key="category.id" :category="category"
                    @remove="removeCategoryHandler(category.id)" @edit="editCategory(category)" />
            </div>
        </div>

        <div class="categories-page__footer">
            <Button :label="t('categories.addCategory')" fluid :icon="plus" @click="drawerVisible = true" />
        </div>
        <CategoryForm v-model:visible="drawerVisible" :edit-data="formEditData" @submit="handleSubmitWrapper" />
    </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { storeToRefs } from 'pinia';
import { useI18n } from 'vue-i18n';
import { arrowLeft, plus, arrowUpRight, arrowDownLeft, warning } from '@/assets/icons';
import router from '@/router/router';
import { Button, SelectButton, ProgressSpinner } from 'primevue';

const { t } = useI18n();
import CategoryForm from '@/components/Categories/CategoryForm.vue';
import CategoryCard from '@/components/Categories/CategoryCard.vue';
import VIcon from '@/components/UI/VIcon.vue';
import type { Category, CategoryFormData } from '@/composables/Categories/types';
import { CategoryType } from '@/composables/Categories/types';
import { useCategoriesStore } from '@/store/categoriesStore';
import { useToastStore } from '@/store/toastsStore';
import { onBeforeMount } from 'vue';
import { useCategoryTypeFilterOptions } from '@/composables/data';

const selectedType = ref<CategoryType | 'all'>('all');
const categoriesStore = useCategoriesStore();
const { categories, drawerVisible, editingCategory, loading } = storeToRefs(categoriesStore);
const { loadCategoriesByType, removeCategory, handleSubmit: handleSubmitInStore, editCategory: editCategoryInStore } = categoriesStore;
const $toast = useToastStore();

const filterOptions = useCategoryTypeFilterOptions();

const filteredCategories = computed(() => {
    return categories.value;
});

const formEditData = computed(() => {
    if (!editingCategory.value) return null;
    return {
        id: editingCategory.value.id,
        name: editingCategory.value.name,
        type: editingCategory.value.type,
        icon: editingCategory.value.icon,
        color: editingCategory.value.color,
        isDefault: editingCategory.value.is_default,
    };
});

const editCategory = (category: Category) => {
    editCategoryInStore(category);
};

const getCategoryIcon = (type: CategoryType) => {
    switch (type) {
        case CategoryType.INCOME:
            return arrowUpRight;
        case CategoryType.EXPENSE:
            return arrowDownLeft;
        default:
            return arrowDownLeft;
    }
};

const removeCategoryHandler = async (id: string) => {
    const category = categories.value.find((cat: Category) => cat.id === id);
    if (category?.is_default) {
        $toast.warning(
            t('categories.cannotDeleteDefault'),
            t('categories.defaultCategoryWarning', { name: category.name }),
            getCategoryIcon(category.type)
        );
        return;
    }
    try {
        await removeCategory(id);
    } catch (error) {
        $toast.error(t('common.error'), t('categories.deleteError'));
    }
};

const handleSubmitWrapper = async (data: CategoryFormData) => {
    try {
        await handleSubmitInStore(data);
    } catch (error) {
        $toast.error(t('common.error'), t('categories.saveError'));
    }
};

const handleTypeChange = async (newType: CategoryType | 'all') => {
    const type = newType === 'all' ? null : newType;
    // При изменении фильтра принудительно загружаем данные
    await loadCategoriesByType(type, true);
};

onBeforeMount(async () => {
    const type = selectedType.value === 'all' ? null : selectedType.value;
    // При первой загрузке проверяем, нужно ли загружать
    await loadCategoriesByType(type, false);
});

</script>

<style scoped lang="scss">
.categories-page {
    padding: 2.4rem;
    padding-bottom: 10rem;

    &__header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 2rem;

        h1 {
            font: var(--font-24-b);
            margin: 0;
        }
    }

    &__header-button {
        width: 3.6rem;
        height: 3.6rem;
    }

    &__header-empty {
        width: 3.6rem;
        height: 3.6rem;
    }

    &__filters {
        margin-bottom: 2rem;

        :deep(.p-selectbutton) {
            width: 100%;

            .p-togglebutton {
                width: 100%;
            }
        }
    }

    &__content {
        display: flex;
        flex-direction: column;
        gap: 2rem;
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
        gap: 2rem;
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
