<script lang="ts" setup>
import { Button } from 'primevue';
import { useRouter } from 'vue-router';
import { backArrow } from '@/assets/icons';

const $router = useRouter();
</script>

<template>
  <div class="error-page">
    <h1 class="font-30-b">
      Not found 404
    </h1>

    <Button label="Back to main" text size="large" :icon="backArrow" @click="$router.push({ name: 'main' })" />
  </div>
</template>

<style scoped lang="scss">
.error-page {
  --p-button-gap: 1.2rem;

  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 1.2rem;

  :deep(.p-button-icon-svg) {
    height: 1.6rem;
  }
}
</style>
