import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import i18n from './i18n'

// Vue Paper Dashboard theme styles
import '@/assets/sass/paper-dashboard.scss'
import '@/assets/css/themify-icons.css'
import '@/assets/sass/paper-theme-overrides.scss'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(i18n)

app.mount('#app')
