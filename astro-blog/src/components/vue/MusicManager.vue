<template>
  <div>
    <div v-if="!loggedIn" class="text-center py-16 glass-card">
      <p class="text-gray-500 mb-4">登录后管理你的私人歌单</p>
      <a href="/auth/login" class="px-6 py-2.5 rounded-button bg-brand-600 text-white font-medium hover:bg-brand-700 transition-colors inline-block no-underline">去登录</a>
    </div>

    <div v-else>
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="text-lg font-semibold text-gray-700">{{ title }}</h2>
          <p class="text-xs text-gray-400 mt-1">歌曲只对当前账号可见</p>
        </div>
        <label class="px-4 py-2 bg-gray-900 text-white text-sm rounded-lg hover:bg-gray-800 transition-colors cursor-pointer">
          {{ uploading ? '上传中...' : '+ 上传音乐' }}
          <input type="file" accept="audio/*" class="hidden" :disabled="uploading" @change="upload" />
        </label>
      </div>

      <div v-if="message" class="mb-4 p-3 rounded-lg text-sm bg-green-50 text-green-600">{{ message }}</div>
      <div v-if="error" class="mb-4 p-3 rounded-lg text-sm bg-red-50 text-red-600">{{ error }}</div>
      <div class="bg-white/80 backdrop-blur rounded-xl shadow-sm overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-gray-50/80 text-gray-500"><tr>
            <th class="text-left px-4 py-3 font-medium">标题</th><th class="text-left px-4 py-3 font-medium w-28">艺术家</th><th class="text-left px-4 py-3 font-medium w-16">排序</th><th class="text-right px-4 py-3 font-medium w-40">操作</th>
          </tr></thead>
          <tbody class="divide-y">
            <tr v-for="m in items" :key="m.id" class="hover:bg-gray-50/50">
              <td class="px-4 py-3 text-gray-800">{{ m.title }}</td>
              <td class="px-4 py-3 text-gray-500">{{ m.artist }}</td>
              <td class="px-4 py-3 text-gray-500">{{ m.sort_order }}</td>
              <td class="px-4 py-3 text-right">
                <button @click="openLyrics(m)" class="text-xs text-brand-600 hover:text-brand-700 mr-2">歌词</button>
                <button @click="remove(m.id)" class="text-xs text-red-500 hover:text-red-600">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="items.length === 0" class="text-center py-12 text-gray-400 text-sm">暂无音乐，上传一首吧</div>
      </div>

      <!-- Lyrics Dialog -->
      <div v-if="lyricsShow" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30" @click.self="lyricsShow=false">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6">
          <h2 class="text-lg font-bold mb-4">{{ lyricsTarget?.title }} - 歌词</h2>
          <textarea v-model="lyricsText" placeholder="粘贴 LRC 歌词或纯文本..." rows="12" class="w-full px-4 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500 font-mono" />
          <div class="flex justify-end gap-2 mt-4">
            <button @click="lyricsShow=false" class="px-4 py-2 border rounded-lg text-sm text-gray-600">取消</button>
            <button @click="saveLyrics" class="px-4 py-2 bg-gray-900 text-white text-sm rounded-lg">保存</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getToken } from '@lib/auth';

const props = withDefaults(defineProps<{ title?: string }>(), { title: '音乐管理' });
const MAX_MUSIC_BYTES = 100 * 1024 * 1024;
const items = ref<any[]>([]);
const lyricsShow = ref(false);
const lyricsTarget = ref<any>(null);
const lyricsText = ref('');
const uploading = ref(false);
const message = ref('');
const error = ref('');
const loggedIn = ref(!!getToken());

async function api(url: string, options?: RequestInit) {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options?.headers,
      token: getToken() || '',
      'Content-Type': 'application/json',
    },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload.code !== '200') {
    throw new Error(payload.detail || payload.msg || '请求失败');
  }
  return payload;
}

async function refresh() {
  const result = await api('/api/music/list');
  items.value = result.data || [];
}

onMounted(async () => {
  if (!loggedIn.value) return;
  try {
    await refresh();
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '歌单加载失败';
  }
});

async function upload(e: Event) {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  message.value = '';
  error.value = '';
  if (file.size > MAX_MUSIC_BYTES) {
    error.value = '音频文件不能超过 100 MB';
    input.value = '';
    return;
  }
  const raw = file.name.replace(/\.[^.]+$/, '');
  let title = raw, artist = '';
  if (raw.includes(' - ')) {
    const parts = raw.split(' - ');
    artist = parts[0].trim();
    title = parts.slice(1).join(' - ').trim();
  }
  const fd = new FormData(); fd.append('file', file); fd.append('title', title); fd.append('artist', artist);
  uploading.value = true;
  try {
    const response = await fetch('/api/music/upload', {
      method: 'POST',
      headers: { token: getToken() || '' },
      body: fd,
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || payload.code !== '200') {
      throw new Error(payload.detail || payload.msg || '上传失败');
    }
    message.value = '上传成功';
    await refresh();
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '上传失败';
  } finally {
    uploading.value = false;
    input.value = '';
  }
}

function openLyrics(m: any) { lyricsTarget.value = m; lyricsText.value = m.lyrics || ''; lyricsShow.value = true; }
async function saveLyrics() {
  if (!lyricsTarget.value) return;
  message.value = '';
  error.value = '';
  try {
    await api(`/api/music/${lyricsTarget.value.id}`, { method: 'PUT', body: JSON.stringify({ lyrics: lyricsText.value }) });
    lyricsShow.value = false;
    await refresh();
    message.value = '歌词已保存';
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '保存歌词失败';
  }
}
async function remove(id: number) {
  if (!confirm('确定删除？')) return;
  message.value = '';
  error.value = '';
  try {
    await api(`/api/music/${id}`, { method: 'DELETE' });
    await refresh();
    message.value = '已删除';
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '删除失败';
  }
}
</script>
