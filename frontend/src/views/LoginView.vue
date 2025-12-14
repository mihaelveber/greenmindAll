<template>
  <div class="login-container">
    <n-card class="login-card" :bordered="false">
      <div class="login-header">
        <div class="logo-container">
          <img src="/logo.png" alt="Greenmind AI" class="logo" />
        </div>
        <n-gradient-text :size="32" type="info">
          Greenmind AI
        </n-gradient-text>
        <p class="subtitle">Prijavite se v svoj račun</p>
      </div>

      <n-tabs
        v-model:value="activeTab"
        type="segment"
        animated
        size="large"
        class="auth-tabs"
      >
        <n-tab-pane name="login" tab="Prijava">
          <n-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            size="large"
            @submit.prevent="handleLogin"
            autocomplete="on"
          >
            <n-form-item path="email" label="Email">
              <n-input
                v-model:value="loginForm.email"
                placeholder="vnesite@email.com"
                autocomplete="email"
                :input-props="{ autocomplete: 'email' }"
              >
                <template #prefix>
                  <n-icon :component="MailOutline" />
                </template>
              </n-input>
            </n-form-item>

            <n-form-item path="password" label="Geslo">
              <n-input
                v-model:value="loginForm.password"
                type="password"
                show-password-on="click"
                placeholder="Vnesite geslo"
                autocomplete="current-password"
                :input-props="{ autocomplete: 'current-password' }"
              >
                <template #prefix>
                  <n-icon :component="LockClosedOutline" />
                </template>
              </n-input>
            </n-form-item>

            <n-button
              type="primary"
              block
              size="large"
              :loading="loading"
              attr-type="submit"
              :disabled="loading"
            >
              Prijava
            </n-button>
          </n-form>

          <n-divider>Ali pa</n-divider>

          <div class="oauth-buttons">
            <n-button
              block
              size="large"
              @click="handleGoogleLogin"
              class="oauth-btn google-btn"
            >
              <template #icon>
                <n-icon :component="LogoGoogle" />
              </template>
              Nadaljuj z Google
            </n-button>

            <n-button
              block
              size="large"
              @click="handleAppleLogin"
              class="oauth-btn apple-btn"
            >
              <template #icon>
                <n-icon :component="LogoApple" />
              </template>
              Nadaljuj z Apple
            </n-button>
          </div>
        </n-tab-pane>

        <n-tab-pane name="register" tab="Registracija">
          <n-form
            ref="registerFormRef"
            :model="registerForm"
            :rules="registerRules"
            size="large"
            @submit.prevent="handleRegister"
          >
            <n-form-item path="username" label="Uporabniško ime">
              <n-input
                v-model:value="registerForm.username"
                placeholder="uporabnik123"
                :input-props="{ autocomplete: 'username' }"
              >
                <template #prefix>
                  <n-icon :component="PersonOutline" />
                </template>
              </n-input>
            </n-form-item>

            <n-form-item path="email" label="Email">
              <n-input
                v-model:value="registerForm.email"
                placeholder="vnesite@email.com"
                :input-props="{ 
                  autocomplete: 'email',
                  name: 'email',
                  id: 'register-email'
                }"
              >
                <template #prefix>
                  <n-icon :component="MailOutline" />
                </template>
              </n-input>
            </n-form-item>

            <n-form-item path="password" label="Geslo">
              <n-input
                v-model:value="registerForm.password"
                type="password"
                show-password-on="click"
                placeholder="Vnesite geslo"
                :input-props="{ 
                  autocomplete: 'new-password',
                  name: 'password',
                  id: 'register-password'
                }"
              >
                <template #prefix>
                  <n-icon :component="LockClosedOutline" />
                </template>
              </n-input>
            </n-form-item>

            <n-form-item path="password_confirm" label="Potrdi geslo">
              <n-input
                v-model:value="registerForm.password_confirm"
                type="password"
                show-password-on="click"
                placeholder="Ponovite geslo"
                :input-props="{ 
                  autocomplete: 'new-password',
                  name: 'password_confirm',
                  id: 'register-password-confirm'
                }"
              >
                <template #prefix>
                  <n-icon :component="LockClosedOutline" />
                </template>
              </n-input>
            </n-form-item>

            <n-button
              type="primary"
              block
              size="large"
              :loading="loading"
              attr-type="submit"
              :disabled="loading"
            >
              Ustvari račun
            </n-button>
          </n-form>
        </n-tab-pane>
      </n-tabs>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { 
  useMessage,
  NCard,
  NGradientText,
  NTabs,
  NTabPane,
  NForm,
  NFormItem,
  NInput,
  NButton,
  NDivider,
  NIcon,
  type FormInst,
  type FormRules
} from 'naive-ui'
import { useAuthStore } from '../stores/auth.store'
import { MailOutline, LockClosedOutline, PersonOutline, LogoGoogle, LogoApple } from '@vicons/ionicons5'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

const activeTab = ref('login')
const loading = ref(false)
const loginFormRef = ref<FormInst | null>(null)
const registerFormRef = ref<FormInst | null>(null)

const loginForm = ref({
  email: '',
  password: ''
})

const registerForm = ref({
  username: '',
  email: '',
  password: '',
  password_confirm: ''
})

const loginRules: FormRules = {
  email: [
    { required: true, message: 'Email je obvezen', trigger: 'blur' },
    { type: 'email', message: 'Neveljaven email', trigger: ['blur', 'input'] }
  ],
  password: [
    { required: true, message: 'Geslo je obvezno', trigger: 'blur' }
  ]
}

const registerRules: FormRules = {
  username: [
    { required: true, message: 'Uporabniško ime je obvezno', trigger: 'blur' },
    { min: 3, message: 'Minimalno 3 znake', trigger: 'blur' }
  ],
  email: [
    { required: true, message: 'Email je obvezen', trigger: 'blur' },
    { type: 'email', message: 'Neveljaven email', trigger: ['blur', 'input'] }
  ],
  password: [
    { required: true, message: 'Geslo je obvezno', trigger: 'blur' },
    { min: 6, message: 'Minimalno 6 znakov', trigger: 'blur' }
  ],
  password_confirm: [
    { required: true, message: 'Potrdite geslo', trigger: 'blur' },
    {
      validator: (_rule, value) => value === registerForm.value.password,
      message: 'Gesli se ne ujemata',
      trigger: ['blur', 'input']
    }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return

  try {
    await loginFormRef.value.validate()
    loading.value = true

    await authStore.login(loginForm.value)
    
    message.success('Uspešna prijava!')
    router.push('/dashboard')
  } catch (error: any) {
    if (error.response?.data?.message) {
      message.error(error.response.data.message)
    } else {
      message.error('Napaka pri prijavi')
    }
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  if (!registerFormRef.value) return

  try {
    await registerFormRef.value.validate()
    loading.value = true

    await authStore.register(registerForm.value)
    
    message.success('Račun uspešno ustvarjen!')
    router.push('/dashboard')
  } catch (error: any) {
    if (error.response?.data?.message) {
      message.error(error.response.data.message)
    } else {
      message.error('Napaka pri registraciji')
    }
  } finally {
    loading.value = false
  }
}

const handleGoogleLogin = () => {
  message.warning('Google OAuth še ni konfiguriran. Prosim uporabite email/geslo prijavo.')
  // const googleUrl = `http://localhost:8090/api/auth/google/login`
  // window.location.href = googleUrl
}

const handleAppleLogin = () => {
  message.warning('Apple OAuth še ni konfiguriran. Prosim uporabite email/geslo prijavo.')
  // const appleUrl = `http://localhost:8090/api/auth/apple/login`
  // window.location.href = appleUrl
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 480px;
  backdrop-filter: blur(20px);
  background: rgba(255, 255, 255, 0.05);
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 24px;
  padding: 20px;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-container {
  margin-bottom: 16px;
}

.logo {
  width: 80px;
  height: 80px;
  border-radius: 16px;
  object-fit: cover;
  box-shadow: 0 4px 12px rgba(84, 217, 68, 0.3);
}

.subtitle {
  color: rgba(255, 255, 255, 0.7);
  margin-top: 8px;
  font-size: 16px;
}

.auth-tabs {
  margin-bottom: 24px;
}

.oauth-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 20px;
}

.oauth-btn {
  font-weight: 500;
  transition: all 0.3s ease;
}

.google-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(66, 133, 244, 0.3);
}

.apple-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 255, 255, 0.2);
}

/* Mobile Responsive Styles */
@media (max-width: 768px) {
  .login-card {
    max-width: 95%;
    padding: 16px;
    border-radius: 16px;
  }

  .logo {
    width: 60px;
    height: 60px;
  }

  .login-header :deep(.n-gradient-text) {
    font-size: 24px !important;
  }

  .subtitle {
    font-size: 14px;
  }

  :deep(.n-form-item) {
    margin-bottom: 16px;
  }

  :deep(.n-button) {
    font-size: 14px;
  }

  :deep(.n-tabs) {
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .login-card {
    max-width: 98%;
    padding: 12px;
    border-radius: 12px;
  }

  .logo {
    width: 50px;
    height: 50px;
  }

  .login-header :deep(.n-gradient-text) {
    font-size: 20px !important;
  }

  .subtitle {
    font-size: 13px;
  }

  :deep(.n-form-item-label) {
    font-size: 13px !important;
  }

  :deep(.n-input) {
    font-size: 14px !important;
  }

  :deep(.n-button) {
    font-size: 13px;
    padding: 8px 16px;
  }
}
</style>
