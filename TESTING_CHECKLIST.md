# 🧪 Testing Checklist - Version 1.0.37

**Version:** 1.0.37 - Chart Management & Markdown Formatting  
**Date:** 11 December 2025 (23:45 CET)  
**Status:** ⚠️ PENDING USER TESTING

---

## ✅ Backend Status
- ✅ Backend running (port 8090)
- ✅ Celery worker running
- ✅ Redis running (port 6379)
- ✅ PostgreSQL with pgvector running (port 5442)
- ✅ All services healthy

---

## 🧪 Test Cases

### Test 1: Chart Label Cleanup ✅ READY
**Objective:** Verify chart labels are clean and professional

**Steps:**
1. Navigate to http://localhost:5173
2. Login as `mihael.veber@gmail.com`
3. Upload ESG document with gender data (e.g., NLB Group report)
4. Wait for "✓ Ready (N chunks)" status indicator
5. Navigate to ESRS → S1 Standards → S1-9 (Characteristics of employees)
6. Click "Get AI Answer"
7. Wait for AI generation to complete

**Expected Results:**
- ✅ Gender chart labels show "Women" and "Men" (not "women represent 69%")
- ✅ Employee chart labels show "Full-time", "Part-time" (not "full-time employees are")
- ✅ Emissions chart labels show "Scope 1", "Scope 2", "Scope 3" (not "scope 1 emissions from")
- ✅ All labels are clean, capitalized, and professional

**Current Status:** ⚠️ Needs user testing

---

### Test 2: Markdown Formatting ✅ READY
**Objective:** Verify AI responses are properly formatted

**Steps:**
1. Same as Test 1 (upload doc → get AI answer)
2. View AI response text in the "AI Analysis" alert

**Expected Results:**
- ✅ Headings (###) rendered as actual H3 elements
- ✅ Lists (- item) rendered as bullet points
- ✅ Bold text (**text**) rendered as bold
- ✅ Proper spacing between paragraphs
- ✅ Text is readable and structured (not plain wall of text)

**Current Status:** ⚠️ Needs user testing

---

### Test 3: Chart Selection Checkbox ✅ READY
**Objective:** Verify user can select/deselect charts for report

**Steps:**
1. Same as Test 1 (upload doc → get AI answer → charts visible)
2. Look at "📊 Visual Analytics" card
3. Each chart should have a checkbox next to the title
4. Click checkbox to uncheck it
5. Refresh page (or navigate away and back)

**Expected Results:**
- ✅ Checkbox visible next to each chart title
- ✅ Checkbox is checked by default (selected_for_report: true)
- ✅ Clicking checkbox shows "Chart deselected from report" message
- ✅ Clicking again shows "Chart selected for report" message
- ✅ State persists across page refreshes

**API Endpoint:** `POST /esrs/toggle-chart-selection`
**Current Status:** ⚠️ Needs user testing

---

### Test 4: AI Edit Chart Dialog ✅ READY
**Objective:** Verify user can edit chart labels with natural language via AI

**Steps:**
1. Same as Test 1 (upload doc → get AI answer → charts visible)
2. Each chart should have an "Edit" button next to the chart type tag
3. Click "Edit" button
4. Modal should open with title "🤖 AI Edit Chart Labels"
5. Enter instruction: "daj moški/ženska namesto men/women"
6. Click "Apply AI Changes"
7. Wait for chart to regenerate

**Expected Results:**
- ✅ "Edit" button visible next to each chart
- ✅ Modal opens with textarea for instruction
- ✅ API call to `/esrs/ai-edit-chart` succeeds
- ✅ Chart image updates automatically
- ✅ Labels change according to instruction (e.g., Men → Moški, Women → Ženska)
- ✅ Success message: "Chart updated by AI!"

**API Endpoint:** `POST /esrs/ai-edit-chart`
**Current Status:** ⚠️ Needs user testing

---

### Test 5: RAG Document Usage ✅ VALIDATED
**Objective:** Verify AI uses uploaded document data

**Steps:**
1. Upload document with specific data (e.g., "7,982 employees")
2. Wait for "✓ Ready (N chunks)" status
3. Click "Get AI Answer"

**Expected Results:**
- ✅ AI answer includes specific numbers from document
- ✅ Example: "7,982 employees", "69% women, 31% men", "average age 43.9"
- ✅ Charts reflect document data accurately

**Status:** ✅ ALREADY VALIDATED (previous session)

---

## 🔧 Backend Changes Summary

### Files Modified:
1. **`backend/accounts/chart_analytics.py`**
   - Lines 28-47: Enhanced Pattern 3 regex
   - Lines 410-588: Category-specific label cleanup

2. **`frontend/src/views/ESRSView.vue`**
   - Lines 830-858: Added imports (marked, NCheckbox, CreateSharp)
   - Lines 1004-1023: Added state variables
   - Lines 164-201, 369-387: Chart UI with checkbox + Edit button
   - Lines 758-787: AI Edit Chart modal
   - Lines 1588-1644: New functions (toggle, AI edit)
   - Lines 1997-2062: Markdown CSS styling

3. **`frontend/package.json`**
   - Added: `marked` library for Markdown parsing

---

## 🎯 Success Criteria

### Must Pass:
- ✅ Chart labels are clean (no "women represent 69%" nonsense)
- ✅ AI text properly formatted with headings, lists, bold
- ✅ Checkbox next to each chart works
- ✅ Edit button opens modal with AI edit functionality

### Nice to Have:
- ✅ Chart selection persists across page refreshes
- ✅ AI edit produces better labels according to user instruction
- ✅ Multiple charts can be selected/deselected independently

---

## 📊 Test Data

### Recommended Test Document:
**NLB Group ESG Report** (already used successfully):
- Contains: Gender statistics (69% women, 31% men)
- Contains: Employee count (7,982 employees)
- Contains: Age data (average age 43.9 years)

### Alternative Test Documents:
- Any ESG report with numeric data
- Corporate sustainability reports
- Annual reports with employee statistics

---

## 🐛 Known Issues
- ⚠️ None currently - all features implemented and ready for testing

---

## 📝 Testing Notes

**Date:** _______________  
**Tester:** _______________  

### Test 1 Results:
- [ ] PASS - Chart labels clean
- [ ] FAIL - Issue: _________________

### Test 2 Results:
- [ ] PASS - Markdown formatted
- [ ] FAIL - Issue: _________________

### Test 3 Results:
- [ ] PASS - Checkbox works
- [ ] FAIL - Issue: _________________

### Test 4 Results:
- [ ] PASS - AI edit works
- [ ] FAIL - Issue: _________________

---

## 🚀 Next Steps After Testing

If all tests pass:
1. ✅ Mark version 1.0.37 as Production Ready
2. ✅ Update report generator to use only `selected_for_report: true` charts
3. ✅ Add user guide for chart management features
4. ✅ Consider adding bulk chart selection (Select All / Deselect All)

If issues found:
1. ❌ Document issues in GitHub/Jira
2. ❌ Fix bugs and restart affected services
3. ❌ Re-run failed tests
4. ❌ Update documentation with known issues

---

**End of Testing Checklist**
