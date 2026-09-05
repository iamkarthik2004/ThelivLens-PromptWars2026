export const evidence = [
  { title: 'Face & Skin Analysis', text: 'Unusual texture consistency and facial-region artifacts detected.', severity: 'High', confidence: 89, icon: 'ScanFace' },
  { title: 'Lighting Analysis', text: 'Light direction differs slightly between the subject and background.', severity: 'Medium', confidence: 76, icon: 'SunMedium' },
  { title: 'Pixel Analysis', text: 'High-frequency patterns differ from typical camera-generated imagery.', severity: 'High', confidence: 91, icon: 'ScanSearch' },
  { title: 'Metadata', text: 'Original EXIF metadata is missing from the submitted file.', severity: 'Medium', confidence: 84, icon: 'FileSearch' },
  { title: 'Model Consensus', text: 'Multiple independent signals point to synthetic-generation traits.', severity: 'High', confidence: 87, icon: 'BrainCircuit' }
];

export const recentAnalyses = [
  { name: 'portrait_01.jpg', type: 'image', result: 'Likely AI', confidence: 87, time: 'Just now', tone: 'warning' },
  { name: 'protest_video.mp4', type: 'video', result: 'Authentic', confidence: 82, time: '2 hours ago', tone: 'success' },
  { name: 'speech_clip.mp3', type: 'audio', result: 'Manipulated', confidence: 79, time: 'Yesterday', tone: 'danger' },
  { name: 'mountain_view.png', type: 'image', result: 'Inconclusive', confidence: 55, time: 'Sep 03', tone: 'neutral' }
];

export const sourceEvents = [
  { date: 'Unknown', source: 'Original upload', platform: 'Unverified', caption: 'Earliest available instance could not be independently confirmed.', status: 'Unverified' },
  { date: 'Aug 28, 2026', source: 'Social repost', platform: 'Social network', caption: 'Caption changed to imply a recent event.', status: 'Review' },
  { date: 'Aug 30, 2026', source: 'Article embed', platform: 'News website', caption: 'Published without an original-source attribution.', status: 'Review' },
  { date: 'Sep 02, 2026', source: 'Viral post', platform: 'Social network', caption: 'Shared widely with materially different context.', status: 'Warning' }
];
