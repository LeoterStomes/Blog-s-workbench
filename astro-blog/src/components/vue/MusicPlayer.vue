<template>
  <div class="glass-card p-4">
    <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3 flex items-center gap-1.5">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"/></svg>
      音乐
    </h3>

    <div v-if="!loggedIn" class="text-center py-4">
      <p class="text-xs text-gray-400 mb-2">登录后使用你的私人歌单</p>
      <a href="/auth/login" class="text-xs text-brand-600 hover:text-brand-700">去登录</a>
    </div>

    <div v-else-if="loading" class="text-xs text-gray-400 text-center py-4">加载歌单中...</div>
    <div v-else-if="loadError" class="text-center py-4">
      <p class="text-xs text-red-500 mb-2">{{ loadError }}</p>
      <button @click="loadPlaylist" class="text-xs text-brand-600 hover:text-brand-700">重新加载</button>
    </div>

    <div v-else-if="playlist.length === 0" class="text-center py-4">
      <p class="text-xs text-gray-400 mb-2">你的歌单还是空的</p>
      <a href="/music" class="text-xs text-brand-600 hover:text-brand-700">添加音乐</a>
    </div>

    <div v-else>
      <div class="text-center mb-3">
        <p class="text-xs font-semibold text-gray-700 truncate">{{ current.title }}</p>
        <p class="text-[10px] text-gray-400 truncate">{{ current.artist }}</p>
      </div>

      <input
        type="range"
        min="0"
        :max="duration || 0"
        step="0.1"
        :value="currentTime"
        :disabled="duration <= 0"
        aria-label="播放进度"
        class="progress-range w-full mb-2"
        :style="{ '--music-progress': progress + '%' }"
        @pointerdown="beginSeeking"
        @input="seekFromInput"
        @change="finishSeeking"
        @pointerup="finishSeeking"
        @blur="finishSeeking"
      />
      <div class="flex justify-between text-[10px] text-gray-400 mb-3">
        <span>{{ formatTime(currentTime) }}</span><span>{{ formatTime(duration) }}</span>
      </div>

      <div class="flex items-center justify-center gap-4">
        <button @click="prev" class="text-gray-500 hover:text-gray-700" :disabled="playlist.length <= 1">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/></svg>
        </button>
        <button @click="togglePlay" :disabled="switching" class="w-9 h-9 rounded-full bg-brand-600 text-white flex items-center justify-center hover:bg-brand-700 shadow-sm disabled:opacity-50">
          <svg v-if="!playing" class="w-4 h-4 ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          <svg v-else class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
        </button>
        <button @click="next" class="text-gray-500 hover:text-gray-700" :disabled="playlist.length <= 1">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/></svg>
        </button>
      </div>

      <div class="flex items-center gap-2 mt-3 px-1">
        <svg class="w-3.5 h-3.5 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072M6.5 8.5H3a1 1 0 00-1 1v5a1 1 0 001 1h3.5l5 4.5V4l-5 4.5z"/></svg>
        <input v-model.number="volume" type="range" min="0" max="1" step="0.05" class="w-full h-1 accent-brand-600 cursor-pointer" @input="setVolume" />
      </div>

      <button @click="showList = !showList" class="w-full mt-3 text-[11px] text-gray-400 hover:text-gray-600 flex items-center justify-center gap-1">
        <svg class="w-3 h-3 transition-transform" :class="{ 'rotate-90': showList }" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
        {{ showList ? '收起' : '播放列表' }} ({{ playlist.length }})
      </button>

      <div v-if="showList" class="mt-2 space-y-0.5 max-h-[180px] overflow-y-auto">
        <div v-for="(s, i) in playlist" :key="s.id" @click="selectTrack(i)"
          :class="['flex items-center justify-between px-2 py-1.5 rounded-lg text-xs cursor-pointer', i === index ? 'bg-brand-50 text-brand-600 font-medium' : 'text-gray-600 hover:bg-gray-50']">
          <span class="truncate flex-1">{{ s.title }}</span>
          <span class="text-[10px] text-gray-400 ml-1">{{ s.artist }}</span>
        </div>
      </div>

      <div v-if="currentLine" class="mt-3 text-center animate-fade-in">
        <p class="text-[11px] text-gray-500 italic leading-relaxed">{{ currentLine }}</p>
      </div>

      <div v-if="error" class="mt-3 text-center text-[11px] text-red-500">{{ error }}</div>

      <a href="/music" class="mt-3 flex items-center justify-center text-[10px] text-gray-400 hover:text-brand-600">管理我的歌单</a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { getToken, getUser } from '@lib/auth';

interface Track { id: number; title: string; artist: string; url: string; lyrics?: string }
interface SavedState { url: string; currentTime: number; volume: number }
interface GlobalAudio {
  load(url: string, volume?: number, time?: number): HTMLAudioElement;
  play(url: string, volume?: number, time?: number): Promise<void>;
  pause(): void;
  setVol(volume: number): void;
  seek(time: number): void;
  getAudio(): HTMLAudioElement | null;
  getVolume(): number;
  isPlaying(): boolean;
}

const playlist = ref<Track[]>([]);
const index = ref(0);
const playing = ref(false);
const loading = ref(true);
const switching = ref(false);
const seeking = ref(false);
const error = ref('');
const loadError = ref('');
const currentTime = ref(0);
const duration = ref(0);
const lyricLines = ref<{ time: number; text: string }[]>([]);
const currentLine = ref('');
const volume = ref(0.7);
const showList = ref(false);
const loggedIn = ref(false);
let tickTimer: ReturnType<typeof setInterval> | null = null;
let userId: number | null = null;

const current = computed(() => playlist.value[index.value] || { title: '', artist: '', url: '' });
const progress = computed(() => duration.value > 0 ? (currentTime.value / duration.value) * 100 : 0);
const engine = () => (window as any).__m as GlobalAudio | undefined;
const stateKey = computed(() => userId ? `music-player:${userId}` : '');

function formatTime(s: number) { const m = Math.floor(s / 60), sec = Math.floor(s % 60); return `${m}:${String(sec).padStart(2, '0')}`; }

function parseLRC(lrc: string) {
  const lines: { time: number; text: string }[] = [];
  const regex = /\[(\d{2}):(\d{2})(?:\.(\d{2,3}))?\]/g;
  for (const raw of lrc.split('\n')) {
    const matches = [...raw.matchAll(regex)];
    const text = raw.replace(regex, '').trim();
    for (const m of matches) {
      lines.push({ time: parseInt(m[1]) * 60 + parseInt(m[2]) + (m[3] ? parseInt(m[3].padEnd(3, '0')) / 1000 : 0), text });
    }
    if (matches.length === 0 && raw.trim()) lines.push({ time: 9999, text: raw.trim() });
  }
  return lines.sort((a, b) => a.time - b.time);
}

function updateLyrics(time: number) {
  let text = '';
  for (const line of lyricLines.value) {
    if (line.time > time) break;
    text = line.text;
  }
  currentLine.value = text;
}

function persistState() {
  if (!stateKey.value || !current.value.url) return;
  const saved: SavedState = {
    url: current.value.url,
    currentTime: currentTime.value || 0,
    volume: volume.value,
  };
  try { localStorage.setItem(stateKey.value, JSON.stringify(saved)); } catch { /* storage may be unavailable */ }
}

function restorePlaybackState() {
  const audio = engine()?.getAudio();
  if (audio) {
    const idx = playlist.value.findIndex(track => audio.src.includes(track.url));
    if (idx >= 0) {
      index.value = idx;
      if (!seeking.value) currentTime.value = audio.currentTime || 0;
      duration.value = audio.duration || 0;
      playing.value = !audio.paused;
      volume.value = audio.volume;
      loadLyrics();
      updateLyrics(currentTime.value);
      return;
    }
    audio.pause();
    playing.value = false;
  }

  if (!stateKey.value) return;
  try {
    const raw = localStorage.getItem(stateKey.value);
    if (!raw) return;
    const saved = JSON.parse(raw) as SavedState;
    const idx = playlist.value.findIndex(track => track.url === saved.url);
    if (idx < 0) return;
    index.value = idx;
    currentTime.value = Number.isFinite(saved.currentTime) ? saved.currentTime : 0;
    volume.value = Number.isFinite(saved.volume) ? saved.volume : 0.7;
    loadLyrics();
    engine()?.load(current.value.url, volume.value, currentTime.value);
    updateLyrics(currentTime.value);
  } catch { /* ignore malformed local state */ }
}

function loadLyrics() {
  lyricLines.value = current.value.lyrics ? parseLRC(current.value.lyrics) : [];
  currentLine.value = '';
  updateLyrics(currentTime.value);
}

async function loadPlaylist() {
  loading.value = true;
  error.value = '';
  loadError.value = '';
  const token = getToken();
  const user = getUser();
  loggedIn.value = !!token && !!user;
  userId = user?.id ?? null;
  if (!loggedIn.value) {
    playlist.value = [];
    loading.value = false;
    return;
  }

  try {
    const response = await fetch('/api/music/list', { headers: { token } });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || payload.code !== '200') {
      throw new Error(payload.detail || payload.msg || '歌单加载失败');
    }
    playlist.value = payload.data || [];
    restorePlaybackState();
  } catch (cause) {
    playlist.value = [];
    loadError.value = cause instanceof Error ? cause.message : '歌单加载失败';
  } finally {
    loading.value = false;
  }
}

function handleAudioEnded() {
  if (playlist.value.length < 2) {
    playing.value = false;
    currentTime.value = 0;
    engine()?.seek(0);
    persistState();
    return;
  }
  changeTrack((index.value + 1) % playlist.value.length, true);
}

function handleAudioError(event: Event) {
  const detail = (event as CustomEvent<{ message?: string }>).detail;
  error.value = detail?.message || '音频播放失败';
  playing.value = false;
}

onMounted(async () => {
  await loadPlaylist();
  tickTimer = setInterval(() => {
    const audio = engine()?.getAudio();
    if (audio) {
      currentTime.value = audio.currentTime || 0;
      duration.value = Number.isFinite(audio.duration) ? audio.duration : 0;
      playing.value = !audio.paused;
      updateLyrics(currentTime.value);
      if (!audio.paused) persistState();
    }
  }, 500);
  window.addEventListener('music:ended', handleAudioEnded);
  window.addEventListener('music:error', handleAudioError);
});

onUnmounted(() => {
  if (tickTimer) clearInterval(tickTimer);
  persistState();
  window.removeEventListener('music:ended', handleAudioEnded);
  window.removeEventListener('music:error', handleAudioError);
});

async function togglePlay() {
  const audioEngine = engine();
  if (!audioEngine || !current.value.url) return;
  const isPlaying = audioEngine.isPlaying();
  error.value = '';
  if (isPlaying) {
    audioEngine.pause();
    playing.value = false;
    persistState();
  } else {
    try {
      await audioEngine.play(current.value.url, volume.value, currentTime.value);
      playing.value = true;
    } catch {
      playing.value = false;
      error.value = '播放失败，请检查音频格式或网络';
    }
  }
}

function prev() {
  changeTrack((index.value - 1 + playlist.value.length) % playlist.value.length);
}

function next() {
  changeTrack((index.value + 1) % playlist.value.length);
}

async function changeTrack(nextIndex: number, forcePlay = false) {
  const audioEngine = engine();
  if (!audioEngine || playlist.value.length === 0) return;
  const shouldPlay = forcePlay || audioEngine.isPlaying();
  switching.value = true;
  error.value = '';
  index.value = nextIndex;
  currentTime.value = 0;
  duration.value = 0;
  loadLyrics();
  try {
    audioEngine.load(current.value.url, volume.value, 0);
    if (shouldPlay) {
      await audioEngine.play(current.value.url, volume.value, 0);
      playing.value = true;
    } else {
      playing.value = false;
    }
    persistState();
  } catch {
    playing.value = false;
    error.value = '无法播放这首歌';
  } finally {
    switching.value = false;
  }
}

function beginSeeking() {
  seeking.value = true;
  error.value = '';
}

function seekFromInput(event: Event) {
  const nextTime = Number((event.target as HTMLInputElement).value);
  if (!Number.isFinite(nextTime)) return;
  const audio = engine()?.getAudio();
  const clampedTime = Math.max(0, Math.min(duration.value || 0, nextTime));
  currentTime.value = clampedTime;
  if (audio) engine()?.seek(clampedTime);
  else engine()?.load(current.value.url, volume.value, clampedTime);
  updateLyrics(clampedTime);
}

function finishSeeking() {
  seeking.value = false;
  persistState();
}

function setVolume() {
  engine()?.setVol(volume.value);
  persistState();
}

function selectTrack(i: number) {
  showList.value = false;
  changeTrack(i, true);
}
</script>

<style scoped>
@keyframes fade-in { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
.animate-fade-in { animation: fade-in 0.4s ease; }

.progress-range {
  height: 12px;
  appearance: none;
  background: transparent;
  cursor: pointer;
}
.progress-range:disabled {
  cursor: not-allowed;
}
.progress-range::-webkit-slider-runnable-track {
  height: 4px;
  border-radius: 9999px;
  background: linear-gradient(
    to right,
    #5b7bff 0,
    #5b7bff var(--music-progress),
    #e5e7eb var(--music-progress),
    #e5e7eb 100%
  );
}
.progress-range::-moz-range-track {
  height: 4px;
  border-radius: 9999px;
  background: #e5e7eb;
}
.progress-range::-moz-range-progress {
  height: 4px;
  border-radius: 9999px;
  background: #5b7bff;
}
.progress-range::-webkit-slider-thumb {
  width: 10px;
  height: 10px;
  margin-top: -3px;
  appearance: none;
  border-radius: 9999px;
  background: #5b7bff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}
.progress-range::-moz-range-thumb {
  width: 10px;
  height: 10px;
  border: 0;
  border-radius: 9999px;
  background: #5b7bff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}
.progress-range:focus-visible {
  outline: 2px solid #5b7bff;
  outline-offset: 3px;
  border-radius: 9999px;
}
</style>
