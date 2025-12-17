<script setup lang="ts">
import { computed, onBeforeMount } from 'vue';
import { storeToRefs } from 'pinia';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { Button } from 'primevue';
import LimitCard from '@/components/Limits/LimitCard.vue';
import VIcon from '@/components/UI/VIcon.vue';
import { useLimitsStore } from '@/store/limitsStore';
import { rounded } from '@/assets/icons';

const router = useRouter();
const { t } = useI18n();
const limitsStore = useLimitsStore();
const { limits, loading } = storeToRefs(limitsStore);
const { loadLimits } = limitsStore;

// Показываем критичные лимиты (>= 70%), если их нет - показываем любые лимиты
const criticalLimits = computed(() => {
    const critical = limits.value
        .filter(limit => limit.percentage >= 70 && !limit.is_exceeded)
        .sort((a, b) => b.percentage - a.percentage);

    // Если есть критичные лимиты, показываем только их (максимум 3)
    if (critical.length > 0) {
        return critical.slice(0, 3);
    }

    // Если критичных нет, показываем любые лимиты (максимум 3)
    return limits.value
        .sort((a, b) => b.percentage - a.percentage)
        .slice(0, 3);
});

const handleViewAll = () => {
    router.push({ name: 'limits' });
};

const handleAddLimit = () => {
    router.push({ name: 'limits' });
};

onBeforeMount(async () => {
    await loadLimits();
});
</script>

<template>
    <div class="main-limits">
        <div class="main-limits__header">
            <h1 class="font-20-b gold-text">{{ t('main.limitsTitle') }}</h1>
            <Button v-if="criticalLimits.length > 0" label="Посмотреть все" text size="small" @click="handleViewAll" />
        </div>

        <div v-if="loading" class="main-limits__loading">
            <p class="font-14-r">{{ t('common.loading') }}</p>
        </div>

        <div v-else-if="criticalLimits.length > 0" class="main-limits__list">
            <LimitCard v-for="limit in criticalLimits" :key="limit.id" hide-menu :limit="limit" :show-menu="false" />
        </div>

        <div v-else class="main-limits__empty" @click="handleAddLimit">
            <div class="main-limits__empty-icon">
                <VIcon :icon="rounded" color="var(--primary-500)" />
            </div>
            <p class="main-limits__empty-text">{{ t('main.limitsRecommendationTitle') }}</p>
            <p class="main-limits__empty-hint">{{ t('main.limitsRecommendationText') }}</p>
        </div>
    </div>
</template>

<style scoped lang="scss">
.main-limits {
    background: var(--gold-card-bg);
    padding: 1.2rem;
    border-radius: 1.6rem;
    margin-top: 1.2rem;
    border: 1px solid var(--gold-border);
    box-shadow: var(--gold-shadow);
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

    &__header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin: 0 0 2rem 0;
        position: relative;
        z-index: 1;
    }

    &__list {
        display: flex;
        flex-direction: column;
        gap: 1.2rem;
        position: relative;
        z-index: 1;
    }

    &__loading {
        display: flex;
        justify-content: center;
        padding: 2rem;
        position: relative;
        z-index: 1;
    }

    &__empty {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        cursor: pointer;
        transition: all 0.3s ease;
        position: relative;
        z-index: 1;

        &:hover {
            transform: translateY(-2px);
        }

        &-icon {
            width: 6.4rem;
            height: 6.4rem;
            margin-bottom: 1.6rem;
            position: relative;
            z-index: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            // padding: 1rem;

            :deep(span) {
                width: 100%;
                height: 100%;
                color: var(--primary-500);
                opacity: 0.8;
            }

            :deep(svg) {
                width: 100%;
                height: 100%;
            }
        }

        &-text {
            font: var(--font-18-b);
            color: var(--text-color);
            margin: 0 0 0.4rem 0;
            position: relative;
            z-index: 1;
            text-align: center;
        }

        &-hint {
            font: var(--font-14-r);
            color: var(--text-color-secondary);
            margin: 0;
            position: relative;
            z-index: 1;
            text-align: center;
        }
    }
}
</style>
