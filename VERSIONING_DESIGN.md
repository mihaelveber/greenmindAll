# AI Conversation & Version System Design

## Overview
Enable users to refine ANY content (text answers, charts, images, tables) through AI chat or manual editing, with full version history stored in a tree structure.

## Core Concepts

### 1. Version Tree Structure
```
Answer v1 (AI generated)
├── v2 (AI refinement: "make it more formal")
│   ├── v3 (AI refinement: "add more details")
│   └── v4 (Manual edit)
└── v5 (AI refinement: "make it shorter")
    └── v6 (AI refinement: "add examples")
```

Each version tracks:
- Parent version (to build tree)
- Change type (AI refinement / manual edit)
- Timestamp
- Who made the change (user or AI)
- Conversation that led to it (for AI refinements)

### 2. Item Types
- **TEXT** - AI answers, manual answers, final answers
- **CHART** - Bar charts, pie charts, line charts
- **IMAGE** - DALL-E generated images
- **TABLE** - Structured data tables

### 3. Conversation Flow
```
User: "Make this chart's colors more vibrant"
  -> AI: "I'll update the chart with brighter colors: ..."
  -> System: Creates new chart version (v2) linked to conversation
  -> UI: Shows both versions, user can select preferred one
```

## Database Schema

### AIConversation
```python
id: UUID (primary key)
user: ForeignKey(User)
disclosure: ForeignKey(ESRSDisclosure, null=True)  # Context
item_type: CharField (TEXT/CHART/IMAGE/TABLE)
item_id: IntegerField  # ID of the ESRSUserResponse or chart/image object
messages: JSONField  # [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
created_at: DateTimeField
updated_at: DateTimeField
```

### ItemVersion
```python
id: UUID (primary key)
user: ForeignKey(User)
disclosure: ForeignKey(ESRSDisclosure)
item_type: CharField (TEXT/CHART/IMAGE/TABLE)
version_number: IntegerField  # Auto-increment per item
parent_version: ForeignKey('self', null=True)  # For tree structure
change_type: CharField (AI_REFINEMENT/MANUAL_EDIT/INITIAL)
change_description: TextField  # Summary of change
content: JSONField  # Actual content (text, chart config, image base64, table data)
conversation: ForeignKey(AIConversation, null=True)
is_selected: BooleanField (default=False)  # Currently active version
created_at: DateTimeField
created_by_user: BooleanField  # True for manual edits, False for AI
```

## Frontend Components

### 1. ChatInterface.vue
**Purpose**: Reusable AI chat component for any item type

**Props**:
- `itemType` - TEXT/CHART/IMAGE/TABLE
- `itemId` - ID of the item
- `currentContent` - Current version content
- `conversationId` - Existing conversation ID (if continuing)

**Features**:
- Display conversation history
- Input field for refinement instructions
- "Send to AI" button
- Loading state while AI processes
- Show new version preview
- "Use This Version" button

### 2. VersionTree.vue
**Purpose**: Visual tree showing all versions

**Features**:
- D3.js or Vue Flow for tree visualization
- Nodes show: version number, timestamp, change description
- Highlight selected/active version
- Click node to preview that version
- Branch lines show parent-child relationships
- Color coding: green (AI), blue (manual), gold (selected)

### 3. RichTextEditor.vue
**Purpose**: Advanced text editing for answers

**Technology**: Quill.js or TipTap
**Features**:
- Bold, italic, underline, lists
- Headings, blockquotes
- Undo/redo
- Auto-save drafts
- Character count
- Export to markdown

### 4. ChartEditor.vue
**Purpose**: Manual chart editing

**Features**:
- Edit labels: click to rename
- Edit values: inline number editing
- Change colors: color picker for each segment
- Edit legend: rename, reorder
- Change chart type: dropdown (pie -> bar -> line)
- Add/remove data points
- Live preview with Chart.js
- Reset to AI version

### 5. TableEditor.vue
**Purpose**: Manual table editing

**Features**:
- Spreadsheet-like interface
- Edit cells inline
- Add/remove rows/columns
- Sort by column
- Format cells (number, percentage, date)
- Formula support (SUM, AVG)
- Export to CSV/Excel
- Import from CSV

## UI Integration

### Answer Section (Text)
```vue
<n-alert type="info" title="AI Answer v3">
  <div v-html="currentAnswer"></div>
  
  <template #action>
    <n-space>
      <n-button @click="openChatModal('TEXT')">
        <n-icon :component="ChatbubbleOutline" />
        Refine with AI
      </n-button>
      <n-button @click="openTextEditor">
        <n-icon :component="CreateOutline" />
        Edit Manually
      </n-button>
      <n-button @click="showVersionTree">
        <n-icon :component="GitBranchOutline" />
        History (3 versions)
      </n-button>
    </n-space>
  </template>
</n-alert>
```

### Chart Section
```vue
<n-card title="Gender Diversity Chart v2">
  <canvas ref="chartCanvas"></canvas>
  
  <template #action>
    <n-space>
      <n-button @click="openChatModal('CHART', chart.id)">
        💬 Refine with AI
      </n-button>
      <n-button @click="openChartEditor(chart)">
        ✏️ Edit Chart
      </n-button>
      <n-button @click="showVersionTree('CHART', chart.id)">
        🌳 History
      </n-button>
    </n-space>
  </template>
</n-card>
```

### Image Section
```vue
<n-card title="Generated Image v1">
  <img :src="imageData" />
  
  <template #action>
    <n-space>
      <n-button @click="openChatModal('IMAGE', image.id)">
        💬 Refine Image
      </n-button>
      <n-button @click="showVersionTree('IMAGE', image.id)">
        🌳 History
      </n-button>
    </n-space>
  </template>
</n-card>
```

## Backend API Endpoints

### Conversation Management
- `POST /api/conversations/start` - Start new conversation
- `POST /api/conversations/{id}/message` - Send message, get AI response
- `GET /api/conversations/{id}/history` - Get full conversation
- `DELETE /api/conversations/{id}` - Delete conversation

### Version Management
- `GET /api/versions/{item_type}/{item_id}` - Get all versions for item
- `GET /api/versions/{id}` - Get specific version
- `POST /api/versions/select` - Mark version as selected
- `DELETE /api/versions/{id}` - Delete version (if not selected)
- `GET /api/versions/{item_type}/{item_id}/tree` - Get version tree structure

### AI Refinement
- `POST /api/refine/text` - Refine text answer
- `POST /api/refine/chart` - Refine chart
- `POST /api/refine/image` - Refine image (regenerate with modified prompt)
- `POST /api/refine/table` - Refine table

## AI Refinement Prompts

### Text Refinement
```python
system_prompt = f"""
You are refining an ESRS disclosure answer.
Original answer: {current_content}
User instruction: {user_instruction}
Disclosure requirement: {disclosure.requirement_text}

Please provide an improved version following the user's instruction while maintaining accuracy and compliance.
"""
```

### Chart Refinement
```python
system_prompt = f"""
You are refining a data visualization chart.
Current chart config: {json.dumps(current_chart)}
User instruction: {user_instruction}

Return a JSON object with the updated chart configuration. You can modify:
- colors: array of hex colors
- labels: array of strings
- data: array of numbers
- chart_type: 'pie', 'bar', 'line'
- title: string
"""
```

### Image Refinement
```python
# For images, append instruction to original prompt
original_prompt = image_version.content['prompt']
refinement = user_instruction
new_prompt = f"{original_prompt}. {refinement}"

# Call DALL-E with new prompt
response = client.images.generate(
    model="dall-e-3",
    prompt=new_prompt,
    size="1024x1024"
)
```

### Table Refinement
```python
system_prompt = f"""
You are refining a data table.
Current table: {json.dumps(current_table)}
User instruction: {user_instruction}

Return a JSON object with the updated table structure:
{
  "headers": ["Column 1", "Column 2"],
  "rows": [["Value 1", "Value 2"]],
  "formatting": {"Column 1": "number", "Column 2": "percentage"}
}
"""
```

## Implementation Phases

### Phase 1: Foundation (Priority 1)
1. Create database models (AIConversation, ItemVersion)
2. Run migrations
3. Create basic ChatInterface.vue component
4. Add "Refine with AI" button to text answers
5. Implement text refinement endpoint
6. Store conversation + new version in DB

### Phase 2: Text Editing (Priority 2)
1. Integrate rich text editor (Quill.js)
2. Add manual editing capability
3. Save manual edits as new versions
4. Show version badges ("v3", "2 refinements")

### Phase 3: Charts (Priority 3)
1. Add "Refine with AI" for charts
2. Implement chart refinement logic
3. Create ChartEditor.vue for manual editing
4. Version system for charts

### Phase 4: Images & Tables (Priority 4)
1. Add "Refine with AI" for images
2. Image refinement (DALL-E)
3. Add "Refine with AI" for tables
4. TableEditor.vue component

### Phase 5: Version Tree (Priority 5)
1. Create VersionTree.vue component
2. Visualize tree structure
3. Compare versions side-by-side
4. Delete old versions

## Success Metrics
- User can refine any content type via AI chat
- User can manually edit any content type
- All versions stored with full history
- Version tree visualizes relationships
- User can switch between versions
- Conversations preserved in database
- UI shows clear version information

## Technical Considerations
- Performance: Lazy load version history (only when requested)
- Storage: Consider storing images as URLs instead of base64 for large version trees
- Caching: Cache current/selected version for fast loading
- Permissions: Only owner can create versions
- Limits: Max 50 versions per item (prevent abuse)
- Cleanup: Archive old unselected versions after 90 days
