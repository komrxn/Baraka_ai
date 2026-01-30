<template>
    <VDrawer v-model:visible="localVisible" @update:visible="handleVisibilityChange">
        <template #header>
            <h2 class="transaction-form__title">{{ isEditMode ? t('transactions.editTransaction') :
                t('transactions.addTransaction') }}</h2>
        </template>

        <VForm @submit-form="handleSubmit" class="transaction-form__form-wrapper">
            <div class="transaction-form__form">
                <div class="transaction-form__form-section">
                    <VSelect v-model="formData.type" :options="typeOptions" option-label="label" option-value="value"
                        :placeholder="t('transactions.selectType')" :label="t('transactions.typeLabel')"
                        :rules="typeRules" size="small" class="font-14-r" />
                </div>

                <div class="transaction-form__form-section">
                    <VInputNumber :model-value="(formData.amount ?? undefined) as number | undefined"
                        @update:model-value="val => formData.amount = (val ?? null) as number | null" class="font-14-r"
                        :min="0" :max-fraction-digits="2" :suffix="` ${formData.currency.toUpperCase()}`"
                        placeholder="0" :label="t('transactions.amount')" :rules="amountRules" />
                </div>

                <div class="transaction-form__form-section">
                    <VSelect v-model="formData.currency" :options="currencyOptions" option-label="label"
                        option-value="value" :placeholder="t('transactions.selectCurrency')"
                        :label="t('debts.currency')" :rules="currencyRules" size="small" class="font-14-r" />
                </div>

                <div class="transaction-form__form-section">
                    <VSelect v-model="formData.category_id" filter :empty-filter-message="t('common.noResults')"
                        :options="filteredCategoriesOptions" option-label="name" option-value="id"
                        :placeholder="t('transactions.selectCategory')" :label="t('transactions.category')" size="small"
                        class="font-14-r" />
                </div>

                <div class="transaction-form__form-section">
                    <VInputText v-model="formData.description" :placeholder="t('transactions.descriptionOptional')"
                        :label="t('transactions.description')" size="small" class="font-14-r" />
                </div>

                <div class="transaction-form__form-section">
                    <VInputText v-model="formData.transaction_date" type="datetime-local"
                        :label="t('transactions.date')" size="small" class="font-14-r" />
                </div>
            </div>

            <div class="transaction-form__footer">
                <Button :label="isEditMode ? t('common.save') : t('transactions.addTransaction')" type="submit" fluid
                    severity="primary" class="transaction-form__submit" />
            </div>
        </VForm>
    </VDrawer>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { storeToRefs } from 'pinia';
import { Button } from 'primevue';
import VDrawer from '@/components/UI/VDrawer.vue';
import VForm from '@/components/Form/VForm.vue';
import VInputText from '@/components/Form/VInputText.vue';
import VInputNumber from '@/components/Form/VInputNumber.vue';
import VSelect from '@/components/Form/VSelect.vue';
import type { FormRule } from '@/composables/Form/types';
import type { TransactionFormData, Transaction, TransactionType, Currency } from '@/composables/Transactions/types';
import { useCategoriesStore } from '@/store/categoriesStore';
import { CategoryType } from '@/composables/Categories/types';

const { t } = useI18n();

const categoriesStore = useCategoriesStore();
const { loadCategories } = categoriesStore;

onMounted(async () => {
    await loadCategories();
});

const props = withDefaults(
    defineProps<{
        visible: boolean;
        editData?: Transaction | null;
    }>(),
    {
        editData: null,
    }
);

const emit = defineEmits<{
    (e: 'update:visible', value: boolean): void;
    (e: 'submit', data: TransactionFormData): void;
}>();

const { categories } = storeToRefs(useCategoriesStore());

const localVisible = ref(props.visible);
const isEditMode = computed(() => !!props.editData);

/**
 * Преобразует datetime в формат для input type="datetime-local" (YYYY-MM-DDTHH:mm)
 */
const formatDatetimeToLocal = (datetimeString: string): string => {
    if (!datetimeString) {
        return '';
    }
    // Если строка содержит T, берем только часть до секунд
    if (datetimeString.includes('T')) {
        return datetimeString.substring(0, 16); // YYYY-MM-DDTHH:mm
    }
    // Если только дата, добавляем текущее время
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    return `${datetimeString}T${hours}:${minutes}`;
};

/**
 * Преобразует формат datetime-local в формат для API (YYYY-MM-DDTHH:mm:ss)
 */
const formatLocalToDatetime = (localString: string): string => {
    if (!localString) {
        return new Date().toISOString();
    }
    // Если уже есть секунды, возвращаем как есть
    if (localString.length >= 19) {
        return localString;
    }
    // Добавляем секунды
    return `${localString}:00`;
};

const formData = ref<Omit<TransactionFormData & { transaction_date: string }, 'amount'> & { amount: number | null }>({
    type: 'expense' as TransactionType,
    amount: null,
    currency: 'uzs' as Currency,
    description: '',
    category_id: '',
    transaction_date: formatDatetimeToLocal(new Date().toISOString()),
});

const typeOptions = computed(() => [
    { label: t('transactions.income'), value: 'income' as TransactionType },
    { label: t('transactions.expense'), value: 'expense' as TransactionType },
]);

const currencyOptions = computed(() => [
    { label: 'UZS', value: 'uzs' as Currency },
    { label: 'USD', value: 'usd' as Currency },
    { label: 'EUR', value: 'eur' as Currency },
    { label: 'RUB', value: 'rub' as Currency },
]);

const filteredCategoriesOptions = computed(() => {
    if (!formData.value.type) {
        return categories.value;
    }
    const categoryType = formData.value.type === 'income' ? CategoryType.INCOME : CategoryType.EXPENSE;
    return categories.value.filter(cat => cat.type === categoryType);
});

watch(() => props.visible, (newValue) => {
    localVisible.value = newValue;
    if (newValue && props.editData) {
        formData.value = {
            type: props.editData.type,
            amount: parseFloat(props.editData.amount),
            currency: props.editData.currency,
            description: props.editData.description || '',
            category_id: props.editData.category_id || '',
            transaction_date: formatDatetimeToLocal(props.editData.transaction_date),
        };
    } else if (!newValue) {
        resetForm();
    }
});

watch(() => props.editData, (newData) => {
    if (newData && localVisible.value) {
        formData.value = {
            type: newData.type,
            amount: parseFloat(newData.amount),
            currency: newData.currency,
            description: newData.description || '',
            category_id: newData.category_id || '',
            transaction_date: formatDatetimeToLocal(newData.transaction_date),
        };
    }
});

// Сбрасываем категорию при изменении типа транзакции, если текущая категория не подходит
watch(() => formData.value.type, (newType) => {
    if (newType && formData.value.category_id) {
        const category = categories.value.find(cat => cat.id === formData.value.category_id);
        if (category) {
            const categoryType = newType === 'income' ? CategoryType.INCOME : CategoryType.EXPENSE;
            if (category.type !== categoryType) {
                formData.value.category_id = '';
            }
        }
    }
});

const handleVisibilityChange = (value: boolean) => {
    localVisible.value = value;
    emit('update:visible', value);
    if (!value) {
        resetForm();
    }
};

const typeRules: FormRule<string | number>[] = [
    (value) => {
        if (!value) return t('transactions.selectType');
        return true;
    },
];

const amountRules: FormRule<number | null | undefined>[] = [
    (value) => {
        if (!value || value <= 0) return t('limits.amountGreaterThanZero');
        return true;
    },
];

const currencyRules: FormRule<string | number>[] = [
    (value) => {
        if (!value) return t('transactions.selectCurrency');
        return true;
    },
];

const resetForm = () => {
    formData.value = {
        type: 'expense' as TransactionType,
        amount: null,
        currency: 'uzs' as Currency,
        description: '',
        category_id: '',
        transaction_date: formatDatetimeToLocal(new Date().toISOString()),
    };
};

const handleSubmit = () => {
    // Если amount пустой, отправляем 0
    const submitData: TransactionFormData = {
        ...formData.value,
        amount: formData.value.amount ?? 0,
        transaction_date: formatLocalToDatetime(formData.value.transaction_date),
    };
    emit('submit', submitData);
    localVisible.value = false;
    emit('update:visible', false);
    resetForm();
};

</script>

<style scoped lang="scss">
.transaction-form {
    &__form-wrapper {
        display: flex;
        flex-direction: column;
        height: 100%;
    }

    &__title {
        font: var(--font-20-b);
        color: var(--text-color);
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
