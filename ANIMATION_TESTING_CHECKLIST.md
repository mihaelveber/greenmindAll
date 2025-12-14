# Animation Testing Checklist

## 🎯 Goal
Verify all new animations meet research-backed UX standards:
- **Doherty Threshold**: All interactions <400ms
- **Aesthetic-Usability Effect**: Beautiful and smooth
- **Peak-End Rule**: Memorable moments (highlight pulse)
- **60fps Performance**: No jank or stuttering

---

## ✅ ChatInterface Animations

### 1. Skeleton Loader
**Location**: Open "Refine with AI" dialog

**Expected Behavior**:
- [ ] 3 shimmer blocks appear immediately
- [ ] Shimmer animation runs smoothly (left to right)
- [ ] Loads for ~100-200ms before showing conversation
- [ ] Smooth fade from skeleton to actual messages

**Performance**:
- [ ] Skeleton renders in <50ms
- [ ] Shimmer animation at 60fps
- [ ] No layout shift when switching to real content

**Command to Test**:
```javascript
// In browser console, measure skeleton performance
performance.mark('skeleton-start')
// Open "Refine with AI"
performance.mark('skeleton-end')
performance.measure('skeleton', 'skeleton-start', 'skeleton-end')
console.log(performance.getEntriesByName('skeleton')[0].duration) // Should be <50ms
```

---

### 2. Message Fade-In Animation
**Location**: ChatInterface - Send message

**Expected Behavior**:
- [ ] User message fades in from bottom (10px translateY)
- [ ] Animation takes exactly 0.4s
- [ ] Cubic-bezier easing feels natural (not linear)
- [ ] AI response fades in the same way
- [ ] Multiple messages animate in sequence (staggered feel)

**Performance**:
- [ ] Animation completes in 400ms ± 50ms
- [ ] No frame drops during animation
- [ ] Smooth on slow devices (test with 4x CPU slowdown)

**Command to Test**:
```javascript
// Measure fade-in timing
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    console.log(entry.name, entry.duration)
  }
})
observer.observe({ entryTypes: ['measure'] })

performance.mark('message-start')
// Type message and press Ctrl+Enter
setTimeout(() => {
  performance.mark('message-end')
  performance.measure('message-fade', 'message-start', 'message-end')
}, 500)
```

---

### 3. Input Focus Animation
**Location**: ChatInterface - Input area

**Expected Behavior**:
- [ ] Click input → lifts 2px (translateY: -2px)
- [ ] Shadow strengthens on focus (rgba(102, 126, 234, 0.4))
- [ ] Transition takes 0.3s
- [ ] Unfocus reverses smoothly
- [ ] Focus ring visible for accessibility

**Performance**:
- [ ] Focus animation <300ms
- [ ] Shadow transition smooth
- [ ] No visual glitches

**Manual Test**:
1. Click outside input
2. Click inside input
3. Observe lift and shadow change
4. Tab to input (keyboard test)
5. Verify focus ring appears

---

### 4. Message Bubble Hover
**Location**: ChatInterface - Message bubbles

**Expected Behavior**:
- [ ] Hover → slides right 4px (translateX: 4px)
- [ ] Shadow increases on hover
- [ ] Transition takes 0.2s
- [ ] Smooth return when unhover
- [ ] Works on both user and AI messages

**Performance**:
- [ ] Hover animation <200ms
- [ ] No lag when moving mouse quickly
- [ ] Smooth on low-end devices

**Manual Test**:
1. Move mouse over message bubble
2. Observe slide-right motion
3. Move mouse away
4. Verify smooth return
5. Hover multiple messages rapidly

---

## ✅ ESRSView Animations

### 5. Disclosure Slide Transition
**Location**: ESRSView - Disclosure items

**Expected Behavior**:
- [ ] New disclosure slides in from left (-20px translateX)
- [ ] Removed disclosure slides out to right (20px translateX)
- [ ] Opacity fades simultaneously
- [ ] Transition takes 0.4s
- [ ] Multiple disclosures animate smoothly

**Performance**:
- [ ] Slide animation <400ms
- [ ] No layout shift during animation
- [ ] Smooth with many disclosures (50+)

**Manual Test**:
1. Select different standards
2. Watch disclosures slide in/out
3. Rapidly switch standards
4. Verify smooth transitions

---

### 6. Highlight Pulse Animation
**Location**: ESRSView - After version selection

**Expected Behavior**:
- [ ] Click "Use This Version"
- [ ] Page scrolls smoothly to disclosure (center)
- [ ] Disclosure pulses green for 2 seconds
- [ ] Pulse: 0% → 50% (green background) → 100% (transparent)
- [ ] Shadow appears/disappears with pulse
- [ ] Success message appears: "✨ Version created and applied!"

**Performance**:
- [ ] Scroll completes in <500ms
- [ ] Pulse animation exactly 2s
- [ ] Smooth 60fps throughout
- [ ] No jank on scroll

**Manual Test**:
1. Open "Refine with AI" dialog
2. Type instruction, send
3. Click "Use This Version" when AI responds
4. Observe smooth scroll
5. Watch 2s green pulse
6. Verify success message

**Command to Measure**:
```javascript
// In onRefinementComplete function, add:
performance.mark('version-start')
// ... existing code ...
setTimeout(() => {
  performance.mark('version-end')
  performance.measure('version-update', 'version-start', 'version-end')
  console.log(performance.getEntriesByName('version-update')[0].duration)
  // Should be ~2500ms (500ms scroll + 2000ms pulse)
}, 2500)
```

---

### 7. Smooth Scroll Behavior
**Location**: ESRSView - Navigation

**Expected Behavior**:
- [ ] Click disclosure → smooth scroll
- [ ] Scroll animation feels natural (not linear)
- [ ] Centers disclosure in viewport (block: 'center')
- [ ] Works on long pages (many disclosures)

**Performance**:
- [ ] Scroll completes in <500ms
- [ ] No frame drops
- [ ] Respects user motion preferences

**Manual Test**:
1. Navigate to different disclosures
2. Observe scroll behavior
3. Test with many disclosures (30+)
4. Verify smooth motion

---

## 🚀 Performance Testing

### Test 1: Slow Network (Slow 3G)
**Chrome DevTools**: Network tab → Slow 3G

**Expected**:
- [ ] Skeleton loader appears immediately
- [ ] Animations still smooth despite slow network
- [ ] Optimistic updates work (messages appear before backend confirms)
- [ ] No animation delays or stuttering

**Steps**:
1. Open DevTools → Network tab
2. Throttle to "Slow 3G"
3. Test all animations above
4. Verify <400ms response time maintained

---

### Test 2: Low-End Device (CPU Slowdown)
**Chrome DevTools**: Performance tab → CPU: 4x slowdown

**Expected**:
- [ ] All animations still hit 60fps
- [ ] No frame drops during transitions
- [ ] Smooth on 4x CPU throttle
- [ ] Hover/focus still responsive

**Steps**:
1. Open DevTools → Performance tab
2. Set CPU throttling to 4x slowdown
3. Record performance
4. Test all animations
5. Check frame rate stays ~60fps

**Command to Check FPS**:
```javascript
let frameCount = 0
let lastTime = performance.now()

function measureFPS() {
  frameCount++
  const currentTime = performance.now()
  
  if (currentTime >= lastTime + 1000) {
    console.log(`FPS: ${frameCount}`)
    frameCount = 0
    lastTime = currentTime
  }
  
  requestAnimationFrame(measureFPS)
}

measureFPS()
// Should log ~60 FPS during animations
```

---

### Test 3: Many Messages (50+)
**Location**: ChatInterface with long conversation

**Expected**:
- [ ] Scroll remains smooth with 50+ messages
- [ ] Fade-in animations still work
- [ ] No memory leaks
- [ ] Performance doesn't degrade

**Steps**:
1. Create conversation with 50+ messages
2. Scroll up and down
3. Add new message
4. Verify smooth fade-in
5. Check memory usage (shouldn't increase)

---

### Test 4: Rapid Interactions
**Location**: All animated components

**Expected**:
- [ ] Rapid clicking doesn't break animations
- [ ] Hover states clean up properly
- [ ] No stuck animations
- [ ] Transitions queue correctly

**Steps**:
1. Rapidly click "Refine with AI" (open/close)
2. Quickly hover many messages
3. Spam version selection
4. Fast scroll through disclosures
5. Verify no visual glitches

---

## 🎨 Visual Quality Checks

### Animation Smoothness
- [ ] All transitions use cubic-bezier(0.4, 0, 0.2, 1)
- [ ] No linear animations (feel robotic)
- [ ] Natural easing (slow start, fast middle, slow end)
- [ ] Consistent timing across components

### Timing Accuracy
- [ ] Message fade: 400ms ± 50ms
- [ ] Input focus: 300ms ± 50ms
- [ ] Message hover: 200ms ± 50ms
- [ ] Disclosure slide: 400ms ± 50ms
- [ ] Highlight pulse: 2000ms ± 100ms

### Shadow & Color Transitions
- [ ] Shadows transition smoothly (no popping)
- [ ] Colors fade naturally
- [ ] Green highlight visible but not jarring
- [ ] Focus states clearly visible

### Accessibility
- [ ] Focus states visible (2px outline)
- [ ] Keyboard navigation works
- [ ] Screen reader announces changes
- [ ] Respects prefers-reduced-motion

**Check Reduced Motion**:
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 📊 Metrics to Track

### Doherty Threshold Compliance
All interactions should complete in <400ms:

| Animation | Target | Measured | Status |
|-----------|--------|----------|--------|
| Skeleton load | <50ms | ___ ms | ⬜ |
| Message fade | 400ms | ___ ms | ⬜ |
| Input focus | 300ms | ___ ms | ⬜ |
| Message hover | 200ms | ___ ms | ⬜ |
| Disclosure slide | 400ms | ___ ms | ⬜ |
| Highlight pulse | 2000ms | ___ ms | ⬜ |
| Smooth scroll | <500ms | ___ ms | ⬜ |

### Performance Metrics
| Test Scenario | FPS Target | Measured | Status |
|---------------|------------|----------|--------|
| Normal device | 60 fps | ___ fps | ⬜ |
| 4x CPU slowdown | 30+ fps | ___ fps | ⬜ |
| 50+ messages | 60 fps | ___ fps | ⬜ |
| Slow 3G | 60 fps | ___ fps | ⬜ |

---

## 🐛 Known Issues to Check

### Potential Problems
- [ ] Skeleton not showing on first load
- [ ] Messages not fading in (instant appear)
- [ ] Input focus state stuck
- [ ] Hover effects lagging on low-end devices
- [ ] Disclosure transitions janky with many items
- [ ] Highlight pulse not visible (timing off)
- [ ] Scroll too fast or too slow
- [ ] Animation conflicts when spamming

### Edge Cases
- [ ] First message in empty conversation
- [ ] Very long messages (1000+ characters)
- [ ] Switching disclosures during animation
- [ ] Closing modal mid-animation
- [ ] Browser window resize during animation
- [ ] Tab switch/focus change during animation

---

## ✨ Quality Criteria (User Demand: "mora biti nor!")

### Professional Grade
- [x] Research-backed (Laws of UX applied)
- [x] Consistent cubic-bezier easing
- [x] Performance optimized (<400ms)
- [ ] Tested on slow devices (**TODO**)
- [ ] No visual glitches (**TODO**)
- [ ] Accessible (keyboard, screen readers)

### "Crazy Good" Features
- [x] Skeleton loaders (industry standard)
- [x] Smooth fade-in animations
- [x] Focus depth perception (shadow lift)
- [x] Hover interactivity
- [x] Optimistic UI updates
- [x] Highlight pulse (memorable moment)
- [ ] All animations <400ms (**VERIFY**)
- [ ] 60fps on all devices (**TEST**)

### User Satisfaction
- [ ] Feels smooth and polished
- [ ] No rough edges
- [ ] Animations enhance UX (not distract)
- [ ] Professional like commercial products
- [ ] "Wow" factor achieved

---

## 🎯 Next Steps

After completing this checklist:

1. **Fix any issues found** (adjust timing, easing, performance)
2. **Document performance metrics** (fill in tables above)
3. **Take screenshots/videos** of animations for documentation
4. **Continue TODO list**:
   - Rich text editor (Quill.js)
   - Chart manual editor
   - Version tree visualization
   - Version comparison view

---

## 📝 Testing Log

**Date**: _______________  
**Tester**: _______________  
**Browser**: Chrome/Firefox/Safari  
**Device**: Desktop/Laptop/Mobile  

**Overall Result**: ⬜ PASS / ⬜ FAIL  
**Issues Found**: _______________  
**Recommended Fixes**: _______________  

**Notes**:
_______________
_______________
_______________

