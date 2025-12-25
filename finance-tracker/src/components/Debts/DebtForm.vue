<template>
    <VDrawer v-model:visible="localVisible" @update:visible="handleVisibilityChange">
        <template #header>
            <h2 class="debt-form__title">{{ isEditMode ? t('debts.editDebt') : t('debts.addDebt') }}</h2>
        </template>

        <VForm @submit-form="handleSubmit" class="debt-form__form-wrapper">
            <div class="debt-form__form">
                <div class="debt-form__form-section">
                    <VSelect v-model="formData.type" :options="typeOptions" option-label="label" option-value="value"
                        :placeholder="t('debts.selectDebtType')" :label="t('debts.type')" :rules="typeRules"
                        size="small" class="font-14-r" />
                </div>

                <div class="debt-form__form-section">
                    <VInputText v-model="formData.person_name" :placeholder="t('debts.enterPersonName')"
                        :label="t('debts.personName')" :rules="nameRules" size="small" class="font-14-r" />
                </div>

                <div class="debt-form__form-section">
                    <VInputNumber :model-value="(formData.amount ?? undefined) as number | undefined"
                        @update:model-value="val => formData.amount = (val ?? null) as number | null" class="font-14-r"
                        :min="0" :max-fraction-digits="0" suffix=" UZS" placeholder="0" :label="t('debts.amount')"
                        :rules="amountRules" />

                </div>

                <div class="debt-form__form-section">
                    <VInputText v-model="formData.description" :placeholder="t('debts.descriptionOptional')"
                        :label="t('debts.description')" size="small" class="font-14-r" />
                </div>

                <div class="debt-form__form-section">
                    <VInputText v-model="formData.due_date" type="date" :label="t('debts.dueDateOptional')" size="small"
                        class="font-14-r" />
                </div>
            </div>

            <div class="debt-form__footer">
                <Button :label="isEditMode ? t('common.save') : t('debts.addDebt')" type="submit" fluid
                    severity="primary" class="debt-form__submit" />
            </div>
        </VForm>
    </VDrawer>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { Button } from 'primevue';
import VDrawer from '@/components/UI/VDrawer.vue';
import VForm from '@/components/Form/VForm.vue';
import VInputText from '@/components/Form/VInputText.vue';
import VInputNumber from '@/components/Form/VInputNumber.vue';
import VSelect from '@/components/Form/VSelect.vue';
import type { FormRule } from '@/composables/Form/types';
import type { DebtFormData } from '@/composables/Debts/types';
import { DebtType } from '@/composables/Debts/types';

const { t } = useI18n();

const props = withDefaults(
    defineProps<{
        visible: boolean;
        editData?: DebtFormData | null;
    }>(),
    {
        editData: null,
    }
);

const emit = defineEmits<{
    (e: 'update:visible', value: boolean): void;
    (e: 'submit', data: DebtFormData): void;
}>();

const localVisible = ref(props.visible);
const isEditMode = computed(() => !!props.editData);

const typeOptions = computed(() => [
    { label: t('debts.iOwe'), value: DebtType.I_OWE },
    { label: t('debts.oweMe'), value: DebtType.OWE_ME },
]);

watch(() => props.visible, (newValue) => {
    localVisible.value = newValue;
    if (newValue && props.editData) {
        formData.value = {
            type: props.editData.type,
            person_name: props.editData.person_name,
            amount: props.editData.amount,
            currency: props.editData.currency || 'uzs',
            description: props.editData.description || '',
            due_date: props.editData.due_date || '',
        };
    } else if (!newValue) {
        resetForm();
    }
});

watch(() => props.editData, (newData) => {
    if (newData && localVisible.value) {
        formData.value = {
            type: newData.type,
            person_name: newData.person_name,
            amount: newData.amount,
            currency: newData.currency || 'uzs',
            description: newData.description || '',
            due_date: newData.due_date || '',
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

const formData = ref<Omit<DebtFormData, 'amount'> & { amount: number | null }>({
    type: DebtType.I_OWE,
    person_name: '',
    amount: null,
    currency: 'uzs',
    description: '',
    due_date: '',
});

const nameRules: FormRule<string>[] = [
    (value) => {
        if (!value || value.trim().length === 0) return t('debts.enterPersonNameError');
        if (value.trim().length < 2) return t('debts.personNameMinLength');
        return true;
    },
];

const typeRules: FormRule<string | number>[] = [
    (value) => {
        if (!value) return t('debts.selectDebtType');
        return true;
    },
];

const amountRules: FormRule<number | null | undefined>[] = [
    (value) => {
        if (!value || value <= 0) {
            return t('limits.amountGreaterThanZero');
        }
        return true;
    },
];

const resetForm = () => {
    formData.value = {
        type: DebtType.I_OWE,
        person_name: '',
        amount: null,
        currency: 'uzs',
        description: '',
        due_date: '',
    };
};

const handleSubmit = () => {
    // Если amount пустой (null или undefined), отправляем 0
    const submitData: DebtFormData = {
        ...formData.value,
        amount: formData.value.amount ?? 0,
    };
    emit('submit', submitData);
    localVisible.value = false;
    emit('update:visible', false);
    resetForm();
};

</script>

<style scoped lang="scss">
.debt-form {
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
