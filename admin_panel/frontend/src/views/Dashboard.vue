<script setup>
import { ref, onMounted, computed } from 'vue';
import { useAuthStore } from '../stores/auth';
import { Users, CreditCard, Activity, TrendingUp, Mic, Camera, Zap, MessageSquare } from 'lucide-vue-next';
import { Line, Doughnut, Bar } from 'vue-chartjs';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
    Filler
} from 'chart.js';
import api from '../api';

// Register Chart.js components
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

const authStore = useAuthStore();

// State
const loading = ref(true);
const stats = ref({
    total_users: 0,
    active_subscriptions: 0,
    new_users_this_month: 0,
    subscription_breakdown: {}
});
const userGrowth = ref({ labels: [], data: [], daily_new: [] });
const subscriptionData = ref({ plus: 0, pro: 0, premium: 0, trial: 0, free: 0 });
const usageData = ref({
    dates: [],
    bg_tasks: [],
    text_today: 0,
    new_users_today: 0,
    subscribed_today: 0
});

// Fetch all data
const fetchData = async () => {
    loading.value = true;
    try {
        const [statsRes, growthRes, subsRes, usageRes] = await Promise.all([
            api.get('/analytics/stats'),
            api.get('/analytics/user-growth?days=30'),
            api.get('/analytics/subscription-growth'),
            api.get('/analytics/bot-usage')
        ]);
        
        stats.value = statsRes.data;
        userGrowth.value = growthRes.data;
        subscriptionData.value = subsRes.data;
        usageData.value = usageRes.data;
    } catch (e) {
        console.error('Failed to fetch analytics:', e);
    } finally {
        loading.value = false;
    }
};

onMounted(fetchData);

// Chart configurations
const userGrowthChartData = computed(() => ({
    labels: userGrowth.value.labels,
    datasets: [
        {
            label: 'Total Users',
            data: userGrowth.value.data,
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            fill: true,
            tension: 0.4,
            pointBackgroundColor: '#3b82f6',
            pointBorderColor: '#fff',
            pointHoverRadius: 8,
            pointHoverBackgroundColor: '#3b82f6'
        },
        {
            label: 'New Users',
            data: userGrowth.value.daily_new,
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            fill: true,
            tension: 0.4,
            pointBackgroundColor: '#10b981',
            pointBorderColor: '#fff',
            pointHoverRadius: 6
        }
    ]
}));

const userGrowthOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
        mode: 'index',
        intersect: false
    },
    plugins: {
        legend: {
            labels: { color: '#9ca3af', font: { size: 12 } }
        },
        tooltip: {
            backgroundColor: 'rgba(17, 24, 39, 0.95)',
            titleColor: '#fff',
            bodyColor: '#9ca3af',
            borderColor: 'rgba(255,255,255,0.1)',
            borderWidth: 1,
            padding: 12,
            displayColors: true,
            callbacks: {
                title: (items) => `📅 ${items[0].label}`
            }
        }
    },
    scales: {
        x: {
            grid: { color: 'rgba(255,255,255,0.05)' },
            ticks: { color: '#6b7280' }
        },
        y: {
            grid: { color: 'rgba(255,255,255,0.05)' },
            ticks: { color: '#6b7280' }
        }
    }
};

const subscriptionChartData = computed(() => ({
    labels: ['Plus', 'Pro', 'Premium', 'Trial', 'Free'],
    datasets: [{
        data: [
            subscriptionData.value.plus,
            subscriptionData.value.pro,
            subscriptionData.value.premium,
            subscriptionData.value.trial,
            subscriptionData.value.free
        ],
        backgroundColor: [
            '#3b82f6', // Plus - blue
            '#8b5cf6', // Pro - purple
            '#f59e0b', // Premium - amber
            '#10b981', // Trial - green
            '#6b7280'  // Free - gray
        ],
        borderWidth: 0,
        hoverOffset: 10
    }]
}));

const subscriptionChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '65%',
    plugins: {
        legend: {
            position: 'bottom',
            labels: { 
                color: '#9ca3af', 
                padding: 20,
                usePointStyle: true,
                font: { size: 12 }
            }
        },
        tooltip: {
            backgroundColor: 'rgba(17, 24, 39, 0.95)',
            titleColor: '#fff',
            bodyColor: '#9ca3af',
            padding: 12,
            callbacks: {
                label: (context) => ` ${context.label}: ${context.raw} users`
            }
        }
    }
};

const usageChartData = computed(() => ({
    labels: usageData.value.dates,
    datasets: [{
        label: 'Text Request Load',
        data: usageData.value.bg_tasks,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#3b82f6',
        pointBorderColor: '#fff',
        pointHoverRadius: 8,
        pointHoverBackgroundColor: '#3b82f6'
    }]
}));

const usageChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
        mode: 'index',
        intersect: false
    },
    plugins: {
        legend: { display: false },
        tooltip: {
            backgroundColor: 'rgba(17, 24, 39, 0.95)',
            titleColor: '#fff',
            bodyColor: '#9ca3af',
            borderColor: 'rgba(255,255,255,0.1)',
            borderWidth: 1,
            padding: 12,
            displayColors: true,
            callbacks: {
                title: (items) => `📅 ${items[0].label}`
            }
        }
    },
    scales: {
        x: {
            grid: { color: 'rgba(255,255,255,0.05)' },
            ticks: { color: '#6b7280' }
        },
        y: {
            grid: { color: 'rgba(255,255,255,0.05)' },
            ticks: { color: '#6b7280' },
            beginAtZero: true
        }
    }
};

// Stat cards config
const statCards = computed(() => [
    { 
        name: 'Total Users', 
        value: stats.value.total_users.toLocaleString(), 
        icon: Users, 
        color: 'text-blue-400',
        bg: 'bg-blue-500/10',
        change: `+${stats.value.new_users_this_month} this month`
    },
    { 
        name: 'Active Subscriptions', 
        value: stats.value.active_subscriptions.toLocaleString(), 
        icon: CreditCard, 
        color: 'text-green-400',
        bg: 'bg-green-500/10',
        change: `${Math.round((stats.value.active_subscriptions / Math.max(stats.value.total_users, 1)) * 100)}% conversion`
    },
    { 
        name: 'New Users Today', 
        value: usageData.value.new_users_today.toLocaleString(), 
        icon: Users, 
        color: 'text-purple-400',
        bg: 'bg-purple-500/10',
        change: 'Registered today'
    },
    { 
        name: 'Requests Today', 
        value: usageData.value.text_today.toLocaleString(), 
        icon: MessageSquare, 
        color: 'text-amber-400',
        bg: 'bg-amber-500/10',
        change: 'Text messages'
    }
]);
</script>

<template>
    <div>
        <h1 class="text-3xl font-bold mb-8">
            Welcome back, <span class="bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">{{ authStore.admin?.email?.split('@')[0] }}</span>
        </h1>

        <!-- Loading State -->
        <div v-if="loading" class="flex items-center justify-center min-h-[400px]">
            <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>

        <div v-else>
            <!-- Stats Cards -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div 
                    v-for="stat in statCards" 
                    :key="stat.name" 
                    class="glass p-6 rounded-xl border border-white/5 hover:border-white/10 transition-all duration-300 hover:transform hover:scale-[1.02]"
                >
                    <div class="flex items-center justify-between mb-4">
                        <span class="text-gray-400 font-medium">{{ stat.name }}</span>
                        <div :class="[stat.bg, 'p-2 rounded-lg']">
                            <component :is="stat.icon" :class="['w-5 h-5', stat.color]" />
                        </div>
                    </div>
                    <div class="text-3xl font-bold text-white mb-1">{{ stat.value }}</div>
                    <div class="text-sm text-gray-500">{{ stat.change }}</div>
                </div>
            </div>

            <!-- Charts Row 1 -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                <!-- User Growth Chart -->
                <div class="lg:col-span-2 glass p-6 rounded-xl border border-white/5">
                    <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <TrendingUp class="w-5 h-5 text-blue-400" />
                        User Growth (Last 30 Days)
                    </h3>
                    <div class="h-[300px]">
                        <Line :data="userGrowthChartData" :options="userGrowthOptions" />
                    </div>
                </div>

                <!-- Subscription Breakdown -->
                <div class="glass p-6 rounded-xl border border-white/5">
                    <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <CreditCard class="w-5 h-5 text-green-400" />
                        Subscriptions
                    </h3>
                    <div class="h-[300px] flex items-center justify-center">
                        <Doughnut :data="subscriptionChartData" :options="subscriptionChartOptions" />
                    </div>
                </div>
            </div>

            <!-- Charts Row 2 -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- Bot Usage -->
                <div class="glass p-6 rounded-xl border border-white/5">
                    <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <Zap class="w-5 h-5 text-amber-400" />
                        Bot Load (Text Requests)
                    </h3>
                    <div class="h-[250px]">
                        <Line :data="usageChartData" :options="usageChartOptions" />
                    </div>
                </div>

                <!-- Quick Stats -->
                <div class="glass p-6 rounded-xl border border-white/5">
                    <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <Activity class="w-5 h-5 text-purple-400" />
                        Today's Activity
                    </h3>
                    <div class="space-y-4">
                        <div class="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                            <div class="flex items-center gap-3">
                                <div class="p-2 bg-blue-500/20 rounded-lg">
                                    <MessageSquare class="w-5 h-5 text-blue-400" />
                                </div>
                                <span class="text-gray-300">Requests (text messages)</span>
                            </div>
                            <span class="text-2xl font-bold text-white">{{ usageData.text_today }}</span>
                        </div>
                        <div class="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                            <div class="flex items-center gap-3">
                                <div class="p-2 bg-green-500/20 rounded-lg">
                                    <CreditCard class="w-5 h-5 text-green-400" />
                                </div>
                                <span class="text-gray-300">Subscribed today</span>
                            </div>
                            <span class="text-2xl font-bold text-white">{{ usageData.subscribed_today }}</span>
                        </div>
                        <div class="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                            <div class="flex items-center gap-3">
                                <div class="p-2 bg-purple-500/20 rounded-lg">
                                    <Users class="w-5 h-5 text-purple-400" />
                                </div>
                                <span class="text-gray-300">New users today</span>
                            </div>
                            <span class="text-2xl font-bold text-white">{{ usageData.new_users_today }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
