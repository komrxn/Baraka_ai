<script setup lang="ts">
import type { InputNumberProps } from 'primevue';
import type { IEmits, InputFieldProps } from '@/composables/Form/types';
import { InputNumber } from 'primevue';
import FormLabel from '@/components/Form/FormLabel.vue';

import { useFormField } from '@/composables/Form';

const props = defineProps<InputFieldProps<number | null | undefined, InputNumberProps>>();
const emit = defineEmits<IEmits<number | null | undefined>>();

const { val, fieldValid, errorMessage } = useFormField<number | null | undefined, InputNumberProps>(props, emit);
</script>

<template>
  <FormLabel :label="props.label" :error-message="!fieldValid ? errorMessage : ''" :loading="loading">
    <InputNumber
      v-bind="{ ...props, ...$attrs }"
      :model-value="val ?? undefined"
      :invalid="!fieldValid"
      :disabled="loading"
      locale="ru-RU"
      @input="$val => val = ($val.value ?? null) as number | null | undefined"
    />
  </FormLabel>
</template>

<style scoped lang="scss"></style>
