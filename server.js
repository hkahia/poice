const express = require('express'); const path = require('path'); const app = express(); const PORT = process.env.PORT || 3000;
const TELEGRAM_BOT_TOKEN = '8462300261:AAGsdA4BmZNkyytXjqPlvTS2B7g9RO5vhWc'; const WEB_APP_URL = 'https://poice-production.up.railway.app/';
app.use(express.json());
// قراءة كل الملفات الثابتة (مثل مجلد assets والصور والـ JS) app.use(express.static(path.join(__dirname)));
// استقبال رسائل البوت وتليغرام app.post(/bot${TELEGRAM_BOT_TOKEN}, (req, res) => { const update = req.body; if (update.message && update.message.text) { const chatId = update.message.chat.id; const text = update.message.text;
    if (text === '/start') {
        const https = require('https');
        const data = JSON.stringify({
            chat_id: chatId,
            text: 'أهلاً بك في اللعبة! اضغط على الزر أدناه للبدء:',
            reply_markup: {
                inline_keyboard: [
                    [{ text: '🎮 العب الآن', web_app: { url: WEB_APP_URL } }]
                ]
            }
        });

        const options = {
            hostname: 'api.telegram.org',
            path: `/bot${TELEGRAM_BOT_TOKEN}/sendMessage`,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(data)
            }
        };

        const reqTelegram = https.request(options);
        reqTelegram.on('error', (e) => console.error(e));
        reqTelegram.write(data);
        reqTelegram.end();
    }
}
res.sendStatus(200);
});
// توجيه أي مسار لملف الـ index الأصلي للعبة app.get('*', (req, res) => { res.sendFile(path.join(__dirname, 'index.html')); });
app.listen(PORT, '0.0.0.0', () => { console.log("Game Server is running on port " + PORT); });