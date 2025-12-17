<template>
    <div class="settings-page">
        <div class="settings-page__header">
            <Button :icon="arrowLeft" severity="secondary" @click="router.back()"
                class="settings-page__header-button" />
            <h1 class="gold-text">{{ t('settings.title') }}</h1>
            <div class="settings-page__header-empty" />
        </div>

        <div class="settings-page__content">
            <!-- Общие настройки -->
            <div class="settings-page__section">
                <h2 class="settings-page__section-title">{{ t('settings.appearance') }}</h2>

                <div class="settings-page__section-content">
                    <!-- Тема -->
                    <div class="settings-page__setting-item">
                        <div class="settings-page__setting-info">
                            <h3 class="settings-page__setting-label">{{ t('settings.theme') }}</h3>
                            <p class="settings-page__setting-hint">{{ t('settings.themeHint') }}</p>
                        </div>
                        <SelectButton v-model="modeModel" :options="themeOptions" option-label="label"
                            option-value="value" :allow-empty="false" class="settings-page__theme-selector" />
                    </div>

                    <!-- Разделитель -->
                    <div class="settings-page__divider"></div>

                    <!-- Язык -->
                    <div class="settings-page__setting-item">
                        <div class="settings-page__setting-info">
                            <h3 class="settings-page__setting-label">{{ t('settings.language') }}</h3>
                            <p class="settings-page__setting-hint">{{ t('settings.languageHint') }}</p>
                        </div>
                        <SelectButton v-model="currentLanguage" :options="languageOptions" option-label="label"
                            option-value="value" :allow-empty="false" class="settings-page__language-selector">
                            <template #option="slotProps">
                                <div class="select-item">
                                    <VIcon :icon="slotProps.option.icon" class="no-fill icon" />
                                    {{ slotProps.option.label }}
                                </div>
                            </template>
                        </SelectButton>
                    </div>
                </div>
            </div>

            <!-- Секция данных пользователя -->
            <div class="settings-page__section">
                <h2 class="settings-page__section-title">{{ t('settings.userData') }}</h2>
                <div v-if="loading" class="settings-page__loading">
                    <ProgressSpinner />
                </div>
                <div v-else class="settings-page__user-info">
                    <div class="settings-page__user-info-item">
                        <VInputText :model-value="userDataFields.username" :label="t('settings.username')" readonly
                            size="small" class="font-14-r" />
                    </div>
                    <div class="settings-page__user-info-item">
                        <VInputText :model-value="userDataFields.email" :label="t('settings.email')" readonly
                            size="small" class="font-14-r" />
                    </div>
                    <div class="settings-page__user-info-item">
                        <VInputText :model-value="userDataFields.default_currency"
                            :label="t('settings.defaultCurrency')" readonly size="small" class="font-14-r" />
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { Button, SelectButton, ProgressSpinner } from 'primevue';
import { arrowLeft } from '@/assets/icons';
import VIcon from '@/components/UI/VIcon.vue';
import { useThemeMode } from '@/composables/UI/useThemeMode';
import VInputText from '@/components/Form/VInputText.vue';
import { useUserStore } from '@/store/userStore';
import { formatDateTime } from '@/utils';
import type { TLangs } from '@/plugins/i18n/models';
import { setCurrentLocale } from '@/plugins/i18n/models';
import { locales } from '@/plugins/i18n';

const router = useRouter();
const { t, locale } = useI18n();
const { modeModel } = useThemeMode();
const userStore = useUserStore();
const { user: userData, loading } = storeToRefs(userStore);
const { loadUser } = userStore;

const userDataFields = computed(() => {
    if (!userData.value) {
        return {
            username: '',
            email: '',
            id: '',
            default_currency: '',
            created_at: '',
        };
    }
    return {
        username: userData.value.username,
        email: userData.value.email,
        id: userData.value.id,
        default_currency: userData.value.default_currency.toUpperCase(),
        created_at: formatDateTime(userData.value.created_at),
    };
});

const themeOptions = computed(() => [
    { label: t('settings.light'), value: 'light' },
    { label: t('settings.dark'), value: 'dark' },
]);

const languageOptions = computed(() => {
    return locales.map((loc: { name: string; value: TLangs; icon: string }) => ({
        label: loc.name,
        value: loc.value,
        icon: loc.icon,
    }));
});

const currentLanguage = computed({
    get() {
        return locale.value as TLangs;
    },
    set(value: TLangs) {
        setCurrentLocale(value);
        locale.value = value;
        document.documentElement.lang = value;
    },
});

onMounted(async () => {
    try {
        await loadUser();
    } catch (error) {
        console.error('Failed to load user data:', error);
    }
});

</script>

<style scoped lang="scss">
.settings-page {
    width: 100%;
    padding: 2rem;

    &__header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 2rem;

        &-button {
            width: 4rem;
            height: 4rem;
        }

        &-empty {
            width: 4rem;
        }

        h1 {
            font: var(--font-24-b);
        }
    }

    &__content {
        display: flex;
        flex-direction: column;
        gap: 2rem;
    }

    &__section {
        background: var(--gold-card-bg);
        padding: 2rem;
        border-radius: 1.6rem;
        border: 1px solid var(--gold-border);
        box-shadow: var(--gold-shadow);
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;

        &:hover {
            border-color: var(--gold-border-hover);
            box-shadow: var(--gold-shadow-hover);
        }

        &::before {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: 1.6rem;
            background: var(--gold-card-radial);
            pointer-events: none;
        }

        &-title {
            font: var(--font-18-b);
            margin: 0 0 1.6rem 0;
            position: relative;
            z-index: 1;
            color: var(--text-color);
        }

        &-content {
            display: flex;
            flex-direction: column;
            gap: 0;
            position: relative;
            z-index: 1;
        }
    }

    &__setting-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1.6rem;
        padding: 1.2rem 0;

        @include media-max($mobile) {
            flex-direction: column;
            align-items: flex-start;
            gap: 1rem;
        }
    }

    &__setting-info {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
        min-width: 0;
    }

    &__setting-label {
        font: var(--font-16-r);
        margin: 0;
        color: var(--text-color);
    }

    &__setting-hint {
        font: var(--font-14-r);
        margin: 0;
        color: var(--text-color-secondary);
        line-height: 1.4;
    }

    &__divider {
        height: 1px;
        background: var(--gold-border);
        margin: 0.8rem 0;
        opacity: 0.5;
    }

    &__theme-selector,
    &__language-selector {
        width: 100%;

        :deep(.p-togglebutton) {
            width: 100%;
        }
    }

    &__language-option {
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }

    &__language-icon {
        width: 1.6rem;
        height: 1.6rem;
        flex-shrink: 0;
    }

    &__loading {
        display: flex;
        justify-content: center;
        padding: 2rem;
        position: relative;
        z-index: 1;
    }

    &__user-info {
        display: flex;
        flex-direction: column;
        gap: 1.2rem;
        position: relative;
        z-index: 1;

        &-item {
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
            padding-bottom: 1.2rem;
            border-bottom: 1px solid var(--gold-border);

            &:last-child {
                border-bottom: none;
                padding-bottom: 0;
            }
        }

        &-label {
            color: var(--text-color-secondary);
        }

        &-value {
            color: var(--text-color);
        }
    }
}

.select-item {
    display: flex;
    gap: 1rem;
    align-items: center;
}
</style>
