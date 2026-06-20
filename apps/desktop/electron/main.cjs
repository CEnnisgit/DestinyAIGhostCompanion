// Electron main process: wraps the Vite-built web app as a desktop window.
const { app, BrowserWindow } = require("electron");
const path = require("path");
const fs = require("fs");

function createWindow() {
  const win = new BrowserWindow({
    width: 440,
    height: 820,
    backgroundColor: "#070b14",
    title: "Ghost Companion",
    webPreferences: { contextIsolation: true },
  });

  const devURL = process.env.VITE_DEV_SERVER_URL;
  if (devURL) {
    win.loadURL(devURL);
  } else {
    win.loadFile(path.join(__dirname, "..", "dist", "index.html"));
  }

  // Headless screenshot mode for verification: capture once loaded, then quit.
  const shot = process.env.GHOST_SHOT;
  if (shot) {
    win.webContents.once("did-finish-load", () => {
      setTimeout(async () => {
        const image = await win.webContents.capturePage();
        fs.writeFileSync(shot, image.toPNG());
        app.quit();
      }, 2500);
    });
  }

  return win;
}

app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
