# Quick Start Guide - Stewart Platform Visualizer Electron App

## First Time Setup

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Choose Your Platform**

   ### Option A: Run as Desktop App (Recommended)
   
   ```bash
   npm run electron-dev
   ```
   
   This will:
   - Start the React development server
   - Launch the Electron desktop app
   - Enable hot-reloading for development
   
   **Note:** If you see "Something is already running on port 3000", stop any other React apps first.

   ### Option B: Run as Web App
   
   ```bash
   npm start
   ```
   
   Then open http://localhost:3000 in your browser.

## Building Desktop Executables

### For macOS (creates .dmg and .zip)
```bash
npm run electron-build-mac
```

### For Windows (creates installer and portable .exe)
```bash
npm run electron-build-win
```

### For Linux (creates AppImage and .deb)
```bash
npm run electron-build-linux
```

**Output:** All builds are saved in the `dist/` folder.

## Troubleshooting

### Port 3000 Already in Use

If you see this error:
```
Something is already running on port 3000
```

**Solution:**
1. Stop any other React apps running on port 3000
2. Or kill the process:
   ```bash
   # On macOS/Linux
   lsof -ti:3000 | xargs kill -9
   
   # On Windows
   netstat -ano | findstr :3000
   taskkill /PID <PID> /F
   ```

### Electron Won't Start

1. Make sure dependencies are installed: `npm install`
2. Try building first: `npm run build`
3. Then run: `npm run electron`

### Build Fails

- **Update Node.js:** Ensure you have Node.js 16 or higher
- **Clear cache:** Delete `node_modules` and `package-lock.json`, then run `npm install`
- **Check logs:** Look for specific error messages in the terminal

## Features Overview

Once the app is running, you can:

1. **Select Configuration:** Choose from 7 different Stewart platform configurations (8-8, 6-6, 6-3-redundant, 6-3-asymmetric, 6-3, 4-4, 3-3)

2. **Adjust Geometry:** Configure base radius, platform radius, and nominal leg length

3. **Control Pose:** Use sliders to adjust X, Y, Z position and Roll, Pitch, Yaw orientation

4. **Animate:** Click "Animate" to see the platform move automatically

5. **Monitor Legs:** View real-time leg lengths and extensions

6. **Run Tests:** Check the self-tests panel to verify calculations

## Next Steps

- Read [ELECTRON.md](ELECTRON.md) for detailed Electron configuration
- Read [README.md](README.md) for full feature documentation
- Customize the app icon in the `public/` folder
- Modify `electron.js` to change window settings

## Distribution

After building, share the executable from the `dist/` folder:

- **macOS users:** Send the `.dmg` file
- **Windows users:** Send the installer `.exe`
- **Linux users:** Send the `.AppImage` or `.deb` file

No installation required for portable versions!
