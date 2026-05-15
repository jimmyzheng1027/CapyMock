import { reactive, watchEffect } from 'vue'

const state = reactive({
  dark: false,
})

function init() {
  const saved = localStorage.getItem('pawfolio-dark')
  if (saved !== null) {
    state.dark = saved === '1'
  } else {
    state.dark = window.matchMedia('(prefers-color-scheme: dark)').matches
  }
}

function toggle() {
  state.dark = !state.dark
}

function set(val) {
  state.dark = val
}

watchEffect(() => {
  document.documentElement.classList.toggle('dark', state.dark)
  localStorage.setItem('pawfolio-dark', state.dark ? '1' : '0')
})

init()

export function useTheme() {
  return { state, toggle, set }
}
