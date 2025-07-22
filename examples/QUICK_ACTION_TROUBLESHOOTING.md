# macOS Quick Action Troubleshooting Guide

## Issue: Quick Action not appearing in Finder context menus

### Files Investigated
- `examples/Clean with cattywampus.workflow/` - Example Quick Action structure
- `templates/macos/info.plist.template` - Service metadata template
- `templates/macos/document.wflow.template` - Workflow definition template

## Issues Found and Fixed

### 1. UTI (Uniform Type Identifier) Declarations
**Problem**: Limited file type support in NSSendFileTypes
**Original UTIs**:
- `NSFilenamesPboardType`
- `public.item`
- `public.movie`
- `public.video`

**Enhanced UTIs** (now includes):
- `public.audiovisual-content` - Broader video/audio content category
- `public.mpeg-4` - Specific MP4 file support
- `org.matroska.mkv` - Specific MKV file support

### 2. Service Port Name
**Problem**: NSPortName was not sufficiently unique
**Fixed**: Changed from `CleanWithcattywampus` to `CleanWithcattywampusService`

### 3. Workflow Structure Verification
**Confirmed correct**:
- Bundle structure: `.workflow/Contents/`
- Required files: `info.plist` and `document.wflow`
- File permissions: Directories executable, files readable
- Workflow metadata: Properly configured for Finder integration

## Potential Remaining Issues

### 1. macOS Version-Specific Behavior
- **Sequoia/Sonoma**: Quick Actions may appear in submenu rather than main context menu
- **User must enable**: Quick Actions must be manually enabled in System Settings

### 2. File Type Recognition
- MKV files may not be properly recognized by macOS system UTI database
- Some video formats require third-party applications to register proper UTIs

### 3. System Settings Configuration
**macOS 13+ (Ventura/Sonoma/Sequoia)**:
```
System Settings > General > Login Items & Extensions > Extensions > Finder (click ⓘ)
```
Or right-click any file/folder > Quick Actions > Customize...

**macOS 12 and earlier**:
```
System Preferences > Extensions > Finder Extensions
```

## Testing Steps

1. **Install the Quick Action**:
   ```bash
   ./install
   ```

2. **Enable in System Settings**:
   Follow the version-specific instructions above

3. **Test on different file types**:
   - Try MP4 files (should work with `public.mpeg-4`)
   - Try MKV files (may need system UTI registration)
   - Try folders (should work with `public.item`)

4. **Check Quick Actions submenu**:
   Right-click a video file and look for "Quick Actions" submenu

## Additional Troubleshooting

### Reset Quick Actions
```bash
# Reset Launch Services database (requires admin)
sudo /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -kill -r -domain local -domain system -domain user
```

### Check UTI Registration
If MKV files still don't work, the system may not recognize the UTI `org.matroska.mkv`. Consider creating a minimal application bundle that declares this UTI.

### Alternative Solutions
- Use broader UTI like `public.item` for all files/folders
- Create separate Quick Actions for different file types
- Use Automator's "receives files or folders" option

## File Structure Reference
```
Clean with cattywampus.workflow/
└── Contents/
    ├── info.plist          # Service metadata and UTI declarations
    └── document.wflow      # Workflow definition and shell script
```

## Key Properties Verified
- `workflowTypeIdentifier`: `com.apple.Automator.servicesMenu`
- `inputTypeIdentifier`: `com.apple.Automator.fileSystemObject`  
- `serviceInputTypeIdentifier`: `com.apple.Automator.fileSystemObject`
- `applicationBundleID`: `com.apple.finder`
- `NSRequiredContext`: Finder-specific context