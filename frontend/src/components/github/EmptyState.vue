<script setup>
const emit = defineEmits(['add'])
</script>

<template>
  <div class="flex flex-col items-center justify-center py-16 px-6 text-center">
    <!-- Capybara illustration -->
    <div class="mb-6 opacity-60">
      <svg width="120" height="120" viewBox="0 0 120 120" fill="none">
        <ellipse cx="60" cy="65" rx="38" ry="30" stroke="var(--color-primary)" stroke-width="2" fill="none" opacity="0.4"/>
        <ellipse cx="60" cy="60" rx="28" ry="22" stroke="var(--color-primary)" stroke-width="2" fill="none" opacity="0.6"/>
        <circle cx="48" cy="55" r="3" fill="var(--color-primary)" opacity="0.6"/>
        <circle cx="72" cy="55" r="3" fill="var(--color-primary)" opacity="0.6"/>
        <path d="M54 65 Q60 72 66 65" stroke="var(--color-primary)" stroke-width="2" stroke-linecap="round" fill="none" opacity="0.6"/>
        <!-- Magnifying glass -->
        <circle cx="88" cy="42" r="12" stroke="var(--color-primary)" stroke-width="2" fill="none" opacity="0.3"/>
        <line x1="96" y1="50" x2="105" y2="59" stroke="var(--color-primary)" stroke-width="2.5" stroke-linecap="round" opacity="0.3"/>
      </svg>
    </div>

    <h3 class="text-lg font-bold text-ink mb-2">还没有分析过仓库</h3>
    <p class="text-sm text-ink-muted mb-6 max-w-xs leading-relaxed">
      粘贴一个 GitHub 仓库链接，Capy 帮你分析代码结构、技术栈和项目亮点
    </p>

    <button class="btn btn--primary" @click="emit('add')">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
      添加第一个仓库
    </button>
  </div>
</template>
