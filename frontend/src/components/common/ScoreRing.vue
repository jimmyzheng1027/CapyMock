<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  score: { type: Number, default: 0 },
  label: { type: String, default: '' },
  summary: { type: String, default: '' },
})

const CIRCUMFERENCE = 213.6
const displayScore = ref(0)
const dashOffset = ref(CIRCUMFERENCE)

function animate(target) {
  const offset = CIRCUMFERENCE - (target / 100) * CIRCUMFERENCE
  dashOffset.value = offset

  let current = 0
  const step = target / 40
  const interval = setInterval(() => {
    current += step
    if (current >= target) {
      current = target
      clearInterval(interval)
    }
    displayScore.value = Math.round(current)
  }, 25)
}

onMounted(() => {
  if (props.score > 0) animate(props.score)
})

watch(() => props.score, (v) => {
  if (v > 0) animate(v)
})
</script>

<template>
  <div
    class="flex items-center gap-6"
    :style="{
      padding: '1.5rem 2rem',
      background: 'var(--color-white)',
      border: '1px solid var(--color-border-light)',
      borderRadius: 'var(--radius-xl)',
    }"
  >
    <svg class="w-20 h-20 shrink-0" viewBox="0 0 80 80">
      <circle cx="40" cy="40" r="34" stroke-width="6" fill="none" :style="{ stroke: 'var(--color-border-light)' }" />
      <circle
        cx="40" cy="40" r="34" stroke-width="6" fill="none"
        :stroke-dasharray="CIRCUMFERENCE"
        :stroke-dashoffset="dashOffset"
        stroke-linecap="round"
        class="origin-center -rotate-90"
        :style="{ stroke: 'var(--color-primary)', transition: 'stroke-dashoffset 1s var(--ease-out)' }"
      />
    </svg>
    <div>
      <div class="text-4xl font-bold leading-none" :style="{ color: 'var(--color-primary)' }">{{ displayScore }}</div>
      <h4 class="text-lg mt-1 font-bold" style="font-family: var(--font-heading)">{{ label }}</h4>
      <p class="text-sm" style="color: var(--color-ink-light)">{{ summary }}</p>
    </div>
  </div>
</template>
