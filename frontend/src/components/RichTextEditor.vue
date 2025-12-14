<template>
  <div class="rich-text-editor-wrapper">
    <QuillEditor
      v-model:content="localContent"
      theme="snow"
      :toolbar="toolbarOptions"
      contentType="html"
      :placeholder="placeholder"
      @update:content="handleUpdate"
      :style="editorStyle"
      class="custom-quill-editor"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'

interface Props {
  modelValue: string
  placeholder?: string
  minHeight?: string
  maxHeight?: string
}

interface Emits {
  (e: 'update:modelValue', value: string): void
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'Write your answer here...',
  minHeight: '300px',
  maxHeight: '600px'
})

const emit = defineEmits<Emits>()

const localContent = ref(props.modelValue || '')

// Toolbar configuration with essential formatting options
const toolbarOptions = [
  ['bold', 'italic', 'underline', 'strike'],        // toggled buttons
  ['blockquote', 'code-block'],
  
  [{ 'header': 1 }, { 'header': 2 }],               // custom button values
  [{ 'list': 'ordered'}, { 'list': 'bullet' }],
  [{ 'script': 'sub'}, { 'script': 'super' }],      // superscript/subscript
  [{ 'indent': '-1'}, { 'indent': '+1' }],          // outdent/indent
  
  [{ 'size': ['small', false, 'large', 'huge'] }],  // custom dropdown
  [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
  
  [{ 'color': [] }, { 'background': [] }],          // dropdown with defaults from theme
  [{ 'align': [] }],
  
  ['link', 'image'],                                // link and image
  ['clean']                                         // remove formatting button
]

const editorStyle = computed(() => ({
  minHeight: props.minHeight,
  maxHeight: props.maxHeight
}))

// Watch for external changes
watch(() => props.modelValue, (newValue) => {
  if (newValue !== localContent.value) {
    localContent.value = newValue || ''
  }
})

// Emit updates with debounce
let updateTimeout: NodeJS.Timeout | null = null
const handleUpdate = (content: string) => {
  if (updateTimeout) clearTimeout(updateTimeout)
  
  updateTimeout = setTimeout(() => {
    emit('update:modelValue', content)
  }, 300) // 300ms debounce
}
</script>

<style scoped>
.rich-text-editor-wrapper {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.3s ease;
}

.rich-text-editor-wrapper:focus-within {
  box-shadow: 0 4px 16px rgba(84, 217, 68, 0.3);
}

:deep(.ql-toolbar) {
  background: linear-gradient(135deg, rgba(84, 217, 68, 0.08) 0%, rgba(84, 217, 68, 0.15) 100%);
  border: 1px solid rgba(84, 217, 68, 0.3) !important;
  border-bottom: 1px solid rgba(84, 217, 68, 0.4) !important;
  border-radius: 8px 8px 0 0;
  padding: 12px 8px;
}

:deep(.ql-container) {
  border: 1px solid rgba(84, 217, 68, 0.3) !important;
  border-top: none !important;
  border-radius: 0 0 8px 8px;
  font-size: 14px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: rgba(0, 0, 0, 0.02);
}

:deep(.ql-editor) {
  min-height: v-bind(minHeight);
  max-height: v-bind(maxHeight);
  overflow-y: auto;
  line-height: 1.6;
  padding: 16px;
}

:deep(.ql-editor.ql-blank::before) {
  color: rgba(150, 150, 150, 0.8);
  font-style: italic;
  font-size: 14px;
}

/* Toolbar button styling */
:deep(.ql-toolbar button) {
  border-radius: 4px;
  transition: all 0.2s ease;
}

:deep(.ql-toolbar button:hover) {
  background: rgba(84, 217, 68, 0.2);
}

:deep(.ql-toolbar button.ql-active) {
  background: rgba(84, 217, 68, 0.3);
  color: #54d944;
}

:deep(.ql-toolbar .ql-stroke) {
  stroke: currentColor;
  transition: stroke 0.2s ease;
}

:deep(.ql-toolbar .ql-fill) {
  fill: currentColor;
  transition: fill 0.2s ease;
}

:deep(.ql-toolbar button:hover .ql-stroke),
:deep(.ql-toolbar button.ql-active .ql-stroke) {
  stroke: #54d944;
}

:deep(.ql-toolbar button:hover .ql-fill),
:deep(.ql-toolbar button.ql-active .ql-fill) {
  fill: #54d944;
}

/* Dropdown styling */
:deep(.ql-picker-label) {
  border-radius: 4px;
  transition: all 0.2s ease;
}

:deep(.ql-picker-label:hover) {
  background: rgba(84, 217, 68, 0.2);
}

:deep(.ql-picker.ql-expanded .ql-picker-label) {
  background: rgba(84, 217, 68, 0.3);
  color: #54d944;
}

/* Editor content styling */
:deep(.ql-editor h1) {
  font-size: 2em;
  margin-bottom: 0.5em;
  color: #54d944;
  font-weight: 600;
}

:deep(.ql-editor h2) {
  font-size: 1.5em;
  margin-bottom: 0.5em;
  color: #54d944;
  font-weight: 600;
}

:deep(.ql-editor h3) {
  font-size: 1.25em;
  margin-bottom: 0.5em;
  color: #54d944;
  font-weight: 600;
}

:deep(.ql-editor blockquote) {
  border-left: 4px solid #54d944;
  padding-left: 16px;
  margin-left: 0;
  font-style: italic;
  color: rgba(0, 0, 0, 0.7);
  background: rgba(84, 217, 68, 0.05);
  padding: 12px 16px;
  border-radius: 0 4px 4px 0;
}

:deep(.ql-editor code) {
  background: rgba(84, 217, 68, 0.1);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.9em;
}

:deep(.ql-editor pre) {
  background: rgba(0, 0, 0, 0.85);
  color: #54d944;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
  border-left: 4px solid #54d944;
}

:deep(.ql-editor a) {
  color: #54d944;
  text-decoration: underline;
  transition: color 0.2s ease;
}

:deep(.ql-editor a:hover) {
  color: #45b837;
}

:deep(.ql-editor ul),
:deep(.ql-editor ol) {
  padding-left: 1.5em;
}

:deep(.ql-editor li) {
  margin-bottom: 0.5em;
}

/* Scrollbar styling */
:deep(.ql-editor::-webkit-scrollbar) {
  width: 8px;
}

:deep(.ql-editor::-webkit-scrollbar-track) {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
}

:deep(.ql-editor::-webkit-scrollbar-thumb) {
  background: rgba(84, 217, 68, 0.4);
  border-radius: 4px;
  transition: background 0.2s ease;
}

:deep(.ql-editor::-webkit-scrollbar-thumb:hover) {
  background: rgba(84, 217, 68, 0.6);
}

/* Animations */
.rich-text-editor-wrapper {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Dark mode support (if needed later) */
@media (prefers-color-scheme: dark) {
  :deep(.ql-container) {
    background: rgba(255, 255, 255, 0.05);
  }
  
  :deep(.ql-editor) {
    color: rgba(255, 255, 255, 0.9);
  }
  
  :deep(.ql-editor blockquote) {
    color: rgba(255, 255, 255, 0.7);
  }
}
</style>
