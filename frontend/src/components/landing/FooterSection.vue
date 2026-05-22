<template>
  <footer :style="{ padding: '3rem 0 2rem', borderTop: '1px solid var(--color-border-light)' }">
    <div class="container flex items-center justify-between">
      <div class="flex items-center gap-3">
        <svg width="28" height="28" viewBox="0 0 36 36" fill="none" style="opacity: 0.5">
          <path d="M18 4 C8 4, 3 10, 3 18 C3 26, 8 32, 18 32 C28 32, 33 26, 33 18 C33 10, 28 4, 18 4 Z" stroke="#C4956A" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
          <path d="M10 7 C9 4, 12 3, 13 6" stroke="#C4956A" stroke-width="2.2" stroke-linecap="round" fill="none"/>
          <path d="M23 6 C24 3, 27 4, 26 7" stroke="#C4956A" stroke-width="2.2" stroke-linecap="round" fill="none"/>
          <circle cx="13" cy="16" r="2" fill="#C4956A"/>
          <circle cx="23" cy="16" r="2" fill="#C4956A"/>
          <path d="M18 19 L18 23" stroke="#C4956A" stroke-width="2" stroke-linecap="round"/>
          <path d="M14 23 Q18 27 22 23" stroke="#C4956A" stroke-width="2" stroke-linecap="round" fill="none"/>
        </svg>
        <span class="text-sm" style="color: var(--color-ink-muted)">&copy; 2026 CapyMock. Made with care.</span>
      </div>
      <ul class="flex gap-6 list-none m-0 p-0">
        <li><a href="#" class="text-sm transition-colors hover:text-primary" style="color: var(--color-ink-muted)">关于我们</a></li>
        <li><a href="#" class="text-sm transition-colors hover:text-primary" style="color: var(--color-ink-muted)">隐私政策</a></li>
        <li><a href="#" class="text-sm transition-colors hover:text-primary" style="color: var(--color-ink-muted)">联系方式</a></li>
      </ul>
    </div>
  </footer>
</template>
