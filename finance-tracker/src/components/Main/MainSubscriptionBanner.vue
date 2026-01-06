<template>
    <div class="main-subscription-banner" @click="handleClick">
        <div class="main-subscription-banner__icon">
            <VIcon icon="👑" class="main-subscription-banner__icon-svg" />
        </div>
        <div class="main-subscription-banner__content">
            <h3 class="main-subscription-banner__title gold-text">{{ t('main.subscriptionBanner.title') }}</h3>
            <p class="main-subscription-banner__description">{{ t('main.subscriptionBanner.description') }}</p>
        </div>
    </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import VIcon from '@/components/UI/VIcon.vue';

const { t } = useI18n();
const router = useRouter();

const handleClick = () => {
    router.push({ name: 'subscription' });
};
</script>

<style scoped lang="scss">
.main-subscription-banner {
    display: flex;
    align-items: center;
    gap: 1.2rem;
    padding: 1.6rem;
    margin-top: 1.2rem;
    border-radius: 1.6rem;
    background: var(--gold-card-bg);
    border: 1px solid var(--gold-border);
    box-shadow: var(--gold-shadow);
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;

    &::before {
        content: '';
        position: absolute;
        inset: 0;
        border-radius: 1.6rem;
        background: var(--gold-card-radial);
        pointer-events: none;
    }

    &:hover {
        border-color: var(--gold-border-hover);
        box-shadow: var(--gold-shadow-hover);
        transform: translateY(-2px);
    }

    &__icon {
        width: 4.8rem;
        height: 4.8rem;
        border-radius: 1.2rem;
        background: linear-gradient(135deg, rgba(220, 180, 0, 0.3) 0%, rgba(220, 180, 0, 0.15) 100%);
        border: 1px solid var(--gold-border);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        position: relative;
        z-index: 1;
    }

    &__icon-svg {
        font-size: 2.4rem;
    }

    &__content {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
        position: relative;
        z-index: 1;
        min-width: 0;
    }

    &__title {
        font: var(--font-16-b);
        color: var(--text-color);
        margin: 0;
    }

    &__description {
        font: var(--font-14-r);
        color: var(--text-color-secondary);
        margin: 0;
        line-height: 1.4;
    }
}
</style>
