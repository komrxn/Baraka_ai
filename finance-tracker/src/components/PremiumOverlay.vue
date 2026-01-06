<template>
    <div v-if="showOverlay" class="premium-overlay">
        <div class="premium-overlay__content">
            <div class="premium-overlay__icon">
                <VIcon icon="🔒" class="premium-overlay__icon-svg" />
            </div>
            <h2 class="premium-overlay__title gold-text">{{ t('premiumOverlay.title') }}</h2>
            <p class="premium-overlay__description">{{ t('premiumOverlay.description') }}</p>
            <div class="premium-overlay__button-container">
                <Button :label="t('premiumOverlay.activateButton')" class="premium-overlay__button"
                    @click="handleActivate" fluid />
                <Button severity="secondary" label="Назад" @click="router.back()" fluid />
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { storeToRefs } from 'pinia';
import { Button } from 'primevue';
import VIcon from '@/components/UI/VIcon.vue';
import { useUserStore } from '@/store/userStore';

const { t } = useI18n();
const router = useRouter();

const userStore = useUserStore();
const { user } = storeToRefs(userStore);

const showOverlay = computed(() => {
    return !user.value?.is_active && !user.value?.is_premium;
});

const handleActivate = () => {
    router.push({ name: 'subscription' });
};
</script>

<style scoped lang="scss">
.premium-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(8px);
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;

    &__content {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 1.6rem;
        padding: 3.2rem 2.4rem;
        max-width: 32rem;
        width: 90%;
    }

    &__icon {
        width: 8rem;
        height: 8rem;
        border-radius: 2rem;
        background: var(--gold-card-bg);
        border: 1px solid var(--gold-border);
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;

        &::before {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: 2rem;
            background: var(--gold-card-radial);
            pointer-events: none;
        }
    }

    &__icon-svg {
        font-size: 4rem;
    }

    &__title {
        font: var(--font-24-b);
        color: var(--gold-text-color);
        margin: 0;
    }

    &__description {
        font: var(--font-16-r);
        color: var(--gold-text-color);
        margin: 0;
        line-height: 1.5;
        text-align: center;
    }


    &__button-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 1.2rem;
        width: 100%;
    }
}
</style>
