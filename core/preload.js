const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('appSettings', {
    clearCache: () => ipcRenderer.send('clear-cache'),
    setCacheTime: (hours) => ipcRenderer.send('set-cache-time', hours),
    getCacheTime: () => ipcRenderer.invoke('get-cache-time'),
    getSettings: () => ipcRenderer.invoke('get-settings')
});
