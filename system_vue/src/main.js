import './assets/main.css'
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import pinia from './stores'
import 'element-plus/dist/index.css'
import useUserStore from '@/stores/user';
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
const app=createApp(App)
pinia.use(piniaPluginPersistedstate)
app.use(router).use(pinia)
// ✅ 关键：应用启动时恢复用户信息
const userStore = useUserStore();
userStore.restoreFromStorage();
app.mount('#app')
