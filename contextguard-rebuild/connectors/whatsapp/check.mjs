// Import check only: never creates a socket or contacts WhatsApp.
try {
  await import('baileys'); await import('qrcode');
  console.log('Baileys and QR runtime installed; account pairing is not verified.');
} catch {
  console.error('WhatsApp runtime missing or incompatible. Run setup-whatsapp.bat.');
  process.exitCode=1;
}
