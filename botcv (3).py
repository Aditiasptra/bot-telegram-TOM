
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime

TOKEN = "7385197009:AAFGxZ03-HmpKQcy6pvH2DvhwmKKWq483s4"  # Ganti dengan token kamu
AUTHORIZED_USERS = [7115511137]  # Ganti dengan user ID kamu
PER_FILE_LIMIT = 1000  # Default jumlah per file
NAME_PREFIX = "Kontak"  # Default prefix nama kontak

# Cek otorisasi
def is_authorized(update):
    return update.effective_user.id in AUTHORIZED_USERS

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("Akses ditolak.")
        return
    await update.message.reply_text("Selamat datang! Kirim file .txt berisi daftar nomor (satu per baris) atau Nama,Nomor.")

# /setjumlah command
async def set_jumlah(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global PER_FILE_LIMIT
    if not is_authorized(update):
        await update.message.reply_text("Akses ditolak.")
        return
    try:
        jumlah = int(context.args[0])
        PER_FILE_LIMIT = jumlah
        await update.message.reply_text(f"Jumlah kontak per file disetel ke {jumlah}.")
    except:
        await update.message.reply_text("Format salah. Contoh: /setjumlah 1000")

# /setprefix command
async def set_prefix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global NAME_PREFIX
    if not is_authorized(update):
        await update.message.reply_text("Akses ditolak.")
        return
    try:
        prefix = " ".join(context.args)
        NAME_PREFIX = prefix
        await update.message.reply_text(f"Prefix nama disetel ke '{NAME_PREFIX}'.")
    except:
        await update.message.reply_text("Format salah. Contoh: /setprefix NamaSaya")

# Fungsi konversi ke VCF
def txt_to_vcf(content, per_file=PER_FILE_LIMIT):
    lines = content.splitlines()
    part = 1
    count = 0
    index = 1
    vcf_data = ""
    results = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if "," in line:
            name, number = line.split(",", 1)
        else:
            name = f"{NAME_PREFIX} {index}"
            number = line
        index += 1

        vcf = f"BEGIN:VCARD\nVERSION:3.0\nFN:{name.strip()}\nTEL;TYPE=CELL:{number.strip()}\nEND:VCARD\n"
        vcf_data += vcf
        count += 1

        if count >= per_file:
            filename = f"FS_part{part}.vcf"
            with open(filename, 'w') as f:
                f.write(vcf_data)
            results.append(filename)
            vcf_data = ""
            count = 0
            part += 1

    if vcf_data:
        filename = f"FS_part{part}.vcf"
        with open(filename, 'w') as f:
            f.write(vcf_data)
        results.append(filename)

    return results

# Handler file
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("Akses ditolak.")
        return

    try:
        file = await update.message.document.get_file()
        file_path = f"kontak_{datetime.now().timestamp()}.txt"
        await file.download_to_drive(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        vcf_files = txt_to_vcf(content)

        for fpath in vcf_files:
            await update.message.reply_document(document=open(fpath, "rb"))
            os.remove(fpath)

        os.remove(file_path)

    except Exception as e:
        await update.message.reply_text(f"Terjadi kesalahan: {str(e)}")

# Main
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setjumlah", set_jumlah))
    app.add_handler(CommandHandler("setprefix", set_prefix))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    print("Bot jalan...")
    app.run_polling()
