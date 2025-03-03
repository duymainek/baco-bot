import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import re

# Danh sách quy tắc
rules = [
    lambda p: len(p) >= 5,  # KHÔNG được ngắn hơn 5 ký tự
    lambda p: any(c.isdigit() for c in p),  # KHÔNG được thiếu số
    lambda p: any(c.isupper() for c in p),  # KHÔNG được thiếu chữ cái in hoa
    lambda p: any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in p),  # KHÔNG được thiếu ký tự đặc biệt
    lambda p: sum(int(c) for c in p if c.isdigit()) == 25 if any(c.isdigit() for c in p) else False,  # KHÔNG được có tổng chữ số khác 25
    lambda p: any(month.lower() in p.lower() for month in ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]),  # KHÔNG được thiếu tháng
    lambda p: any(roman in p for roman in ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]),  # KHÔNG được thiếu số La Mã
    lambda p: check_roman_numerals(p),  # KHÔNG được có tích số La Mã khác 35
    lambda p: any(element.lower() in p.lower() for element in ["He", "Li", "Be", "Ne", "Na", "Mg", "Al", "Si", "Cl", "Ar"]),  # KHÔNG được thiếu ký hiệu 2 chữ từ bảng tuần hoàn
    lambda p: check_leap_year(p),  # KHÔNG được thiếu năm nhuận
]

# Danh sách mô tả quy tắc đã chỉnh sửa
rule_descriptions = [
    "Có ít nhất 5 ký tự trong mật khẩu của bạn",
    "Có chữ số trong mật khẩu của bạn",
    "Có chữ cái in hoa trong mật khẩu của bạn",
    "Có ký tự đặc biệt trong mật khẩu của bạn",
    "Có tổng các chữ số trong mật khẩu của bạn bằng 25",
    "Có tên một tháng trong năm trong mật khẩu của bạn",
    "Có số La Mã trong mật khẩu của bạn",
    "Có tích các số La Mã trong mật khẩu của bạn bằng 35",
    "Có ký hiệu hai chữ cái từ bảng tuần hoàn trong mật khẩu của bạn",
    "Có một năm nhuận trong mật khẩu của bạn",
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

    current_rule = user_progress[user_id]
    password = update.message.text.strip()  # Loại bỏ khoảng trắng thừa

    # Kiểm tra tất cả quy tắc từ 0 đến current_rule
    for i in range(current_rule + 1):
        if not rules[i](password):
            await update.message.reply_text(f"Sai rồi! Mật khẩu của bạn vi phạm Quy tắc {i + 1}: {rule_descriptions[i]}")
            return

    # Nếu vượt qua tất cả quy tắc đến current_rule, chuyển sang bước tiếp theo
    user_progress[user_id] += 1
    if current_rule + 1 == len(rules):
        await update.message.reply_text("Chúc mừng! Bạn đã vượt qua tất cả 10 quy tắc và chiến thắng!")
        del user_progress[user_id]
    else:
        await update.message.reply_text(f"Đúng rồi! Tiếp theo, Quy tắc {current_rule + 2}: {rule_descriptions[current_rule + 1]}")

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