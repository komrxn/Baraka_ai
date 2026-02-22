import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useLayoutStore = defineStore('layout', () => {
    const hideBottomBar = ref(false);

    const setHideBottomBar = (value: boolean) => {
        hideBottomBar.value = value;
    };

    return { hideBottomBar, setHideBottomBar };
});
