const express = require('path'); // عذراً، سنستخدم express بالشكل الصحيح
const expressApp = require('express');
const path = require('path');

const app = expressApp();
const PORT = process.env.PORT || 3000;

// قراءة الملفات الثابتة واللعبة مباشرة
app.use(expressApp.static(path.join(__dirname)));

// توجيه أي مسار لملف الـ index الأصلي
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
    console.log("Server is running on port " + PORT);
});