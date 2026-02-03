<script setup>
import { ref, onMounted, watch } from 'vue';
import api from '../api';
import { Search, Edit, Trash2, CheckCircle, XCircle, MoreVertical, Calendar } from 'lucide-vue-next';
import { Dialog, DialogPanel, DialogTitle, TransitionChild, TransitionRoot } from '@headlessui/vue';

const users = ref([]);
const total = ref(0);
const page = ref(1);
const search = ref('');
const loading = ref(false);

const fetchData = async () => {
    loading.value = true;
    try {
        const res = await api.get('/users/', {
            params: {
                page: page.value,
                size: 10,
                search: search.value
            }
        });
        users.value = res.data.items;
        total.value = res.data.total;
    } catch (e) {
        console.error(e);
    } finally {
        loading.value = false;
    }
};

onMounted(fetchData);

// Debounce search
let timeout;
watch(search, () => {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
        page.value = 1;
        fetchData();
    }, 500);
});

watch(page, fetchData);

// Modal Logic
const isModalOpen = ref(false);
const selectedUser = ref(null);
const actionType = ref('grant'); // grant, revoke
const selectedPlan = ref('monthly');
const customDays = ref(null);

const openGrantModal = (user) => {
    selectedUser.value = user;
    actionType.value = 'grant';
    isModalOpen.value = true;
};

const handleRevoke = async (user) => {
    if (!confirm(`Are you sure you want to revoke subscription for ${user.name}?`)) return;
    try {
        await api.put(`/users/${user.id}/subscription`, { action: 'revoke' });
        fetchData();
    } catch (e) {
        alert('Error revoking subscription');
    }
};

const handleDelete = async (user) => {
    if (!confirm(`DANGER: Are you sure you want to DELETE user ${user.name}? This cannot be undone.`)) return;
    try {
        await api.delete(`/users/${user.id}`);
        fetchData();
    } catch (e) {
        alert('Error deleting user');
    }
};

const submitSubscription = async () => {
    try {
        await api.put(`/users/${selectedUser.value.id}/subscription`, {
            action: 'grant',
            plan: selectedPlan.value,
            duration_days: customDays.value ? parseInt(customDays.value) : null
        });
        isModalOpen.value = false;
        fetchData();
    } catch (e) {
        alert('Error updating subscription');
    }
};

const formatDate = (isoString) => {
    if (!isoString) return '-';
    return new Date(isoString).toLocaleDateString();
};
</script>

<template>
    <div>
        <div class="flex items-center justify-between mb-8">
            <h1 class="text-3xl font-bold">User Management</h1>
            <div class="relative w-64">
                <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input 
                    v-model="search"
                    type="text" 
                    placeholder="Search users..." 
                    class="input-field pl-10"
                />
            </div>
        </div>

        <!-- Table -->
        <div class="glass rounded-xl border border-white/5 overflow-hidden">
            <div class="overflow-x-auto">
                <table class="w-full text-left">
                    <thead class="bg-surface/50 border-b border-white/5 text-gray-400 text-sm uppercase">
                        <tr>
                            <th class="p-4 font-medium">User</th>
                            <th class="p-4 font-medium">Status</th>
                            <th class="p-4 font-medium">Plan</th>
                            <th class="p-4 font-medium">Expires</th>
                            <th class="p-4 font-medium">Registered</th>
                            <th class="p-4 font-medium text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-white/5">
                        <tr v-for="user in users" :key="user.id" class="hover:bg-white/5 transition-colors">
                            <td class="p-4">
                                <div class="font-medium text-white">{{ user.name }}</div>
                                <div class="text-sm text-gray-500">{{ user.phone_number }} (ID: {{ user.telegram_id }})</div>
                            </td>
                                <span 
                                    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border capitalize"
                                    :class="{
                                        'bg-success/10 text-success border-success/20': ['plus', 'pro', 'premium'].includes(user.subscription_type),
                                        'bg-warning/10 text-warning border-warning/20': user.subscription_type === 'trial',
                                        'bg-gray-700/30 text-gray-400 border-gray-600/30': !user.subscription_type || user.subscription_type === 'free'
                                    }"
                                >
                                    {{ user.subscription_type || 'Free' }}
                                </span>
                            </td>
                            <td class="p-4 text-sm text-gray-300 capitalize">{{ user.subscription_type || '-' }}</td>
                            <td class="p-4 text-sm text-gray-300">{{ formatDate(user.subscription_ends_at) }}</td>
                            <td class="p-4 text-sm text-gray-500">{{ formatDate(user.created_at) }}</td>
                            <td class="p-4 text-right space-x-2">
                                <button 
                                    @click="openGrantModal(user)"
                                    class="p-2 hover:bg-primary/20 hover:text-primary rounded-lg transition-colors"
                                    title="Manage Subscription"
                                >
                                    <Edit class="w-4 h-4" />
                                </button>
                                <button 
                                    v-if="user.is_premium"
                                    @click="handleRevoke(user)"
                                    class="p-2 hover:bg-warning/20 hover:text-warning rounded-lg transition-colors"
                                    title="Revoke Subscription"
                                >
                                    <XCircle class="w-4 h-4" />
                                </button>
                                <button 
                                    @click="handleDelete(user)"
                                    class="p-2 hover:bg-danger/20 hover:text-danger rounded-lg transition-colors"
                                    title="Delete User"
                                >
                                    <Trash2 class="w-4 h-4" />
                                </button>
                            </td>
                        </tr>
                        <tr v-if="users.length === 0 && !loading">
                            <td colspan="6" class="p-8 text-center text-gray-500">No users found.</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Pagination -->
            <div class="p-4 border-t border-white/5 flex items-center justify-between text-sm">
                <span class="text-gray-400">Total: {{ total }} users</span>
                <div class="flex gap-2">
                    <button 
                        @click="page--" 
                        :disabled="page === 1"
                        class="px-3 py-1 rounded bg-surface border border-white/10 hover:bg-white/5 disabled:opacity-50"
                    >
                        Prev
                    </button>
                    <span class="px-3 py-1">{{ page }}</span>
                    <button 
                        @click="page++" 
                        :disabled="users.length < 10" 
                        class="px-3 py-1 rounded bg-surface border border-white/10 hover:bg-white/5 disabled:opacity-50"
                    >
                        Next
                    </button>
                </div>
            </div>
        </div>

        <!-- Grant Modal -->
        <TransitionRoot appear :show="isModalOpen" as="template">
            <Dialog as="div" @close="isModalOpen = false" class="relative z-50">
                <TransitionChild
                    as="template"
                    enter="duration-300 ease-out"
                    enter-from="opacity-0"
                    enter-to="opacity-100"
                    leave="duration-200 ease-in"
                    leave-from="opacity-100"
                    leave-to="opacity-0"
                >
                    <div class="fixed inset-0 bg-black/80 backdrop-blur-sm" />
                </TransitionChild>

                <div class="fixed inset-0 overflow-y-auto">
                    <div class="flex min-h-full items-center justify-center p-4 text-center">
                        <TransitionChild
                            as="template"
                            enter="duration-300 ease-out"
                            enter-from="opacity-0 scale-95"
                            enter-to="opacity-100 scale-100"
                            leave="duration-200 ease-in"
                            leave-from="opacity-100 scale-100"
                            leave-to="opacity-0 scale-95"
                        >
                            <DialogPanel class="w-full max-w-md transform overflow-hidden rounded-2xl bg-surface border border-white/10 p-6 text-left align-middle shadow-xl transition-all">
                                <DialogTitle as="h3" class="text-lg font-medium leading-6 text-white mb-4">
                                    Manage Subscription: {{ selectedUser?.name }}
                                </DialogTitle>
                                
                                <div class="space-y-4">
                                    <div>
                                        <label class="block text-sm text-gray-400 mb-2">Select Plan</label>
                                        <select v-model="selectedPlan" class="input-field">
                                            <option value="plus">Plus (30 Days)</option>
                                            <option value="pro">Pro (30 Days)</option>
                                            <option value="premium">Premium (30 Days)</option>
                                            <option value="monthly">Monthly (30 Days)</option>
                                            <option value="quarterly">Quarterly (90 Days)</option>
                                            <option value="annual">Annual (365 Days)</option>
                                            <option value="trial">Trial (3 Days)</option>
                                            <option value="custom">Custom Duration</option>
                                        </select>
                                    </div>

                                    <div v-if="selectedPlan === 'custom'">
                                        <label class="block text-sm text-gray-400 mb-2">Duration (Days)</label>
                                        <input v-model="customDays" type="number" class="input-field" placeholder="e.g. 7" />
                                    </div>
                                </div>

                                <div class="mt-6 flex justify-end gap-3">
                                    <button 
                                        @click="isModalOpen = false"
                                        class="px-4 py-2 rounded-lg text-sm font-medium hover:bg-white/5 transition-colors"
                                    >
                                        Cancel
                                    </button>
                                    <button 
                                        @click="submitSubscription"
                                        class="btn btn-primary text-sm"
                                    >
                                        Grant Subscription
                                    </button>
                                </div>
                            </DialogPanel>
                        </TransitionChild>
                    </div>
                </div>
            </Dialog>
        </TransitionRoot>
    </div>
</template>
