<template>
  <div class="moving-arrow" :style="arrowStyle"></div>
</template>
<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  moveY?: number
}

const props = withDefaults(defineProps<Props>(), {
  moveY: 0
})

const arrowStyle = computed(() => ({
  transform: `translate3d(0px, ${props.moveY}px, 0px)`
}))
</script>
<style lang="scss">
$bg-nude: #f4f3ef !default;

.moving-arrow {
  border-right: 17px solid $bg-nude;
  border-top: 17px solid transparent;
  border-bottom: 17px solid transparent;
  display: inline-block;
  position: absolute;
  left: 243px;
  top: 95px;
  transition: all 0.5s cubic-bezier(0.29, 1.42, 0.79, 1);
}
@media (max-width: 992px) {
  .moving-arrow {
    display: none;
  }
}
</style>
