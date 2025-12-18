<template>
    <div class="main-header" @click="handleClick">
        <div class="main-header__content">
            <div class="main-header__content-avatar">
                <img src="https://img.freepik.com/free-psd/3d-render-avatar-character_23-2150611765.jpg?semt=ais_hybrid&w=740&q=80"
                    alt="logo" />
            </div>
            <div class="main-header__content-info">
                <h1>
                    {{ t('main.greeting', { username: userData?.name || t('main.user') }) }}
                </h1>
                <p>{{ t('main.smartTracker') }}</p>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useUserStore } from '@/store/userStore';

const { t } = useI18n();

const router = useRouter();
const userStore = useUserStore();
const { user: userData } = storeToRefs(userStore);
const { loadUser } = userStore;

onMounted(async () => {
    try {
        await loadUser();
    } catch (error) {
        console.error('Failed to load user data:', error);
    }
});

const handleClick = () => {
    router.push({ name: 'settings' });
};
</script>

<style scoped lang="scss">
.main-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    cursor: pointer;
    transition: opacity 0.2s;

    &:hover {
        opacity: 0.8;
    }

    &__content {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;

    }

    &__content-avatar {
        width: 4rem;
        height: 4rem;
        border-radius: 50%;
        overflow: hidden;

        img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
    }

    &__content-info {
        display: flex;
        flex-direction: column;
        gap: 0.4rem;

        h1 {
            font: var(--font-18-b);
        }

        p {
            font: var(--font-14-r);
        }
    }

}
</style>