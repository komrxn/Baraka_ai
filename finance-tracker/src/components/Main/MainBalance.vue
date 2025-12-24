<template>
    <div class="main-balance">
        <div class="main-balance__card">
            <div class="main-balance__total">
                <div class="main-balance__total-content">
                    <h5 class="font-14-r">{{ t('main.totalBalance') }}</h5>
                    <p v-if="isVisible" class="gold-text">{{ formatAmount(balance) }} UZS</p>
                    <p v-else class="gold-text">••••••</p>
                </div>
                <VIcon :icon="isVisible ? eyeIcon : eyeClosedIcon" class="main-balance__total-icon"
                    color="var(--primary-600)" @click="toggleVisibility" />
            </div>
            <div class="main-balance__divider"></div>
            <div class="main-balance__items">
                <div class="main-balance__item">
                    <Button :icon="arrowDownLeft" severity="success" outlined class="main-balance__item-button" />
                    <div class="main-balance__item-content">
                        <h5>{{ t('main.income') }}</h5>
                        <p v-if="isVisible" class="gold-text">{{ formatAmountWithSign(income) }} UZS</p>
                        <p v-else class="gold-text">••••••</p>
                    </div>
                </div>
                <div class="main-balance__item">
                    <Button :icon="arrowUpRight" severity="danger" outlined class="main-balance__item-button" />
                    <div class="main-balance__item-content">
                        <h5>{{ t('main.expense') }}</h5>
                        <p v-if="isVisible" class="gold-text">{{ formatAmountWithSign(-expense) }} UZS</p>
                        <p v-else class="gold-text">••••••</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import { useI18n } from 'vue-i18n';
import { Button } from 'primevue';
import { arrowDownLeft, arrowUpRight, eyeIcon, eyeClosedIcon } from '@/assets/icons';
import VIcon from '../UI/VIcon.vue';
import { formatAmount, formatAmountWithSign } from '@/utils';
import { useBalanceStore } from '@/store/balanceStore';
import { useLocalStorage } from '@vueuse/core';

const { t } = useI18n();

const balanceStore = useBalanceStore();
const { balance: balanceData } = storeToRefs(balanceStore);
const { loadBalance } = balanceStore;

const isVisible = useLocalStorage('isVisibleBalance', true);

const toggleVisibility = () => {
    isVisible.value = !isVisible.value;
};

const balance = computed(() => {
    return balanceData.value ? parseFloat(balanceData.value.balance) : 0;
});

const income = computed(() => {
    return balanceData.value ? parseFloat(balanceData.value.total_income) : 0;
});

const expense = computed(() => {
    return balanceData.value ? parseFloat(balanceData.value.total_expense) : 0;
});

onMounted(async () => {
    try {
        await loadBalance({ period: 'month' });
    } catch (error) {
        console.error('Failed to load balance:', error);
    }
});
</script>

<style scoped lang="scss">
.main-balance {
    padding: 3rem 0 0 0;

    &__card {
        padding: 2rem 1.6rem;
        border-radius: 1.6rem;
        background: var(--gold-card-bg);
        border: 1px solid var(--gold-border);
        box-shadow: var(--gold-shadow);
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;

        &::before {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 60%;
            height: 100%;
            background: var(--gold-card-radial);
            pointer-events: none;
        }

        &:hover {
            border-color: var(--gold-border-hover);
            box-shadow: var(--gold-shadow-hover);
            transform: translateY(-2px);
        }
    }

    &__total {
        display: flex;
        align-items: center;
        justify-content: space-between;
        position: relative;
        z-index: 1;
        padding-bottom: 1.6rem;
    }


    &__total-icon {
        width: 2rem;
        height: 2rem;
        cursor: pointer;
    }

    &__total-content {
        display: flex;
        flex-direction: column;
        gap: 0.8rem;
        flex: 1;
        min-width: 0;

        h5 {
            color: var(--text-color-secondary);
        }

        p {
            font: var(--font-26-b);

            @include media-max($small) {
                font: var(--font-22-b);
            }
        }
    }

    &__divider {
        height: 2px;
        background: var(--gold-border);
        margin: 1rem 0;
        position: relative;
        z-index: 1;
    }

    &__card {
        @include media-max($mobile) {
            padding: 1.6rem 1.2rem;
        }
    }

    &__items {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 2rem;
        position: relative;
        z-index: 1;
        padding: 0 1rem;

        @include media-max($mobile) {
            gap: 1rem;
        }
    }

    &__item {
        padding: 1.2rem;
        display: flex;
        align-items: center;
        gap: 1rem;

        @include media-max($mobile) {
            padding: 0.8rem;
            gap: 0.8rem;
        }
    }

    &__item-content {
        display: flex;
        flex-direction: column;
        gap: 0.6rem;
        flex: 1;
        min-width: 0;

        h5 {
            color: var(--text-color-secondary);
            font: var(--font-14-r);

            @include media-max($small) {
                font: var(--font-12-r);
            }
        }

        p {
            word-break: break-word;
            overflow-wrap: break-word;
            font: var(--font-16-r);

            @include media-max($small) {
                font: var(--font-14-r);
            }
        }
    }

    &__item-button {
        align-self: flex-end;
        width: 3.6rem;
        height: 3.6rem;
        --p-button-border-radius: 50%;
        flex-shrink: 0;

        @include media-max($mobile) {
            width: 3rem;
            height: 3rem;
        }

        @include media-max($small) {
            width: 2.6rem;
            height: 2.6rem;
        }
    }
}
</style>