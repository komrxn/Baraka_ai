<template>
    <div class="main-page">
        <MainHeader />
        <MainBalance />
        <!-- <MainQuickInput /> -->
        <MainChart />
        <MainGrid />
        <MainLimits />
    </div>
</template>

<script setup lang="ts">
import MainChart from '@/components/Main/MainChart.vue';
import MainHeader from '@/components/Main/MainHeader.vue';
import MainBalance from '@/components/Main/MainBalance.vue';
// import MainQuickInput from '@/components/Main/MainQuickInput.vue';
import MainLimits from '@/components/Main/MainLimits.vue';
import MainGrid from '@/components/Main/MainGrid.vue';
</script>

<style scoped lang="scss">
.main-page {
    width: 100%;
    padding: 2rem;
    min-height: 100dvh;
}
</style>