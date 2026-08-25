const expressApp = require('express'); const path = require('path'); const https = require('https');
const app = expressApp(); const PORT = process.env.PORT || 3000;
// توكن البوت الخاص بك const TELEGRAM_BOT_TOKEN = '8462300261:AAGsdA4BmZNkyytXjqPlvTS2B7g9RO5vhWc'; // رابط موقعك على Railway const WEB_APP_URL = 'https://poice-production.up.railway.app/';
app.use(expressApp.static(path.join(__dirname)));
// نقطة استقبال تحديثات تليغرام (Webhook) app.use(expressApp.json());
app.post(/bot${TELEGRAM_BOT_TOKEN}, (req, res) => { const update = req.body; if (update.message && update.message.text) { const chatId = update.message.chat.id; const text = update.message.text;
    if (text === '/start') {
        sendTelegramMessage(chatId, 'أهلاً بك في اللعبة! اضغط على الزر أدناه للبدء:', {
            inline_keyboard: [
                [{ text: '🎮 العب الآن', web_app: { url: WEB_APP_URL } }]
            ]
        });
    }
}
res.sendStatus(200);
});
function sendTelegramMessage(chatId, text, replyMarkup) { const data = JSON.stringify({ chat_id: chatId, text: text, reply_markup: replyMarkup });
const options = {
    hostname: 'api.telegram.org',
    path: `/bot${TELEGRAM_BOT_TOKEN}/sendMessage`,
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data)
    }
};

const req = https.request(options, (res) => {
    res.on('data', (d) => { process.stdout.write(d); });
});

req.on('error', (error) => {
    console.error(error);
});

req.write(data);
req.end();
}
app.listen(PORT, '0.0.0.0', () => { console.log("Server and Bot are running on port " + PORT);
// ربط الـ Webhook تلقائياً مع تليغرام عند تشغيل السيرفر
const webhookUrl = https://poice-production.up.railway.app/bot${TELEGRAM_BOT_TOKEN};
https.get(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook?url=${encodeURIComponent(webhookUrl)}`, (res) => {
    console.log("Webhook set status:", res.statusCode);
});
});