<script setup lang="ts">
import type { SelectProps } from 'primevue';
import type { IEmits, InputFieldProps } from '@/composables/Form/types';
import { Select } from 'primevue';
import { useI18n } from 'vue-i18n';

import FormLabel from '@/components/Form/FormLabel.vue';
import { useFormField } from '@/composables/Form';

const props = defineProps<InputFieldProps<string | number, SelectProps> & { modelValue?: string | number }>();
const emit = defineEmits<IEmits<string | number>>();

const { t } = useI18n();
const { val, fieldValid, errorMessage } = useFormField<string | number, SelectProps>(props, emit);
</script>

<template>
  <FormLabel :label="props.label" :error-message="!fieldValid ? errorMessage : ''" :loading="loading">
    <Select v-bind="{ ...props, ...$attrs }" :pt="{ emptyMessage: { class: 'font-12-r' } }" filter
      :empty-filter-message="t('common.noResults')" :model-value="val" :invalid="!fieldValid" :disabled="loading"
      @update:model-value="val = $event" />
  </FormLabel>
</template>

<style scoped lang="scss"></style>
