# Stewart Platform Visualizer - Electron App

This document describes how to run and build the Stewart Platform Visualizer as a desktop application using Electron.

## Development

### Run in Development Mode

To run the app in development mode with hot-reloading:

```bash
npm run electron-dev
```

This will:
1. Start the React development server
2. Wait for it to be ready
3. Launch the Electron app

### Run Production Build Locally

To test the production build locally:

```bash
npm run build
npm run electron
```

## Building Executables

### Build for macOS

```bash
npm run electron-build-mac
```

This creates:
- `.dmg` installer
- `.zip` archive

Output location: `dist/`

### Build for Windows

```bash
npm run electron-build-win
```

This creates:
- NSIS installer (`.exe`)
- Portable executable

Output location: `dist/`

### Build for Linux

```bash
npm run electron-build-linux
```

This creates:
- AppImage
- Debian package (`.deb`)

Output location: `dist/`

### Build for All Platforms

```bash
npm run electron-build
```

**Note:** Building for Windows on macOS/Linux requires Wine. Building for macOS on Windows/Linux requires a macOS machine or CI service.

## Application Features

The Electron app includes:

- **Native Window**: Runs as a native desktop application
- **No Browser Chrome**: Clean interface without browser UI
- **Offline Support**: Works without internet connection
- **Better Performance**: Direct access to system resources
- **Menu Bar**: Hidden by default (can be customized in `electron.js`)
- **DevTools**: Available in development mode

## Configuration

### Window Settings

Edit `electron.js` to customize:
- Window size (default: 1400x900)
- Window title
- DevTools behavior
- Menu bar visibility

### Build Settings

Edit `package.json` under the `"build"` section to customize:
- App ID and product name
- Icons for different platforms
- Build targets
- File inclusion/exclusion

## Icons

To customize the app icon, replace the following files in the `public/` directory:

- **macOS**: `icon.icns` (512x512 or larger)
- **Windows**: `icon.ico` (256x256 or larger)
- **Linux**: `icon.png` (512x512 or larger)

You can generate these from a single PNG using tools like:
- [electron-icon-builder](https://www.npmjs.com/package/electron-icon-builder)
- [icon-gen](https://www.npmjs.com/package/icon-gen)

## Troubleshooting

### Port Already in Use

If port 3000 is already in use:
1. Stop the process using port 3000
2. Or change the port in `package.json` scripts

### Build Fails

Common issues:
- **Missing dependencies**: Run `npm install`
- **Outdated Node**: Update to Node.js 16 or higher
- **Platform-specific builds**: Ensure you have the required tools for your target platform

### App Won't Start

1. Check console for errors
2. Verify `build/` directory exists and contains files
3. Try rebuilding: `npm run build`

## Distribution

After building, you can distribute the executables from the `dist/` folder:

- **macOS**: Distribute the `.dmg` file
- **Windows**: Distribute the installer `.exe` or portable `.exe`
- **Linux**: Distribute the `.AppImage` or `.deb` file

## Auto-Updates (Optional)

To add auto-update functionality:
1. Install `electron-updater`
2. Configure update server
3. Add update logic to `electron.js`

See [electron-updater documentation](https://www.electron.build/auto-update) for details.

## Security

The app is configured with:
- `nodeIntegration: true` - Allows Node.js in renderer
- `contextIsolation: false` - Simplifies React integration

For production apps handling sensitive data, consider:
- Enabling `contextIsolation`
- Using IPC for secure communication
- Implementing Content Security Policy

## Resources

- [Electron Documentation](https://www.electronjs.org/docs)
- [electron-builder Documentation](https://www.electron.build/)
- [React Three Fiber](https://docs.pmnd.rs/react-three-fiber)
