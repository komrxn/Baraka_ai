import { createRouter, createWebHistory } from 'vue-router';
import { layoutMiddleware } from '@/middlewares/layoutMiddleware.ts';
import { subscriptionMiddleware } from '@/middlewares/subscriptionMiddleware.ts';
// import { pageTransitionMiddleware } from '@/middlewares/pageTransitionMiddleware.ts';
import routes from './routes.ts';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    if (savedPosition) {
      return savedPosition;
    } else {
      return { top: 0 };
    }
  },
});

router.beforeEach(layoutMiddleware);
router.beforeEach(subscriptionMiddleware);
// router.beforeEach(pageTransitionMiddleware);
export default router;
