<template>
  <div class="conversation-container">
    <!-- Header -->
    <n-card :title="`💬 AI Conversation - ${disclosureCode}`" size="small">
      <template #header-extra>
        <n-space>
          <n-tag type="info" size="small">
            {{ messages.length }} messages
          </n-tag>
          <n-button
            size="small"
            text
            @click="$emit('close')"
          >
            ✕
          </n-button>
        </n-space>
      </template>

      <!-- Messages Area -->
      <div class="messages-area" ref="messagesContainer">
        <!-- Empty state -->
        <div v-if="messages.length === 0" class="empty-state">
          <n-empty description="No messages yet" size="small">
            <template #extra>
              <n-text depth="3">Start a conversation by asking a question below</n-text>
            </template>
          </n-empty>
        </div>

        <!-- Messages -->
        <div
          v-for="(message, index) in messages"
          :key="message.id"
          :class="['message-bubble', message.role]"
        >
          <!-- User Message -->
          <div v-if="message.role === 'user'" class="user-message">
            <div class="message-header">
              <n-tag type="info" size="small">You</n-tag>
              <span class="timestamp">{{ formatTime(message.created_at) }}</span>
            </div>
            <div class="message-content">{{ message.content }}</div>
          </div>

          <!-- Assistant Message -->
          <div v-else class="assistant-message">
            <div class="message-header">
              <n-space align="center">
                <n-tag type="success" size="small">🤖 AI Assistant</n-tag>
                <span class="timestamp">{{ formatTime(message.created_at) }}</span>
                <n-tag v-if="message.temperature !== null" size="tiny" type="default">
                  🌡️ {{ message.temperature.toFixed(1) }}
                </n-tag>
                <n-tag v-if="message.confidence_score" size="tiny" :type="getConfidenceType(message.confidence_score)">
                  {{ Math.round(message.confidence_score) }}% confidence
                </n-tag>
              </n-space>
              <n-space>
                <n-button
                  size="tiny"
                  text
                  @click="copyMessage(message.content)"
                  title="Copy"
                >
                  📋
                </n-button>
                <n-button
                  size="tiny"
                  text
                  @click="openRegenerateModal(message.id, index)"
                  title="Regenerate with different temperature"
                >
                  🔄
                </n-button>
                <n-button
                  size="tiny"
                  type="primary"
                  @click="useAsAnswer(message.id)"
                  :loading="savingAsAnswer === message.id"
                  title="Use this as final answer"
                >
                  ✅ Use as Answer
                </n-button>
              </n-space>
            </div>
            <div class="message-content markdown-content" v-html="renderMarkdown(message.content)"></div>
            
            <!-- Charts/Images/Tables if present -->
            <div v-if="message.chart_data || message.table_data || message.image_data" class="message-artifacts">
              <n-divider style="margin: 12px 0;" />
              <n-space vertical>
                <n-tag v-if="message.chart_data" type="warning" size="small">📊 Charts attached</n-tag>
                <n-tag v-if="message.table_data" type="warning" size="small">📋 Tables attached</n-tag>
                <n-tag v-if="message.image_data" type="warning" size="small">🖼️ Images attached</n-tag>
              </n-space>
            </div>
          </div>
        </div>

        <!-- Typing indicator -->
        <div v-if="isGenerating" class="typing-indicator">
          <n-spin size="small" />
          <span style="margin-left: 8px;">AI is thinking...</span>
        </div>
      </div>

      <!-- Input Area -->
      <n-divider style="margin: 16px 0;" />
      
      <!-- Temperature Control -->
      <n-alert type="info" style="margin-bottom: 12px;" closable title="🌡️ AI Creativity Level">
        <n-space align="center">
          <n-button
            size="small"
            :type="currentTemperature === 0.0 ? 'primary' : 'default'"
            @click="currentTemperature = 0.0"
          >
            0.0
          </n-button>
          <n-button
            size="small"
            :type="currentTemperature === 0.2 ? 'primary' : 'default'"
            @click="currentTemperature = 0.2"
          >
            0.2
          </n-button>
          <n-button
            size="small"
            :type="currentTemperature === 0.5 ? 'primary' : 'default'"
            @click="currentTemperature = 0.5"
          >
            0.5
          </n-button>
          <n-button
            size="small"
            :type="currentTemperature === 0.7 ? 'primary' : 'default'"
            @click="currentTemperature = 0.7"
          >
            0.7
          </n-button>
          <n-button
            size="small"
            :type="currentTemperature === 1.0 ? 'primary' : 'default'"
            @click="currentTemperature = 1.0"
          >
            1.0
          </n-button>
          <n-input-number
            v-model:value="currentTemperature"
            :min="0"
            :max="1"
            :step="0.1"
            size="small"
            style="width: 100px;"
          />
          <span style="font-size: 12px; color: #999;">
            {{ getTemperatureLabel(currentTemperature) }}
          </span>
        </n-space>
      </n-alert>

      <!-- Message Input -->
      <n-space vertical style="width: 100%;">
        <n-input
          v-model:value="newMessage"
          type="textarea"
          :rows="3"
          placeholder="Ask a follow-up question about this disclosure..."
          :disabled="isGenerating"
          @keydown.enter.exact="handleEnterKey"
        />
        <n-space justify="space-between">
          <n-text depth="3" style="font-size: 12px;">
            Press Enter to send, Shift+Enter for new line
          </n-text>
          <n-button
            type="primary"
            :loading="isGenerating"
            :disabled="!newMessage.trim()"
            @click="sendMessage"
          >
            Send Message
          </n-button>
        </n-space>
      </n-space>
    </n-card>

    <!-- Regenerate Modal -->
    <n-modal
      v-model:show="showRegenerateModal"
      preset="dialog"
      title="🔄 Regenerate Response"
      positive-text="Regenerate"
      negative-text="Cancel"
      :loading="isRegenerating"
      @positive-click="regenerateMessage"
    >
      <n-space vertical>
        <n-alert type="info">
          Regenerate this AI response with a different temperature setting.
        </n-alert>
        <n-divider style="margin: 8px 0;" />
        <n-space align="center">
          <strong>Temperature:</strong>
          <n-button size="small" @click="regenerateTemperature = 0.0">0.0</n-button>
          <n-button size="small" @click="regenerateTemperature = 0.2">0.2</n-button>
          <n-button size="small" @click="regenerateTemperature = 0.5">0.5</n-button>
          <n-button size="small" @click="regenerateTemperature = 0.7">0.7</n-button>
          <n-button size="small" @click="regenerateTemperature = 1.0">1.0</n-button>
          <n-input-number
            v-model:value="regenerateTemperature"
            :min="0"
            :max="1"
            :step="0.1"
            size="small"
            style="width: 100px;"
          />
        </n-space>
      </n-space>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { NCard, NSpace, NTag, NButton, NInput, NInputNumber, NAlert, NDivider, NSpin, NModal, NText, NEmpty, useMessage } from 'naive-ui'
import { marked } from 'marked'
import api from '../services/api'

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  temperature?: number
  confidence_score?: number
  created_at: string
  chart_data?: any
  table_data?: any
  image_data?: any
  edited?: boolean
  regenerated?: boolean
}

const props = defineProps<{
  threadId: number
  disclosureCode: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'messageAdded'): void
  (e: 'answerSaved', answer: string): void
}>()

const message = useMessage()
const messages = ref<Message[]>([])
const newMessage = ref('')
const currentTemperature = ref(0.2)
const isGenerating = ref(false)
const messagesContainer = ref<HTMLElement>()
const savingAsAnswer = ref<number | null>(null)

// Regenerate modal
const showRegenerateModal = ref(false)
const isRegenerating = ref(false)
const regenerateMessageId = ref<number | null>(null)
const regenerateMessageIndex = ref<number | null>(null)
const regenerateTemperature = ref(0.2)

// Load conversation history on mount
onMounted(async () => {
  await loadMessages()
  scrollToBottom()
})

// Auto-scroll on new messages
watch(messages, () => {
  nextTick(() => scrollToBottom())
}, { deep: true })

const loadMessages = async () => {
  try {
    const response = await api.get(`/esrs/conversation/${props.threadId}/messages`)
    messages.value = response.data.messages
  } catch (error: any) {
    console.error('Error loading messages:', error)
    message.error('Failed to load conversation history')
  }
}

const sendMessage = async () => {
  if (!newMessage.value.trim() || isGenerating.value) return

  const userMessageText = newMessage.value.trim()
  newMessage.value = ''
  isGenerating.value = true

  try {
    const response = await api.post(`/esrs/conversation/message/${props.threadId}`, {
      message: userMessageText,
      temperature: currentTemperature.value
    })

    // Only add messages if API call succeeded
    if (response.data.message_id && response.data.content) {
      // Add user message
      messages.value.push({
        id: Date.now(), // Temporary ID
        role: 'user',
        content: userMessageText,
        created_at: new Date().toISOString()
      })

      // Add AI response
      messages.value.push({
        id: response.data.message_id,
        role: 'assistant',
        content: response.data.content,
        temperature: response.data.temperature,
        confidence_score: response.data.confidence_score,
        created_at: new Date().toISOString()
      })

      emit('messageAdded')
      message.success('Message sent')
    } else {
      // Restore user message to input if response incomplete
      newMessage.value = userMessageText
      message.error('Incomplete response from server')
    }
  } catch (error: any) {
    console.error('Error sending message:', error)
    // Restore user message to input on error
    newMessage.value = userMessageText
    message.error(error.response?.data?.error || 'Failed to send message')
  } finally {
    isGenerating.value = false
  }
}

const handleEnterKey = (e: KeyboardEvent) => {
  if (!e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

const openRegenerateModal = (messageId: number, index: number) => {
  regenerateMessageId.value = messageId
  regenerateMessageIndex.value = index
  regenerateTemperature.value = messages.value[index].temperature || 0.2
  showRegenerateModal.value = true
}

const regenerateMessage = async () => {
  if (regenerateMessageId.value === null) return

  isRegenerating.value = true
  try {
    const response = await api.post(`/esrs/conversation/message/${regenerateMessageId.value}/regenerate`, {
      temperature: regenerateTemperature.value
    })

    // Update message in list
    if (regenerateMessageIndex.value !== null) {
      messages.value[regenerateMessageIndex.value] = {
        ...messages.value[regenerateMessageIndex.value],
        content: response.data.content,
        temperature: response.data.temperature,
        confidence_score: response.data.confidence_score,
        regenerated: true
      }
    }

    message.success('Response regenerated')
    showRegenerateModal.value = false
  } catch (error: any) {
    console.error('Error regenerating:', error)
    message.error('Failed to regenerate response')
  } finally {
    isRegenerating.value = false
  }
}

const copyMessage = async (content: string) => {
  try {
    await navigator.clipboard.writeText(content)
    message.success('Copied to clipboard')
  } catch {
    message.error('Failed to copy')
  }
}

const useAsAnswer = async (messageId: number) => {
  console.log('🔵 useAsAnswer called, messageId:', messageId)
  savingAsAnswer.value = messageId
  try {
    console.log('🔵 Calling POST /esrs/conversation/message/' + messageId + '/use-as-answer')
    const response = await api.post(`/esrs/conversation/message/${messageId}/use-as-answer`)
    console.log('🟢 POST response:', response.data)
    
    if (response.data.success) {
      message.success('✅ Saved as final answer!')
      console.log('🔵 Emitting answerSaved event with answer length:', response.data.ai_answer?.length)
      emit('answerSaved', response.data.ai_answer)
    } else {
      console.error('🔴 Backend returned success: false')
      message.error('Failed to save answer')
    }
  } catch (error: any) {
    console.error('🔴 Error saving answer:', error)
    console.error('🔴 Error response:', error.response)
    console.error('🔴 Error status:', error.response?.status)
    message.error('Failed to save answer')
  } finally {
    savingAsAnswer.value = null
  }
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const renderMarkdown = (content: string): string => {
  return marked.parse(content) as string
}

const formatTime = (timestamp: string): string => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

const getConfidenceType = (score: number): 'success' | 'warning' | 'error' => {
  if (score >= 70) return 'success'
  if (score >= 40) return 'warning'
  return 'error'
}

const getTemperatureLabel = (temp: number): string => {
  if (temp <= 0.2) return 'Precise & Factual'
  if (temp <= 0.5) return 'Balanced'
  if (temp <= 0.7) return 'Creative'
  return 'Very Creative'
}
</script>

<style scoped>
.conversation-container {
  width: 100%;
  max-width: 900px;
  margin: 20px auto;
  position: relative;
  z-index: 1;
}

.messages-area {
  max-height: 500px;
  overflow-y: auto;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  padding: 40px 20px;
}

.message-bubble {
  margin-bottom: 16px;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-message {
  margin-left: auto;
  max-width: 70%;
  background: #1890ff;
  color: white;
  padding: 12px 16px;
  border-radius: 12px 12px 0 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.assistant-message {
  max-width: 85%;
  background: white;
  color: #333;
  padding: 12px 16px;
  border-radius: 12px 12px 12px 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
}

.timestamp {
  color: #999;
  font-size: 11px;
  margin-left: 8px;
}

.user-message .timestamp {
  color: rgba(255, 255, 255, 0.8);
}

.message-content {
  line-height: 1.6;
  word-wrap: break-word;
  pointer-events: auto;
}

.markdown-content {
  font-size: 14px;
  color: #333;
}

.markdown-content :deep(p) {
  margin: 8px 0;
  color: #333;
}

.markdown-content :deep(ul), 
.markdown-content :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
  color: #333;
}

.markdown-content :deep(code) {
  background: #f0f0f0;
  color: #333;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 13px;
}

.markdown-content :deep(pre) {
  background: #f0f0f0;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
}

.markdown-content :deep(pre code) {
  background: none;
  padding: 0;
}

.message-artifacts {
  margin-top: 8px;
}

.typing-indicator {
  display: flex;
  align-items: center;
  padding: 12px;
  color: #666;
  font-size: 13px;
}
</style>
