<script setup lang="ts">
import { Button, Checkbox, InputText, Message, Select, SelectButton } from 'primevue';
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { backArrow, marker } from '@/assets/icons';
import FormLabel from '@/components/Form/FormLabel.vue';
import VForm from '@/components/Form/VForm.vue';
import VInputMask from '@/components/Form/VInputMask.vue';
import VInputNumber from '@/components/Form/VInputNumber.vue';
import VInputText from '@/components/Form/VInputText.vue';
import LangSwitcher from '@/components/UI/LangSwitcher.vue';

import { useThemeMode } from '@/composables/UI/';
import { $confirm } from '@/plugins/confirmation.ts';
import { useToastStore } from '@/store/toastsStore.ts';

const { t } = useI18n();
const $toast = useToastStore();
const $router = useRouter();
const defaultConfirm = async () => {
  const result = await $confirm.default({ title: 'toast.warn', subtitle: 'confirmations.warning' });
  if (result) {
    $toast.info('Do smth after accept.');
  }
  else {
    $toast.warning('Do smth after reject.');
  }
};
const infoConfirm = async () => {
  await $confirm.info({ title: 'toast.info', subtitle: 'confirmations.warning' });
  $toast.info('After button click. Info');
};
const successConfirm = async () => {
  await $confirm.success({ title: 'toast.success', subtitle: 'confirmations.warning' });
  $toast.success('After button click. Success');
};
const errorConfirm = async () => {
  await $confirm.error({ title: 'toast.error', subtitle: 'confirmations.warning' });
  $toast.error('After button click. Error');
};

const severities = ['error', 'secondary', 'info', 'success', 'warn', 'contrast'];

const buttonLoading = ref(true);

const text = ref('');
const text2 = ref('');
const numberFieldValue = ref(0);
const maskFieldValue = ref('');
const maskFieldValue2 = ref('');

const secondField = ref(false);

const handleSubmit = () => {
  $confirm.success({ title: 'toast.success', subtitle: 'confirmations.warning' });
};

const { modeModel, modes } = useThemeMode();
</script>

<template>
  <div class="page">
    <div style="display: flex; align-items: center; gap: 1rem; width: 100%;">
      <LangSwitcher />

      <h1> {{ t('toast.info') }} </h1>

      <div style="margin-left: auto" />
      <SelectButton v-model="modeModel" :options="modes" :allow-empty="false" size="small" />
      <SelectButton v-model="modeModel" :options="modes" :allow-empty="false" />
      <SelectButton v-model="modeModel" :options="modes" :allow-empty="false" size="large" />
    </div>

    <div style="display: flex; align-items: center; gap: 1rem;">
      <pre
        style="background: var(--black); color: var(--white); padding: 4rem; border-radius: var(--radius-l); font-size: 16px">
        {{`const getPosts = async () => {
            const { data, error } = await $axios.get('/posts', body, { loading });
            posts.value = error ? [] : data;
            postsError.value = Boolean(error);
            console.log(posts.value);
        };` }}
      </pre>

      <Button label="Check router transition" size="large"
        @click="$router.push({ name: 'status', params: { type: 'approved' } })" />
    </div>

    <hr>

    <Button label="Primary small" size="small" />
    <Button label="Primary" />
    <Button label="Primary large" size="large" />

    <Button label="Secondary small" size="small" severity="secondary" />
    <Button label="Secondary" severity="secondary" />
    <Button label="Secondary large" size="large" severity="secondary" />

    <hr>

    <Button label="svg icon" :icon="marker" severity="success" />
    <Button label="Icon no-fill" :icon="marker" icon-pos="right" severity="info" icon-class="no-fill" />
    <Button label="Icon fill-red" :icon="marker" icon-pos="top" severity="secondary" icon-color="red" />

    <Button :icon="backArrow" severity="primary" text />

    <Button label="Loading test" severity="help" :loading="buttonLoading" />
    <Button label="Loading test" severity="help" />

    <hr>

    <Button label="Default confirmation" severity="warn" @click="defaultConfirm" />
    <Button label="Info confirmation" severity="info" @click="infoConfirm" />
    <Button label="Success confirmation" severity="success" @click="successConfirm" />
    <Button label="Error confirmation" severity="danger" @click="errorConfirm" />

    <Button label="Success toast" severity="success" @click="$toast.success('success toast')" />
    <Button label="Info toast" severity="info" @click="$toast.info('info toast')" />
    <Button label="Warning toast" severity="warn" @click="$toast.warning('warning toast')" />
    <Button label="Error toast" severity="danger" @click="$toast.error('error toast')" />

    <hr>

    <Message v-for="type in severities" :key="type" :severity="type">
      {{ type }} message example
    </Message>

    <hr>

    <div class="field-group" style="align-items: center">
      <InputText placeholder="Text-field-small" size="small" />
      <InputText placeholder="Text-field-regular" />
      <InputText placeholder="Text-field-large" size="large" />

      <Select size="small" :options="severities" placeholder="Select small" />
      <Select :options="severities" placeholder="Select" />
      <Select size="large" :options="severities" placeholder="Select large" />
    </div>

    <VForm @submit-form="handleSubmit">
      <div class="form-wrapper">
        <div class="field-group">
          <VInputText v-model="text" placeholder="Text-field-1"
            :rules="[$formRules.required(), $formRules.minLength(10)]" />

          <VInputText v-if="secondField" v-model="text2" placeholder="Text-field-2" :rules="[$formRules.required()]" />
          <template v-else>
            <div class="font-16-b w-full" style="text-align: center;">
              Second field!
            </div>
          </template>
        </div>

        <div class="field-group">
          <VInputNumber v-model="numberFieldValue" :min="0" :rules="[$formRules.required(), $formRules.minValue(20)]"
            show-buttons button-layout="horizontal" placeholder="Number field" />
          <VInputNumber v-model="numberFieldValue" :min="0" :rules="[$formRules.required(), $formRules.minValue(10)]"
            show-buttons placeholder="Number field" />
        </div>

        <div class="field-group">
          <VInputMask v-model="maskFieldValue" mask="##-##-##" placeholder="Numbers with mask"
            :pt="{ root: { inputmode: 'numeric' } }" :rules="[$formRules.required()]" />
          <VInputMask v-model="maskFieldValue2" mask="@@-@@-AA" placeholder="Letters with mask" />
        </div>
        <div class="field-group">
          <FormLabel label="Show second field" for="check-1">
            <Checkbox v-model="secondField" binary input-id="check-1" />
          </FormLabel>
        </div>
      </div>
      <Button type="submit" label="Submit" fluid style="margin-top: 1.6rem" />
    </VForm>
  </div>
</template>

<style lang="scss" scoped>
.page {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: center;
  padding: 1rem;

  hr {
    width: 100%;
  }
}

.form-wrapper {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.field-group {
  display: flex;
  gap: 1rem;
}
</style>
