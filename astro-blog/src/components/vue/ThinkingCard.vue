<template>
  <div ref="rootEl" class="thinking-stream" :class="{ expanded, streaming }">
    <button class="thinking-toggle" type="button" :aria-expanded="expanded" @click="toggle">
      <span class="thinking-pulse" aria-hidden="true" />
      <span class="thinking-label">{{ stateLabel }}</span>
      <span v-if="steps.length" class="thinking-count">{{ steps.length }} 条</span>
      <svg class="thinking-chevron" :class="{ open: expanded }" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <polyline points="6 9 12 15 18 9" />
      </svg>
    </button>

    <Transition name="thinking-reveal">
      <ol v-if="expanded && steps.length" class="thinking-steps" aria-live="polite">
        <li
          v-for="(step, index) in steps"
          :key="step.key"
          class="thinking-step"
          :class="{ current: index === steps.length - 1 && isTyping }"
        >
          <span class="step-marker" aria-hidden="true" />
          <span class="step-copy">{{ step.text }}</span>
          <span v-if="index === steps.length - 1 && isTyping" class="typing-caret" aria-hidden="true" />
        </li>
      </ol>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue';

const props = defineProps<{ text: string; streaming?: boolean }>();

interface ThoughtStep {
  key: string;
  text: string;
}

const rootEl = ref<HTMLElement>();
const revealedLength = ref(0);
const expanded = ref(props.streaming !== false);
const userToggled = ref(false);
const prefersReducedMotion = typeof window !== 'undefined'
  && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

let typingTimer: ReturnType<typeof setTimeout> | null = null;
let collapseTimer: ReturnType<typeof setTimeout> | null = null;

const graphemeSegmenter = typeof Intl !== 'undefined' && 'Segmenter' in Intl
  ? new Intl.Segmenter('zh-CN', { granularity: 'grapheme' })
  : null;
const textUnits = computed(() => graphemeSegmenter
  ? Array.from(graphemeSegmenter.segment(props.text), (part) => part.segment)
  : Array.from(props.text));
const textLength = computed(() => textUnits.value.length);
const visibleText = computed(() => textUnits.value.slice(0, revealedLength.value).join(''));
const isTyping = computed(() => revealedLength.value < textLength.value || !!props.streaming);
const stateLabel = computed(() => {
  if (props.streaming) return expanded.value ? '正在思考' : '继续思考中';
  if (revealedLength.value < textLength.value) return '整理思考中';
  return expanded.value ? '思考过程' : '思考完成';
});

const steps = computed<ThoughtStep[]>(() => splitThoughtSteps(visibleText.value));

function splitThoughtSteps(text: string): ThoughtStep[] {
  if (!text) return [];

  const normalized = text.replace(/\r\n?/g, '\n').replace(/[ \t]+\n/g, '\n').trimStart();
  if (!normalized) return [];

  const sentences = normalized.split(/(?<=[。！？!?；;])|(?<=\.)(?=\s)|(?<=\n)/);
  const parts: string[] = [];

  for (const sentence of sentences) {
    const clean = sentence.trim();
    if (!clean) continue;
    // 长段落再按分句切开，避免一整套推理挤在同一行里一次性出现。
    const clauses = clean.length > 46 ? clean.split(/(?<=[，,：:])/) : [clean];
    for (const clause of clauses) {
      const piece = clause.trim();
      if (piece) parts.push(piece);
    }
  }

  return parts.map((piece, index) => ({ key: `${index}:${piece.slice(0, 12)}`, text: piece }));
}

function revealNextBatch() {
  const remaining = textLength.value - revealedLength.value;
  if (remaining <= 0) {
    finishTyping();
    return;
  }

  const batch = remaining > 420 ? 8 : remaining > 180 ? 5 : remaining > 70 ? 3 : remaining > 24 ? 2 : 1;
  revealedLength.value = Math.min(textLength.value, revealedLength.value + batch);
  keepLatestStepVisible();

  if (revealedLength.value >= textLength.value && !props.streaming) finishTyping();
}

function startTyping() {
  if (typingTimer || revealedLength.value >= textLength.value) return;
  if (prefersReducedMotion) {
    revealedLength.value = textLength.value;
    finishTyping();
    return;
  }
  typingTimer = setTimeout(function tick() {
    typingTimer = null;
    revealNextBatch();
    if (revealedLength.value < textLength.value) startTyping();
  }, 24);
}

function finishTyping() {
  if (typingTimer) {
    clearTimeout(typingTimer);
    typingTimer = null;
  }
  if (!props.streaming && !userToggled.value) {
    if (collapseTimer) clearTimeout(collapseTimer);
    collapseTimer = setTimeout(() => {
      expanded.value = false;
      collapseTimer = null;
      keepLatestStepVisible();
    }, 900);
  }
}

function scheduleCollapse() {
  if (props.streaming || userToggled.value) return;
  if (revealedLength.value >= textLength.value) finishTyping();
}

function toggle() {
  userToggled.value = true;
  if (collapseTimer) {
    clearTimeout(collapseTimer);
    collapseTimer = null;
  }
  expanded.value = !expanded.value;
}

function keepLatestStepVisible() {
  nextTick(() => {
    const container = rootEl.value?.closest<HTMLElement>('[data-chat-scroll]');
    if (!container) return;
    const distanceToBottom = container.scrollHeight - container.scrollTop - container.clientHeight;
    if (distanceToBottom < 140) container.scrollTop = container.scrollHeight;
  });
}

watch(
  () => props.text,
  (value, previous) => {
    if (!value) {
      revealedLength.value = 0;
      return;
    }
    if (!value.startsWith(previous || '')) {
      revealedLength.value = 0;
      if (previous && !userToggled.value) expanded.value = true;
    }
    if (prefersReducedMotion) {
      revealedLength.value = textLength.value;
      scheduleCollapse();
      return;
    }
    startTyping();
  },
  { immediate: true },
);

watch(
  () => props.streaming,
  (streaming) => {
    if (collapseTimer) {
      clearTimeout(collapseTimer);
      collapseTimer = null;
    }
    if (streaming) {
      userToggled.value = false;
      expanded.value = true;
      startTyping();
      return;
    }
    if (revealedLength.value >= textLength.value) finishTyping();
    else startTyping();
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  if (typingTimer) clearTimeout(typingTimer);
  if (collapseTimer) clearTimeout(collapseTimer);
});
</script>

<style scoped>
.thinking-stream {
  width: 100%;
  margin: 1px 0 3px;
  color: #64748b;
  font-size: 12px;
}

.thinking-toggle {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  max-width: 100%;
  padding: 3px 0;
  border: 0;
  background: transparent;
  color: #94a3b8;
  font: inherit;
  cursor: pointer;
  text-align: left;
}

.thinking-toggle:hover { color: #64748b; }
.thinking-toggle:focus-visible {
  outline: 2px solid rgba(91, 123, 255, 0.4);
  outline-offset: 3px;
  border-radius: 4px;
}

.thinking-pulse {
  width: 6px;
  height: 6px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: #a5b4fc;
  box-shadow: 0 0 0 3px rgba(165, 180, 252, 0.14);
}

.thinking-stream.streaming .thinking-pulse {
  background: #5b7bff;
  animation: typing-pulse 1.5s ease-in-out infinite;
}

.thinking-label { white-space: nowrap; }
.thinking-count {
  color: #b0bac9;
  font-variant-numeric: tabular-nums;
}
.thinking-chevron {
  flex: 0 0 auto;
  transition: transform 180ms ease;
}
.thinking-chevron.open { transform: rotate(180deg); }

.thinking-steps {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin: 4px 0 7px 2px;
  padding: 2px 0 2px 15px;
  border-left: 1px solid #e4e9f3;
  list-style: none;
}

.thinking-step {
  position: relative;
  display: flex;
  align-items: flex-start;
  color: #6b7280;
  line-height: 1.65;
  text-wrap: pretty;
  word-break: break-word;
}

.thinking-step.current { color: #526075; }

.step-marker {
  position: absolute;
  top: 0.72em;
  left: -18px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #cbd5e1;
}

.thinking-step.current .step-marker {
  background: #8298ff;
  box-shadow: 0 0 0 3px rgba(130, 152, 255, 0.13);
}

.step-copy {
  min-width: 0;
  white-space: pre-wrap;
}

.typing-caret {
  width: 1px;
  height: 1.1em;
  flex: 0 0 auto;
  margin: 0.28em 0 0 3px;
  border-radius: 1px;
  background: #7188ff;
  animation: caret-blink 0.9s step-end infinite;
}

.thinking-reveal-enter-active { transition: opacity 180ms ease, transform 180ms ease; }
.thinking-reveal-leave-active { transition: opacity 120ms ease; }
.thinking-reveal-enter-from { opacity: 0; transform: translateY(-2px); }
.thinking-reveal-leave-to { opacity: 0; }

@keyframes typing-pulse {
  0%, 100% { transform: scale(1); opacity: 0.75; }
  50% { transform: scale(1.35); opacity: 1; }
}

@keyframes caret-blink {
  50% { opacity: 0; }
}

@media (prefers-reduced-motion: reduce) {
  .thinking-pulse,
  .typing-caret { animation: none; }
  .thinking-chevron,
  .thinking-reveal-enter-active,
  .thinking-reveal-leave-active { transition: none; }
}
</style>
