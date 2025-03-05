import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import re

# Danh sách quy tắc
rules = [
    lambda p: sum(c.isalpha() for c in p) >= 5,  # Ít nhất 5 ký tự chữ cái
    lambda p: any(c.isdigit() for c in p),  # KHÔNG được thiếu số
    lambda p: len(p) % 2 == 1 and p[len(p) // 2].isupper(),  # Phải có ít nhất một chữ in hoa ở giữa
    lambda p: any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in p),  # KHÔNG được thiếu ký tự đặc biệt
    lambda p: sum(int(c) for c in p if c.isdigit()) == 25 if any(c.isdigit() for c in p) else False,  # KHÔNG được có tổng chữ số khác 25
    lambda p: any(month.lower() in p.lower() for month in ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]),  # KHÔNG được thiếu tháng
    lambda p: any(roman in p for roman in ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]),  # KHÔNG được thiếu số La Mã
    lambda p: check_roman_numerals(p),  # KHÔNG được có tích số La Mã khác 35
    lambda p: any(element.lower() in p.lower() for element in ["He", "Li", "Be", "Ne", "Na", "Mg", "Al", "Si", "Cl", "Ar"]),  # KHÔNG được thiếu ký hiệu 2 chữ từ bảng tuần hoàn
    lambda p: check_leap_year(p),  # KHÔNG được thiếu năm nhuận
]

rule_descriptions = [
    "Có ít nhất 5 ký tự chữ cái trong mật khẩu của bạn",
    "Có ít nhất một chữ số trong mật khẩu của bạn",
    "Có ít nhất một chữ cái in hoa nằm ở vị trí giữa trong mật khẩu của bạn",
    "Có ít nhất một ký tự đặc biệt trong mật khẩu của bạn",
    "Có tổng các chữ số trong mật khẩu bằng 25",
    "Contains at least one month name in your password",
    "Có ít nhất một số La Mã trong mật khẩu của bạn",
    "Có tích của các số La Mã trong mật khẩu bằng 35",
    "Có ít nhất một ký hiệu hai chữ cái từ bảng tuần hoàn trong mật khẩu của bạn",
    "Có ít nhất một năm nhuận trong mật khẩu của bạn",
]

# Hàm phụ để phân tích và tính tích số La Mã
def check_roman_numerals(password):
    roman_values = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10}
    roman_pattern = r'(IX|IV|VIII|VII|VI|III|II|I|V|X)'
    matches = re.findall(roman_pattern, password)
    if not matches:
        return False
    product = 1
    for match in matches:
        product *= roman_values[match]
    return product == 35

# Hàm kiểm tra năm nhuận
def check_leap_year(password):
    # Tìm tất cả các số có 4 chữ số trong mật khẩu
    years = re.findall(r'\d{4}', password)
    for year in years:
        year_int = int(year)
        # Kiểm tra điều kiện năm nhuận
        if (year_int % 4 == 0 and year_int % 100 != 0) or (year_int % 400 == 0):
            return True
    return False

# Lưu trạng thái người chơi
user_progress = {}

async def start(update, context):
    user_id = update.message.from_user.id
    user_progress[user_id] = 0  # Bắt đầu từ quy tắc 0
    await update.message.reply_text("Chào mừng bạn đến với Password Master! Hãy nhập một mật khẩu để bắt đầu.\nQuy tắc 1: " + rule_descriptions[0])

async def check_password(update, context):
    user_id = update.message.from_user.id
    if user_id not in user_progress:
        await update.message.reply_text("Vui lòng bắt đầu bằng lệnh /start!")
        return

    password = update.message.text.strip()
    current_rule = user_progress[user_id]

    passed_rules = []  # Danh sách quy tắc đã vượt qua

    # Kiểm tra từng quy tắc một
    for i in range(current_rule, len(rules)):
        if rules[i](password):
            passed_rules.append(f"✅ Quy tắc {i + 1}: {rule_descriptions[i]}\n")
        else:
            # Nếu gặp quy tắc đầu tiên bị sai, dừng lại ngay
            await update.message.reply_text(
                "\n".join(passed_rules) +
                f"\n❌ Mật khẩu của bạn vi phạm Quy tắc {i + 1}: {rule_descriptions[i]}"
            )
            return

    # Nếu không bị sai quy tắc nào, cập nhật trạng thái và tiếp tục
    user_progress[user_id] = len(rules)
    await update.message.reply_text("\n".join(passed_rules) + "\n🎉 Chúc mừng! Bạn đã vượt qua tất cả các quy tắc và chiến thắng!")
    del user_progress[user_id]

def main():
    # Token bot của bạn
    TOKEN = "8174630573:AAHoOluAArZx15egGCrF4BrcWfIhGEJkV6w"
    
    # Tạo ứng dụng
    application = Application.builder().token(TOKEN).build()

    # Thêm handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_password))

    # Chạy bot
    application.run_polling()

if __name__ == "__main__":
    main()