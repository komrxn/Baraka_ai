<template>
    <div class="main-page">
        <MainHeader />

        <MainBalance />
        <MainSubscriptionBanner v-if="!hasSubscription" />
        <!-- <MainQuickInput /> -->
        <MainChart />
        <MainGrid />
        <MainLimits />
    </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import MainChart from '@/components/Main/MainChart.vue';
import MainHeader from '@/components/Main/MainHeader.vue';
import MainBalance from '@/components/Main/MainBalance.vue';
import MainSubscriptionBanner from '@/components/Main/MainSubscriptionBanner.vue';
// import MainQuickInput from '@/components/Main/MainQuickInput.vue';
import MainLimits from '@/components/Main/MainLimits.vue';
import MainGrid from '@/components/Main/MainGrid.vue';
import { useUserStore } from '@/store/userStore';

const userStore = useUserStore();
const { user } = storeToRefs(userStore);
const { loadUser } = userStore;

const hasSubscription = computed(() => {
    return user.value?.is_premium ?? false;
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
.main-page {
    width: 100%;
    padding: 2.4rem;
    min-height: 100dvh;
}
</style>