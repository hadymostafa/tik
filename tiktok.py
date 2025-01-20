
import logging
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
import os

# إعداد التوكن الخاص بالبوت
TOKEN = '7754711488:AAG4rwKxBWFBvetZLolyys_K95tSAQiaXtU'

# إعداد تسجيل الأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ذاكرة مؤقتة لتخزين الروابط
url_cache = {}

# دالة لتحميل الفيديو أو الصوت من تيك توك باستخدام yt-dlp
def download_tiktok(url, quality, audio_only):
    ydl_opts = {
        'format': 'bestaudio/best' if audio_only else quality,
        'noplaylist': True,
        'outtmpl': 'downloads/%(title)s.%(ext)s',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        logging.error(f"Error while downloading: {e}")
        return None

# دالة لبدء المحادثة
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text('مرحبًا! أرسل لي رابط فيديو من تيك توك لتحميله بدون علامة مائية.')

# دالة لمعالجة الرسائل النصية (روابط الفيديو)
async def handle_message(update: Update, context: CallbackContext):
    url = update.message.text.strip()
    if 'tiktok.com' in url:
        # إنشاء معرف فريد للرابط
        unique_id = str(len(url_cache))
        url_cache[unique_id] = url

        keyboard = [
            [InlineKeyboardButton("جودة عالية (1080p)", callback_data=f"{unique_id}|high")],
            [InlineKeyboardButton("جودة متوسطة (720p)", callback_data=f"{unique_id}|medium")],
            [InlineKeyboardButton("صوت فقط (MP3)", callback_data=f"{unique_id}|audio")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('اختر الجودة المطلوبة:', reply_markup=reply_markup)
    else:
        await update.message.reply_text('يرجى إرسال رابط صحيح من تيك توك.')

# دالة لمعالجة الرد على الأزرار
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data.split('|')
    unique_id, quality = data[0], data[1]

    url = url_cache.get(unique_id)
    if not url:
        await query.edit_message_text('حدث خطأ. الرابط غير موجود.')
        return

    await query.edit_message_text('جاري التحميل...')

    if quality == "high":
        video_path = download_tiktok(url, "best[height<=1080]", False)
    elif quality == "medium":
        video_path = download_tiktok(url, "best[height<=720]", False)
    elif quality == "audio":
        video_path = download_tiktok(url, "bestaudio", True)
    else:
        await query.edit_message_text('حدث خطأ. يرجى المحاولة مرة أخرى.')
        return

    if video_path and os.path.exists(video_path):
        try:
            if quality == "audio":
                await context.bot.send_audio(chat_id=query.message.chat_id, audio=open(video_path, 'rb'))
            else:
                await context.bot.send_video(chat_id=query.message.chat_id, video=open(video_path, 'rb'))
            await query.edit_message_text('تم التحميل بنجاح!')
        except Exception as e:
            logging.error(f"Error while sending file: {e}")
            await query.edit_message_text('حدث خطأ أثناء إرسال الملف.')
        finally:
            os.remove(video_path)
    else:
        await query.edit_message_text('حدث خطأ أثناء التحميل. تأكد من صحة الرابط.')

# دالة رئيسية لتشغيل البوت
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))

    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    application.run_polling()

if __name__ == '__main__':
    main()

