import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import axios from 'axios'

// Configure axios base URL
axios.defaults.baseURL = import.meta.env.DEV ? 'http://localhost:8090' : ''
axios.defaults.withCredentials = true

// Add admin API key header for all requests
axios.defaults.headers.common['X-Admin-Key'] = 'greenmind-admin-secret-key-2024'

createApp(App).mount('#app')
