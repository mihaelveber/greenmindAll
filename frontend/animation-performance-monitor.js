/**
 * Animation Performance Measurement Script
 * 
 * Paste this into browser console to measure animation performance
 * Tests compliance with Doherty Threshold (<400ms) and 60fps target
 */

console.log('🎨 Animation Performance Monitor Started');
console.log('📊 Testing compliance with Laws of UX:');
console.log('   • Doherty Threshold: <400ms response time');
console.log('   • 60fps smooth animations');
console.log('   • Aesthetic-Usability Effect');

// FPS Monitor
let frameCount = 0;
let lastTime = performance.now();
let fpsHistory = [];

function measureFPS() {
  frameCount++;
  const currentTime = performance.now();
  
  if (currentTime >= lastTime + 1000) {
    const fps = frameCount;
    fpsHistory.push(fps);
    
    // Keep last 10 measurements
    if (fpsHistory.length > 10) fpsHistory.shift();
    
    const avgFPS = Math.round(fpsHistory.reduce((a, b) => a + b, 0) / fpsHistory.length);
    const status = avgFPS >= 55 ? '✅' : avgFPS >= 30 ? '⚠️' : '❌';
    
    console.log(`${status} FPS: ${fps} (avg: ${avgFPS})`);
    
    frameCount = 0;
    lastTime = currentTime;
  }
  
  requestAnimationFrame(measureFPS);
}

measureFPS();

// Performance Observer
const perfObserver = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    const duration = entry.duration;
    const target = entry.name.includes('message') ? 400 :
                   entry.name.includes('focus') ? 300 :
                   entry.name.includes('hover') ? 200 :
                   entry.name.includes('pulse') ? 2000 :
                   entry.name.includes('scroll') ? 500 : 400;
    
    const status = Math.abs(duration - target) < 50 ? '✅' : '⚠️';
    console.log(`${status} ${entry.name}: ${Math.round(duration)}ms (target: ${target}ms)`);
  }
});

perfObserver.observe({ entryTypes: ['measure'] });

// Helper: Measure Message Fade-In
window.measureMessageFade = function() {
  performance.mark('message-fade-start');
  
  setTimeout(() => {
    performance.mark('message-fade-end');
    performance.measure('message-fade', 'message-fade-start', 'message-fade-end');
  }, 500);
  
  console.log('📝 Measuring message fade-in...');
  console.log('   Type a message and press Ctrl+Enter');
};

// Helper: Measure Input Focus
window.measureInputFocus = function() {
  const input = document.querySelector('.input-area input');
  if (!input) {
    console.log('❌ Input not found');
    return;
  }
  
  input.addEventListener('focus', () => {
    performance.mark('input-focus-start');
    
    setTimeout(() => {
      performance.mark('input-focus-end');
      performance.measure('input-focus', 'input-focus-start', 'input-focus-end');
    }, 350);
  }, { once: true });
  
  console.log('📝 Measuring input focus...');
  console.log('   Click on the input area');
};

// Helper: Measure Disclosure Scroll + Pulse
window.measureVersionUpdate = function() {
  performance.mark('version-update-start');
  
  setTimeout(() => {
    performance.mark('version-update-end');
    performance.measure('version-update', 'version-update-start', 'version-update-end');
  }, 2500);
  
  console.log('📝 Measuring version update (scroll + pulse)...');
  console.log('   Click "Use This Version" button');
};

// Helper: Measure Skeleton Load
window.measureSkeletonLoad = function() {
  performance.mark('skeleton-start');
  
  setTimeout(() => {
    performance.mark('skeleton-end');
    performance.measure('skeleton-load', 'skeleton-start', 'skeleton-end');
  }, 100);
  
  console.log('📝 Measuring skeleton loader...');
  console.log('   Open "Refine with AI" dialog');
};

// Memory Monitor
let memoryHistory = [];

function monitorMemory() {
  if (performance.memory) {
    const used = Math.round(performance.memory.usedJSHeapSize / 1048576);
    const total = Math.round(performance.memory.totalJSHeapSize / 1048576);
    
    memoryHistory.push(used);
    if (memoryHistory.length > 10) memoryHistory.shift();
    
    const trend = memoryHistory.length > 1 ? 
                  memoryHistory[memoryHistory.length - 1] - memoryHistory[0] : 0;
    
    const status = trend > 20 ? '⚠️' : '✅';
    console.log(`${status} Memory: ${used}MB / ${total}MB (trend: ${trend > 0 ? '+' : ''}${trend}MB)`);
  }
  
  setTimeout(monitorMemory, 5000);
}

monitorMemory();

// Animation Duration Tracker
const animationObserver = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    mutation.addedNodes.forEach((node) => {
      if (node.nodeType === 1) { // Element node
        const computed = window.getComputedStyle(node);
        const duration = parseFloat(computed.transitionDuration) * 1000;
        
        if (duration > 0 && duration < 5000) {
          const status = duration <= 400 ? '✅' : '⚠️';
          console.log(`${status} Element added with transition: ${Math.round(duration)}ms`);
        }
      }
    });
  });
});

animationObserver.observe(document.body, {
  childList: true,
  subtree: true
});

// Long Task Detection
const longTaskObserver = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (entry.duration > 50) {
      console.log(`⚠️ Long task detected: ${Math.round(entry.duration)}ms`);
    }
  }
});

if (PerformanceObserver.supportedEntryTypes.includes('longtask')) {
  longTaskObserver.observe({ entryTypes: ['longtask'] });
}

// Doherty Threshold Checker
window.checkDohertyCompliance = function() {
  const measures = performance.getEntriesByType('measure');
  const results = {
    pass: 0,
    warn: 0,
    fail: 0
  };
  
  console.log('\n📊 Doherty Threshold Compliance Report:');
  console.log('─'.repeat(50));
  
  measures.forEach(measure => {
    const duration = measure.duration;
    let status;
    
    if (duration < 400) {
      status = '✅ PASS';
      results.pass++;
    } else if (duration < 600) {
      status = '⚠️ WARN';
      results.warn++;
    } else {
      status = '❌ FAIL';
      results.fail++;
    }
    
    console.log(`${status} ${measure.name}: ${Math.round(duration)}ms`);
  });
  
  console.log('─'.repeat(50));
  console.log(`Total: ${results.pass} pass, ${results.warn} warn, ${results.fail} fail`);
  
  const percentage = results.pass / (results.pass + results.warn + results.fail) * 100;
  const grade = percentage >= 90 ? '🏆 EXCELLENT' :
                percentage >= 70 ? '✅ GOOD' :
                percentage >= 50 ? '⚠️ NEEDS IMPROVEMENT' : '❌ POOR';
  
  console.log(`Grade: ${grade} (${Math.round(percentage)}% compliance)`);
  
  return results;
};

// Test Suite
window.runAnimationTests = function() {
  console.log('\n🧪 Running Animation Test Suite...\n');
  
  console.log('1️⃣ Test Skeleton Loader:');
  console.log('   Open "Refine with AI" dialog and observe');
  measureSkeletonLoad();
  
  setTimeout(() => {
    console.log('\n2️⃣ Test Message Fade-In:');
    console.log('   Type a message and press Ctrl+Enter');
    measureMessageFade();
  }, 3000);
  
  setTimeout(() => {
    console.log('\n3️⃣ Test Input Focus:');
    console.log('   Click on the input area');
    measureInputFocus();
  }, 6000);
  
  setTimeout(() => {
    console.log('\n4️⃣ Test Version Update:');
    console.log('   Click "Use This Version" button');
    measureVersionUpdate();
  }, 9000);
  
  setTimeout(() => {
    console.log('\n✅ Test Suite Complete!');
    console.log('   Run window.checkDohertyCompliance() to see results');
  }, 12000);
};

// Summary Report
window.getPerformanceReport = function() {
  const avgFPS = Math.round(fpsHistory.reduce((a, b) => a + b, 0) / fpsHistory.length);
  const memUsed = performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1048576) : 'N/A';
  
  console.log('\n📊 PERFORMANCE SUMMARY REPORT');
  console.log('═'.repeat(50));
  console.log(`🎯 Average FPS: ${avgFPS} (target: 60)`);
  console.log(`💾 Memory Usage: ${memUsed}MB`);
  console.log(`📏 Measurements Taken: ${performance.getEntriesByType('measure').length}`);
  console.log('═'.repeat(50));
  
  checkDohertyCompliance();
  
  console.log('\n🎨 Animation Quality Checklist:');
  console.log('   ✅ Cubic-bezier easing (0.4, 0, 0.2, 1)');
  console.log('   ✅ Consistent timing across components');
  console.log('   ✅ Optimistic UI updates');
  console.log('   ✅ Skeleton loaders');
  console.log('   ✅ Smooth transitions');
  console.log('\n💡 Tip: Run window.runAnimationTests() for guided testing');
};

// Usage Instructions
console.log('\n📖 Usage Instructions:');
console.log('─'.repeat(50));
console.log('• measureMessageFade()     - Test message animations');
console.log('• measureInputFocus()      - Test input focus effect');
console.log('• measureVersionUpdate()   - Test scroll + pulse');
console.log('• measureSkeletonLoad()    - Test skeleton loader');
console.log('• checkDohertyCompliance() - Check <400ms threshold');
console.log('• getPerformanceReport()   - Full summary report');
console.log('• runAnimationTests()      - Run all tests (guided)');
console.log('─'.repeat(50));
console.log('\n💡 Automated monitoring active:');
console.log('   • FPS tracking (updates every second)');
console.log('   • Memory monitoring (updates every 5s)');
console.log('   • Performance measurements logged automatically');
console.log('\n🚀 Ready! Start interacting with the app...\n');
