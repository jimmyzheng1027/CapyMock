<script setup>
defineProps({
  size: { type: Number, default: 36 },
  color: { type: String, default: 'var(--color-primary, #C4956A)' },
  strokeWidth: { type: Number, default: 2.2 },
})
</script>

<template>
  <svg :width="size" :height="size" viewBox="0 0 36 36" fill="none">
    <path
      d="M18 4 C8 4, 3 10, 3 18 C3 26, 8 32, 18 32 C28 32, 33 26, 33 18 C33 10, 28 4, 18 4 Z"
      :stroke="color" :stroke-width="strokeWidth" stroke-linecap="round" stroke-linejoin="round" fill="none"
    />
    <path d="M10 7 C9 4, 12 3, 13 6" :stroke="color" :stroke-width="strokeWidth" stroke-linecap="round" fill="none" />
    <path d="M23 6 C24 3, 27 4, 26 7" :stroke="color" :stroke-width="strokeWidth" stroke-linecap="round" fill="none" />
    <circle cx="13" cy="16" r="2" :fill="color" />
    <circle cx="23" cy="16" r="2" :fill="color" />
    <path d="M18 19 L18 23" :stroke="color" :stroke-width="strokeWidth * 0.9" stroke-linecap="round" />
    <path d="M14 23 Q18 27 22 23" :stroke="color" :stroke-width="strokeWidth * 0.9" stroke-linecap="round" fill="none" />
  </svg>
</template>
