<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { analitcs, book, categories, rounded } from '@/assets/icons';
import VIcon from '../UI/VIcon.vue';
import { Button } from 'primevue';

const { t } = useI18n();

const items = computed(() => [
  {
    id: 4,
    title: t('analytics.title'),
    icon: analitcs,
    color: '#8b00ff',
    link: '/analytics'
  },
  {
    id: 2,
    title: t('categories.title'),
    icon: categories,
    color: 'var(--p-blue-500)',
    link: '/categories'
  },
  {
    id: 3,
    title: t('debts.title'),
    icon: book,
    color: 'var(--p-red-500)',
    link: '/debts'
  },
  {
    id: 1,
    title: t('limits.title'),
    icon: rounded,
    color: 'var(--primary-500)',
    link: '/limits'
  },
]);
//   {
//     id: 1,
//     title: 'Лимиты',
//     icon: rounded,
//     color: 'var(--primary-500)'
//   },
//   {
//     id: 2,
//     title: 'Категории',
//     icon: categories,
//     color: 'var(--primary-500)'
//   },
//   {
//     id: 3,
//     title: 'Долги',
//     icon: book,
//     color: 'var(--primary-500)'
//   },
//   {
//     id: 4,
//     title: 'Аналитика',
//     icon: analitcs,
//     color: 'var(--primary-500)'
//   }
// ];
</script>


<template>
  <div class="main-grid">
    <Button class="main-grid__item" v-for="i in items" :key="i.id" as="router-link" text :to="i.link">
      <VIcon :icon="i.icon" class="main-grid__item-icon" />
      <h1 class="font-14-r gold-text">{{ i.title }}</h1>
    </Button>
  </div>
</template>

<style scoped lang="scss">
.main-grid {
  display: flex;
  gap: 1rem;
  overflow-x: auto;
  overflow-y: hidden;
  padding-bottom: 0.5rem;
  margin: 1.4rem -2rem 0 -2rem;
  padding: 0 2rem;
  scrollbar-width: none;

  &__item {
    padding: 3rem 1.6rem;
    border-radius: 1.6rem;
    display: flex;
    align-items: center;
    flex-direction: column;
    justify-content: center;
    gap: 0.8rem;
    min-width: 120px;
    flex-shrink: 0;
    text-decoration: none;
    background: var(--gold-card-bg);
    border: 1px solid var(--gold-border);
    box-shadow: var(--gold-shadow);
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;

    &::before {
      content: '';
      position: absolute;
      inset: 0;
      border-radius: 1.6rem;
      background: var(--gold-card-radial);
      pointer-events: none;
      opacity: 0;
      transition: opacity 0.3s ease;
    }

    &:hover {
      border-color: var(--gold-border-hover);
      box-shadow: var(--gold-shadow-hover);
      transform: translateY(-2px);

      &::before {
        opacity: 1;
      }
    }
  }

  &__item-icon {
    width: 2.4rem;
    height: 2.4rem;
    // color: var(--primary-500);
    // filter: drop-shadow(0 2px 4px rgba(255, 215, 0, 0.3));

    :deep(svg) {
      width: 100%;
      height: 100%;
    }
  }
}
</style>