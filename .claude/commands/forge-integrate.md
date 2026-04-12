# VoiceForge / VisionAudioForge Integration Command

## Integration Repos
- VoiceForge: navigreen311/voiceforge
- VisionAudioForge: navigreen311/visionaudioforge

## VoiceForge Pattern
- Check VoiceForgeService.isAvailable() before any call
- Graceful degradation: if offline, hide UI element (never show error)

## VisionAudioForge Pattern
- CRITICAL: Always check IntegrityMode before screen capture
- Screen capture: Offline Lab / Training ONLY
- Replay analysis: Always allowed (post-game)

## Integration Task
$ARGUMENTS
