import { createI18n } from 'vue-i18n'
import en from './locales/en'
import de from './locales/de'
import sl from './locales/sl'

const messages = {
  en,
  de,
  sl
}

const i18n = createI18n({
  legacy: false,
  locale: localStorage.getItem('locale') || 'en',
  fallbackLocale: 'en',
  messages
})

export default i18n
