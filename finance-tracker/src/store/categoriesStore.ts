import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { Category, GetCategoriesParams, CategoryFormData, CategoryCreateData, CategoryUpdateData } from '@/composables/Categories/types';
import { CategoryType } from '@/composables/Categories/types';
import { useCategoriesRequests } from '@/composables/Categories/requests';

export const useCategoriesStore = defineStore('categories', () => {
    const categories = ref<Category[]>([]);
    const loading = ref<boolean>(false);
    const isLoaded = ref<boolean>(false);
    const currentFilter = ref<GetCategoriesParams | undefined>(undefined);
    const drawerVisible = ref(false);
    const editingCategory = ref<Category | null>(null);
    const { getCategories: fetchCategories, createCategory: createCategoryRequest, updateCategory: updateCategoryRequest, deleteCategory: deleteCategoryRequest } = useCategoriesRequests();

    const convertFormDataToCreateData = (formData: CategoryFormData): CategoryCreateData => {
        // Генерируем slug из name
        const slug = formData.name
            .toLowerCase()
            .replace(/[^a-z0-9а-яё]+/gi, '-')
            .replace(/(^-|-$)/g, '');

        return {
            name: formData.name,
            slug: slug,
            type: formData.type || CategoryType.EXPENSE,
            icon: formData.icon || '',
            color: formData.color || '#2ECC71',
        };
    };

    const convertFormDataToUpdateData = (formData: CategoryFormData): CategoryUpdateData => {
        return {
            name: formData.name,
            icon: formData.icon || '',
            color: formData.color || '#000000',
        };
    };

    const loadCategories = async (params?: GetCategoriesParams, force = false) => {
        // Проверяем, изменился ли фильтр
        const filterChanged = JSON.stringify(currentFilter.value) !== JSON.stringify(params);

        // Если данные уже загружены, фильтр не изменился и не требуется принудительная загрузка, не загружаем заново
        if (!force && isLoaded.value && !filterChanged && categories.value.length > 0) {
            return;
        }

        if (loading.value) return;
        try {
            loading.value = true;
            currentFilter.value = params;
            categories.value = await fetchCategories(params);
            isLoaded.value = true;
        } catch (error) {
            console.error('Failed to load categories:', error);
        } finally {
            loading.value = false;
        }
    };

    const loadCategoriesByType = async (type: CategoryType | null, force = false) => {
        const params: GetCategoriesParams | undefined = type ? { type } : undefined;
        await loadCategories(params, force);
    };

    const addCategory = async (categoryData: Parameters<typeof createCategoryRequest>[0]) => {
        try {
            loading.value = true;
            await createCategoryRequest(categoryData);
            // Перезагружаем список с текущим фильтром, чтобы получить полные данные с сервера
            categories.value = await fetchCategories(currentFilter.value);
        } catch (error) {
            console.error('Failed to create category:', error);
            throw error;
        } finally {
            loading.value = false;
        }
    };

    const updateCategory = async (id: string, categoryData: Parameters<typeof updateCategoryRequest>[1]) => {
        try {
            loading.value = true;
            await updateCategoryRequest(id, categoryData);
            // Перезагружаем список с текущим фильтром, чтобы получить полные данные с сервера
            categories.value = await fetchCategories(currentFilter.value);
        } catch (error) {
            console.error('Failed to update category:', error);
            throw error;
        } finally {
            loading.value = false;
        }
    };

    const removeCategory = async (id: string) => {
        try {
            loading.value = true;
            await deleteCategoryRequest(id);
            // Перезагружаем список с текущим фильтром
            categories.value = await fetchCategories(currentFilter.value);
        } catch (error) {
            console.error('Failed to delete category:', error);
            throw error;
        } finally {
            loading.value = false;
        }
    };

    const editCategory = (category: Category) => {
        editingCategory.value = category;
        drawerVisible.value = true;
    };

    const handleSubmit = async (formData: CategoryFormData) => {
        if (editingCategory.value) {
            const updateData = convertFormDataToUpdateData(formData);
            await updateCategory(editingCategory.value.id, updateData);
            editingCategory.value = null;
        } else {
            const createData = convertFormDataToCreateData(formData);
            await addCategory(createData);
        }
        drawerVisible.value = false;
    };

    const closeForm = () => {
        drawerVisible.value = false;
        editingCategory.value = null;
    };

    const refreshCategories = async () => {
        await loadCategories(currentFilter.value, true);
    };

    return {
        categories,
        loading,
        isLoaded,
        drawerVisible,
        editingCategory,
        loadCategories,
        loadCategoriesByType,
        addCategory,
        removeCategory,
        updateCategory,
        editCategory,
        handleSubmit,
        closeForm,
        refreshCategories,
    };
});
