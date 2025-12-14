<template>
  <div class="esrs-container">
    <!-- Mobile Header with Menu Button -->
    <div class="mobile-header">
      <n-button text @click="showMobileMenu = true" size="large">
        <template #icon>
          <n-icon :component="MenuOutline" size="28" />
        </template>
      </n-button>
      <n-h3 style="margin: 0; flex: 1; text-align: center;">{{ standardMetadata.icon }} {{ standardMetadata.name }}</n-h3>
      <n-button text @click="$router.push('/dashboard')" size="large">
        <template #icon>
          <n-icon :component="ArrowBackOutline" size="24" />
        </template>
      </n-button>
    </div>

    <!-- Mobile Drawer Menu -->
    <n-drawer v-model:show="showMobileMenu" :width="280" placement="left">
      <n-drawer-content :title="`${standardMetadata.icon} ${standardMetadata.name}`" :native-scrollbar="false">
        <n-spin :show="loading">
          <div v-for="category in categories" :key="category.id" class="category-section">
            <div class="category-header">
              <n-text strong>{{ category.name }} ({{ category.code }})</n-text>
            </div>
            
            <n-menu
              :value="selectedStandardId?.toString()"
              :options="getStandardsForCategory(category.id)"
              @update:value="handleStandardSelectMobile"
            />
          </div>
        </n-spin>
      </n-drawer-content>
    </n-drawer>

    <n-layout has-sider>
      <!-- Desktop Sidebar with ESRS standards -->
      <n-layout-sider
        bordered
        :width="300"
        :native-scrollbar="false"
        class="esrs-sidebar desktop-only"
      >
        <div class="sidebar-header">
          <n-space align="center" :size="12">
            <n-button text @click="$router.push('/dashboard')" size="large">
              <template #icon>
                <n-icon :component="ArrowBackOutline" size="24" />
              </template>
            </n-button>
            <n-h3 style="margin: 0;">{{ standardMetadata.icon }} {{ standardMetadata.name }}</n-h3>
          </n-space>
        </div>

        <n-spin :show="loading">
          <div v-for="category in categories" :key="category.id" class="category-section">
            <div class="category-header">
              <n-text strong>{{ category.name }} ({{ category.code }})</n-text>
            </div>
            
            <n-menu
              :value="selectedStandardId?.toString()"
              :options="getStandardsForCategory(category.id)"
              @update:value="handleStandardSelect"
            />
          </div>
        </n-spin>
      </n-layout-sider>

      <!-- Main content area -->
      <n-layout-content content-style="padding: 24px;">
        <n-card v-if="!selectedStandard" :bordered="false">
          <n-empty
            :description="`Select a ${standardMetadata.name} standard from the sidebar to view requirements`"
            size="large"
          >
            <template #icon>
              <n-icon :component="DocumentTextOutline" size="80" color="rgba(255,255,255,0.3)" />
            </template>
          </n-empty>
        </n-card>

        <n-card v-else :bordered="false">
          <template #header>
            <n-space justify="space-between" align="center">
              <n-space vertical :size="8">
                <n-h2 style="margin: 0;">
                  <n-text type="success">{{ selectedStandard.code }}</n-text>: {{ selectedStandard.name }}
                </n-h2>
                <n-text depth="3">{{ selectedStandard.description }}</n-text>
              </n-space>
              <n-button 
                type="primary" 
                :loading="loadingBulkAI"
                @click="startBulkAIGeneration"
                size="large"
              >
                <template #icon>
                  <n-icon :component="SparklesOutline" />
                </template>
                Get AI Answers for All
              </n-button>
            </n-space>
          </template>

          <n-spin :show="loadingDetails">
            <div v-if="selectedStandard.disclosures && selectedStandard.disclosures.length > 0">
              <n-h3>Disclosure Requirements ({{ selectedStandard.disclosures.length }})</n-h3>
              
              <n-collapse>
                <n-collapse-item
                  v-for="disclosure in selectedStandard.disclosures"
                  :key="disclosure.id"
                  :title="`${disclosure.code}: ${disclosure.name}`"
                  :name="disclosure.id.toString()"
                  :id="`disclosure-${disclosure.id}`"
                  class="disclosure-item"
                >
                  <template #header-extra>
                    <n-tag v-if="disclosure.is_mandatory" type="error" size="small">
                      Mandatory
                    </n-tag>
                    <n-tag v-else type="info" size="small">
                      Optional
                    </n-tag>
                  </template>

                  <n-space vertical :size="16">
                    <!-- AI Temperature Control - FIRST ELEMENT -->
                    <n-alert type="info" style="margin-bottom: 16px;">
                      <template #header>
                        <n-space align="center" justify="space-between">
                          <n-text strong>🎯 AI Creativity Level</n-text>
                          <n-tag 
                            :type="(aiTemperatures[disclosure.id] ?? 0.2) <= 0.3 ? 'info' : (aiTemperatures[disclosure.id] ?? 0.2) <= 0.7 ? 'warning' : 'error'" 
                            size="small"
                          >
                            {{ (aiTemperatures[disclosure.id] ?? 0.2) <= 0.3 ? '📊 Factual' : (aiTemperatures[disclosure.id] ?? 0.2) <= 0.7 ? '🎨 Balanced' : '🚀 Creative' }}
                          </n-tag>
                        </n-space>
                      </template>
                      <n-space vertical :size="16">
                        <n-space align="center" :size="12">
                          <n-button size="small" @click="aiTemperatures[disclosure.id] = 0.0; updateAITemperature(disclosure.id)">0.0</n-button>
                          <n-button size="small" @click="aiTemperatures[disclosure.id] = 0.2; updateAITemperature(disclosure.id)">0.2</n-button>
                          <n-button size="small" @click="aiTemperatures[disclosure.id] = 0.5; updateAITemperature(disclosure.id)">0.5</n-button>
                          <n-button size="small" @click="aiTemperatures[disclosure.id] = 0.7; updateAITemperature(disclosure.id)">0.7</n-button>
                          <n-button size="small" @click="aiTemperatures[disclosure.id] = 1.0; updateAITemperature(disclosure.id)">1.0</n-button>
                          <n-input-number 
                            v-model:value="aiTemperatures[disclosure.id]"
                            :min="0"
                            :max="1"
                            :step="0.1"
                            size="small"
                            style="width: 100px;"
                            @update:value="updateAITemperature(disclosure.id)"
                          />
                        </n-space>
                        <n-text depth="3" style="font-size: 12px;">
                          <strong>Current: {{ (aiTemperatures[disclosure.id] ?? 0.2).toFixed(1) }}</strong> - 
                          {{ (aiTemperatures[disclosure.id] ?? 0.2) <= 0.3 
                            ? '📊 Factual & precise - best for data-heavy disclosures' 
                            : (aiTemperatures[disclosure.id] ?? 0.2) <= 0.7 
                            ? '🎨 Balanced creativity - good for most cases'
                            : '🚀 Creative - may hallucinate, use with caution' }}
                        </n-text>
                      </n-space>
                    </n-alert>

                    <div>
                      <n-text strong>Description:</n-text>
                      <n-text>{{ disclosure.description }}</n-text>
                    </div>

                    <div>
                      <n-text strong>Requirement:</n-text>
                      <n-blockquote>
                        {{ disclosure.requirement_text }}
                      </n-blockquote>
                    </div>

                    <!-- Manual Answer Section -->
                    <div v-if="disclosureResponses[disclosure.id]?.manual_answer" class="manual-answer-section">
                      <n-alert type="success" title="Your Answer" closable>
                        <div v-html="disclosureResponses[disclosure.id].manual_answer" style="max-height: 400px; overflow-y: auto;" class="rich-content"></div>
                      </n-alert>
                    </div>

                    <!-- AI Generation Progress -->
                    <div v-if="aiTaskStatus[disclosure.id]" style="margin-top: 16px;">
                      <n-alert type="info" :title="`Generating AI Answer - ${aiTaskStatus[disclosure.id].progress}%`">
                        <n-space vertical :size="8">
                          <n-text>Status: {{ aiTaskStatus[disclosure.id].status }}</n-text>
                          <n-progress 
                            type="line" 
                            :percentage="aiTaskStatus[disclosure.id].progress" 
                            :show-indicator="true"
                            status="info"
                          />
                        </n-space>
                      </n-alert>
                    </div>

                    <!-- AI Answer Section -->
                    <div 
                      v-if="disclosureResponses[disclosure.id]?.ai_answer" 
                      :ref="el => setAIAnswerRef(disclosure.id, el)"
                      class="ai-answer-section"
                    >
                      <n-alert type="info" closable>
                        <template #header>
                          <n-space align="center" justify="space-between">
                            <n-text strong>AI Analysis</n-text>
                            <n-tag 
                              v-if="disclosureResponses[disclosure.id]?.confidence_score != null"
                              :type="disclosureResponses[disclosure.id].confidence_score >= 70 ? 'success' : disclosureResponses[disclosure.id].confidence_score >= 50 ? 'warning' : 'error'"
                              size="small"
                              :bordered="false"
                            >
                              {{ disclosureResponses[disclosure.id].confidence_score >= 70 ? '✅' : '⚠️' }}
                              Confidence: {{ Math.round(disclosureResponses[disclosure.id].confidence_score) }}%
                            </n-tag>
                          </n-space>
                        </template>
                        <div v-html="parseMarkdownToHtml(disclosureResponses[disclosure.id].ai_answer)" style="max-height: 400px; overflow-y: auto;" class="markdown-content"></div>
                        <template #action>
                          <n-space>
                            <n-button
                              text
                              type="success"
                              @click="openChatInterface(disclosure, 'TEXT')"
                            >
                              <template #icon>
                                <n-icon :component="ChatbubbleOutline" />
                              </template>
                              Refine with AI
                            </n-button>
                            <n-button
                              text
                              type="primary"
                              @click="openVersionTree(disclosure, 'TEXT')"
                            >
                              <template #icon>
                                <n-icon :component="GitBranchOutline" />
                              </template>
                              View Versions
                            </n-button>
                            <n-button
                              text
                              type="warning"
                              @click="editAIAnswer(disclosure)"
                            >
                              <template #icon>
                                <n-icon :component="CreateOutline" />
                              </template>
                              Edit This Answer
                            </n-button>
                            <n-button
                              v-if="disclosureResponses[disclosure.id]?.ai_sources"
                              text
                              type="info"
                              @click="openSourcesModal(disclosure.id)"
                            >
                              <template #icon>
                                <n-icon :component="BookOutline" />
                              </template>
                              View Sources
                            </n-button>
                          </n-space>
                        </template>
                      </n-alert>

                      <!-- Start Conversation & AI Explain Buttons -->
                      <n-space style="margin-top: 12px;">
                        <n-button 
                          type="success"
                          :disabled="!disclosureResponses[disclosure.id]?.ai_answer || activeConversations[disclosure.id]"
                          @click="startConversation(disclosure)"
                        >
                          <template #icon>
                            <n-icon>💬</n-icon>
                          </template>
                          {{ activeConversations[disclosure.id] ? 'Conversation Active' : 'Start Conversation' }}
                        </n-button>
                        <n-button 
                          type="info"
                          @click="openAIExplainModal(disclosure)"
                        >
                          <template #icon>
                            <n-icon :component="BulbOutline" />
                          </template>
                          AI Explain
                        </n-button>
                      </n-space>

                      <!-- Conversation Thread Component -->
                      <div v-if="activeConversations[disclosure.id]" style="margin-top: 20px;">
                        <ConversationThread
                          :thread-id="activeConversations[disclosure.id]"
                          :disclosure-code="disclosure.code"
                          @close="closeConversation(disclosure.id)"
                          @message-added="onConversationMessageAdded(disclosure.id)"
                          @answer-saved="onAnswerSavedFromConversation(disclosure.id, $event)"
                        />
                      </div>
                      
                      <!-- Charts Section -->
                      <div v-if="disclosureResponses[disclosure.id]?.chart_data && disclosureResponses[disclosure.id].chart_data.length > 0" style="margin-top: 16px;">
                        <n-card title="📊 Visual Analytics" size="small">
                          <n-space vertical size="large">
                            <div v-for="(chart, idx) in disclosureResponses[disclosure.id].chart_data" :key="chart.id || idx">
                              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <n-space align="center">
                                  <n-checkbox 
                                    :checked="chart.selected_for_report !== false" 
                                    @update:checked="toggleChartSelection(disclosure.id, chart.id)"
                                  >
                                    <n-text strong>{{ chart.title }}</n-text>
                                  </n-checkbox>
                                  <n-tag size="tiny" type="info">{{ chart.selected_for_report !== false ? '✓ In Report' : 'Not in Report' }}</n-tag>
                                </n-space>
                                <n-space>
                                  <n-tag :type="chart.type === 'pie' ? 'success' : chart.type === 'bar' ? 'info' : 'warning'" size="small">
                                    {{ chart.type.toUpperCase() }} Chart
                                  </n-tag>
                                  <n-button size="tiny" type="success" @click="openChartEditorModal(disclosure.id, chart)" ghost>
                                    <template #icon>
                                      <n-icon :component="StatsChartOutline" />
                                    </template>
                                    Manual Edit
                                  </n-button>
                                  <n-button size="tiny" type="primary" @click="openAIEditChartModal(disclosure.id, chart)">
                                    <template #icon>
                                      <n-icon :component="CreateSharp" />
                                    </template>
                                    AI Refine
                                  </n-button>
                                </n-space>
                              </div>
                              <!-- Interactive Chart Rendering -->
                              <ChartRenderer v-if="chart.data && Array.isArray(chart.data)" :chartData="chart" :width="600" :height="400" />
                              <!-- Fallback to PNG if old format -->
                              <img 
                                v-else-if="chart.image_base64"
                                :src="`data:image/png;base64,${chart.image_base64}`" 
                                :alt="chart.title"
                                style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"
                              />
                            </div>
                          </n-space>
                        </n-card>
                      </div>
                      
                      <!-- Tables Section -->
                      <div v-if="disclosureResponses[disclosure.id]?.table_data && disclosureResponses[disclosure.id].table_data.length > 0" style="margin-top: 16px;">
                        <n-card title="📋 Data Tables" size="small">
                          <n-space vertical size="large">
                            <div v-for="(table, idx) in disclosureResponses[disclosure.id].table_data" :key="idx">
                              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <n-text strong>{{ table.title }}</n-text>
                                <n-button size="tiny" type="success" @click="openTableEditorModal(disclosure.id, table)" ghost>
                                  <template #icon>
                                    <n-icon :component="CreateSharp" />
                                  </template>
                                  Edit Table
                                </n-button>
                              </div>
                              <n-data-table
                                :columns="table.headers.map((h: string) => ({ title: h, key: h }))"
                                :data="table.rows.map((r: any[]) => {
                                  const obj: any = {}
                                  table.headers.forEach((h: string, i: number) => { obj[h] = r[i] })
                                  return obj
                                })"
                                :pagination="false"
                                size="small"
                                bordered
                                striped
                              />
                            </div>
                          </n-space>
                        </n-card>
                      </div>
                    </div>

                    <!-- Final Approved Answer for Report -->
                    <div v-if="disclosureResponses[disclosure.id]?.final_answer" class="final-answer-section">
                      <n-alert type="warning" title="✓ Approved Answer for Report" closable>
                        <div v-html="parseMarkdownToHtml(disclosureResponses[disclosure.id].final_answer)" style="max-height: 400px; overflow-y: auto;" class="markdown-content"></div>
                      </n-alert>
                    </div>

                    <!-- Notes Section -->
                    <div v-if="disclosureResponses[disclosure.id]?.notes" class="notes-section">
                      <n-text strong>Your Notes:</n-text>
                      <div style="white-space: pre-wrap; margin-top: 8px;">{{ disclosureResponses[disclosure.id].notes }}</div>
                    </div>

                    <!-- Linked Documents -->
                    <div v-if="linkedDocuments[disclosure.id]?.length > 0" class="linked-docs-section">
                      <n-text strong>Linked Documents ({{ linkedDocuments[disclosure.id].length }}):</n-text>
                      <n-space vertical :size="8" style="margin-top: 8px;">
                        <n-space v-for="evidence in linkedDocuments[disclosure.id]" :key="evidence.id" justify="space-between" style="padding: 8px; background: rgba(255,255,255,0.05); border-radius: 4px;">
                          <n-space>
                            <n-icon :component="DocumentOutline" size="20" :color="evidence.document.is_global ? '#18a0fb' : undefined" />
                            <n-text>{{ evidence.document.file_name }}</n-text>
                            <n-tag v-if="evidence.document.is_global" type="info" size="tiny" :bordered="false">🌐</n-tag>
                          </n-space>
                          <n-button text :type="evidence.document.is_global ? 'warning' : 'error'" size="small" @click="unlinkDocument(evidence.id, disclosure.id)">
                            <template #icon>
                              <n-icon :component="TrashOutline" />
                            </template>
                          </n-button>
                        </n-space>
                      </n-space>
                    </div>

                    <n-divider />

                    <n-space>
                      <n-button 
                        :type="disclosureResponses[disclosure.id]?.is_completed ? 'success' : 'default'" 
                        size="small"
                        @click="toggleCompletion(disclosure.id)"
                      >
                        <template #icon>
                          <n-icon :component="CheckmarkCircleOutline" />
                        </template>
                        {{ disclosureResponses[disclosure.id]?.is_completed ? 'Completed' : 'Mark as Completed' }}
                      </n-button>
                      <n-button size="small" type="info" @click="openUploadEvidenceModal(disclosure)">
                        <template #icon>
                          <n-icon :component="CloudUploadOutline" />
                        </template>
                        Upload Evidence
                      </n-button>
                      <n-button size="small" type="warning" @click="openNotesModal(disclosure)">
                        <template #icon>
                          <n-icon :component="CreateOutline" />
                        </template>
                        Add Notes
                      </n-button>
                      <n-button 
                        size="small" 
                        type="success"
                        @click="openManualAnswerModal(disclosure)"
                      >
                        <template #icon>
                          <n-icon :component="CreateSharp" />
                        </template>
                        {{ disclosureResponses[disclosure.id]?.manual_answer ? '✏️ Edit Answer' : '✍️ Write Answer' }}
                      </n-button>
                      <n-button 
                        size="small" 
                        type="primary" 
                        :loading="loadingAI[disclosure.id]"
                        :disabled="loadingAI[disclosure.id]"
                        @click="getAIAnswer(disclosure)"
                      >
                        <template #icon>
                          <n-icon :component="SparklesOutline" />
                        </template>
                        Get AI Answer
                      </n-button>
                      <n-button 
                        size="small" 
                        type="info"
                        :loading="loadingCharts[disclosure.id]"
                        :disabled="!disclosureResponses[disclosure.id]?.ai_answer"
                        @click="extractChartsAndTables(disclosure.id)"
                      >
                        <template #icon>
                          <n-icon :component="StatsChartOutline" />
                        </template>
                        Extract Charts
                      </n-button>
                      <n-button 
                        size="small" 
                        type="success"
                        :loading="loadingImage[disclosure.id]"
                        :disabled="!disclosureResponses[disclosure.id]?.ai_answer"
                        @click="openGenerateImageModal(disclosure)"
                      >
                        <template #icon>
                          <n-icon :component="ImageOutline" />
                        </template>
                        Generate Image
                      </n-button>
                      <n-button size="small" type="error" @click="openFinalAnswerModal(disclosure)">
                        <template #icon>
                          <n-icon :component="CheckmarkCircleOutline" />
                        </template>
                        Approved Answer
                      </n-button>
                    </n-space>

                    <!-- Sub-disclosures section -->
                    <div v-if="disclosure.sub_disclosures && disclosure.sub_disclosures.length > 0" style="margin-top: 24px;">
                      <n-divider />
                      <n-h4>Sub-disclosure Requirements</n-h4>
                      <n-collapse>
                        <n-collapse-item
                          v-for="subDisclosure in disclosure.sub_disclosures"
                          :key="`sub-${subDisclosure.id}`"
                          :title="`└─ ${subDisclosure.code}: ${subDisclosure.name}`"
                          :name="`sub-${subDisclosure.id}`"
                          class="sub-disclosure"
                        >
                  <n-space vertical :size="16">
                    <div>
                      <n-text strong>Description:</n-text>
                      <n-text>{{ subDisclosure.description }}</n-text>
                    </div>

                    <div>
                      <n-text strong>Requirement:</n-text>
                      <n-blockquote>
                        {{ subDisclosure.requirement_text }}
                      </n-blockquote>
                    </div>

                    <!-- Manual Answer -->
                    <div v-if="disclosureResponses[subDisclosure.id]?.manual_answer" class="manual-answer-section">
                      <n-alert type="success" title="Your Answer" closable>
                        <div v-html="disclosureResponses[subDisclosure.id].manual_answer" style="max-height: 400px; overflow-y: auto;" class="rich-content"></div>
                      </n-alert>
                    </div>

                    <!-- AI Generation Progress -->
                    <div v-if="aiTaskStatus[subDisclosure.id]" style="margin-top: 16px;">
                      <n-alert type="info" :title="`Generating AI Answer - ${aiTaskStatus[subDisclosure.id].progress}%`">
                        <n-space vertical :size="8">
                          <n-text>Status: {{ aiTaskStatus[subDisclosure.id].status }}</n-text>
                          <n-progress 
                            type="line" 
                            :percentage="aiTaskStatus[subDisclosure.id].progress" 
                            :show-indicator="true"
                            status="info"
                          />
                        </n-space>
                      </n-alert>
                    </div>

                    <!-- AI Answer -->
                    <div v-if="disclosureResponses[subDisclosure.id]?.ai_answer" class="ai-answer-section">
                      <n-alert type="info" title="AI Analysis" closable>
                        <div v-html="parseMarkdownToHtml(disclosureResponses[subDisclosure.id].ai_answer)" style="max-height: 400px; overflow-y: auto;" class="markdown-content"></div>
                        <template #action>
                          <n-button
                            v-if="disclosureResponses[subDisclosure.id]?.ai_sources"
                            text
                            type="info"
                            @click="openSourcesModal(subDisclosure.id)"
                          >
                            <template #icon>
                              <n-icon :component="BookOutline" />
                            </template>
                            View Sources
                          </n-button>
                        </template>
                      </n-alert>
                      
                      <!-- Charts Section -->
                      <div v-if="disclosureResponses[subDisclosure.id]?.chart_data && disclosureResponses[subDisclosure.id].chart_data.length > 0" style="margin-top: 16px;">
                        <n-card title="📊 Visual Analytics" size="small">
                          <n-space vertical size="large">
                            <div v-for="(chart, idx) in disclosureResponses[subDisclosure.id].chart_data" :key="chart.id || idx">
                              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <n-space align="center">
                                  <n-checkbox 
                                    :checked="chart.selected_for_report !== false" 
                                    @update:checked="toggleChartSelection(subDisclosure.id, chart.id)"
                                  >
                                    <n-text strong>{{ chart.title }}</n-text>
                                  </n-checkbox>
                                </n-space>
                                <n-space>
                                  <n-tag :type="chart.type === 'pie' ? 'success' : chart.type === 'bar' ? 'info' : 'warning'" size="small">
                                    {{ chart.type.toUpperCase() }} Chart
                                  </n-tag>
                                  <n-button size="tiny" type="success" @click="openChartEditorModal(subDisclosure.id, chart)" ghost>
                                    <template #icon>
                                      <n-icon :component="StatsChartOutline" />
                                    </template>
                                    Manual Edit
                                  </n-button>
                                  <n-button size="tiny" type="primary" @click="openAIEditChartModal(subDisclosure.id, chart)">
                                    <template #icon>
                                      <n-icon :component="CreateSharp" />
                                    </template>
                                    AI Refine
                                  </n-button>
                                </n-space>
                              </div>
                              <!-- Interactive Chart Rendering -->
                              <ChartRenderer v-if="chart.data && Array.isArray(chart.data)" :chartData="chart" :width="600" :height="400" />
                              <!-- Fallback to PNG if old format -->
                              <img 
                                v-else-if="chart.image_base64"
                                :src="`data:image/png;base64,${chart.image_base64}`" 
                                :alt="chart.title"
                                style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"
                              />
                            </div>
                          </n-space>
                        </n-card>
                      </div>
                      
                      <!-- Tables Section -->
                      <div v-if="disclosureResponses[subDisclosure.id]?.table_data && disclosureResponses[subDisclosure.id].table_data.length > 0" style="margin-top: 16px;">
                        <n-card title="📋 Data Tables" size="small">
                          <n-space vertical size="large">
                            <div v-for="(table, idx) in disclosureResponses[subDisclosure.id].table_data" :key="idx">
                              <n-space justify="space-between" align="center" style="margin-bottom: 8px;">
                                <n-text strong>{{ table.title }}</n-text>
                                <n-button size="tiny" type="primary" @click="openTableEditorModal(subDisclosure.id, table, idx)">
                                  <template #icon>
                                    <n-icon :component="CreateOutline" />
                                  </template>
                                  Edit Table
                                </n-button>
                              </n-space>
                              <n-data-table
                                :columns="table.headers.map((h: string) => ({ title: h, key: h }))"
                                :data="table.rows.map((r: any[]) => {
                                  const obj: any = {}
                                  table.headers.forEach((h: string, i: number) => { obj[h] = r[i] })
                                  return obj
                                })"
                                :pagination="false"
                                size="small"
                              />
                            </div>
                          </n-space>
                        </n-card>
                      </div>
                    </div>

                    <!-- Final Answer -->
                    <div v-if="disclosureResponses[subDisclosure.id]?.final_answer" class="final-answer-section">
                      <n-alert type="warning" title="✓ Approved Answer for Report" closable>
                        <div v-html="parseMarkdownToHtml(disclosureResponses[subDisclosure.id].final_answer)" style="max-height: 400px; overflow-y: auto;" class="markdown-content"></div>
                      </n-alert>
                    </div>

                    <!-- Notes -->
                    <div v-if="disclosureResponses[subDisclosure.id]?.notes" class="notes-section">
                      <n-text strong>Your Notes:</n-text>
                      <div style="white-space: pre-wrap; margin-top: 8px;">{{ disclosureResponses[subDisclosure.id].notes }}</div>
                    </div>

                    <!-- Linked Documents -->
                    <div v-if="linkedDocuments[subDisclosure.id]?.length > 0" class="linked-docs-section">
                      <n-text strong>Linked Documents ({{ linkedDocuments[subDisclosure.id].length }}):</n-text>
                      <n-space vertical :size="8" style="margin-top: 8px;">
                        <n-space v-for="evidence in linkedDocuments[subDisclosure.id]" :key="evidence.id" justify="space-between" style="padding: 8px; background: rgba(255,255,255,0.05); border-radius: 4px;">
                          <n-space>
                            <n-icon :component="DocumentOutline" size="20" :color="evidence.document.is_global ? '#18a0fb' : undefined" />
                            <n-text>{{ evidence.document.file_name }}</n-text>
                            <n-tag v-if="evidence.document.is_global" type="info" size="tiny" :bordered="false">🌐</n-tag>
                          </n-space>
                          <n-button text :type="evidence.document.is_global ? 'warning' : 'error'" size="small" @click="unlinkDocument(evidence.id, subDisclosure.id)">
                            <template #icon>
                              <n-icon :component="TrashOutline" />
                            </template>
                          </n-button>
                        </n-space>
                      </n-space>
                    </div>

                    <n-divider />

                    <n-space>
                      <n-button 
                        :type="disclosureResponses[subDisclosure.id]?.is_completed ? 'success' : 'default'" 
                        size="small"
                        @click="toggleCompletion(subDisclosure.id)"
                      >
                        <template #icon>
                          <n-icon :component="CheckmarkCircleOutline" />
                        </template>
                        {{ disclosureResponses[subDisclosure.id]?.is_completed ? 'Completed' : 'Mark as Completed' }}
                      </n-button>
                      <n-button size="small" type="info" @click="openUploadEvidenceModal(subDisclosure)">
                        <template #icon>
                          <n-icon :component="CloudUploadOutline" />
                        </template>
                        Upload Evidence
                      </n-button>
                      <n-button size="small" type="warning" @click="openNotesModal(subDisclosure)">
                        <template #icon>
                          <n-icon :component="CreateOutline" />
                        </template>
                        Add Notes
                      </n-button>
                      <n-button 
                        size="small" 
                        type="primary" 
                        :loading="loadingAI[subDisclosure.id]"
                        @click="getAIAnswer(subDisclosure)"
                      >
                        <template #icon>
                          <n-icon :component="SparklesOutline" />
                        </template>
                        Get AI Answer
                      </n-button>
                      <n-button size="small" type="error" @click="openFinalAnswerModal(subDisclosure)">
                        <template #icon>
                          <n-icon :component="CheckmarkCircleOutline" />
                        </template>
                        Approved Answer
                      </n-button>
                    </n-space>
                  </n-space>
                        </n-collapse-item>
                      </n-collapse>
                    </div>
                  </n-space>
                </n-collapse-item>
              </n-collapse>
            </div>

            <n-empty v-else description="No disclosure requirements found" />
          </n-spin>
        </n-card>
      </n-layout-content>
    </n-layout>

    <!-- Add Notes Modal -->
    <n-modal v-model:show="showNotesModal" preset="dialog" title="Add Notes" style="width: 600px;">
      <n-space vertical :size="16">
        <div v-if="currentDisclosure">
          <n-text strong style="font-size: 16px;">{{ currentDisclosure.code }}: {{ currentDisclosure.name }}</n-text>
        </div>
        <n-input
          v-model:value="notesText"
          type="textarea"
          placeholder="Enter your notes here..."
          :rows="10"
        />
      </n-space>
      <template #action>
        <n-space>
          <n-button @click="showNotesModal = false">Cancel</n-button>
          <n-button type="primary" @click="saveNotes" :loading="savingNotes">
            Save Notes
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- Manual Answer Modal -->
    <n-modal v-model:show="showManualAnswerModal" preset="dialog" :title="manualAnswerText ? '✏️ Edit Your Answer' : '✍️ Write Your Answer'" style="width: 900px; max-width: 95vw;">
      <n-space vertical :size="16">
        <div v-if="currentDisclosure">
          <n-text strong style="font-size: 16px;">{{ currentDisclosure.code }}: {{ currentDisclosure.name }}</n-text>
          <n-text depth="3" style="display: block; margin-top: 8px;">{{ currentDisclosure.requirement_text }}</n-text>
        </div>
        <n-alert type="info" size="small">
          💡 Use the rich text editor below. Format your answer with headings, lists, bold, italic, and more!
        </n-alert>
        <RichTextEditor
          v-model="manualAnswerText"
          placeholder="Enter your answer to this disclosure requirement..."
          min-height="400px"
          max-height="500px"
        />
      </n-space>
      <template #action>
        <n-space>
          <n-button @click="showManualAnswerModal = false">Cancel</n-button>
          <n-button type="primary" @click="saveManualAnswer" :loading="savingManualAnswer">
            Save Answer
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- Final Answer Modal -->
    <n-modal v-model:show="showFinalAnswerModal" preset="dialog" title="✓ Approved Answer for Report" style="width: 900px; max-width: 95vw;">
      <n-space vertical :size="16">
        <div v-if="currentDisclosure">
          <n-text strong style="font-size: 16px;">{{ currentDisclosure.code }}: {{ currentDisclosure.name }}</n-text>
          <n-text depth="3" style="display: block; margin-top: 8px;">{{ currentDisclosure.requirement_text }}</n-text>
        </div>
        <n-alert type="success" style="margin-bottom: 12px;">
          ✅ Official answer for ESRS reports. Format with the rich text editor for professional documents.
        </n-alert>
        <RichTextEditor
          v-model="finalAnswerText"
          placeholder="Enter the final approved answer for official reports..."
          min-height="400px"
          max-height="500px"
        />
      </n-space>
      <template #action>
        <n-space>
          <n-button @click="showFinalAnswerModal = false">Cancel</n-button>
          <n-button type="error" @click="saveFinalAnswer" :loading="savingFinalAnswer">
            Save Approved Answer
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- Chat Interface Modal -->
    <n-modal v-model:show="showChatInterface" style="width: 800px; max-height: 80vh;">
      <ChatInterface
        v-if="showChatInterface && currentDisclosure"
        :item-type="chatItemType"
        :item-id="chatItemId"
        :disclosure-id="chatDisclosureId"
        @close="showChatInterface = false"
        @refinement-complete="onRefinementComplete"
      />
    </n-modal>

    <!-- Chart Editor Modal -->
    <n-modal v-model:show="showChartEditorModal" style="width: 95vw; max-width: 1200px;">
      <n-card title="📊 Chart Editor" :bordered="false" size="large" style="background: rgba(0,0,0,0.85);">
        <template #header-extra>
          <n-button text @click="showChartEditorModal = false">
            <template #icon>
              <n-icon :component="CloseOutline" />
            </template>
          </n-button>
        </template>
        <ChartEditor
          v-if="showChartEditorModal && editingChartData"
          :chart-data="editingChartData"
          @save="handleSaveChart"
          @cancel="showChartEditorModal = false"
        />
      </n-card>
    </n-modal>

    <!-- Table Editor Modal -->
    <n-modal v-model:show="showTableEditorModal" style="width: 95vw; max-width: 1200px;">
      <n-card title="📋 Table Editor" :bordered="false" size="large" style="background: rgba(0,0,0,0.85);">
        <template #header-extra>
          <n-button text @click="showTableEditorModal = false">
            <template #icon>
              <n-icon :component="CloseOutline" />
            </template>
          </n-button>
        </template>
        <TableEditor
          v-if="showTableEditorModal && editingTableData"
          :table-data="editingTableData"
          @save="handleSaveTable"
          @cancel="showTableEditorModal = false"
        />
      </n-card>
    </n-modal>

    <!-- Version Tree Modal -->
    <n-modal v-model:show="showVersionTreeModal" style="width: 95vw; max-width: 1000px;">
      <n-card title="🌳 Version History" :bordered="false" size="large" style="background: rgba(0,0,0,0.85);">
        <template #header-extra>
          <n-button text @click="showVersionTreeModal = false">
            <template #icon>
              <n-icon :component="CloseOutline" />
            </template>
          </n-button>
        </template>
        <VersionTree
          v-if="showVersionTreeModal"
          :item-type="versionTreeItemType"
          :item-id="versionTreeItemId"
          @version-selected="onVersionSelected"
        />
      </n-card>
    </n-modal>

    <!-- Generate Image Modal -->
    <n-modal v-model:show="showGenerateImageModal" preset="dialog" title="🎨 Generate Image with AI" style="width: 700px;">
      <n-space vertical :size="16">
        <div v-if="currentImageDisclosure">
          <n-text strong style="font-size: 16px;">{{ currentImageDisclosure.code }}: {{ currentImageDisclosure.name }}</n-text>
          <n-alert type="info" style="margin-top: 8px;">
            Describe the image you want to generate. AI will create a professional visualization based on your prompt.
          </n-alert>
        </div>
        
        <n-input
          v-model:value="imagePrompt"
          type="textarea"
          placeholder="Example: Create a professional infographic showing gender diversity metrics with pie charts and modern design"
          :rows="6"
        />
        
        <n-alert type="warning" title="💡 Tips">
          <ul style="margin: 0; padding-left: 20px;">
            <li>Be specific about style (professional, modern, minimalist, etc.)</li>
            <li>Mention what data to visualize</li>
            <li>Specify chart types if needed (pie chart, bar graph, infographic)</li>
            <li>You can refine the image later with additional instructions</li>
          </ul>
        </n-alert>
      </n-space>
      
      <template #action>
        <n-space>
          <n-button @click="showGenerateImageModal = false">Cancel</n-button>
          <n-button type="success" @click="generateImage" :loading="loadingImage[currentImageDisclosure?.id || 0]" :disabled="!imagePrompt">
            <template #icon>
              <n-icon :component="ImageOutline" />
            </template>
            Generate Image
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- AI Explain Modal -->
    <n-modal v-model:show="showAIExplainModal" preset="card" title="💡 AI Explain - What Should I Answer?" style="width: 900px; max-height: 85vh;">
      <n-scrollbar style="max-height: 70vh;">
        <n-space vertical :size="16">
          <div v-if="currentExplainDisclosure">
            <n-alert type="info">
              <template #header>
                <n-text strong>{{ currentExplainDisclosure.code }}: {{ currentExplainDisclosure.name }}</n-text>
              </template>
              <div style="margin-top: 8px;">
                <n-text depth="3" style="font-size: 13px;">Ask AI to explain what should be included in your answer for this disclosure. AI will use the ESRS requirements and your linked documents to provide guidance.</n-text>
              </div>
            </n-alert>
          </div>

          <!-- Question Input -->
          <n-card title="❓ Your Question" size="small">
            <n-input
              v-model:value="aiExplainQuestion"
              type="textarea"
              placeholder="Example: What exactly should I include in this disclosure? What are the key requirements? Can you give me examples based on my documents?"
              :rows="4"
              :disabled="loadingExplain"
            />
            <template #footer>
              <n-space justify="end">
                <n-button 
                  type="primary" 
                  :loading="loadingExplain" 
                  :disabled="!aiExplainQuestion.trim()"
                  @click="getAIExplanation"
                >
                  <template #icon>
                    <n-icon :component="SparklesOutline" />
                  </template>
                  Get AI Explanation
                </n-button>
              </n-space>
            </template>
          </n-card>

          <!-- AI Answer Display -->
          <n-card v-if="aiExplainAnswer" title="🤖 AI Explanation" size="small">
            <div v-html="parseMarkdownToHtml(aiExplainAnswer)" class="markdown-content" style="line-height: 1.8;"></div>
            <template #footer>
              <n-space justify="end">
                <n-button 
                  text
                  type="info"
                  @click="copyToClipboard(aiExplainAnswer)"
                >
                  <template #icon>
                    <n-icon :component="DownloadOutline" />
                  </template>
                  Copy Explanation
                </n-button>
              </n-space>
            </template>
          </n-card>

          <n-alert type="warning" title="💡 Note" v-if="!aiExplainAnswer">
            This explanation is for your guidance only and won't be saved. Use it to understand what to write in your actual answer.
          </n-alert>
        </n-space>
      </n-scrollbar>
    </n-modal>

    <!-- Upload Evidence Modal -->
    <n-modal v-model:show="showUploadModal" preset="dialog" title="📎 Upload Evidence for This Question" style="width: 800px;">
      <n-space vertical :size="16">
        <div v-if="currentDisclosure">
          <n-text strong style="font-size: 16px;">{{ currentDisclosure.code }}: {{ currentDisclosure.name }}</n-text>
          <n-alert type="info" style="margin-top: 8px;">
            Documents uploaded here will be linked specifically to this question only.
          </n-alert>
        </div>

        <!-- Already Linked Documents Section -->
        <n-card v-if="currentDisclosure && linkedDocuments[currentDisclosure.id]?.length > 0" title="✅ Evidence for This Question" size="small" :bordered="true" style="border-color: #54d944;">
          <n-alert type="info" size="small" style="margin-bottom: 12px;">
            🌐 <strong>Global documents</strong> are automatically available for all questions. <strong>Question-specific documents</strong> are linked only to this question.
          </n-alert>
          <n-space vertical :size="8">
            <!-- All Linked Documents (Global + Question-Specific) -->
            <div
              v-for="evidence in linkedDocuments[currentDisclosure.id]"
              :key="evidence.id"
              :style="{
                padding: '12px',
                background: evidence.document.is_global ? 'rgba(24, 160, 251, 0.1)' : 'rgba(84, 217, 68, 0.1)',
                border: evidence.document.is_global ? '1px solid rgba(24, 160, 251, 0.3)' : '1px solid rgba(84, 217, 68, 0.3)',
                borderRadius: '8px'
              }"
            >
              <n-space justify="space-between" align="center">
                <n-space>
                  <n-icon :component="DocumentOutline" size="24" :color="evidence.document.is_global ? '#18a0fb' : '#54d944'" />
                  <n-space vertical :size="2">
                    <n-space align="center" :size="8">
                      <n-text strong>{{ evidence.document.file_name }}</n-text>
                      <n-tag v-if="evidence.document.is_global" type="info" size="small" :bordered="false">
                        🌐 Global
                      </n-tag>
                    </n-space>
                    <n-text depth="3" style="font-size: 12px;">
                      {{ (evidence.document.file_size / 1024).toFixed(2) }} KB • Linked {{ new Date(evidence.linked_at).toLocaleDateString() }}
                    </n-text>
                    <n-text v-if="evidence.notes && evidence.notes !== 'Auto-linked global document'" depth="2" style="font-size: 12px; font-style: italic;">
                      📝 {{ evidence.notes }}
                    </n-text>
                    <n-text v-if="evidence.document.is_global" depth="3" style="font-size: 11px; color: #18a0fb;">
                      ✨ Auto-linked to all questions
                    </n-text>
                  </n-space>
                </n-space>
                <n-button
                  :type="evidence.document.is_global ? 'warning' : 'error'"
                  size="small"
                  ghost
                  @click="unlinkDocument(evidence.id, currentDisclosure!.id)"
                >
                  <template #icon>
                    <n-icon :component="TrashOutline" />
                  </template>
                  {{ evidence.document.is_global ? 'Exclude' : 'Unlink' }}
                </n-button>
              </n-space>
            </div>
          </n-space>
        </n-card>

        <!-- Excluded Global Documents Section -->
        <n-card v-if="currentDisclosure && excludedDocuments[currentDisclosure.id]?.length > 0" title="🚫 Excluded Global Documents" size="small" :bordered="true" style="border-color: #f5a623; margin-top: 16px;">
          <n-alert type="warning" size="small" style="margin-bottom: 12px;">
            These global documents were excluded from this question. You can re-link them if they're relevant.
          </n-alert>
          <n-space vertical :size="8">
            <div
              v-for="evidence in excludedDocuments[currentDisclosure.id]"
              :key="evidence.id"
              style="padding: 12px; background: rgba(245, 166, 35, 0.1); border: 1px solid rgba(245, 166, 35, 0.3); border-radius: 8px;"
            >
              <n-space justify="space-between" align="center">
                <n-space>
                  <n-icon :component="DocumentOutline" size="24" color="#f5a623" />
                  <n-space vertical :size="2">
                    <n-space align="center" :size="8">
                      <n-text strong style="color: #666;">{{ evidence.document.file_name }}</n-text>
                      <n-tag type="warning" size="small" :bordered="false">
                        🌐 Global (Excluded)
                      </n-tag>
                    </n-space>
                    <n-text depth="3" style="font-size: 12px;">
                      {{ (evidence.document.file_size / 1024).toFixed(2) }} KB • Originally linked {{ new Date(evidence.linked_at).toLocaleDateString() }}
                    </n-text>
                  </n-space>
                </n-space>
                <n-button
                  type="success"
                  size="small"
                  ghost
                  @click="relinkDocument(evidence.id, currentDisclosure!.id)"
                >
                  <template #icon>
                    <n-icon :component="AddOutline" />
                  </template>
                  Re-Link
                </n-button>
              </n-space>
            </div>
          </n-space>
        </n-card>

        <n-divider v-if="currentDisclosure && linkedDocuments[currentDisclosure.id]?.length > 0">Add More Evidence</n-divider>

        <!-- Upload New Document Section (Question-Specific) -->
        <n-card title="📤 Upload New Document (For This Question Only)" size="small" :bordered="true">
          <n-upload
            multiple
            :file-list="uploadFileList"
            @update:file-list="handleFileListUpdate"
            :custom-request="handleUploadInModal"
            :show-file-list="true"
          >
            <n-upload-dragger>
              <div style="padding: 20px;">
                <n-icon size="48" :component="CloudUploadOutline" color="#54d944" />
                <n-text style="font-size: 16px; display: block; margin-top: 12px;">
                  Click or drag file to upload
                </n-text>
                <n-text depth="3" style="font-size: 12px; display: block; margin-top: 8px;">
                  PDF, Word, Excel, Images supported
                </n-text>
              </div>
            </n-upload-dragger>
          </n-upload>
          
          <n-divider style="margin: 12px 0;">OR</n-divider>
          
          <n-upload
            multiple
            :custom-request="handleUploadInModal"
            :show-file-list="false"
          >
            <n-button type="primary" size="large" block>
              <template #icon>
                <n-icon :component="CloudUploadOutline" />
              </template>
              Browse Files on Computer
            </n-button>
          </n-upload>
        </n-card>

      </n-space>
      <template #action>
        <n-space>
          <n-button @click="showUploadModal = false">Close</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- AI Edit Chart Modal -->
    <n-modal
      v-model:show="showAIEditChartModal"
      preset="card"
      title="🤖 AI Edit Chart Labels"
      style="width: 600px;"
    >
      <template #default>
        <n-space vertical :size="16">
          <n-alert type="info" title="Instruction">
            Tell AI how to improve the chart labels or title. For example: "daj moški/ženska" or "use English labels" or "shorten the labels"
          </n-alert>
          
          <n-input
            v-model:value="aiEditInstructionText"
            type="textarea"
            placeholder="E.g., 'daj moški/ženska namesto men/women' or 'make labels shorter'"
            :rows="4"
          />

          <n-space justify="end">
            <n-button @click="showAIEditChartModal = false">Cancel</n-button>
            <n-button 
              type="primary" 
              :loading="savingAIEdit"
              @click="handleAIEditChart"
            >
              Apply AI Changes
            </n-button>
          </n-space>
        </n-space>
      </template>
    </n-modal>

    <!-- Sources Modal -->
    <n-modal
      v-model:show="showSourcesModal"
      preset="card"
      title="📚 AI Answer Sources"
      :style="{ width: '900px', maxHeight: '80vh' }"
      :bordered="false"
    >
      <n-scrollbar style="max-height: 60vh;">
        <n-space vertical :size="16" v-if="currentSources">
          <!-- Linked Documents Section -->
          <n-card v-if="currentSources.linked_documents?.length > 0" title="📎 Question-Specific Documents" :bordered="true" size="small">
            <n-text depth="3">These documents were specifically linked to this ESRS disclosure:</n-text>
            <n-list bordered style="margin-top: 12px;">
              <n-list-item v-for="doc in currentSources.linked_documents" :key="doc.id">
                <template #prefix>
                  <n-icon :component="DocumentOutline" size="24" color="#faad14" />
                </template>
                <n-thing :title="doc.file_name">
                  <template #description>
                    <n-space :size="8">
                      <n-tag size="small" :bordered="false">{{ doc.file_type }}</n-tag>
                      <n-tag v-if="doc.rag_processing_status === 'processing'" type="warning" size="small" :bordered="false">
                        <template #icon><n-spin :size="12" /></template>
                        Processing for AI...
                      </n-tag>
                      <n-tag v-else-if="doc.rag_processing_status === 'completed'" type="success" size="small" :bordered="false">
                        ✓ Ready ({{ doc.rag_chunks_count }} chunks)
                      </n-tag>
                      <n-tag v-else-if="doc.rag_processing_status === 'failed'" type="error" size="small" :bordered="false">
                        ✗ Processing failed
                      </n-tag>
                      <n-text depth="3" style="font-size: 12px;">Uploaded: {{ formatDate(doc.uploaded_at) }}</n-text>
                    </n-space>
                    <div v-if="doc.notes" style="margin-top: 8px; padding: 8px; background: rgba(250, 173, 20, 0.1); border-radius: 4px;">
                      <n-text depth="2" style="font-size: 12px;">📝 {{ doc.notes }}</n-text>
                    </div>
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
          </n-card>

          <!-- Global Documents Section -->
          <n-card v-if="currentSources.global_documents?.length > 0" title="🌐 Global Documents" :bordered="true" size="small">
            <n-text depth="3">These documents were available to AI for all ESRS questions:</n-text>
            <n-list bordered style="margin-top: 12px;">
              <n-list-item v-for="doc in currentSources.global_documents" :key="doc.id">
                <template #prefix>
                  <n-icon :component="doc.is_website ? GlobeOutline : DocumentOutline" size="24" :color="doc.is_website ? '#54d944' : '#52c41a'" />
                </template>
                <n-thing :title="doc.file_name">
                  <template #description>
                    <n-space :size="8">
                      <n-tag v-if="doc.is_website" type="success" size="small" :bordered="false">Company Website</n-tag>
                      <n-tag v-else size="small" :bordered="false">{{ doc.file_type }}</n-tag>
                      <n-tag v-if="doc.rag_processing_status === 'processing'" type="warning" size="small" :bordered="false">
                        <template #icon><n-spin :size="12" /></template>
                        Processing for AI...
                      </n-tag>
                      <n-tag v-else-if="doc.rag_processing_status === 'completed'" type="success" size="small" :bordered="false">
                        ✓ Ready ({{ doc.rag_chunks_count }} chunks)
                      </n-tag>
                      <n-tag v-else-if="doc.rag_processing_status === 'failed'" type="error" size="small" :bordered="false">
                        ✗ Processing failed
                      </n-tag>
                      <n-text depth="3" style="font-size: 12px;">Uploaded: {{ formatDate(doc.uploaded_at) }}</n-text>
                    </n-space>
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
          </n-card>

          <!-- User Provided Info Section -->
          <n-card v-if="currentSources.user_provided?.has_notes || currentSources.user_provided?.has_manual_answer" 
                  title="📝 Your Input" :bordered="true" size="small">
            <n-space vertical :size="8">
              <n-alert v-if="currentSources.user_provided.has_notes" type="info" :bordered="false">
                ✓ AI considered your notes for this disclosure
              </n-alert>
              <n-alert v-if="currentSources.user_provided.has_manual_answer" type="success" :bordered="false">
                ✓ AI analyzed your manual answer
              </n-alert>
            </n-space>
          </n-card>

          <!-- No Sources Info -->
          <n-alert v-if="!hasSources" type="warning" :bordered="false">
            No specific sources were recorded for this AI answer. This may be from an older generation before source tracking was implemented.
          </n-alert>
        </n-space>
      </n-scrollbar>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showSourcesModal = false">Close</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  useMessage,
  NLayout,
  NLayoutSider,
  NLayoutContent,
  NCard,
  NH2,
  NH3,
  NH4,
  NText,
  NButton,
  NIcon,
  NSpin,
  NEmpty,
  NMenu,
  NProgress,
  NSpace,
  NCollapse,
  NCollapseItem,
  NTag,
  NBlockquote,
  NDivider,
  NModal,
  NInput,
  NAlert,
  NDrawer,
  NDrawerContent,
  NUpload,
  NUploadDragger,
  NScrollbar,
  NList,
  NListItem,
  NThing,
  NCheckbox,
  NDataTable,
  NInputNumber,
  type MenuOption,
  type UploadFileInfo,
  type UploadCustomRequestOptions
} from 'naive-ui'
import {
  DocumentTextOutline,
  ArrowBackOutline,
  CheckmarkCircleOutline,
  CreateOutline,
  CloudUploadOutline,
  SparklesOutline,
  DocumentOutline,
  TrashOutline,
  MenuOutline,
  BookOutline,
  GlobeOutline,
  AddOutline,
  LinkOutline,
  CreateSharp,
  StatsChartOutline,
  ImageOutline,
  ChatbubbleOutline,
  CloseOutline,
  DownloadOutline,
  GitBranchOutline,
  BulbOutline
} from '@vicons/ionicons5'
import api from '../services/api'
import { h } from 'vue'
import ChartRenderer from '../components/ChartRenderer.vue'
import ChatInterface from '../components/ChatInterface.vue'
import RichTextEditor from '../components/RichTextEditor.vue'
import ChartEditor from '../components/ChartEditor.vue'
import TableEditor from '../components/TableEditor.vue'
import VersionTree from '../components/VersionTree.vue'
import ConversationThread from '../components/ConversationThread.vue'

// Simple Markdown to HTML parser (no external dependencies)
const parseMarkdownToHtml = (mdText: string): string => {
  if (!mdText) return ''
  
  let html = mdText
  
  // Headers
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>')
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>')
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>')
  
  // Bold
  html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
  html = html.replace(/__(.*?)__/gim, '<strong>$1</strong>')
  
  // Italic
  html = html.replace(/\*(.*?)\*/gim, '<em>$1</em>')
  html = html.replace(/_(.*?)_/gim, '<em>$1</em>')
  
  // Lists
  html = html.replace(/^\* (.*$)/gim, '<li>$1</li>')
  html = html.replace(/^- (.*$)/gim, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
  
  // Line breaks
  html = html.replace(/\n\n/g, '</p><p>')
  html = html.replace(/\n/g, '<br>')
  
  // Wrap in paragraph
  if (!html.startsWith('<h') && !html.startsWith('<ul')) {
    html = '<p>' + html + '</p>'
  }
  
  return html
}

interface ESRSCategory {
  id: number
  name: string
  code: string
  description: string
  order: number
  standard_type: string
}

interface ESRSDisclosure {
  id: number
  code: string
  name: string
  description: string
  requirement_text: string
  is_mandatory: boolean
  order: number
  parent_id?: number | null
  sub_disclosures?: ESRSDisclosure[]
}

interface ESRSStandard {
  id: number
  code: string
  name: string
  description: string
  order: number
  category: ESRSCategory
  disclosures?: ESRSDisclosure[]
}

interface UserResponse {
  id: number
  disclosure_id: number
  notes: string | null
  manual_answer: string | null
  is_completed: boolean
  ai_answer: string | null
  final_answer: string | null
}

interface DocumentEvidence {
  id: number
  document_id: number
  document: UserDocument
  linked_at: string
  notes: string | null
}

interface UserDocument {
  id: number
  file_name: string
  file_size: number
  file_type: string
  uploaded_at: string
  is_global: boolean
  rag_processing_status?: 'pending' | 'processing' | 'completed' | 'failed'
  rag_chunks_count?: number
}

const message = useMessage()
const route = useRoute()

// Props
const standardType = computed(() => route.params.standardType as string || 'ESRS')

// Standard metadata
const standardMetadata = computed(() => {
  const metadata: Record<string, { name: string; icon: string }> = {
    'ESRS': { name: 'ESRS Reporting', icon: '🌍' },
    'ISO9001': { name: 'ISO 9001:2015', icon: '🏆' }
  }
  return metadata[standardType.value] || { name: standardType.value, icon: '📋' }
})

const loading = ref(false)
const loadingDetails = ref(false)
const loadingBulkAI = ref(false)
const showMobileMenu = ref(false)
const categories = ref<ESRSCategory[]>([])
const standards = ref<ESRSStandard[]>([])
const selectedStandardId = ref<number | null>(null)
const selectedStandard = ref<ESRSStandard | null>(null)

// User responses and evidence
const disclosureResponses = ref<Record<number, UserResponse>>({})
const linkedDocuments = ref<Record<number, DocumentEvidence[]>>({})
const excludedDocuments = ref<Record<number, DocumentEvidence[]>>({})  // Excluded global docs
const loadingAI = ref<Record<number, boolean>>({})
const loadingCharts = ref<Record<number, boolean>>({})
const loadingImage = ref<Record<number, boolean>>({})

// Conversation thread state
const activeConversations = ref<Record<number, number>>({}) // disclosureId -> threadId
const aiAnswerRefs = ref<Record<number, HTMLElement | null>>({})

// AI Explain modal state
const showAIExplainModal = ref(false)
const aiExplainQuestion = ref('')
const aiExplainAnswer = ref('')
const currentExplainDisclosure = ref<any>(null)
const loadingExplain = ref(false)

const aiTaskStatus = ref<Record<number, { progress: number; status: string; task_id: string }>>({})
const pollingIntervals = ref<Record<string, ReturnType<typeof setInterval>>>({})
const aiTemperatures = ref<Record<number, number>>({})

// Modal states
const showNotesModal = ref(false)
const showUploadModal = ref(false)
const showManualAnswerModal = ref(false)
const showFinalAnswerModal = ref(false)
const showGenerateImageModal = ref(false)
const imagePrompt = ref('')
const currentImageDisclosure = ref<ESRSDisclosure | null>(null)
const showSourcesModal = ref(false)
const showAIEditChartModal = ref(false)
const showChartEditorModal = ref(false)
const showTableEditorModal = ref(false)
const showChatInterface = ref(false)
const chatItemType = ref<'TEXT' | 'CHART' | 'IMAGE' | 'TABLE'>('TEXT')
const chatItemId = ref<number>(0)
const chatDisclosureId = ref<number>(0)
const currentDisclosure = ref<ESRSDisclosure | null>(null)
const currentSources = ref<any>(null)
const currentChart = ref<any>(null)
const currentChartDisclosureId = ref<number | null>(null)
const editingChartData = ref<any>(null)
const currentTable = ref<any>(null)
const currentTableDisclosureId = ref<number | null>(null)
const editingTableData = ref<any>(null)

// Version Tree state
const showVersionTreeModal = ref(false)
const versionTreeItemType = ref<string>('')
const versionTreeItemId = ref<number>(0)

const aiEditInstructionText = ref('')
const savingAIEdit = ref(false)
const notesText = ref('')
const manualAnswerText = ref('')
const finalAnswerText = ref('')
const savingNotes = ref(false)
const savingManualAnswer = ref(false)
const savingFinalAnswer = ref(false)

// Upload evidence modal
const uploadFileList = ref<UploadFileInfo[]>([])
const userDocuments = ref<UserDocument[]>([])
const loadingDocuments = ref(false)
const selectedDocumentId = ref<number | null>(null)
const evidenceNotes = ref('')
const linkingDocument = ref(false)

// Computed: Available documents (exclude already linked to current disclosure)
const availableDocuments = computed(() => {
  if (!currentDisclosure.value) return userDocuments.value
  
  const linkedDocIds = (linkedDocuments.value[currentDisclosure.value.id] || []).map(ev => ev.document.id)
  const excludedDocIds = (excludedDocuments.value[currentDisclosure.value.id] || []).map(ev => ev.document.id)
  
  // Filter out both linked and excluded documents
  return userDocuments.value.filter(doc => 
    !linkedDocIds.includes(doc.id) && !excludedDocIds.includes(doc.id)
  )
})

// Computed: Global documents to display (always show, unless explicitly excluded)
const globalDocumentsForDisplay = computed(() => {
  if (!currentDisclosure.value) return []
  
  const excludedDocIds = (excludedDocuments.value[currentDisclosure.value.id] || []).map(ev => ev.document.id)
  
  // Show all global documents that are NOT explicitly excluded
  return userDocuments.value
    .filter(doc => doc.is_global && !excludedDocIds.includes(doc.id))
    .map(doc => ({
      id: doc.id,
      document: doc,
      notes: 'Global document - available for all questions',
      linked_at: new Date().toISOString(),
      is_excluded: false
    }))
})

const handleFileListUpdate = (fileList: UploadFileInfo[]) => {
  uploadFileList.value = fileList
}

const loadUserDocuments = async () => {
  loadingDocuments.value = true
  try {
    const response = await api.get('/documents/list')
    userDocuments.value = response.data
    console.log('📚 Loaded global documents:', userDocuments.value.length)
  } catch (error: any) {
    message.error('Failed to load documents')
    console.error('❌ Load documents failed:', error)
  } finally {
    loadingDocuments.value = false
  }
}

const handleUploadInModal = async (options: UploadCustomRequestOptions) => {
  const { file, onFinish, onError } = options
  
  try {
    const formData = new FormData()
    formData.append('file', file.file as File)

    console.log('📤 Uploading file:', file.name, 'Size:', file.file?.size)

    const response = await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    console.log('✅ Upload response:', response.data)
    const uploadedDocId = response.data.file_id
    
    // Automatically link uploaded document to current disclosure and add to linked section
    if (currentDisclosure.value && uploadedDocId) {
      console.log('🔗 Auto-linking document', uploadedDocId, 'to disclosure', currentDisclosure.value.id)
      try {
        await api.post('/esrs/link-document', {
          disclosure_id: currentDisclosure.value.id,
          document_id: uploadedDocId,
          notes: null
        })
        console.log('✅ Document auto-linked successfully')
        
        // Reload linked documents for this disclosure
        const linkedResponse = await api.get(`/esrs/linked-documents/${currentDisclosure.value.id}`)
        linkedDocuments.value[currentDisclosure.value.id] = linkedResponse.data
        
        message.success(`${file.name} uploaded and linked to this question`)
      } catch (linkError: any) {
        console.error('❌ Auto-link failed:', linkError)
        message.error(`Failed to link ${file.name}. Try linking manually.`)
      }
    }
    
    onFinish()
    
    // Don't clear uploadFileList here - allow multiple uploads
    // It will be cleared when modal closes
  } catch (error: any) {
    console.error('❌ Upload failed:', error)
    console.error('Error response:', error.response?.data)
    console.error('Error status:', error.response?.status)
    
    const errorMsg = error.response?.data?.message || error.message || 'Unknown error'
    message.error(`Upload failed: ${errorMsg}`)
    onError()
  }
}

const loadCategories = async () => {
  try {
    const response = await api.get(`/standards/${standardType.value}/categories`)
    categories.value = response.data
  } catch (error) {
    message.error(`Failed to load ${standardMetadata.value.name} categories`)
  }
}

const loadStandards = async () => {
  try {
    loading.value = true
    const response = await api.get('/esrs/standards')
    console.log('📊 All standards from API:', response.data.length)
    // Filter standards by current standardType
    standards.value = response.data.filter((s: ESRSStandard) => 
      s.category.standard_type === standardType.value
    )
    console.log(`✅ Filtered standards for ${standardType.value}:`, standards.value.length, standards.value)
  } catch (error) {
    console.error('❌ Failed to load standards:', error)
    message.error(`Failed to load ${standardMetadata.value.name} standards`)
  } finally {
    loading.value = false
  }
}

const loadStandardDetails = async (standardId: number) => {
  try {
    loadingDetails.value = true
    console.log('🔍 Loading standard details for ID:', standardId)
    const response = await api.get(`/esrs/standards/${standardId}`)
    console.log('✅ Standard details loaded:', response.data)
    selectedStandard.value = response.data
    
    // Load user responses and evidence for all disclosures
    if (response.data.disclosures) {
      await loadDisclosureData(response.data.disclosures)
    }
  } catch (error) {
    console.error('❌ Failed to load standard details:', error)
    message.error(`Failed to load standard details: ${error.message || 'Unknown error'}`)
  } finally {
    loadingDetails.value = false
  }
}

const getStandardsForCategory = (categoryId: number): MenuOption[] => {
  return standards.value
    .filter(s => s.category.id === categoryId)
    .map(standard => ({
      label: `${standard.code}: ${standard.name}`,
      key: standard.id.toString(),
      icon: () => h(NIcon, null, { default: () => h(DocumentTextOutline) })
    }))
}

const handleStandardSelect = (key: string) => {
  console.log('🎯 Standard selected - key:', key)
  const standardId = parseInt(key)
  console.log('🎯 Standard ID:', standardId)
  selectedStandardId.value = standardId
  loadStandardDetails(standardId)
}

const handleStandardSelectMobile = (key: string) => {
  handleStandardSelect(key)
  showMobileMenu.value = false
}

const loadDisclosureData = async (disclosures: ESRSDisclosure[]) => {
  for (const disclosure of disclosures) {
    // Initialize default temperature
    if (aiTemperatures.value[disclosure.id] === undefined) {
      aiTemperatures.value[disclosure.id] = 0.2
    }
    
    // Load user response
    try {
      const response = await api.get(`/esrs/notes/${disclosure.id}`)
      if (response.data.id !== 0) {
        disclosureResponses.value[disclosure.id] = response.data
        // Update temperature from response
        aiTemperatures.value[disclosure.id] = response.data.ai_temperature ?? 0.2
      }
    } catch (error) {
      // Ignore
    }

    // Load linked documents
    try {
      const response = await api.get(`/esrs/linked-documents/${disclosure.id}`)
      linkedDocuments.value[disclosure.id] = response.data
    } catch (error) {
      linkedDocuments.value[disclosure.id] = []
    }

    // Load sub-disclosures recursively
    if (disclosure.sub_disclosures && disclosure.sub_disclosures.length > 0) {
      await loadDisclosureData(disclosure.sub_disclosures)
    }
  }
}

const toggleCompletion = async (disclosureId: number) => {
  try {
    await api.post(`/esrs/toggle-completion/${disclosureId}`, {})
    
    // Reload response
    const response = await api.get(`/esrs/notes/${disclosureId}`)
    disclosureResponses.value[disclosureId] = response.data
    
    message.success('Completion status updated')
  } catch (error: any) {
    message.error('Failed to update completion status')
    console.error(error)
  }
}

const updateAITemperature = async (disclosureId: number) => {
  try {
    const temperature = aiTemperatures.value[disclosureId] ?? 0.2
    await api.post(`/esrs/notes/${disclosureId}`, {
      ai_temperature: temperature
    })
    console.log(`Temperature updated to ${temperature} for disclosure ${disclosureId}`)
  } catch (error: any) {
    console.error('Failed to update temperature:', error)
    message.error('Failed to save temperature setting')
  }
}

const openNotesModal = (disclosure: ESRSDisclosure) => {
  currentDisclosure.value = disclosure
  notesText.value = disclosureResponses.value[disclosure.id]?.notes || ''
  showNotesModal.value = true
}

const saveNotes = async () => {
  if (!currentDisclosure.value) return
  
  savingNotes.value = true
  try {
    await api.post('/esrs/notes', {
      disclosure_id: currentDisclosure.value.id,
      notes: notesText.value
    })
    
    // Reload response
    const response = await api.get(`/esrs/notes/${currentDisclosure.value.id}`)
    disclosureResponses.value[currentDisclosure.value.id] = response.data
    
    message.success('Notes saved successfully')
    showNotesModal.value = false
  } catch (error: any) {
    message.error('Failed to save notes')
    console.error(error)
  } finally {
    savingNotes.value = false
  }
}

const openManualAnswerModal = (disclosure: ESRSDisclosure) => {
  currentDisclosure.value = disclosure
  manualAnswerText.value = disclosureResponses.value[disclosure.id]?.manual_answer || ''
  showManualAnswerModal.value = true
}

const editAIAnswer = (disclosure: ESRSDisclosure) => {
  currentDisclosure.value = disclosure
  // Pre-fill with AI answer so user can edit it
  manualAnswerText.value = disclosureResponses.value[disclosure.id]?.ai_answer || ''
  showManualAnswerModal.value = true
}

const openChatInterface = (disclosure: ESRSDisclosure, itemType: 'TEXT' | 'CHART' | 'IMAGE' | 'TABLE') => {
  currentDisclosure.value = disclosure
  chatItemType.value = itemType
  chatItemId.value = disclosureResponses.value[disclosure.id]?.id || disclosure.id
  chatDisclosureId.value = disclosure.id
  showChatInterface.value = true
}

const openVersionTree = (disclosure: ESRSDisclosure, itemType: string) => {
  versionTreeItemType.value = itemType
  versionTreeItemId.value = disclosureResponses.value[disclosure.id]?.id || disclosure.id
  showVersionTreeModal.value = true
}

const onVersionSelected = async (versionId: string) => {
  // Reload disclosure to get updated content
  if (currentDisclosure.value) {
    message.loading('Loading selected version...', { duration: 0 })
    // Reload will happen in VersionTree component
    showVersionTreeModal.value = false
  }
}

const onRefinementComplete = async (data: any) => {
  // Reload disclosure response to get updated content
  if (currentDisclosure.value) {
    try {
      // Show loading state
      const loadingMsg = message.loading('🔄 Updating answer...', { duration: 0 })
      
      // Small delay for smooth transition (Doherty Threshold - perceived responsiveness)
      await new Promise(resolve => setTimeout(resolve, 200))
      
      const response = await api.get(`/esrs/notes/${currentDisclosure.value.id}`)
      disclosureResponses.value[currentDisclosure.value.id] = response.data
      
      // Close loading message
      loadingMsg.destroy()
      
      // Show success with animation
      message.success('✨ Version applied! Answer updated.', { duration: 3000 })
      
      // Optional: Scroll to updated answer
      setTimeout(() => {
        const answerElement = document.querySelector(`#disclosure-${currentDisclosure.value!.id}`)
        if (answerElement) {
          answerElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
        }
      }, 300)
    } catch (error) {
      console.error('Failed to reload response:', error)
      message.error('Failed to refresh answer. Please reload the page.')
    }
  }
}

const openSourcesModal = (disclosureId: number) => {
  const response = disclosureResponses.value[disclosureId]
  currentSources.value = response?.ai_sources || null
  showSourcesModal.value = true
}

const hasSources = computed(() => {
  if (!currentSources.value) return false
  return (currentSources.value.linked_documents?.length > 0) ||
         (currentSources.value.global_documents?.length > 0) ||
         (currentSources.value.user_provided?.has_notes) ||
         (currentSources.value.user_provided?.has_manual_answer)
})

const saveManualAnswer = async () => {
  if (!currentDisclosure.value) return
  
  savingManualAnswer.value = true
  try {
    await api.post('/esrs/manual-answer', {
      disclosure_id: currentDisclosure.value.id,
      manual_answer: manualAnswerText.value
    })
    
    // Reload response
    const response = await api.get(`/esrs/notes/${currentDisclosure.value.id}`)
    disclosureResponses.value[currentDisclosure.value.id] = response.data
    
    message.success('Manual answer saved successfully')
    showManualAnswerModal.value = false
  } catch (error: any) {
    message.error('Failed to save manual answer')
    console.error(error)
  } finally {
    savingManualAnswer.value = false
  }
}

const openFinalAnswerModal = (disclosure: ESRSDisclosure) => {
  currentDisclosure.value = disclosure
  // Prefill with existing final_answer, or AI answer, or empty
  const response = disclosureResponses.value[disclosure.id]
  finalAnswerText.value = response?.final_answer || response?.ai_answer || ''
  showFinalAnswerModal.value = true
}

const saveFinalAnswer = async () => {
  if (!currentDisclosure.value) return
  
  savingFinalAnswer.value = true
  try {
    await api.post('/esrs/final-answer', {
      disclosure_id: currentDisclosure.value.id,
      final_answer: finalAnswerText.value
    })
    
    // Reload response
    const response = await api.get(`/esrs/notes/${currentDisclosure.value.id}`)
    disclosureResponses.value[currentDisclosure.value.id] = response.data
    
    message.success('Approved answer saved successfully')
    showFinalAnswerModal.value = false
  } catch (error: any) {
    message.error('Failed to save approved answer')
    console.error(error)
  } finally {
    savingFinalAnswer.value = false
  }
}

const openUploadEvidenceModal = async (disclosure: ESRSDisclosure) => {
  console.log('📂 Opening Upload Evidence modal for:', disclosure.code)
  
  currentDisclosure.value = disclosure
  selectedDocumentId.value = null
  evidenceNotes.value = ''
  uploadFileList.value = []
  
  // Load global documents (from Documents page)
  console.log('📚 Loading global documents...')
  await loadUserDocuments()
  console.log('📚 Loaded userDocuments:', userDocuments.value.length, 'docs')
  console.log('🌐 Global documents:', userDocuments.value.filter(d => d.is_global).length)
  console.log('📄 Available documents:', availableDocuments.value.length)
  console.log('🌐 Available global:', availableDocuments.value.filter(d => d.is_global).length)
  
  // Load linked documents for this disclosure
  console.log('🔗 Loading linked documents for disclosure:', disclosure.id)
  try {
    const linkedResponse = await api.get(`/esrs/linked-documents/${disclosure.id}`)
    linkedDocuments.value[disclosure.id] = linkedResponse.data
    console.log('✅ Loaded linked documents:', linkedResponse.data.length)
  } catch (error: any) {
    console.error('❌ Failed to load linked documents:', error)
  }
  
  // Load excluded global documents for this disclosure
  console.log('🚫 Loading excluded documents for disclosure:', disclosure.id)
  try {
    const excludedResponse = await api.get(`/esrs/excluded-documents/${disclosure.id}`)
    excludedDocuments.value[disclosure.id] = excludedResponse.data
    console.log('✅ Loaded excluded documents:', excludedResponse.data.length)
  } catch (error: any) {
    console.error('❌ Failed to load excluded documents:', error)
  }
  
  showUploadModal.value = true
  console.log('✅ Modal opened')
}

const linkDocument = async () => {
  if (!currentDisclosure.value || !selectedDocumentId.value) {
    console.warn('⚠️ Link document: missing disclosure or document ID')
    return
  }
  
  console.log('🔗 Linking global document:', {
    disclosureId: currentDisclosure.value.id,
    documentId: selectedDocumentId.value,
    notes: evidenceNotes.value
  })
  
  linkingDocument.value = true
  try {
    const response = await api.post('/esrs/link-document', {
      disclosure_id: currentDisclosure.value.id,
      document_id: selectedDocumentId.value,
      notes: evidenceNotes.value || null
    })
    
    console.log('✅ Link response:', response.data)
    
    // Reload linked documents
    const linkedResponse = await api.get(`/esrs/linked-documents/${currentDisclosure.value.id}`)
    linkedDocuments.value[currentDisclosure.value.id] = linkedResponse.data
    console.log('📚 Reloaded linked documents:', linkedResponse.data.length)
    
    message.success('Global document linked successfully')
    
    // Clear selection and notes
    selectedDocumentId.value = null
    evidenceNotes.value = ''
  } catch (error: any) {
    console.error('❌ Link failed:', error)
    const errorMsg = error.response?.data?.message || 'Failed to link document'
    message.error(errorMsg)
  } finally {
    linkingDocument.value = false
  }
}

const excludeGlobalDocument = async (documentId: number) => {
  if (!currentDisclosure.value) return
  
  console.log('🚫 Excluding global document:', documentId, 'from disclosure:', currentDisclosure.value.id)
  
  try {
    // Create DocumentEvidence with is_excluded=True
    const response = await api.post('/esrs/link-document', {
      disclosure_id: currentDisclosure.value.id,
      document_id: documentId,
      notes: 'Excluded from this question',
      is_excluded: true
    })
    
    console.log('✅ Exclude response:', response.data)
    
    // Reload excluded documents
    const excludedResponse = await api.get(`/esrs/excluded-documents/${currentDisclosure.value.id}`)
    excludedDocuments.value[currentDisclosure.value.id] = excludedResponse.data
    
    message.success('Global document excluded from this question')
  } catch (error: any) {
    console.error('❌ Exclude failed:', error)
    message.error('Failed to exclude document')
  }
}

const unlinkDocument = async (evidenceId: number, disclosureId: number) => {
  console.log('🔓 Unlinking/excluding evidence:', evidenceId, 'from disclosure:', disclosureId)
  
  try {
    const response = await api.delete(`/esrs/unlink-document/${evidenceId}`)
    console.log('✅ Unlink response:', response.data)
    
    // Reload both linked and excluded documents for current disclosure
    const linkedResponse = await api.get(`/esrs/linked-documents/${disclosureId}`)
    linkedDocuments.value[disclosureId] = linkedResponse.data
    console.log('📚 Reloaded linked documents:', linkedResponse.data.length)
    
    const excludedResponse = await api.get(`/esrs/excluded-documents/${disclosureId}`)
    excludedDocuments.value[disclosureId] = excludedResponse.data
    console.log('🚫 Reloaded excluded documents:', excludedResponse.data.length)
    
    message.success(response.data.message || 'Document updated successfully')
  } catch (error: any) {
    console.error('❌ Unlink failed:', error)
    message.error('Failed to update document')
  }
}

const relinkDocument = async (evidenceId: number, disclosureId: number) => {
  console.log('🔗 Re-linking evidence:', evidenceId, 'to disclosure:', disclosureId)
  
  try {
    const response = await api.post(`/esrs/relink-document/${evidenceId}`)
    console.log('✅ Re-link response:', response.data)
    
    // Reload both linked and excluded documents for current disclosure
    const linkedResponse = await api.get(`/esrs/linked-documents/${disclosureId}`)
    linkedDocuments.value[disclosureId] = linkedResponse.data
    console.log('📚 Reloaded linked documents:', linkedResponse.data.length)
    
    const excludedResponse = await api.get(`/esrs/excluded-documents/${disclosureId}`)
    excludedDocuments.value[disclosureId] = excludedResponse.data
    console.log('🚫 Reloaded excluded documents:', excludedResponse.data.length)
    
    message.success(response.data.message || 'Document re-linked successfully')
  } catch (error: any) {
    console.error('❌ Re-link failed:', error)
    message.error('Failed to re-link document')
  }
}



const pollTaskStatus = async (taskId: string, disclosureId: number) => {
  try {
    const response = await api.get(`/esrs/task-status/${taskId}`)
    const status = response.data
    
    // Update task status for this disclosure
    aiTaskStatus.value[disclosureId] = {
      progress: status.progress,
      status: status.status,
      task_id: taskId
    }
    
    // If task is completed or failed, stop polling and reload response
    if (status.status === 'completed' || status.status === 'failed') {
      if (pollingIntervals.value[taskId]) {
        clearInterval(pollingIntervals.value[taskId])
        delete pollingIntervals.value[taskId]
      }
      loadingAI.value[disclosureId] = false
      delete aiTaskStatus.value[disclosureId]
      
      if (status.status === 'completed') {
        message.success(`AI answer generated for ${status.disclosure_code}!`)
        // Reload the disclosure response to get the new AI answer
        const responseData = await api.get(`/esrs/notes/${disclosureId}`)
        disclosureResponses.value[disclosureId] = responseData.data
      } else {
        message.error(`AI generation failed: ${status.error_message || 'Unknown error'}`)
      }
    }
  } catch (error: any) {
    console.error('Failed to poll task status:', error)
    // Don't show error message - might be temporary network issue
  }
}

const toggleChartSelection = async (disclosureId: number, chartId: string) => {
  try {
    console.log('🔄 Toggling chart selection:', chartId, 'for disclosure:', disclosureId)
    
    const response = await api.post('/esrs/toggle-chart-selection', {
      disclosure_id: disclosureId,
      chart_id: chartId
    })
    
    console.log('✅ Toggle response:', response.data)
    
    // Update local state
    const chart = disclosureResponses.value[disclosureId]?.chart_data?.find((c: any) => c.id === chartId)
    if (chart) {
      chart.selected_for_report = response.data.selected_for_report
      message.success(response.data.selected_for_report ? 'Chart selected for report' : 'Chart deselected from report')
    }
  } catch (error: any) {
    console.error('❌ Toggle chart selection failed:', error)
    message.error('Failed to toggle chart selection')
  }
}

const openAIEditChartModal = (disclosureId: number, chart: any) => {
  currentChartDisclosureId.value = disclosureId
  currentChart.value = chart
  aiEditInstructionText.value = ''
  showAIEditChartModal.value = true
}

const openChartEditorModal = (disclosureId: number, chart: any) => {
  currentChartDisclosureId.value = disclosureId
  currentChart.value = chart
  editingChartData.value = chart
  showChartEditorModal.value = true
}

const handleSaveChart = async (chartData: any) => {
  if (!currentChartDisclosureId.value || !currentChart.value) {
    message.error('Chart information missing')
    return
  }

  try {
    // Save chart to backend
    const response = await api.post('/esrs/update-chart', {
      disclosure_id: currentChartDisclosureId.value,
      chart_id: currentChart.value.id,
      chart_data: chartData
    })

    // Update local chart data
    const disclosureId = currentChartDisclosureId.value
    const chartId = currentChart.value.id
    
    if (disclosureResponses.value[disclosureId]?.chart_data) {
      const chartIndex = disclosureResponses.value[disclosureId].chart_data.findIndex((c: any) => c.id === chartId)
      if (chartIndex !== -1) {
        disclosureResponses.value[disclosureId].chart_data[chartIndex] = {
          ...disclosureResponses.value[disclosureId].chart_data[chartIndex],
          ...chartData
        }
      }
    }

    message.success('Chart updated successfully! 📊')
    showChartEditorModal.value = false
  } catch (error: any) {
    console.error('Failed to save chart:', error)
    message.error('Failed to save chart: ' + (error.response?.data?.message || error.message))
  }
}

const openTableEditorModal = (disclosureId: number, table: any, idx: number) => {
  currentTableDisclosureId.value = disclosureId
  currentTable.value = table
  currentTableIndex.value = idx
  editingTableData.value = table
  showTableEditorModal.value = true
}

const handleSaveTable = async (tableData: any) => {
  if (!currentTableDisclosureId.value || !currentTable.value) {
    message.error('Table information missing')
    return
  }

  try {
    // Save table to backend
    const response = await api.post('/esrs/update-table', {
      disclosure_id: currentTableDisclosureId.value,
      table_id: currentTable.value.id,
      table_data: tableData
    })

    // Update local table data
    const disclosureId = currentTableDisclosureId.value
    const tableId = currentTable.value.id
    
    if (disclosureResponses.value[disclosureId]?.table_data) {
      const tableIndex = disclosureResponses.value[disclosureId].table_data.findIndex((t: any) => t.id === tableId)
      if (tableIndex !== -1) {
        disclosureResponses.value[disclosureId].table_data[tableIndex] = {
          ...disclosureResponses.value[disclosureId].table_data[tableIndex],
          ...tableData
        }
      }
    }

    message.success('Table updated successfully! 📋')
    showTableEditorModal.value = false
  } catch (error: any) {
    console.error('Failed to save table:', error)
    message.error('Failed to save table: ' + (error.response?.data?.message || error.message))
  }
}

const handleAIEditChart = async () => {
  if (!currentChart.value || !currentChartDisclosureId.value || !aiEditInstructionText.value.trim()) {
    message.warning('Please provide instruction for AI')
    return
  }
  
  savingAIEdit.value = true
  try {
    console.log('🤖 AI editing chart:', currentChart.value.id, 'with instruction:', aiEditInstructionText.value)
    
    const response = await api.post('/esrs/ai-edit-chart', {
      disclosure_id: currentChartDisclosureId.value,
      chart_id: currentChart.value.id,
      user_instruction: aiEditInstructionText.value
    })
    
    console.log('✅ AI edit response:', response.data)
    
    // Reload the disclosure response to get updated chart
    const responseData = await api.get(`/esrs/notes/${currentChartDisclosureId.value}`)
    disclosureResponses.value[currentChartDisclosureId.value] = responseData.data
    
    message.success('Chart updated by AI!')
    showAIEditChartModal.value = false
    aiEditInstructionText.value = ''
    currentChart.value = null
    currentChartDisclosureId.value = null
  } catch (error: any) {
    console.error('❌ AI edit chart failed:', error)
    message.error(error.response?.data?.message || 'Failed to edit chart with AI')
  } finally {
    savingAIEdit.value = false
  }
}

const getAIAnswer = async (disclosure: ESRSDisclosure) => {
  loadingAI.value[disclosure.id] = true
  try {
    const response = await api.post('/esrs/ai-answer', {
      disclosure_id: disclosure.id,
      ai_temperature: aiTemperatures.value[disclosure.id] ?? 0.2
    })
    
    if (response.data.task_id) {
      const taskId = response.data.task_id
      
      // Initialize task status
      aiTaskStatus.value[disclosure.id] = {
        progress: 0,
        status: 'pending',
        task_id: taskId
      }
      
      message.info(`Generating AI answer for ${disclosure.code}...`)
      
      // Start polling task status every 2 seconds
      pollingIntervals.value[taskId] = setInterval(() => {
        pollTaskStatus(taskId, disclosure.id)
      }, 2000)
      
      // Do initial poll immediately
      pollTaskStatus(taskId, disclosure.id)
    }
  } catch (error: any) {
    message.error(error.response?.data?.message || 'Failed to start AI generation')
    console.error(error)
    loadingAI.value[disclosure.id] = false
  }
}

const startBulkAIGeneration = async () => {
  if (!selectedStandard.value) return
  
  try {
    loadingBulkAI.value = true
    
    const response = await api.post(`/esrs/bulk-ai-answer/${selectedStandard.value.id}`)
    
    if (response.data.task_id) {
      message.success(`Bulk AI generation started for ${selectedStandard.value.code}! Check Dashboard for progress.`)
    }
  } catch (error: any) {
    message.error(error.response?.data?.message || 'Failed to start bulk AI generation')
    console.error(error)
  } finally {
    loadingBulkAI.value = false
  }
}

// Watch modal close - clear error states
watch(showUploadModal, (newValue) => {
  if (!newValue) {
    // Modal closed - clear all states
    selectedDocumentId.value = null
    evidenceNotes.value = ''
    uploadFileList.value = []
  }
})

// Watch disclosure change - clear error states
watch(currentDisclosure, () => {
  selectedDocumentId.value = null
  evidenceNotes.value = ''
  uploadFileList.value = []
})

// Helper function to format dates
const formatDate = (dateString: string): string => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const extractChartsAndTables = async (disclosureId: number) => {
  console.log('🔍 Extract Charts called for disclosure:', disclosureId)
  loadingCharts.value[disclosureId] = true
  try {
    console.log('📡 Calling API:', `/esrs/extract-charts/${disclosureId}`)
    const response = await api.post(`/esrs/extract-charts/${disclosureId}`)
    console.log('✅ API Response:', response.data)
    
    if (response.data.success) {
      message.success('Charts and tables extracted successfully!')
      // Reload disclosure response to get updated charts
      const updatedResponse = await api.get(`/esrs/notes/${disclosureId}`)
      console.log('📊 Updated disclosure data:', updatedResponse.data)
      console.log('📊 chart_data:', updatedResponse.data.chart_data)
      console.log('📊 table_data:', updatedResponse.data.table_data)
      
      // Force reactivity update
      disclosureResponses.value = {
        ...disclosureResponses.value,
        [disclosureId]: updatedResponse.data
      }
      
      console.log('📊 Updated in state:', disclosureResponses.value[disclosureId])
    } else {
      message.error(response.data.message || 'Failed to extract charts')
    }
  } catch (error: any) {
    console.error('❌ Extract charts error:', error)
    message.error(error.response?.data?.message || 'Failed to extract charts and tables')
  } finally {
    loadingCharts.value[disclosureId] = false
  }
}

const openGenerateImageModal = (disclosure: ESRSDisclosure) => {
  currentImageDisclosure.value = disclosure
  imagePrompt.value = `Create a professional infographic visualizing the key data from: ${disclosureResponses.value[disclosure.id]?.ai_answer?.substring(0, 200) || disclosure.name}`
  showGenerateImageModal.value = true
}

const generateImage = async () => {
  if (!currentImageDisclosure.value || !imagePrompt.value) return
  
  const disclosureId = currentImageDisclosure.value.id
  loadingImage.value[disclosureId] = true
  
  try {
    const response = await api.post(`/esrs/generate-image/${disclosureId}`, {
      prompt: imagePrompt.value
    })
    
    if (response.data.success) {
      message.success('Image generated successfully!')
      // Reload disclosure response to get updated image
      const updatedResponse = await api.get(`/esrs/notes/${disclosureId}`)
      disclosureResponses.value[disclosureId] = updatedResponse.data
      showGenerateImageModal.value = false
    } else {
      message.error(response.data.message || 'Failed to generate image')
    }
  } catch (error: any) {
    message.error(error.response?.data?.message || 'Failed to generate image')
    console.error(error)
  } finally {
    loadingImage.value[disclosureId] = false
  }
}

// Conversation Thread Functions
const startConversation = async (disclosure: any) => {
  console.log('🚀 Starting conversation for disclosure:', disclosure.id)
  try {
    console.log('📡 Calling API:', `/esrs/conversation/start/${disclosure.id}`)
    const response = await api.post(`/esrs/conversation/start/${disclosure.id}`)
    console.log('✅ API Response:', response.data)
    
    if (response.data.thread_id) {
      console.log('✅ Setting thread_id:', response.data.thread_id, 'for disclosure:', disclosure.id)
      activeConversations.value[disclosure.id] = response.data.thread_id
      console.log('✅ activeConversations updated:', activeConversations.value)
      message.success('Conversation started!')
    } else {
      console.warn('⚠️ No thread_id in response')
    }
  } catch (error: any) {
    console.error('❌ Start conversation error:', error)
    message.error('Failed to start conversation')
    console.error(error)
  }
}

const closeConversation = (disclosureId: number) => {
  delete activeConversations.value[disclosureId]
}

const onConversationMessageAdded = (disclosureId: number) => {
  // Optional: reload disclosure response if needed
  console.log('New message added for disclosure:', disclosureId)
}

const onAnswerSavedFromConversation = async (disclosureId: number, answer: string) => {
  console.log('🔵 onAnswerSavedFromConversation called')
  console.log('🔵 disclosureId:', disclosureId)
  console.log('🔵 answer length:', answer?.length)
  console.log('🔵 answer preview:', answer?.substring(0, 100))
  
  // Reload the disclosure response to show updated AI answer
  try {
    console.log('🔵 Calling GET /esrs/notes/' + disclosureId)
    const response = await api.get(`/esrs/notes/${disclosureId}`)
    console.log('🟢 GET response:', response.data)
    console.log('🟢 Has ai_answer:', !!response.data.ai_answer)
    console.log('🟢 ai_answer length:', response.data.ai_answer?.length)
    
    disclosureResponses.value[disclosureId] = response.data
    
    // Close conversation to show the updated answer
    closeConversation(disclosureId)
    
    message.success('✅ Answer saved and updated!')
    
    // Scroll to AI answer section after a short delay
    setTimeout(() => {
      const aiAnswerEl = aiAnswerRefs.value[disclosureId]
      if (aiAnswerEl) {
        console.log('🔵 Scrolling to AI answer')
        aiAnswerEl.scrollIntoView({ behavior: 'smooth', block: 'start' })
      } else {
        console.log('🔴 No aiAnswerRef found for disclosure:', disclosureId)
      }
    }, 300)
  } catch (error: any) {
    console.error('🔴 Error reloading disclosure:', error)
    console.error('🔴 Error response:', error.response)
    console.error('🔴 Error status:', error.response?.status)
    console.error('🔴 Error data:', error.response?.data)
    message.error('Failed to reload answer')
  }
}

const setAIAnswerRef = (disclosureId: number, el: any) => {
  if (el) {
    aiAnswerRefs.value[disclosureId] = el
  }
}

// AI Explain Functions
const openAIExplainModal = (disclosure: any) => {
  currentExplainDisclosure.value = disclosure
  aiExplainQuestion.value = ''
  aiExplainAnswer.value = ''
  showAIExplainModal.value = true
}

const getAIExplanation = async () => {
  if (!currentExplainDisclosure.value || !aiExplainQuestion.value.trim()) return
  
  loadingExplain.value = true
  try {
    const response = await api.post(`/esrs/ai-explain/${currentExplainDisclosure.value.id}`, {
      question: aiExplainQuestion.value
    })
    
    aiExplainAnswer.value = response.data.explanation
    message.success('AI explanation generated!')
  } catch (error: any) {
    message.error('Failed to get AI explanation')
    console.error(error)
  } finally {
    loadingExplain.value = false
  }
}

const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    message.success('Copied to clipboard!')
  } catch {
    message.error('Failed to copy')
  }
}

onMounted(async () => {
  await Promise.all([loadCategories(), loadStandards()])
  
  // Check if category query parameter exists and auto-select first standard
  const categoryId = route.query.category
  if (categoryId) {
    const catId = parseInt(categoryId as string)
    const categoryStandards = standards.value.filter(s => s.category === catId)
    if (categoryStandards.length > 0) {
      // Auto-select first standard in the category
      handleStandardSelect(categoryStandards[0].id)
    }
  }
})

// Watch for standardType changes (when navigating between different standards)
watch(standardType, async () => {
  selectedStandardId.value = null
  selectedStandard.value = null
  await Promise.all([loadCategories(), loadStandards()])
})

onBeforeUnmount(() => {
  // Clear all polling intervals when component unmounts
  Object.values(pollingIntervals.value).forEach(interval => clearInterval(interval))
  pollingIntervals.value = {}
})
</script>

<style scoped>
.esrs-container {
  height: 100vh;
  overflow: hidden;
}

.esrs-sidebar {
  height: 100vh;
  background: rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(10px);
}

:deep(.n-layout-content) {
  height: 100vh;
  overflow-y: auto;
  scroll-behavior: smooth; /* Smooth scrolling */
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.category-section {
  margin: 16px 0;
}

.category-header {
  padding: 12px 16px;
  background: rgba(84, 217, 68, 0.1);
  border-left: 3px solid #54d944;
}

:deep(.n-menu-item) {
  border-radius: 0 !important;
  font-size: 13px;
  transition: all 0.2s ease;
}

:deep(.n-menu-item.n-menu-item--selected) {
  background: rgba(84, 217, 68, 0.2) !important;
  border-left: 3px solid #54d944;
}

:deep(.n-collapse-item__header) {
  font-size: 15px;
  font-weight: 500;
  transition: all 0.2s ease;
}

/* Disclosure item highlight animation */
.disclosure-item {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.disclosure-item:target {
  animation: highlight 1.5s ease-in-out;
}

@keyframes highlight {
  0%, 100% {
    background: transparent;
    box-shadow: none;
  }
  50% {
    background: rgba(84, 217, 68, 0.15);
    box-shadow: 0 0 20px rgba(84, 217, 68, 0.3);
  }
}

/* Answer section update animation */
.manual-answer-section,
.ai-answer-section,
.final-answer-section {
  transition: all 0.3s ease;
  animation: fadeIn 0.4s ease-out;
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

:deep(.n-blockquote) {
  border-left: 3px solid #54d944;
  padding-left: 16px;
  margin: 8px 0;
  color: rgba(255, 255, 255, 0.85);
}

.sub-disclosure {
  margin-left: 24px;
  border-left: 2px solid rgba(84, 217, 68, 0.3);
}

.sub-disclosure :deep(.n-collapse-item__header) {
  font-size: 14px;
  padding-left: 8px;
}

.manual-answer-section {
  margin-top: 16px;
  padding: 16px;
  background: rgba(84, 217, 68, 0.1);
  border-radius: 8px;
  border-left: 3px solid #54d944;
}

.manual-answer-section :deep(.n-alert__content) {
  max-height: 400px;
  overflow-y: auto;
}

/* Rich content styling for displayed answers */
.rich-content {
  line-height: 1.6;
  font-size: 14px;
}

.rich-content h1 {
  font-size: 1.8em;
  margin: 0.5em 0;
  color: #54d944;
  font-weight: 600;
}

.rich-content h2 {
  font-size: 1.5em;
  margin: 0.5em 0;
  color: #54d944;
  font-weight: 600;
}

.rich-content h3 {
  font-size: 1.25em;
  margin: 0.5em 0;
  color: #54d944;
  font-weight: 600;
}

.rich-content p {
  margin: 0.5em 0;
}

.rich-content ul,
.rich-content ol {
  padding-left: 1.5em;
  margin: 0.5em 0;
}

.rich-content li {
  margin: 0.25em 0;
}

.rich-content blockquote {
  border-left: 4px solid #54d944;
  padding-left: 16px;
  margin: 0.5em 0;
  font-style: italic;
  color: rgba(255, 255, 255, 0.7);
  background: rgba(84, 217, 68, 0.05);
  padding: 12px 16px;
  border-radius: 0 4px 4px 0;
}

.rich-content code {
  background: rgba(84, 217, 68, 0.1);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 0.9em;
}

.rich-content pre {
  background: rgba(0, 0, 0, 0.6);
  color: #54d944;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 0.5em 0;
}

.rich-content a {
  color: #54d944;
  text-decoration: underline;
}

.rich-content strong {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
}

.rich-content em {
  font-style: italic;
}

.ai-answer-section {
  margin-top: 16px;
  padding: 16px;
  background: rgba(24, 160, 251, 0.1);
  border-radius: 8px;
  border-left: 3px solid #18a0fb;
}

.ai-answer-section :deep(.n-alert__content) {
  max-height: 400px;
  overflow-y: auto;
}

.final-answer-section {
  margin-top: 16px;
  padding: 16px;
  background: rgba(255, 193, 7, 0.15);
  border-radius: 8px;
  border-left: 4px solid #ffc107;
}

.final-answer-section :deep(.n-alert__content) {
  max-height: 400px;
  overflow-y: auto;
}

/* Custom scrollbar styling for answer sections */
.manual-answer-section :deep(.n-alert__content)::-webkit-scrollbar,
.ai-answer-section :deep(.n-alert__content)::-webkit-scrollbar,
.final-answer-section :deep(.n-alert__content)::-webkit-scrollbar {
  width: 8px;
}

.manual-answer-section :deep(.n-alert__content)::-webkit-scrollbar-track,
.ai-answer-section :deep(.n-alert__content)::-webkit-scrollbar-track,
.final-answer-section :deep(.n-alert__content)::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

.manual-answer-section :deep(.n-alert__content)::-webkit-scrollbar-thumb {
  background: rgba(84, 217, 68, 0.5);
  border-radius: 4px;
}

.ai-answer-section :deep(.n-alert__content)::-webkit-scrollbar-thumb {
  background: rgba(24, 160, 251, 0.5);
  border-radius: 4px;
}

.final-answer-section :deep(.n-alert__content)::-webkit-scrollbar-thumb {
  background: rgba(255, 193, 7, 0.6);
  border-radius: 4px;
}

.manual-answer-section :deep(.n-alert__content)::-webkit-scrollbar-thumb:hover {
  background: rgba(84, 217, 68, 0.8);
}

.ai-answer-section :deep(.n-alert__content)::-webkit-scrollbar-thumb:hover {
  background: rgba(24, 160, 251, 0.8);
}

.final-answer-section :deep(.n-alert__content)::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 193, 7, 0.9);
}

.notes-section {
  margin-top: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  border-left: 3px solid #54d944;
}

.linked-docs-section {
  margin-top: 12px;
}

/* Mobile Header */
.mobile-header {
  display: none;
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
}

.desktop-only {
  display: block;
}

/* Mobile Responsive Styles */
@media (max-width: 768px) {
  .mobile-header {
    display: flex !important;
  }

  .desktop-only {
    display: none !important;
  }

  .esrs-container {
    height: auto;
    min-height: 100vh;
  }

  :deep(.n-layout-content) {
    padding: 12px !important;
    height: auto !important;
  }

  :deep(.n-layout.n-layout--has-sider) {
    flex-direction: column;
  }

  .category-header {
    padding: 10px 12px;
    font-size: 14px;
  }

  :deep(.n-menu-item) {
    font-size: 13px !important;
    padding: 10px 12px !important;
  }

  :deep(.n-card) {
    margin: 0 !important;
  }

  :deep(.n-card .n-card__content) {
    padding: 12px !important;
  }

  :deep(.n-h2) {
    font-size: 20px !important;
  }

  :deep(.n-h3) {
    font-size: 18px !important;
  }

  :deep(.n-h4) {
    font-size: 16px !important;
  }

  :deep(.n-space) {
    gap: 8px !important;
  }

  :deep(.n-button) {
    font-size: 13px !important;
    padding: 6px 12px !important;
  }

  :deep(.n-collapse-item__header) {
    font-size: 14px !important;
    padding: 10px 12px !important;
  }

  .manual-answer-section,
  .ai-answer-section,
  .final-answer-section {
    padding: 12px !important;
    font-size: 14px;
  }

  .sub-disclosure {
    margin-left: 12px;
  }

  /* Markdown content styling */
  .markdown-content {
    line-height: 1.6;
  }

  .markdown-content h1,
  .markdown-content h2,
  .markdown-content h3,
  .markdown-content h4 {
    margin-top: 16px;
    margin-bottom: 8px;
    font-weight: 600;
  }

  .markdown-content h1 {
    font-size: 1.5em;
  }

  .markdown-content h2 {
    font-size: 1.3em;
  }

  .markdown-content h3 {
    font-size: 1.15em;
  }

  .markdown-content h4 {
    font-size: 1em;
  }

  .markdown-content p {
    margin-bottom: 12px;
  }

  .markdown-content ul,
  .markdown-content ol {
    margin-left: 20px;
    margin-bottom: 12px;
  }

  .markdown-content li {
    margin-bottom: 6px;
  }

  .markdown-content strong {
    font-weight: 600;
  }

  .markdown-content em {
    font-style: italic;
  }

  .markdown-content code {
    background-color: rgba(0, 0, 0, 0.05);
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Monaco', 'Courier New', monospace;
  }

  .markdown-content pre {
    background-color: rgba(0, 0, 0, 0.05);
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
    margin-bottom: 12px;
  }

  .markdown-content blockquote {
    border-left: 3px solid #ddd;
    padding-left: 12px;
    margin-left: 0;
    color: #666;
  }

  :deep(.n-modal) {
    width: 95% !important;
    max-width: 95% !important;
  }

  :deep(.n-alert) {
    font-size: 13px !important;
  }

  :deep(.n-blockquote) {
    font-size: 13px;
    padding-left: 12px;
  }
}

@media (max-width: 480px) {
  .sidebar-header h3 {
    font-size: 16px !important;
  }

  :deep(.n-button) {
    font-size: 12px !important;
    padding: 4px 8px !important;
  }

  :deep(.n-h2) {
    font-size: 18px !important;
  }

  :deep(.n-h3) {
    font-size: 16px !important;
  }

  :deep(.n-h4) {
    font-size: 14px !important;
  }

  .manual-answer-section,
  .ai-answer-section,
  .final-answer-section {
    padding: 10px !important;
    font-size: 13px;
  }

  :deep(.n-collapse-item__header) {
    font-size: 13px !important;
  }

  :deep(.n-modal) {
    width: 98% !important;
  }
}

/* Disclosure slide transition animations */
.disclosure-slide-enter-active,
.disclosure-slide-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.disclosure-slide-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.disclosure-slide-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

/* Highlight pulse animation for updated disclosures */
@keyframes highlight-pulse {
  0%, 100% {
    background-color: transparent;
    box-shadow: none;
  }
  50% {
    background-color: rgba(84, 217, 68, 0.2);
    box-shadow: 0 0 30px rgba(84, 217, 68, 0.4);
  }
}

.highlight-pulse {
  animation: highlight-pulse 2s ease-in-out;
}

/* Performance optimizations */
.message-bubble,
.disclosure-item,
:deep(.n-collapse-item) {
  will-change: transform, opacity;
}

.conversation-timeline {
  contain: layout style paint;
}

/* Smooth transitions for all interactive elements */
:deep(.n-button),
:deep(.n-collapse-item__header),
:deep(.n-menu-item) {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Focus states for accessibility */
:deep(.n-button:focus-visible) {
  outline: 2px solid rgba(84, 217, 68, 0.6);
  outline-offset: 2px;
}

:deep(.n-input:focus-within) {
  box-shadow: 0 0 0 2px rgba(84, 217, 68, 0.3);
}
</style>
