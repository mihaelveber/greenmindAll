<template>
  <div class="chat-interface-wrapper">
    <!-- Skeleton loader while loading conversation -->
    <div v-if="loadingConversation" class="skeleton-loader">
      <n-space vertical size="large">
        <n-skeleton height="80px" round />
        <n-skeleton height="120px" round />
        <n-skeleton height="80px" round />
      </n-space>
    </div>

    <!-- Conversation Timeline -->
    <div v-else class="conversation-timeline">
      <n-scrollbar style="max-height: 450px;">
        <!-- Empty state with animation -->
        <div v-if="conversationHistory.length === 0" class="empty-state">
          <n-icon size="64" color="#a0a0a0" :component="SparklesOutline" class="pulse-icon" />
          <h3 style="margin: 16px 0 8px;">Start refining your answer</h3>
          <p style="color: #909090; font-size: 14px;">Type an instruction below to get AI suggestions</p>
        </div>
        
        <n-timeline v-else size="medium">
          <n-timeline-item
            v-for="(msg, idx) in conversationHistory"
            :key="idx"
            :type="msg.role === 'user' ? 'success' : 'info'"
            :time="formatTime(msg.timestamp)"
            class="timeline-item-animated"
          >
            <template #icon>
              <div class="icon-wrapper" :class="`icon-${msg.role}`">
                <n-icon v-if="msg.role === 'user'" :component="PersonOutline" size="18" />
                <n-icon v-else :component="SparklesOutline" size="18" />
              </div>
            </template>
            
            <template #header>
              <n-text :depth="2" style="font-size: 13px; font-weight: 500;">
                {{ msg.role === 'user' ? '👤 You asked' : '🤖 AI responded' }}
              </n-text>
            </template>
            
            <div class="message-bubble" :class="`message-${msg.role}`">
              <div class="message-text">
                <n-text v-if="msg.role === 'user'" style="font-size: 14px;">{{ msg.content }}</n-text>
                <div v-else v-html="parseMarkdown(msg.content)" class="ai-response"></div>
              </div>
              
              <!-- Version created badge -->
              <div v-if="msg.version_created" class="version-actions">
                <n-divider style="margin: 12px 0;" />
                <n-space align="center" :size="12">
                  <n-tag type="success" size="small" round class="version-badge">
                    <template #icon>
                      <n-icon :component="GitBranchOutline" />
                    </template>
                    v{{ msg.version_number }}
                  </n-tag>
                  <n-button
                    size="small"
                    type="primary"
                    @click="useVersion(msg.version_id)"
                    class="use-version-btn"
                    ghost
                  >
                    ✨ Use This Version
                  </n-button>
                </n-space>
              </div>
            </div>
          </n-timeline-item>
        </n-timeline>
      </n-scrollbar>
    </div>

    <!-- Input Area with modern gradient -->
    <div class="input-area" :class="{ 'input-focused': userMessage.trim() }">
      <n-space vertical size="small">
        <n-space align="center" justify="space-between">
          <n-text style="color: white; font-size: 14px; font-weight: 600; letter-spacing: 0.3px;">
            💡 How should AI refine this?
          </n-text>
          <n-tag size="small" :bordered="false" style="background: rgba(255,255,255,0.25); color: white; font-weight: 500;">
            Ctrl+Enter
          </n-tag>
        </n-space>
        <n-space align="center">
          <n-input
            v-model:value="userMessage"
            type="textarea"
            placeholder="e.g., Make it more formal • Add specific examples • Simplify the language..."
            :autosize="{ minRows: 2, maxRows: 6 }"
            @keydown.enter.ctrl="sendRefinement"
            style="flex: 1;"
            class="refined-input"
          />
          <n-button
            type="primary"
            :loading="loading"
            :disabled="!userMessage.trim()"
            @click="sendRefinement"
            size="large"
            class="send-button"
            strong
          >
            <template #icon>
              <n-icon :component="SendOutline" />
            </template>
            {{ loading ? '✨ Refining...' : 'Send' }}
          </n-button>
        </n-space>
      </n-space>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useMessage } from 'naive-ui'
import { 
  SendOutline, 
  PersonOutline, 
  SparklesOutline, 
  GitBranchOutline
} from '@vicons/ionicons5'
import { marked } from 'marked'
import api from '../services/api'

const props = defineProps<{
  itemType: 'TEXT' | 'CHART' | 'IMAGE' | 'TABLE'
  itemId: number
  disclosureId: number
}>()

const emit = defineEmits<{
  (e: 'refinement-complete', data: any): void
  (e: 'close'): void
}>()

const message = useMessage()
const userMessage = ref('')
const loading = ref(false)
const loadingConversation = ref(true)
const conversationHistory = ref<any[]>([])
const conversationId = ref<string | null>(null)

const parseMarkdown = (text: string) => {
  return marked.parse(text || '')
}

const formatTime = (timestamp: string) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  
  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

// Load existing conversation on mount
const loadConversation = async () => {
  loadingConversation.value = true
  try {
    const response = await api.get(`/conversations/${props.itemType}/${props.itemId}`)
    if (response.data && response.data.messages) {
      conversationHistory.value = response.data.messages
      conversationId.value = response.data.id
    }
  } catch (error: any) {
    // No existing conversation - that's OK
    if (error.response?.status !== 404) {
      console.error('Error loading conversation:', error)
    }
  } finally {
    loadingConversation.value = false
  }
}

// Load conversation when component mounts
import { onMounted } from 'vue'
onMounted(() => {
  loadConversation()
})

const sendRefinement = async () => {
  if (!userMessage.value.trim() || loading.value) return
  
  const currentMessage = userMessage.value
  loading.value = true
  
  // Add user message immediately
  conversationHistory.value.push({
    role: 'user',
    content: currentMessage,
    timestamp: new Date().toISOString()
  })
  
  userMessage.value = ''
  
  try {
    const response = await api.post(`/api/refine/${props.itemType.toLowerCase()}`, {
      disclosure_id: props.disclosureId,
      instruction: currentMessage
    })
    
    // Add AI response
    conversationHistory.value.push({
      role: 'assistant',
      content: response.data.message || 'Refinement completed!',
      timestamp: new Date().toISOString(),
      version_created: true,
      version_number: response.data.version_number,
      version_id: response.data.version_id
    })
    
    message.success('✨ AI refinement completed!')
    emit('refinement-complete', response.data)
    
  } catch (error: any) {
    // Remove user message on error
    conversationHistory.value.pop()
    userMessage.value = currentMessage
    message.error(error.response?.data?.message || 'Failed to refine content')
  } finally {
    loading.value = false
  }
}

const useVersion = async (versionId: string) => {
  try {
    await api.post('/api/versions/select', { version_id: versionId })
    message.success('✓ Version activated!')
    emit('refinement-complete', { version_id: versionId })
  } catch (error) {
    message.error('Failed to activate version')
  }
}
</script>

<style scoped>
.chat-interface-wrapper {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
}

/* Skeleton Loader */
.skeleton-loader {
  padding: 24px;
  background: linear-gradient(to bottom, #fafbfc 0%, #ffffff 100%);
  border-radius: 16px;
  border: 1px solid #e1e4e8;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-state h3 {
  color: #374151;
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.empty-state p {
  color: #6b7280;
  font-size: 14px;
  margin: 8px 0 0;
}

.pulse-icon {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: .7;
    transform: scale(1.05);
  }
}

/* Conversation Timeline */
.conversation-timeline {
  background: linear-gradient(to bottom, #fafbfc 0%, #ffffff 100%);
  padding: 24px;
  border-radius: 16px;
  border: 1px solid #e1e4e8;
  min-height: 250px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

/* Timeline Item Animation */
.timeline-item-animated {
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

/* Icon Wrapper */
.icon-wrapper {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: all 0.2s ease;
}

.icon-wrapper.icon-user {
  background: linear-gradient(135deg, #f3f0ff 0%, #e8deff 100%);
  color: #7c3aed;
}

.icon-wrapper.icon-assistant {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  color: #3b82f6;
}

.icon-wrapper:hover {
  transform: scale(1.1);
}

/* Message Bubbles */
.message-bubble {
  padding: 16px 20px;
  border-radius: 16px;
  margin-top: 8px;
  margin-left: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.message-bubble::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  transition: width 0.3s ease;
}

.message-bubble:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateX(2px);
}

.message-bubble.message-user {
  background: linear-gradient(135deg, #f3f0ff 0%, #e8deff 100%);
}

.message-bubble.message-user::before {
  background: linear-gradient(180deg, #7c3aed 0%, #9333ea 100%);
}

.message-bubble.message-assistant {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
}

.message-bubble.message-assistant::before {
  background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%);
}

.message-text {
  font-size: 14.5px;
  line-height: 1.8;
  color: #1f2937;
  padding-left: 8px;
}

.ai-response {
  font-size: 14.5px;
  line-height: 1.8;
  padding-left: 8px;
}

.ai-response :deep(p) {
  margin: 12px 0;
}

.ai-response :deep(ul),
.ai-response :deep(ol) {
  margin-left: 24px;
  margin: 12px 0;
}

.ai-response :deep(li) {
  margin: 6px 0;
}

.ai-response :deep(strong) {
  font-weight: 700;
  color: #111827;
}

.ai-response :deep(code) {
  background: rgba(0,0,0,0.05);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 13px;
}

/* Version Actions */
.version-actions {
  margin-top: 12px;
  padding-top: 12px;
}

.version-badge {
  animation: badgePulse 2s ease infinite;
  font-weight: 600;
}

@keyframes badgePulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4);
  }
  50% {
    box-shadow: 0 0 0 4px rgba(34, 197, 94, 0);
  }
}

.use-version-btn {
  font-weight: 600;
  transition: all 0.2s ease;
}

.use-version-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
}

/* Input Area */
.input-area {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
  border-radius: 16px;
  box-shadow: 0 8px 16px rgba(102, 126, 234, 0.25);
  transition: all 0.3s ease;
}

.input-area.input-focused {
  box-shadow: 0 12px 24px rgba(102, 126, 234, 0.35);
  transform: translateY(-2px);
}

.refined-input :deep(.n-input__textarea-el) {
  background: rgba(255, 255, 255, 0.98);
  border: 2px solid transparent;
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 14.5px;
  line-height: 1.6;
  transition: all 0.2s ease;
}

.refined-input :deep(.n-input__textarea-el:focus) {
  background: white;
  border-color: rgba(255, 255, 255, 0.5);
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.2);
}

.refined-input :deep(.n-input__textarea-el::placeholder) {
  color: #9ca3af;
  font-style: italic;
}

.send-button {
  border-radius: 12px;
  font-weight: 600;
  transition: all 0.2s ease;
  min-width: 120px;
}

.send-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0,0,0,0.15);
}

.send-button:active:not(:disabled) {
  transform: translateY(0);
}

/* Responsive */
@media (max-width: 768px) {
  .conversation-timeline {
    padding: 16px;
  }
  
  .message-bubble {
    padding: 12px 16px;
  }
  
  .input-area {
    padding: 16px;
  }
}
</style>
