<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { dollar, home } from '@/assets/icons';
import VIcon from '@/components/UI/VIcon.vue';

const route = useRoute();
const { t } = useI18n();

const navItems = computed(() => [
    {
        name: 'main',
        title: t('main.title'),
        icon: home,
        path: '/',
    },
    {
        name: 'transactions',
        title: t('transactions.title'),
        icon: dollar,
        path: '/transactions',
    },
]);

const isActive = (path: string) => {
    return route.path === path;
};

const showBottomBar = computed(() => {
    return route.name === 'main' || route.name === 'transactions';
});
</script>

<template>
    <div class="app-inner" :class="{ 'app-inner--with-bottom-bar': showBottomBar }">
        <slot />
        <nav v-if="showBottomBar" class="bottom-bar">
            <router-link v-for="item in navItems" :key="item.name" :to="item.path" class="bottom-bar__item"
                :class="{ 'bottom-bar__item--active': isActive(item.path) }">
                <VIcon :icon="item.icon" class="bottom-bar__icon" />
                <span class="bottom-bar__label font-12-r">{{ item.title }}</span>
            </router-link>
        </nav>
    </div>
</template>

<style scoped lang="scss">
.app-inner {
    width: 100%;
    display: flex;
    flex-direction: column;
    position: relative;
    padding-bottom: 8rem;
}

.bottom-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    display: flex;
    justify-content: space-around;
    align-items: center;
    background: var(--card-default, var(--secondary-50));
    border-top: 1px solid var(--gold-border);
    padding: 1.2rem 2rem;
    padding-bottom: calc(1.2rem + env(safe-area-inset-bottom));
    box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);
    z-index: 100;
    backdrop-filter: blur(10px);
    background: color-mix(in srgb, var(--card-default, var(--secondary-50)) 95%, transparent);

    &__item {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 0.4rem;
        padding: 0.8rem 1.6rem;
        border-radius: var(--radius-m);
        text-decoration: none;
        color: var(--text-color-secondary);
        transition: var(--transition-fast);
        flex: 1;
        max-width: 12rem;

        &:hover {
            background: color-mix(in srgb, var(--primary-500) 10%, transparent);
        }

        &--active {
            color: var(--primary-500);

            .bottom-bar__icon {
                color: var(--primary-500);
            }

            .bottom-bar__label {
                color: var(--primary-500);
            }
        }
    }

    &__icon {
        width: 2.4rem;
        height: 2.4rem;
        color: currentColor;
        transition: var(--transition-fast);

        :deep(svg) {
            width: 100%;
            height: 100%;
        }
    }

    &__label {
        color: currentColor;
        transition: var(--transition-fast);
    }
}
</style>
