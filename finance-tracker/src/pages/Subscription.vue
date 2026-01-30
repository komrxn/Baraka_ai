<template>
    <div class="subscription-page">
        <div class="subscription-page__header">
            <Button :icon="arrowLeft" severity="secondary" @click="router.back()"
                class="subscription-page__header-button" />
            <h1 class="">{{ t('subscription.title') }}</h1>
            <div class="subscription-page__header-empty" />
        </div>

        <div class="subscription-page__content">
            <!-- Иконка и описание -->
            <div class="subscription-page__intro">
                <div class="subscription-page__icon">
                    <VIcon icon="👑" class="subscription-page__icon-svg" />
                </div>
                <h2 class="subscription-page__intro-title">{{ t('subscription.introTitle') }}</h2>
                <p class="subscription-page__intro-subtitle">{{ t('subscription.introSubtitle') }}</p>
            </div>

            <!-- Список функций -->
            <div class="subscription-page__features">
                <div class="subscription-page__feature">
                    <div class="subscription-page__feature-icon subscription-page__feature-icon--purple">
                        <VIcon icon="⚡" class="subscription-page__feature-icon-svg" />
                    </div>
                    <div class="subscription-page__feature-content">
                        <h3 class="subscription-page__feature-title">{{ t('subscription.features.aiAnalytics.title') }}
                        </h3>
                        <p class="subscription-page__feature-description">{{
                            t('subscription.features.aiAnalytics.description') }}</p>
                    </div>
                </div>

                <div class="subscription-page__feature">
                    <div class="subscription-page__feature-icon subscription-page__feature-icon--yellow">
                        <VIcon icon="🎯" class="subscription-page__feature-icon-svg" />
                    </div>
                    <div class="subscription-page__feature-content">
                        <h3 class="subscription-page__feature-title">{{ t('subscription.features.categoryLimits.title')
                            }}</h3>
                        <p class="subscription-page__feature-description">{{
                            t('subscription.features.categoryLimits.description') }}</p>
                    </div>
                </div>

                <div class="subscription-page__feature">
                    <div class="subscription-page__feature-icon subscription-page__feature-icon--green">
                        <VIcon icon="⚡" class="subscription-page__feature-icon-svg" />
                    </div>
                    <div class="subscription-page__feature-content">
                        <h3 class="subscription-page__feature-title">{{
                            t('subscription.features.unlimitedTransactions.title') }}</h3>
                        <p class="subscription-page__feature-description">{{
                            t('subscription.features.unlimitedTransactions.description') }}</p>
                    </div>
                </div>
            </div>

            <!-- Планы подписки -->
            <div class="subscription-page__plans">
                <div v-for="plan in plans" :key="plan.id" class="subscription-page__plan"
                    :class="{ 'subscription-page__plan--selected': selectedPlan === plan.id }"
                    @click="selectPlan(plan.id)">
                    <div v-if="plan.badge" class="subscription-page__plan-badge">
                        {{ plan.badge }}
                    </div>
                    <div class="subscription-page__plan-content">
                        <h3 class="subscription-page__plan-title">{{ plan.title }}</h3>
                        <p class="subscription-page__plan-subtitle">{{ plan.subtitle }}</p>
                        <div v-if="plan.bonus" class="subscription-page__plan-bonus">
                            <VIcon :icon="successIcon" class="subscription-page__plan-check" />
                            <span>{{ plan.bonus }}</span>
                        </div>
                        <div class="subscription-page__plan-price">
                            <span class="subscription-page__plan-amount">{{ plan.price }}</span>
                            <span class="subscription-page__plan-currency">{{ plan.currency }}</span>
                        </div>
                        <p class="subscription-page__plan-period">{{ plan.period }}</p>
                    </div>
                </div>
            </div>

            <!-- Информация об отмене -->
            <div class="subscription-page__info">
                <p class="subscription-page__info-text">{{ t('subscription.billingInfo') }}</p>
                <div class="subscription-page__info-item">
                    <VIcon :icon="successIcon" class="subscription-page__info-check" />
                    <span>{{ t('subscription.cancelAnytime') }}</span>
                </div>
            </div>

            <div v-if="!isTrialUsed && !hasActiveSubscription" class="subscription-page__button-container">
                <Button label="Start Free Trial (3 days)" severity="secondary" fluid class="subscription-page__button"
                    :loading="loading" @click="handleActivateTrial" />
            </div>

            <!-- Кнопка подписки -->
            <div class="subscription-page__button-container">
                <Button :label="t('subscription.subscribeButton', { price: selectedPlanPrice })" fluid
                    class="subscription-page__button" :loading="loading" @click="handleSubscribe" />

            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { Button } from 'primevue';
import VIcon from '@/components/UI/VIcon.vue';
import successIcon from '@/assets/icons/status/success.svg?raw';
import { arrowLeft } from '@/assets/icons';
import router from '@/router/router';
import subscriptionApi from '@/api/subscription';
import { useToastStore } from '@/store/toastsStore';

const { t } = useI18n();
const toast = useToastStore();

const loading = ref(false);
const isTrialUsed = ref(false);
const hasActiveSubscription = ref(false);

const selectedPlan = ref<string>('annual');

const plans = computed(() => [
    {
        id: 'monthly',
        title: t('subscription.plans.monthly.title'),
        subtitle: t('subscription.plans.monthly.subtitle'),
        price: '34 990',
        currency: 'UZS',
        period: t('subscription.plans.monthly.period'),
        badge: null,
        bonus: null,
    },
    {
        id: 'quarterly',
        title: t('subscription.plans.quarterly.title'),
        subtitle: t('subscription.plans.quarterly.subtitle'),
        price: '56 990',
        currency: 'UZS',
        period: t('subscription.plans.quarterly.period'),
        badge: null,
        bonus: null,
    },
    {
        id: 'annual',
        title: t('subscription.plans.annual.title'),
        subtitle: t('subscription.plans.annual.subtitle'),
        price: '199 900',
        currency: 'UZS',
        period: t('subscription.plans.annual.period'),
        badge: t('subscription.plans.annual.badge'),
        bonus: t('subscription.plans.annual.bonus'),
    },
]);

const selectedPlanPrice = computed(() => {
    const plan = plans.value.find(p => p.id === selectedPlan.value);
    return plan ? `${plan.price} ${plan.currency}` : '';
});

const selectPlan = (planId: string) => {
    selectedPlan.value = planId;
};

const handleSubscribe = async () => {
    loading.value = true;
    try {
        const { data } = await subscriptionApi.generatePaymentLink(selectedPlan.value);
        if (data.url) {
            window.location.href = data.url;
        }
    } catch (error) {
        toast.error(t('subscription.subscribeError'));
    } finally {
        loading.value = false;
    }
};

const handleActivateTrial = async () => {
    loading.value = true;
    try {
        await subscriptionApi.activateTrial();
        toast.success(t('subscription.trialActivated'));
        await checkStatus();
    } catch (error) {
        console.error("Trial error:", error);
    } finally {
        loading.value = false;
    }
}

const checkStatus = async () => {
    try {
        const { data } = await subscriptionApi.getStatus();
        isTrialUsed.value = data.is_trial_used;
        hasActiveSubscription.value = data.is_active;
    } catch (e) {
        console.error("Status check failed", e);
    }
}

onMounted(() => {
    checkStatus();
});
</script>

<style scoped lang="scss">
.subscription-page {
    width: 100%;
    padding: 2.4rem;
    padding-bottom: 10rem;
    min-height: 100dvh;
    display: flex;
    flex-direction: column;

    &__header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 2rem;
    }

    &__header-button {
        width: 3.6rem;
        height: 3.6rem;
    }

    &__header-empty {
        width: 3.6rem;
        height: 3.6rem;
    }

    &__content {
        display: flex;
        flex-direction: column;
        gap: 2.4rem;
        flex: 1;
    }

    &__intro {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        gap: 1.2rem;
    }

    &__icon {
        width: 8rem;
        height: 8rem;
        border-radius: 2rem;
        background: var(--card-default);
        border: 1px solid var(--border-medium);
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 0.8rem;
        position: relative;
        overflow: hidden;

        &::before {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: 2rem;
            background: transparent;
            pointer-events: none;
        }
    }

    &__icon-svg {
        font-size: 4rem;
    }

    &__intro-title {
        font: var(--font-24-b);
        color: var(--text-color);
        margin: 0;
    }

    &__intro-subtitle {
        font: var(--font-14-r);
        color: var(--text-color-secondary);
        margin: 0;
        opacity: 0.8;
    }

    &__features {
        display: flex;
        flex-direction: column;
        gap: 1.2rem;
    }

    &__feature {
        display: flex;
        gap: 1.2rem;
        padding: 1.6rem;
        background: var(--card-default);
        border-radius: 1.6rem;
        border: 1px solid var(--border-light);
    }

    &__feature-icon {
        width: 4.8rem;
        height: 4.8rem;
        border-radius: 1.2rem;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;

        &--purple {
            background: linear-gradient(135deg, rgba(147, 51, 234, 0.2) 0%, rgba(147, 51, 234, 0.1) 100%);
        }

        &--yellow {
            background: linear-gradient(135deg, rgba(234, 179, 8, 0.2) 0%, rgba(234, 179, 8, 0.1) 100%);
        }

        &--green {
            background: var(--card-default);
            border: 1px solid var(--border-medium);
        }
    }

    &__feature-icon-svg {
        font-size: 2.4rem;
    }

    &__feature-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
    }

    &__feature-title {
        font: var(--font-16-b);
        color: var(--text-color);
        margin: 0;
    }

    &__feature-description {
        font: var(--font-14-r);
        color: var(--text-color-secondary);
        margin: 0;
        line-height: 1.5;
    }

    &__plans {
        display: flex;
        flex-direction: column;
        gap: 1.2rem;
    }

    &__plan {
        position: relative;
        padding: 1.6rem;
        background: var(--card-default);
        border-radius: 1.6rem;
        border: 2px solid var(--border-light);
        cursor: pointer;
        transition: all 0.3s ease;

        &:hover {
            border-color: var(--border-medium);
            transform: translateY(-2px);
        }

        &--selected {
            background: var(--card-default);
            border-color: var(--border-medium);
            box-shadow: none;
            position: relative;
            overflow: hidden;

            &::before {
                content: '';
                position: absolute;
                inset: 0;
                border-radius: 1.6rem;
                background: transparent;
                pointer-events: none;
            }
        }
    }

    &__plan-badge {
        position: absolute;
        top: 1.2rem;
        right: 1.2rem;
        padding: 0.4rem 0.8rem;
        background: linear-gradient(135deg, rgba(147, 51, 234, 0.8) 0%, rgba(147, 51, 234, 0.6) 100%);
        border-radius: 1.2rem;
        font: var(--font-12-b);
        color: var(--white);
    }

    &__plan-content {
        display: flex;
        flex-direction: column;
        gap: 0.8rem;
        position: relative;
        z-index: 1;
    }

    &__plan-title {
        font: var(--font-18-b);
        color: var(--text-color);
        margin: 0;
    }

    &__plan-subtitle {
        font: var(--font-14-r);
        color: var(--text-color-secondary);
        margin: 0;
    }

    &__plan-bonus {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        font: var(--font-14-r);
        color: var(--text-color);
    }

    &__plan-check {
        width: 1.6rem;
        height: 1.6rem;
        flex-shrink: 0;
        color: var(--text-color);
    }

    &__plan-price {
        display: flex;
        align-items: baseline;
        gap: 0.4rem;
        margin-top: 0.4rem;
    }

    &__plan-amount {
        font: var(--font-24-b);
        color: var(--text-color);
    }

    &__plan-currency {
        font: var(--font-14-r);
        color: var(--text-color-secondary);
    }

    &__plan-period {
        font: var(--font-14-r);
        color: var(--text-color-secondary);
        margin: 0;
    }

    &__info {
        display: flex;
        flex-direction: column;
        gap: 1.2rem;
        padding: 1.6rem;
        background: var(--card-default);
        border-radius: 1.6rem;
        border: 1px solid var(--border-light);
    }

    &__info-text {
        font: var(--font-14-r);
        color: var(--text-color);
        margin: 0;
    }

    &__info-item {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        font: var(--font-14-r);
        color: var(--text-color);
    }

    &__info-check {
        width: 1.6rem;
        height: 1.6rem;
        flex-shrink: 0;
        color: var(--text-color);
    }

    &__button {
        padding: 1.6rem 2rem;
        font: var(--font-16-b);
        background: var(--primary-500) !important;
        border-top: 1px solid var(--border-medium) !important;
        color: var(--text-color) !important;
        box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.2);
    }

    &__button-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 1.6rem;
        z-index: 100;
        background: var(--card-default);
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    &__trial-button {
        padding: 1.6rem 2rem;
        font: var(--font-16-b);
        border: 1px solid var(--border-medium) !important;
    }

    &__trial-container {
        padding: 0 1.6rem 1.6rem 1.6rem;
        position: fixed;
        bottom: 8rem;
        /* Place above the subscribe button area if separate, but better to put locally inside container */
        left: 0;
        right: 0;
        z-index: 99;
    }
}
</style>
