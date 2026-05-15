import { reactive, watchEffect } from 'vue'

const state = reactive({
  primary: '#C4956A',
  fontSize: 16,
  radius: 16,
  animations: true,
})

function setPrimary(hex) {
  state.primary = hex
  document.documentElement.style.setProperty('--color-primary', hex)
}

function setFontSize(px) {
  state.fontSize = px
  document.documentElement.style.fontSize = px + 'px'
}

function setRadius(px) {
  state.radius = px
  document.documentElement.style.setProperty('--radius-xl', px + 'px')
  document.documentElement.style.setProperty('--radius-lg', (px * 0.8) + 'px')
}

function toggleAnimations() {
  state.animations = !state.animations
  const d = state.animations ? undefined : '0ms'
  document.documentElement.style.setProperty('--duration-fast', d || '')
  document.documentElement.style.setProperty('--duration-normal', d || '')
  document.documentElement.style.setProperty('--duration-slow', d || '')
}

export function useTweaks() {
  return { state, setPrimary, setFontSize, setRadius, toggleAnimations }
}
