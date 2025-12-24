<template>
    <VDrawer v-model:visible="localVisible" @update:visible="handleVisibilityChange">
        <template #header>
            <h2 class="limit-form__title">{{ isEditMode ? t('limits.editLimit') : t('limits.addLimit') }}</h2>
        </template>

        <VForm @submit-form="handleSubmit" class="limit-form__form-wrapper">
            <div class="limit-form__form">
                <div class="limit-form__form-section">
                    <VSelect v-model="formData.category" :options="categoriesOptions" option-label="localizedName"
                        option-value="name" :placeholder="t('limits.selectCategory')" :label="t('limits.category')"
                        :rules="categoryRules" size="small" class="font-14-r" />
                </div>

                <div class="limit-form__form-section">
                    <VInputNumber v-model="formData.budget" class="font-14-r" :min="0" :max-fraction-digits="0"
                        suffix=" UZS" placeholder="0" :label="t('limits.monthlyBudget')" :rules="budgetRules" />
                </div>

                <div class="limit-form__form-section">
                    <div class="limit-form__form-info">
                        <label class="limit-form__form-info-label">{{ t('limits.budgetPeriod') }}</label>
                        <p class="limit-form__form-info-text">
                            {{ t('limits.budgetPeriodHint', { month: currentMonth }) }}
                        </p>
                    </div>
                </div>

                <div class="limit-form__form-section">
                    <p class="limit-form__form-hint">
                        {{ t('limits.budgetHint') }}
                    </p>
                </div>
            </div>

            <div class="limit-form__footer">
                <Button :label="isEditMode ? t('limits.saveChanges') : t('limits.saveLimit')" type="submit" fluid
                    severity="primary" class="limit-form__submit" />
            </div>
        </VForm>
    </VDrawer>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useI18n } from 'vue-i18n';
import { Button } from 'primevue';
import VDrawer from '@/components/UI/VDrawer.vue';
import VForm from '@/components/Form/VForm.vue';
import VInputNumber from '@/components/Form/VInputNumber.vue';
import VSelect from '@/components/Form/VSelect.vue';
import type { FormRule } from '@/composables/Form/types';
import type { LimitFormData } from '@/composables/Limits/types';
import { useCategoriesStore } from '@/store/categoriesStore';

const { t } = useI18n();


const props = withDefaults(
    defineProps<{
        visible: boolean;
        editData?: LimitFormData | null;
    }>(),
    {
        editData: null,
    }
);

const { categories } = storeToRefs(useCategoriesStore());

const categoriesOptions = computed(() => {
    return categories.value
        .filter((cat: any) => cat.type === CategoryType.EXPENSE)
        .map((cat: any) => ({
            ...cat,
            localizedName: t(`categoryList.${cat.slug}`)
        }));
});

const emit = defineEmits<{
    (e: 'update:visible', value: boolean): void;
    (e: 'submit', data: LimitFormData | null): void;
}>();

const localVisible = ref(props.visible);

const isEditMode = computed(() => !!props.editData);

watch(() => props.visible, (newValue) => {
    localVisible.value = newValue;
    if (newValue && props.editData) {
        formData.value = {
            category: props.editData.category,
            budget: props.editData.budget,
        };
    } else if (!newValue) {
        resetForm();
    }
});

watch(() => props.editData, (newData) => {
    if (newData && localVisible.value) {
        formData.value = {
            category: newData.category,
            budget: newData.budget,
        };
    }
});

const handleVisibilityChange = (value: boolean) => {
    localVisible.value = value;
    emit('update:visible', value);
    if (!value) {
        resetForm();
    }
};

const formData = ref<LimitFormData>({
    category: undefined,
    budget: 0,
});

import { MONTHS_FULL } from '@/composables/data';
import { CategoryType } from '@/composables/Categories/types';

const currentMonth = computed(() => {
    const date = new Date();
    return `${MONTHS_FULL[date.getMonth()]} ${date.getFullYear()} г.`;
});

const categoryRules: FormRule<string | number | undefined>[] = [
    (value) => {
        if (!value) return t('limits.selectCategoryError');
        return true;
    },
];

const budgetRules: FormRule<number>[] = [
    (value) => {
        if (!value || value <= 0) return t('limits.amountGreaterThanZero');
        return true;
    },
];

const resetForm = () => {
    formData.value = {
        category: undefined,
        budget: 0,
    };
};

const handleSubmit = () => {
    emit('submit', formData.value);
    localVisible.value = false;
    emit('update:visible', false);
    resetForm();
};

</script>

<style scoped lang="scss">
.limit-form {
    &__form-wrapper {
        display: flex;
        flex-direction: column;
        height: 100%;
    }

    &__title {
        font: var(--font-20-b);
        margin: 0;
    }

    &__form {
        display: flex;
        flex-direction: column;
        gap: 1.2rem;
        padding-bottom: 1.6rem;
    }

    &__form-section {
        display: flex;
        flex-direction: column;
        gap: 0.8rem;
    }

    &__form-info {
        padding: 1.6rem;
        background-color: var(--card-default);
        border-radius: var(--radius-l);
    }

    &__form-info-label {
        font: var(--font-14-r);
        display: block;
        margin-bottom: 0.8rem;
        color: var(--text-color);
    }

    &__form-info-text {
        font: var(--font-12-r);
        color: var(--text-color-secondary);
        margin: 0;
    }

    &__form-hint {
        font: var(--font-12-r);
        color: var(--text-color-secondary);
        margin: 0;
        padding: 1.6rem;
        background-color: var(--card-default);
        border-radius: var(--radius-l);
    }

    &__footer {
        padding: 2rem 0 .6rem 0;
        border-top: 1px solid var(--border-light);
        margin-top: auto;
    }

    &__submit {
        width: 100%;
    }
}
</style>
