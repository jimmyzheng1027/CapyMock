<script setup>
import capyLogo from '@/assets/capy_logo.png'

defineProps({
  size: { type: Number, default: 36 },
  color: { type: String, default: 'var(--color-primary, #C4956A)' },
  strokeWidth: { type: Number, default: 2.2 },
})
</script>

<template>
  <img
    :src="capyLogo"
    alt="CapyMock"
    :width="size"
    :height="size"
    class="object-contain shrink-0"
    :style="color === 'white' ? { filter: 'brightness(0) invert(1)' } : undefined"
  />
</template>
