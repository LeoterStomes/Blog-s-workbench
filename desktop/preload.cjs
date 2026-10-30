const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('desktop', Object.freeze({
  isElectron: true,
  platform: process.platform,
  getInfo: () => ipcRenderer.invoke('desktop:info'),
  getWorkspace: () => ipcRenderer.invoke('workspace:get'),
  chooseWorkspace: () => ipcRenderer.invoke('workspace:choose'),
  listWorkspace: (relativePath = '') => ipcRenderer.invoke('workspace:list', relativePath),
  readWorkspaceText: (relativePath) => ipcRenderer.invoke('workspace:read-text', relativePath),
  openWorkspace: () => ipcRenderer.invoke('workspace:open'),
  revealWorkspace: () => ipcRenderer.invoke('workspace:reveal'),
  openFile: (relativePath) => ipcRenderer.invoke('workspace:open-file', relativePath),
}));
