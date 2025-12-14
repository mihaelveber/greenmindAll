# 🧪 AI Conversation & Version Control - Testing Guide

## Pre-Test Checklist

✅ Backend running: `docker compose ps` (backend should show "Up")
✅ Frontend running: `docker compose ps` (frontend should show "Up")  
✅ Database has sample data: 10 user responses with AI answers available
✅ Backend endpoints created: `/api/refine/text`, `/api/versions/select`
✅ ChatInterface component created with timeline UI

## Test Scenarios

### 1️⃣ Test Manual Answer Editing

**Purpose:** Verify user can write/edit answers manually

**Steps:**
1. Open browser: http://localhost:5173
2. Login with credentials
3. Navigate to any ESRS disclosure with AI answer
4. Click green "Write/Edit Answer" button
5. Type test answer in textarea
6. Click "Save Answer"
7. Verify answer appears in "Your Answer" section

**Expected Result:**
- ✅ Modal opens with empty textarea (or pre-filled if editing)
- ✅ Save button works
- ✅ Answer appears in main view
- ✅ Manual answer saved to database

---

### 2️⃣ Test AI Refinement Flow (CORE TEST)

**Purpose:** Test complete AI conversation and version creation

**Steps:**

#### A. Open Chat Interface
1. Navigate to disclosure with AI answer (e.g., S1-9)
2. Click "💬 Refine with AI" button
3. Verify modal opens with ChatInterface

**Expected:**
- ✅ Modal opens (800px width)
- ✅ Timeline visible (purple/blue gradient background)
- ✅ No messages shown (first time)
- ✅ Input area at bottom with purple gradient

#### B. Send Refinement Instruction
1. Type in input: "Make this answer more professional and formal"
2. Press Ctrl+Enter (or click Send)

**Expected:**
- ✅ User message appears immediately in purple bubble
- ✅ Message indented left with 3px purple border
- ✅ Timestamp shows "just now"
- ✅ Loading state visible

#### C. Receive AI Response
1. Wait 5-10 seconds for OpenAI API

**Expected:**
- ✅ AI response appears in blue bubble
- ✅ Message indented left with 3px blue border
- ✅ Green version badge shows "v2" (or higher)
- ✅ "Use This Version" button appears
- ✅ Response text is refined version of original

#### D. Create More Versions
1. Send another instruction: "Add more specific examples"
2. Wait for response

**Expected:**
- ✅ New user message in purple
- ✅ New AI response in blue
- ✅ Version badge shows "v3"
- ✅ Timeline shows full conversation history

#### E. Select a Version
1. Click "Use This Version" on any AI response
2. Close modal
3. Check main disclosure view

**Expected:**
- ✅ Success message: "✨ Version created successfully!"
- ✅ "Your Answer" section updates with selected version
- ✅ Selected version marked in database (`is_selected=True`)

---

### 3️⃣ Test Database Persistence

**Purpose:** Verify conversations and versions saved to PostgreSQL

**Commands:**
```bash
# Check database after refinement
docker compose exec backend python manage.py shell -c "
from accounts.models import AIConversation, ItemVersion

# Check conversations
convs = AIConversation.objects.all()
print(f'Total conversations: {convs.count()}')

if convs.exists():
    conv = convs.last()
    print(f'Latest conversation:')
    print(f'  Item Type: {conv.item_type}')
    print(f'  Messages: {len(conv.messages)}')
    print(f'  Last message: {conv.messages[-1][\"role\"]} - {conv.messages[-1][\"content\"][:50]}...')

# Check versions
versions = ItemVersion.objects.all()
print(f'\nTotal versions: {versions.count()}')

if versions.exists():
    for v in versions.order_by('version_number'):
        print(f'  v{v.version_number}: {v.change_type} - Selected: {v.is_selected}')
"
```

**Expected Output:**
```
Total conversations: 1 (or more)
Latest conversation:
  Item Type: TEXT
  Messages: 4 (2 user + 2 assistant)
  Last message: assistant - [refined content]...

Total versions: 3
  v1: INITIAL - Selected: False
  v2: AI_REFINEMENT - Selected: False
  v3: AI_REFINEMENT - Selected: True
```

---

### 4️⃣ Test Conversation Reopening

**Purpose:** Verify conversation history persists across sessions

**Steps:**
1. Click "💬 Refine with AI" on same disclosure again
2. Check if previous messages load

**Expected (CURRENTLY NOT WORKING):**
- ❌ Previous conversation should load from database
- ❌ Timeline should show all previous messages

**Status:** Feature not yet implemented - need to add in Priority 5

---

### 5️⃣ Test Error Handling

**Purpose:** Ensure graceful error handling

**Test Cases:**

#### A. Empty Message
1. Open chat interface
2. Click Send without typing anything

**Expected:**
- ✅ Send button disabled or nothing happens

#### B. API Error Simulation
1. Stop backend: `docker compose stop backend`
2. Try to send message

**Expected:**
- ✅ Error message: "Failed to refine content"
- ✅ User message removed from timeline
- ✅ Input restored with original text

#### C. Very Long Message
1. Type 1000+ character instruction
2. Send

**Expected:**
- ✅ Message sends successfully
- ✅ AI responds normally

---

### 6️⃣ Test Extract Charts (Bug Fix)

**Purpose:** Verify chart extraction works after parameter fix

**Steps:**
1. Navigate to disclosure with AI answer
2. Click "Extract Charts" button
3. Wait for processing

**Expected:**
- ✅ No error about "takes 3 positional arguments but 4 were given"
- ✅ Charts extracted successfully
- ✅ Charts appear in charts section

**Previous Bug:** `extract_charts_from_answer()` called with temperature parameter
**Fix Applied:** Removed temperature parameter from API call

---

### 7️⃣ Test Generate Image (Bug Fix)

**Purpose:** Verify image generation works after schema fix

**Steps:**
1. Navigate to disclosure with AI answer
2. Click "Generate Image" button
3. Modal should pre-fill with AI answer as prompt
4. Click "Generate Image"
5. Wait 20-30 seconds (DALL-E is slow)

**Expected:**
- ✅ Modal opens with prompt pre-filled
- ✅ No "Unprocessable Entity" error
- ✅ Image generates successfully
- ✅ Image appears in charts section

**Previous Bug:** Endpoint used `data: dict` instead of Schema
**Fix Applied:** Created `GenerateImageSchema(prompt: str)`

---

## Known Issues & Limitations

### ⚠️ Not Yet Implemented

1. **Conversation History Loading**
   - Reopening chat doesn't load previous messages
   - Need to add `loadConversation()` on component mount
   - Priority: HIGH (next task)

2. **Version Selection UI Refresh**
   - Clicking "Use This Version" updates DB but doesn't refresh main view
   - Need to emit event and reload response
   - Priority: HIGH (next task)

3. **Chart/Image/Table Refinement**
   - Only TEXT refinement implemented
   - Other types return 501 "Coming soon"
   - Priority: MEDIUM

4. **Rich Text Editor**
   - Manual answer uses plain textarea
   - No formatting toolbar
   - Priority: MEDIUM

5. **Version Tree Visualization**
   - No visual tree of version history
   - Can't see parent-child relationships
   - Priority: LOW

### ✅ Working Features

1. ✅ Manual answer editing (write from scratch or edit AI answer)
2. ✅ AI refinement for TEXT content
3. ✅ Timeline conversation UI
4. ✅ Version creation and storage
5. ✅ Version selection (backend)
6. ✅ Extract charts (bug fixed)
7. ✅ Generate image (bug fixed)

---

## Debug Commands

### Check Backend Logs
```bash
docker compose logs backend -f
```

### Check Frontend Console
Open browser DevTools → Console → Look for:
- API request errors
- Vue component warnings
- Network tab for failed requests

### Check Database State
```bash
docker compose exec backend python manage.py shell

# In shell:
from accounts.models import AIConversation, ItemVersion, ESRSUserResponse

# List all conversations
for c in AIConversation.objects.all():
    print(f"Conv {c.id}: {c.item_type} - {len(c.messages)} messages")

# List all versions
for v in ItemVersion.objects.all():
    print(f"v{v.version_number} ({v.change_type}): Selected={v.is_selected}")

# Check specific response
r = ESRSUserResponse.objects.get(id=52)
print(f"Response {r.id}: AI={len(r.ai_answer or '')}ch, Manual={len(r.manual_answer or '')}ch")
```

### Reset Test Data
```bash
# Delete all conversations and versions (careful!)
docker compose exec backend python manage.py shell -c "
from accounts.models import AIConversation, ItemVersion
AIConversation.objects.all().delete()
ItemVersion.objects.all().delete()
print('Test data cleared!')
"
```

---

## Success Criteria

For test to be considered successful:

✅ User can open chat interface
✅ User can send refinement instruction
✅ AI responds within 10 seconds
✅ Response appears in blue bubble with version badge
✅ Conversation saved to database (AIConversation.messages)
✅ Version created in database (ItemVersion)
✅ User can select version
✅ Selected version marked in database
✅ Extract charts works without errors
✅ Generate image works without errors

---

## Next Steps After Testing

1. **Add conversation loading** - Load previous messages on modal open
2. **Fix UI refresh** - Reload response after version selection
3. **Test at scale** - Multiple users, multiple conversations
4. **Add rich text editor** - Quill.js for manual answers
5. **Implement version tree** - Visual parent-child relationships
6. **Add comparison view** - Side-by-side version diff

---

## Contact & Support

- Backend errors: Check `docker compose logs backend`
- Frontend errors: Check browser DevTools console
- Database issues: Use Django shell commands above
- API testing: Use Postman or curl with JWT token

**Last Updated:** 12 Dec 2025, 19:00 CET
**Version:** 1.1.0 - AI Conversation & Version Control System
