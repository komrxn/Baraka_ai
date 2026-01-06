
import { useUserStore } from '@/store/userStore';

export const subscriptionMiddleware = async () => {
    const userStore = useUserStore();

    try {
        await userStore.loadUser(true);
    } catch (error) {
        console.error('Failed to load user in subscription middleware:', error);
        return { name: 'login' };
    }

    return true;
};

