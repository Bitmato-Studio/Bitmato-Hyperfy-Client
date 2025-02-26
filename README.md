

# **Hyperfy Electron Base**
An **Electron starter project** built for [Hyperfy](https://hyperfy.io/) with **network request caching** and **configurable settings**. It also includes **a TUI (Terminal UI) and a GUI (Graphical UI) for easy project management**, allowing users to **clone** and **build** projects interactively.

---

## **Features**

### 🚀 **Electron-Based Hyperfy App**
- Loads **Hyperfy** content from `remoteUrl` (default: `https://hyperfy.bitmato.dev`).
- Supports **network caching** to reduce bandwidth and improve load times.
- Provides **configurable settings** via `settings.json` (customizable window size, cache duration, developer mode, etc.).

### 🖥️ **Graphical User Interface (GUI)**
- A **Tkinter-based GUI** that allows users to:
  - **Clone** the Electron base project into a new directory.
  - **Customize settings** before the project is created.
  - **Build the project** into a distributable app for different OS platforms.
- Features **real-time logging** for `npm install` and `electron-builder` processes.

### 📟 **Terminal User Interface (TUI)**
- A **Rich-based TUI** that provides:
  - **Interactive prompts** for cloning and building projects.
  - **A streamlined CLI experience** for managing Hyperfy Electron apps.
  - **Real-time feedback** on operations like `npm install` and `electron-builder` builds.

### ⚡ **Network Request Caching**
- Stores and serves assets from a **cache directory** to improve performance.
- Cache automatically expires after a configurable time (`cacheExpirationHours`).
- CLI option `--clear-cache` allows manual cache clearing.

### 🔧 **Developer Features**
- Toggle **Developer Mode** with `--enable-dev` or via `settings.json`.
- Open **DevTools** when enabled.
- Run **npm install & build** automatically after cloning.

---

### **3️⃣ Use the GUI for Cloning & Building**
```bash
python gui.py
```
**Features in the GUI:**
- **Clone Electron projects** with customized settings.
- **Modify and save settings.json** before cloning.
- **Build Electron projects** for different OS & architectures.

### **4️⃣ Use the TUI for Cloning & Building**
```bash
python tui.py
```
**Features in the TUI:**
- **Simple keyboard-driven interface** to select options.
- **Step-by-step process** to configure and build Electron apps.
- **Real-time command output** for cloning and building.

---

## **Configuration - `settings.json`**
This file controls how the **Electron app** behaves.

```jsonc
{
  "appName": "MyElectronApp",
  "remoteUrl": "https://hyperfy.bitmato.dev",
  "windowSize": { "width": 1024, "height": 768 },
  "cacheExpirationHours": 24,
  "isDeveloper": false,
  "startMaximized": false,
  "alwaysOnTop": false
}
```
### **Notable Settings**
- **`appName`** – Sets the Electron window title.
- **`remoteUrl`** – Defines the Hyperfy content source.
- **`cacheExpirationHours`** – Determines cache validity duration.
- **`isDeveloper`** – Enables **DevTools** and a developer-friendly UI.

---

## **Building the App**
Use **the GUI or TUI** to build the project

This packages the Electron app into a **distributable executable**.

---

## **How Caching Works**
- **First-time requests** are stored in `cache/`.
- **Subsequent loads** fetch from the cache **if still valid**.
- Cache expires based on `cacheExpirationHours` (default: 24h).
- **Manually clear cache** using `--clear-cache`.

## **License**
[GPL V3 License](https://www.gnu.org/licenses/gpl-3.0.en.html)

---
