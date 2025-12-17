<script lang="ts" setup>
import { onBeforeMount, ref } from 'vue';
import { useThemeMode } from '@/composables/UI/';
import AppLayout from '@/layouts/AppLayout.vue';
import TelegramRequired from '@/components/TelegramRequired.vue';
import { getCurrentLocale, setCurrentLocale } from '@/plugins/i18n/models';
import { isTelegramWebApp } from '@/telegramAuth';
// import { usePageTransitionStore } from '@/store/pageTransitionStore.ts';

const { setTheme } = useThemeMode();

const isTelegramMode = ref(false);
const hasToken = ref(false);

onBeforeMount(() => {
  setCurrentLocale(getCurrentLocale());
  setTheme();

  // Check if in Telegram WebApp
  isTelegramMode.value = isTelegramWebApp();
  hasToken.value = !!localStorage.getItem('access_token');

  // TEMPORARY: Allow testing without Telegram
  hasToken.value = true;
});

// const pageTransition = usePageTransitionStore();
</script>

<template>
  <!-- Show Telegram required message if not in Telegram -->
  <TelegramRequired v-if="!isTelegramMode && !hasToken" />

  <!-- Main app if in Telegram or has token -->
  <AppLayout v-else>
    <router-view v-slot="{ Component, route }">
      <!-- <transition :name="pageTransition.transitionName"> -->
      <component :is="Component" :key="route.path" />
      <!-- </transition> -->
    </router-view>
  </AppLayout>
</template>

<style scoped lang="scss"></style>
