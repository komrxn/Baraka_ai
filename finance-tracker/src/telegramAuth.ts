/**
 * Telegram Web App authentication service.
 * 
 * Handles automatic authentication when app is opened through Telegram Mini App.
 */

import axios from 'axios';

export interface TelegramAuthResponse {
    access_token: string;
    token_type: string;
    user: {
        id: string;
        telegram_id: number;
        phone_number: string;
        name: string;
    };
}

/**
 * Checks if app is running inside Telegram Web App.
 */
export function isTelegramWebApp(): boolean {
    return !!window.Telegram?.WebApp;
}

/**
 * Initializes Telegram WebApp and authenticates user.
 * 
 * @returns JWT access token or null if not in Telegram or no initData
 * @throws Error if authentication fails
 */
export async function authenticateViaTelegram(): Promise<string | null> {
    if (!isTelegramWebApp()) {
        console.warn('Not running in Telegram WebApp');
        return null;
    }

    const tg = window.Telegram.WebApp;
    tg.ready();

    console.log('[Telegram Auth] Telegram WebApp initialized');

    const initData = tg.initData;
    if (!initData) {
        console.warn('[Telegram Auth] No initData available');
        return null;
    }

    console.log('[Telegram Auth] Sending initData to backend for validation');

    try {
        // Call backend Telegram auth endpoint
        const response = await axios.post<TelegramAuthResponse>(
            '/midas-api/auth/telegram-auth',
            { init_data: initData }
        );

        console.log('[Telegram Auth] Authentication successful');

        return response.data.access_token;
    }
    catch (error) {
        console.error('[Telegram Auth] Authentication failed:', error);
        throw new Error('Telegram authentication failed');
    }
}

/**
 * Gets Telegram user info (without authentication).
 */
export function getTelegramUser() {
    if (!isTelegramWebApp()) {
        return null;
    }

    const user = window.Telegram.WebApp.initDataUnsafe?.user;
    return user ? {
        id: user.id,
        first_name: user.first_name,
        last_name: user.last_name,
        username: user.username,
    } : null;
}
