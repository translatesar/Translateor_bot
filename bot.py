import os
import urllib.request
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from googletrans import Translator
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

TOKEN = os.environ.get('BOT_TOKEN')
PORT = int(os.environ.get('PORT', 8080))

translator = Translator()

# تنظیم فونت
FONT_DIR = 'fonts'
os.makedirs(FONT_DIR, exist_ok=True)

try:
    if not os.path.exists(f'{FONT_DIR}/Vazir.ttf'):
        urllib.request.urlretrieve(
            'https://github.com/rastikerdar/vazir-font/raw/master/dist/Vazir.ttf',
            f'{FONT_DIR}/Vazir.ttf'
        )
    pdfmetrics.registerFont(TTFont('Vazir', f'{FONT_DIR}/Vazir.ttf'))
    FONT_READY = True
except:
    FONT_READY = False

class SmartTranslator:
    """مترجم هوشمند با قابلیت ترجمه روان و طبیعی"""
    
    def __init__(self):
        self.translator = Translator()
        # اصطلاحات رایج عربی به فارسی
        self.common_phrases = {
            'السلام علیکم': 'سلام علیکم',
            'وعلیکم السلام': 'و علیکم السلام',
            'بسم الله': 'به نام خدا',
            'الحمد لله': 'خدا را شکر',
            'إن شاء الله': 'ان‌شاءالله',
            'ما شاء الله': 'ماشاءالله',
            'جزاک الله خیراً': 'خداوند به شما جزای خیر دهد',
            'أهلاً وسهلاً': 'خوش آمدید',
            'صباح الخیر': 'صبح بخیر',
            'مساء الخیر': 'عصر بخیر',
            'کیف حالک': 'حال شما چطور است',
            'بخیر': 'خوبم',
            'شکراً': 'متشکرم',
            'عفواً': 'خواهش می‌کنم',
            'مع السلامة': 'به سلامت',
            'فی أمان الله': 'در پناه خدا',
        }
    
    def preprocess_arabic(self, text):
        """پیش‌پردازش متن عربی برای ترجمه بهتر"""
        # حذف حرکات (اعراب) عربی
        text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
        
        # نرمال‌سازی حروف
        text = text.replace('ة', 'ه')  # تای مأنوس به ه
        text = text.replace('ي', 'ی')  # ی عربی به فارسی
        text = text.replace('ك', 'ک')  # ک عربی به فارسی
        
        # جایگزینی اصطلاحات رایج
        for arabic, persian in self.common_phrases.items():
            text = text.replace(arabic, persian)
        
        return text
    
    def postprocess_translation(self, text, source_lang, target_lang):
        """پس‌پردازش ترجمه برای روان‌تر شدن"""
        
        if source_lang == 'ar' and target_lang == 'fa':
            # اصلاح ساختار جملات فارسی
            text = self.fix_persian_structure(text)
            
            # اصلاح نیم‌فاصله‌ها
            text = self.fix_half_spaces(text)
            
            # اصلاح علائم نگارشی
            text = self.fix_punctuation(text)
            
            # حذف کلمات تکراری
            text = self.remove_redundant_words(text)
        
        return text
    
    def fix_persian_structure(self, text):
        """اصلاح ساختار جملات فارسی"""
        # اصلاح ترتیب کلمات (عربی معمولاً فعل اول میاد)
        # مثال: "ذهب محمد إلى المدرسة" → "محمد به مدرسه رفت"
        
        # الگوهای رایج اصلاح
        patterns = [
            (r'می باشد', 'است'),
            (r'می باشند', 'هستند'),
            (r'بوده است', 'بوده'),
            (r'شده است', 'شده'),
            (r'می نماید', 'می‌کند'),
            (r'به عمل آورد', 'انجام داد'),
            (r'مورد استفاده قرار', 'استفاده'),
            (r'به منظور', 'برای'),
            (r'در خصوص', 'درباره'),
            (r'با توجه به اینکه', 'از آنجا که'),
            (r'علیرغم', 'با وجود'),
            (r'متأسفانه', 'متاسفانه'),
        ]
        
        for old, new in patterns:
            text = text.replace(old, new)
        
        return text
    
    def fix_half_spaces(self, text):
        """اصلاح نیم‌فاصله‌ها در فارسی"""
        # کلماتی که نیاز به نیم‌فاصله دارند
        patterns = [
            (r'می (\w+)', r'می‌\1'),
            (r'نمی (\w+)', r'نمی‌\1'),
            (r'(\w+)ها', r'\1‌ها'),
            (r'(\w+)تر', r'\1‌تر'),
            (r'(\w+)ترین', r'\1‌ترین'),
            (r'(\w+)گر', r'\1‌گر'),
            (r'(\w+)مند', r'\1‌مند'),
            (r'(\w+)وار', r'\1‌وار'),
        ]
        
        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text)
        
        return text
    
    def fix_punctuation(self, text):
        """اصلاح علائم نگارشی"""
        # تبدیل علائم نگارشی انگلیسی به فارسی
        text = text.replace('?', '؟')
        text = text.replace(';', '؛')
        text = text.replace(',', '،')
        
        # فاصله‌گذاری صحیح علائم نگارشی
        text = re.sub(r'\s+([،؛؟!])', r'\1', text)
        text = re.sub(r'([،؛؟!])(\S)', r'\1 \2', text)
        
        return text
    
    def remove_redundant_words(self, text):
        """حذف کلمات زائد و تکراری"""
        # حذف تکرارهای رایج
        redundancies = [
            'که که', 'و و', 'در در', 'به به', 'از از',
            'است است', 'را را', 'با با', 'تا تا'
        ]
        
        for redundant in redundancies:
            text = text.replace(redundant, redundant.split()[0])
        
        return text
    
    def translate_text(self, text, target_lang='fa'):
        """ترجمه هوشمند متن"""
        try:
            # تشخیص زبان
            detected = self.translator.detect(text[:200])
            source_lang = detected.lang
            
            # پیش‌پردازش مخصوص عربی
            if source_lang == 'ar':
                text = self.preprocess_arabic(text)
            
            # ترجمه
            if len(text) > 3000:
                # ترجمه پاراگراف به پاراگراف برای دقت بیشتر
                paragraphs = text.split('\n')
                translated_paragraphs = []
                
                for para in paragraphs:
                    if para.strip():
                        translated = self.translator.translate(
                            para, 
                            src=source_lang, 
                            dest=target_lang
                        )
                        # پس‌پردازش
                        processed = self.postprocess_translation(
                            translated.text, 
                            source_lang, 
                            target_lang
                        )
                        translated_paragraphs.append(processed)
                    else:
                        translated_paragraphs.append('')
                
                final_text = '\n'.join(translated_paragraphs)
            else:
                # ترجمه یکجا برای متون کوتاه
                translated = self.translator.translate(
                    text, 
                    src=source_lang, 
                    dest=target_lang
                )
                final_text = self.postprocess_translation(
                    translated.text, 
                    source_lang, 
                    target_lang
                )
            
            return {
                'text': final_text,
                'source_lang': source_lang,
                'target_lang': target_lang
            }
            
        except Exception as e:
            print(f"Translation error: {e}")
            return None

# ساخت نمونه از مترجم هوشمند
smart_translator = SmartTranslator()

def wrap_text(text, max_width, canvas_obj, font_name, font_size, is_rtl=False):
    """شکستن متن به خطوط"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        if canvas_obj.stringWidth(test_line, font_name, font_size) < max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(reversed(current_line) if is_rtl else current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(reversed(current_line) if is_rtl else current_line))
    
    return lines

def create_translated_pdf(output_path, translated_pages, target_lang):
    """ساخت PDF ترجمه شده با کیفیت بالا"""
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    font_name = 'Vazir' if (target_lang in ['fa', 'ar'] and FONT_READY) else 'Helvetica'
    is_rtl = target_lang in ['fa', 'ar', 'ur', 'he']
    
    for page_num, page_data in enumerate(translated_pages):
        if page_num > 0:
            c.showPage()
        
        y_position = height - 70
        
        # هدر صفحه
        c.setFillColorRGB(0.2, 0.5, 0.9)
        c.rect(0, height - 50, width, 50, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont(font_name, 14)
        header = f"📄 صفحه {page_num + 1} | ترجمه روان و طبیعی"
        if is_rtl:
            c.drawRightString(width - 30, height - 35, header)
        else:
            c.drawString(30, height - 35, header)
        
        c.setFillColorRGB(0, 0, 0)
        y_position = height - 80
        
        if page_data:
            # متن اصلی
            c.setFont(font_name, 12)
            c.setFillColorRGB(0.1, 0.1, 0.6)
            title = "📝 متن اصلی:"
            if is_rtl:
                c.drawRightString(width - 50, y_position, title)
            else:
                c.drawString(50, y_position, title)
            y_position -= 25
            
            c.setFont(font_name, 9)
            c.setFillColorRGB(0.2, 0.2, 0.2)
            lines = wrap_text(page_data['original'][:2500], width - 100, c, font_name, 9, is_rtl)
            for line in lines[:12]:
                if y_position < 100:
                    c.showPage()
                    y_position = height - 80
                if is_rtl:
                    c.drawRightString(width - 60, y_position, line)
                else:
                    c.drawString(60, y_position, line)
                y_position -= 13
            
            y_position -= 25
            
            # خط جداکننده
            c.setStrokeColorRGB(0.9, 0.3, 0.3)
            c.setLineWidth(2)
            c.line(50, y_position, width - 50, y_position)
            y_position -= 25
            
            # متن ترجمه
            c.setFont(font_name, 12)
            c.setFillColorRGB(0.6, 0.1, 0.1)
            title = "🌍 ترجمه روان:"
            if is_rtl:
                c.drawRightString(width - 50, y_position, title)
            else:
                c.drawString(50, y_position, title)
            y_position -= 25
            
            c.setFont(font_name, 9)
            c.setFillColorRGB(0, 0, 0)
            trans_lines = wrap_text(page_data['translated'][:2500], width - 100, c, font_name, 9, is_rtl)
            for line in trans_lines:
                if y_position < 70:
                    c.showPage()
                    y_position = height - 80
                if is_rtl:
                    c.drawRightString(width - 60, y_position, line)
                else:
                    c.drawString(60, y_position, line)
                y_position -= 13
        
        # فوتر
        c.setFont(font_name, 7)
        c.setFillColorRGB(0.6, 0.6, 0.6)
        footer = "ترجمه شده با مترجم هوشمند | ترجمه روان و طبیعی"
        if is_rtl:
            c.drawRightString(width - 30, 20, footer)
        else:
            c.drawString(30, 20, footer)
    
    c.save()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور شروع"""
    await update.message.reply_text(
        "🌟 سلام! به ربات مترجم هوشمند خوش آمدید!\n\n"
        "✨ ویژگی‌های خاص:\n"
        "• ترجمه روان و طبیعی\n"
        "• بهینه‌سازی مخصوص عربی به فارسی\n"
        "• حفظ اصطلاحات و ضرب‌المثل‌ها\n"
        "• اصلاح ساختار جملات فارسی\n\n"
        "📄 فایل txt یا PDF بفرستید\n"
        "🎯 /setlang fa - تنظیم فارسی\n"
        "/help - راهنمای کامل"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """راهنما"""
    await update.message.reply_text(
        "🔍 راهنمای مترجم هوشمند\n\n"
        "📤 ارسال فایل:\n"
        "• فایل txt یا PDF بفرستید\n"
        "• ترجمه خودکار انجام می‌شود\n\n"
        "⚙️ تنظیمات:\n"
        "/setlang fa - فارسی 🇮🇷\n"
        "/setlang ar - عربی 🇸🇦\n"
        "/setlang en - انگلیسی 🇬🇧\n\n"
        "💡 نکات:\n"
        "• ترجمه عربی به فارسی با دقت بالا\n"
        "• حفظ ساختار و روانی متن\n"
        "• اصلاح خودکار نگارش فارسی\n"
        "• پشتیبانی از اصطلاحات رایج"
    )

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تنظیم زبان"""
    if not context.args:
        await update.message.reply_text("❌ مثال: /setlang fa")
        return
    
    lang = context.args[0].lower()
    context.user_data['target_lang'] = lang
    
    langs = {
        'fa': '🇮🇷 فارسی', 'ar': '🇸🇦 عربی', 'en': '🇬🇧 انگلیسی',
        'es': '🇪🇸 اسپانیایی', 'fr': '🇫🇷 فرانسوی', 'de': '🇩🇪 آلمانی',
        'tr': '🇹🇷 ترکی', 'ru': '🇷🇺 روسی'
    }
    
    lang_name = langs.get(lang, f'🌍 {lang}')
    await update.message.reply_text(f"✅ زبان مقصد: {lang_name}")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت فایل‌ها"""
    document = update.message.document
    filename = document.file_name.lower()
    
    if not (filename.endswith('.pdf') or filename.endswith('.txt')):
        await update.message.reply_text("❌ فقط فایل txt و PDF پشتیبانی می‌شود!")
        return
    
    processing_msg = await update.message.reply_text("⏳ در حال دریافت فایل...")
    
    try:
        file = await context.bot.get_file(document.file_id)
        file_bytes = await file.download_as_bytearray()
        target_lang = context.user_data.get('target_lang', 'fa')
        
        if filename.endswith('.pdf'):
            # ترجمه PDF
            await processing_msg.edit_text("📄 در حال پردازش PDF...")
            
            temp_input = f"/tmp/input_{update.message.message_id}.pdf"
            with open(temp_input, 'wb') as f:
                f.write(file_bytes)
            
            pdf_reader = PyPDF2.PdfReader(temp_input)
            total_pages = len(pdf_reader.pages)
            
            translated_pages = []
            for i in range(total_pages):
                text = pdf_reader.pages[i].extract_text()
                if text and text.strip():
                    await processing_msg.edit_text(f"🔄 ترجمه صفحه {i+1} از {total_pages}")
                    
                    # استفاده از مترجم هوشمند
                    result = smart_translator.translate_text(text[:3000], target_lang)
                    
                    if result:
                        translated_pages.append({
                            'original': text[:2000],
                            'translated': result['text']
                        })
                    else:
                        translated_pages.append({
                            'original': text[:2000],
                            'translated': 'خطا در ترجمه'
                        })
                else:
                    translated_pages.append(None)
            
            await processing_msg.edit_text("📝 در حال ساخت PDF...")
            
            output_pdf = f"/tmp/translated_{document.file_name}"
            create_translated_pdf(output_pdf, translated_pages, target_lang)
            
            await update.message.reply_document(
                document=open(output_pdf, 'rb'),
                filename=f"ترجمه_روان_{document.file_name}",
                caption=f"✅ ترجمه هوشمند انجام شد!\n📊 {total_pages} صفحه\n🎯 ترجمه روان و طبیعی"
            )
            
            os.remove(temp_input)
            os.remove(output_pdf)
        
        else:
            # ترجمه txt
            await processing_msg.edit_text("🔄 در حال ترجمه هوشمند...")
            
            text = file_bytes.decode('utf-8')
            
            # استفاده از مترجم هوشمند
            result = smart_translator.translate_text(text[:5000], target_lang)
            
            if result:
                output_txt = f"/tmp/translated_{document.file_name}"
                with open(output_txt, 'w', encoding='utf-8') as f:
                    f.write(f"ترجمه هوشمند | {result['source_lang']} → {result['target_lang']}\n")
                    f.write("=" * 60 + "\n")
                    f.write("🎯 ترجمه روان و طبیعی\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(result['text'])
                
                await update.message.reply_document(
                    document=open(output_txt, 'rb'),
                    filename=f"ترجمه_روان_{document.file_name}",
                    caption=f"✅ ترجمه هوشمند انجام شد!\n🔤 {result['source_lang']} → {result['target_lang']}"
                )
                
                os.remove(output_txt)
            else:
                await processing_msg.edit_text("❌ خطا در ترجمه!")
                return
        
        await processing_msg.delete()
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ خطا: {str(e)[:200]}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت پیام متنی"""
    await update.message.reply_text(
        "📎 لطفاً فایل txt یا PDF بفرستید تا با دقت بالا ترجمه کنم.\n"
        "✨ ترجمه روان و طبیعی، مخصوص عربی به فارسی!"
    )

def main():
    """اجرای ربات"""
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("setlang", set_language))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("✅ ربات مترجم هوشمند آماده است!")
    app.run_polling()

if __name__ == "__main__":
    main()
