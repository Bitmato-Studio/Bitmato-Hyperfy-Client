const { app, BrowserWindow, session, ipcMain, Tray, Menu } = require('electron');
const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');

let startTime = Date.now();

const USER_DATA = app.getPath('userData'); 

const CACHE_DIR = app.isPackaged? path.join(USER_DATA, 'cache') : path.join('./', 'cache');
const SETTINGS_FILE = app.isPackaged ? path.join(process.resourcesPath, 'settings.json') : path.join('./', 'settings.json');
console.log(CACHE_DIR, SETTINGS_FILE);

// Default settings
const defaultSettings = {
    appName: "MyElectronApp",
    remoteUrl: "https://hyperfy.bitmato.dev",
    windowSize: { width: 1024, height: 768 },
    cacheExpirationHours: 24,
    isDeveloper: false,
    startMaximized: false,
    alwaysOnTop: false,
    trayEnabled: false,
    customUserAgent: "",
    disableCache: false,
    hardwareAcceleration: true,
};

// Load settings (merge with defaults but don't overwrite)
function loadSettings() {
    console.log(fs.existsSync(SETTINGS_FILE));
    if (fs.existsSync(SETTINGS_FILE)) {
        try {
            const fileData = JSON.parse(fs.readFileSync(SETTINGS_FILE, 'utf-8'));
            return { ...defaultSettings, ...fileData };
        } catch (err) {
            console.error("Error loading settings:", err);
            return defaultSettings;
        }
    } else {
        saveSettings(defaultSettings);
        return defaultSettings;
    }
}

// Save settings
function saveSettings(updatedSettings) {
    if (app.isPackaged) { return; }
    fs.writeFileSync(SETTINGS_FILE, JSON.stringify(updatedSettings, null, 4));
}

// Load settings once
let settings = loadSettings();

// CLI parsing with yargs
const argv = yargs(hideBin(process.argv))
    .option('clear-cache', { alias: 'c', type: 'boolean', description: 'Clear the cache' })
    .option('set-cache-time', { alias: 't', type: 'number', description: 'Set cache expiration in hours' })
    .option('enable-dev', { type: 'boolean', description: 'Enable developer mode' })
    .option('disable-dev', { type: 'boolean', description: 'Disable developer mode' })
    .option('disable-cache', { type: 'boolean', description: 'Disable caching' })
    .help()
    .argv;

// Handle CLI
if (argv.clearCache) {
    fs.rmSync(CACHE_DIR, { recursive: true, force: true });
    console.log("Cache cleared!");
    process.exit(0);
}
if (argv.setCacheTime) {
    settings.cacheExpirationHours = argv.setCacheTime;
    saveSettings(settings);
    console.log(`Cache expiration set to ${argv.setCacheTime} hours.`);
    process.exit(0);
}
if (argv.enableDev) settings.isDeveloper = true;
if (argv.disableDev) settings.isDeveloper = false;

// Persist any CLI changes
saveSettings(settings);

//////////////////////
// Wait until ready //
//////////////////////

app.whenReady().then(() => {

    // 2) Ensure userData-based directories exist
    if (!fs.existsSync(CACHE_DIR)) {
        fs.mkdirSync(CACHE_DIR, { recursive: true });
        console.log(`Created cache directory: ${CACHE_DIR}`);
    }

    if (!settings.hardwareAcceleration) {
        app.disableHardwareAcceleration();
    }

    createMainWindow();

    if (settings.trayEnabled) {
        createTray();
    }

    // Network caching
    session.defaultSession.webRequest.onBeforeRequest((details, callback) => {
        if (!details.url.startsWith('http') || settings.disableCache) {
            callback({ cancel: false });
            return;
        }

        const requestUrl = new URL(details.url);
        const fileName = encodeURIComponent(requestUrl.pathname + requestUrl.search);
        const filePath = path.join(CACHE_DIR, fileName);
        const metaFilePath = filePath + ".meta";

        if (fs.existsSync(filePath) && fs.existsSync(metaFilePath)) {
            const fileStat = fs.statSync(metaFilePath);
            try {
                // Check expiration
                if (Date.now() - fileStat.mtimeMs < settings.cacheExpirationHours * 3600000) {
                    console.log(`Serving from cache: ${details.url}`);
                    callback({ cancel: false });
                    return;
                } else {
                    fs.unlinkSync(filePath);
                    fs.unlinkSync(metaFilePath);
                }
            } catch (e) {
                console.log(`Error reading from cache: ${e}`);
            }        
        }

        console.log(`Downloading and caching: ${details.url}`);
        const protocol = details.url.startsWith('https') ? https : http;
        protocol.get(details.url, (response) => {
            if (response.statusCode !== 200) return;
            const fileStream = fs.createWriteStream(filePath);
            response.pipe(fileStream);
            fileStream.on('finish', () => {
                fileStream.close();
                fs.writeFileSync(metaFilePath, Date.now().toString());
            });
        }).on('error', (err) => {
            console.error(`Download error: ${details.url}`, err);
        });

        callback({ cancel: false });
    });

    let appReadyTime = Date.now(); 
    console.log(`App ready in ${appReadyTime - startTime}ms`);
});

// Create main application window
function createMainWindow() {
    const windowStartTime = Date.now(); 

    // Use your appName, etc. from settings
    mainWindow = new BrowserWindow({
        width: settings.windowSize.width,
        height: settings.windowSize.height,
        title: settings.appName,
        autoHideMenuBar: !settings.isDeveloper,
        alwaysOnTop: settings.alwaysOnTop,
        frame: true,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            devTools: settings.isDeveloper,
            // Preload script still references __dirname, but just for code, not for writing.
            preload: path.join(__dirname, 'preload.js')
        }
    });

    if (settings.startMaximized) {
        mainWindow.maximize();
    }

    if (settings.isDeveloper) {
        mainWindow.webContents.openDevTools({ mode: 'detach' });
    }

    if (settings.customUserAgent) {
        mainWindow.webContents.setUserAgent(settings.customUserAgent);
    }

    mainWindow.loadURL(settings.remoteUrl);

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
    mainWindow.webContents.once('did-finish-load', () => {
        const fullLoadTime = Date.now();
        console.log(`Window created in ${fullLoadTime - windowStartTime}ms`);
        console.log(`Total time from start to full load: ${fullLoadTime - startTime}ms`);
        mainWindow.setTitle(settings.appName);
    });
}

// Create system tray icon
function createTray() {
    // If your icon is inside asar, you might do:
    // const iconPath = path.join(process.resourcesPath, 'icon.png');
    // otherwise, if you have an external path, that's fine.
    const iconPath = path.join(process.resourcesPath, 'icon.png');

    tray = new Tray(iconPath);
    const contextMenu = Menu.buildFromTemplate([
        { label: 'Show', click: () => mainWindow.show() },
        { label: 'Quit', click: () => app.quit() }
    ]);
    tray.setToolTip(settings.appName);
    tray.setContextMenu(contextMenu);
}

// IPC Handlers
ipcMain.on('clear-cache', () => fs.rmSync(CACHE_DIR, { recursive: true, force: true }));
ipcMain.on('set-cache-time', (_, hours) => {
    settings.cacheExpirationHours = parseInt(hours, 10);
    saveSettings(settings);
});
ipcMain.handle('get-settings', async () => settings);
ipcMain.on('enable-developer-mode', () => {
    settings.isDeveloper = true;
    saveSettings(settings);
});
ipcMain.on('disable-developer-mode', () => {
    settings.isDeveloper = false;
    saveSettings(settings);
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});
