const expressApp = require('express');
const path = require('path');
const app = expressApp();
const PORT = process.env.PORT || 3000;

app.use(expressApp.static(path.join(__dirname)));

// ضمان إعادة توجيه أي مسار لملف الـ index إذا لزم الأمر
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log("Server running on port " + PORT);
});