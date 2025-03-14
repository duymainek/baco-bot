import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import re
from collections import Counter
import random
import string
from supabase import create_client, Client

SUPABASE_URL = "https://ifkusnuoxzllhniwkywh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlma3VzbnVveHpsbGhuaXdreXdoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNjE0MTY1MywiZXhwIjoyMDUxNzE3NjUzfQ.PcLgon96CK6xB8Mf82FRRCZ_b7XvidAQlDD4cQ_wFKM"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


rules = [
    lambda p: 10 < sum(c.isalpha() for c in p) < 25 and ' ' not in p,
    lambda p: all(c.isalpha() and c.upper() in string.ascii_uppercase for c in p if c.isalpha()),
    lambda p: any(c.isdigit() for c in p),  # KHÔNG được thiếu số
    lambda p: sum(1 for c in p if c.isupper()) == 1 and p[len(p) // 2].isupper(),  # Chỉ có 1 chữ cái in hoa và nó nằm ở giữa
    lambda p: sum(int(c) for c in p if c.isdigit()) == 25 if any(c.isdigit() for c in p) else False,  # KHÔNG được có tổng chữ số khác 25
    lambda p: sum(1 for month in ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"] if month in p.lower()) == 1,  # Chỉ có duy nhất 1 tháng
    lambda p: check_roman_numerals(p),  # Số La Mã có thể viết thường hoặc hoa
    lambda p: check_roman_numeral_product(p),  # KHÔNG được có tích số La Mã khác 35
    lambda p: check_leap_year(p),  # KHÔNG được thiếu năm nhuận
]

TEXT_MAPPING = [
  {"text": "DANANG", "length": 6},
  {"text": "DDANANG", "length": 7},
  {"text": "DDAFNANG", "length": 8},
  {"text": "DDAFNAWNG", "length": 9},
  {"text": "KHANGCHIEN", "length": 10},
  {"text": "TONGTANCONG", "length": 11},
  {"text": "KHÔNGCÓHỘĐÓI", "length": 12},
  {"text": "MỘTDISẢNTOLỚN", "length": 13},
  {"text": "HỖTRỢNHÀỞHỢPLÝ", "length": 14},
  {"text": "CẢITHIỆNĐỜISỐNG", "length": 15},
  {"text": "TOCCHIENTOCTHANG", "length": 16},
  {"text": "KHÔNGCÓNGƯỜIMÙCHỮ", "length": 17},
  {"text": "TỆNẠNXÃHỘIBỊĐẨYLÙI", "length": 18},
  {"text": "SỐNGANTOÀNVÀVĂNMINH", "length": 19},
  {"text": "ANHHUNGDANTOCVIETNAM", "length": 20},
  {"text": "CÓNẾPSỐNGVĂNMINHĐÔTHỊ", "length": 21},
  {"text": "ĐÁNGSỐNGBẬCNHẤTVIỆTNAM", "length": 22},
  {"text": "SINHRAVÀLỚNLÊNTẠIĐÀNẴNG", "length": 23},
  {"text": "CẢITHIỆNCHẤTLƯỢNGĐỜISỐNG", "length": 24},
  {"text": "KHÔNGCÓGIẾTNGƯỜIĐỂCƯỚPCỦA", "length": 25},
  {"text": "KHÔNGCÓNGƯỜILANGTHANGXINĂN", "length": 26},
  {"text": "HỘDÂNNGHÈOĐÃCÓMÁIẤMVỮNGCHÃI", "length": 27},
  {"text": "MÔITRƯỜNGSỐNGANTOÀNVÀVĂNMINH", "length": 28},
  {"text": "PHÁTTRIỂNBỀNVỮNGVÀTIẾNBỘXÃHỘI", "length": 29},
  {"text": "NGUYỄNBÁTHANHVỊLÃNHĐẠOKIỆTXUẤT", "length": 30},
  {"text": "THÀNHPHỐCHÚTRỌNGPHÁTTRIỂNKINHTẾ", "length": 31},
  {"text": "ÔNGBÁTHANHLÀLÃNHĐẠOTÀIBAKIỆTXUẤT", "length": 32},
  {"text": "TẦMNHÌNVÀTÂMHUYẾTCỦANGUYỄNBÁTHANH", "length": 33},
  {"text": "TẦMNHÌNVÀCHIẾNLƯỢCCỦANGUYỄNBÁTHANH", "length": 34},
  {"text": "MANGLẠICUỘCSỐNGTỐTĐẸPHƠNCHONGƯỜIDÂN", "length": 35},
  {"text": "BÁCNGUYỄNBÁTHANHĐÃĐỂLẠIMỘTDISẢNTOLỚN", "length": 36},
  {"text": "NẾPSỐNGVĂNMINHĐÔTHỊĐƯỢCQUANTÂMHÀNGĐẦU", "length": 37},
  {"text": "KHUCÔNGNGHỆCAOVÀCÁCDỰÁNCHỈNHTRANGĐÔTHỊ", "length": 38},
  {"text": "KHẮCKHOẢILÀMSAOĐỂTHAYĐỔIDIỆNMẠOTHÀNHPHỐ", "length": 39},
  {"text": "THAYĐỔIHOÀNTOÀNCUỘCSỐNGCỦANGƯỜIDÂNĐÀNẴNG", "length": 40},
  {"text": "ƯUTIÊNTRIỂNKHAINẾPSỐNGVĂNMINHĐÔTHỊHÀNGĐẦU", "length": 41},
  {"text": "XÂYDỰNGKHUCÔNGNGHỆCAOVÀDỰÁNCHỈNHTRANGĐÔTHỊ", "length": 42},
  {"text": "TỪMỘTTHÀNHPHỐNGHÈONÀNTRỞTHÀNHĐÔTHỊPHÁTTRIỂN", "length": 43},
  {"text": "XÂYDỰNGNẾPSỐNGVĂNMINHĐÔTHỊĐƯỢCQUANTÂMHÀNGĐẦU", "length": 44},
  {"text": "XÂYDỰNGKHUCÔNGNGHỆCAOVÀCÁCDỰÁNCHỈNHTRANGĐÔTHỊ", "length": 45},
  {"text": "ĐÀNẴNGĐÃTRIỂNKHAICÁCCHƯƠNGTRÌNHHỖTRỢNGƯỜINGHÈO", "length": 46},
  {"text": "VƯƠNMÌNHTỪ1THÀNHPHỐNGHÈONÀNTRỞTHÀNHĐÔTHỊLỚNMẠNH", "length": 47},
  {"text": "TẠONỀNTẢNGCHOSỰPHÁTTRIỂNVƯỢTBẬCCỦATHÀNHPHỐĐÀNẴNG", "length": 48},
  {"text": "ĐÀNẴNGTHÀNHTHÀNHPHỐCÓMÔITRƯỜNGSỐNGANTOÀNVÀVĂNMINH", "length": 49},
  {"text": "VƯƠNMÌNHTHÀNHĐÔTHỊĐÁNGSỐNGVỚITỐCĐỘPHÁTTRIỂNVƯỢTBẬC", "length": 50},
  {"text": "VƯƠNMÌNHTỪMỘTTHÀNHPHỐNGHÈONÀNTRỞTHÀNHĐÔTHỊPHÁTTRIỂN", "length": 51},
  {"text": "ĐÀNẴNGĐÃBẮTĐẦUTRIỂNKHAICÁCCHƯƠNGTRÌNHHỖTRỢNGƯỜINGHÈO", "length": 52},
  {"text": "TRỰCTIẾPCHỈĐẠOHÀNGLOẠTCÔNGTRÌNHTRỌNGĐIỂMNHƯCẦUSÔNGHÀN", "length": 53},
  {"text": "NHỮNGDẤUẤNCỦAÔNGVẪNCÒNNGUYÊNVẸNTRONGLÒNGNGƯỜIDÂNĐÀNẴNG", "length": 54},
  {"text": "TRỞTHÀNHHÌNHMẪUCHOSỰĐỔIMỚIPHÁTTRIỂNBỀNVỮNGVÀTIẾNBỘXÃHỘI", "length": 55},
  {"text": "TẬPTRUNGTẠONỀNTẢNGCHOSỰPHÁTTRIỂNVƯỢTBẬCCỦATHÀNHPHỐĐÀNẴNG", "length": 56},
  {"text": "ĐÀNẴNGTẬPTRUNGTHÀNHTHÀNHPHỐCÓMÔITRƯỜNGSỐNGANTOÀNVÀVĂNMINH", "length": 57},
  {"text": "HỖTRỢNGƯỜINGHÈOGIÚPĐỠNGƯỜILANGTHANGCƠNHỠBẰNGCÁCHTẠOVIỆCLÀM", "length": 58},
  {"text": "TẬPTRUNGVƯƠNMÌNHTỪMỘTTHÀNHPHỐNGHÈONÀNTRỞTHÀNHĐÔTHỊPHÁTTRIỂN", "length": 59},
  {"text": "ĐÀNẴNGĐÃBẮTĐẦUTẬPTRUNGTRIỂNKHAICÁCCHƯƠNGTRÌNHHỖTRỢNGƯỜINGHÈO", "length": 60},
  {"text": "HIỂUNHỮNGMONGMUỐNKHÓKHĂNCỦANGƯỜIDÂNĐỂTÌMRAHƯỚNGGIẢIQUYẾTTỐIƯU", "length": 61},
  {"text": "CỐGẮNGTẬPTRUNGTẠONỀNTẢNGCHOSỰPHÁTTRIỂNVƯỢTBẬCCỦATHÀNHPHỐĐÀNẴNG", "length": 62},
  {"text": "TẬPTRUNGTRỞTHÀNHHÌNHMẪUCHOSỰĐỔIMỚIPHÁTTRIỂNBỀNVỮNGVÀTIẾNBỘXÃHỘI", "length": 63},
  {"text": "CỐGẮNGHỖTRỢNGƯỜINGHÈOGIÚPĐỠNGƯỜILANGTHANGCƠNHỠBẰNGCÁCHTẠOVIỆCLÀM", "length": 64},
  {"text": "HÀNGLOẠTCÔNGTRÌNHTRỌNGĐIỂMNHƯCẦUSÔNGHÀNĐƯỜNGVENBIỂNNGUYỄNTẤTTHÀNH", "length": 65},
  {"text": "TẬPTRUNGHỖTRỢNGƯỜINGHÈOGIÚPĐỠNGƯỜILANGTHANGCƠNHỠBẰNGCÁCHTẠOVIỆCLÀM", "length": 66},
  {"text": "CỐGẮNGHIỂUNHỮNGMONGMUỐNKHÓKHĂNCỦANGƯỜIDÂNĐỂTÌMRAHƯỚNGGIẢIQUYẾTTỐIƯU", "length": 67},
  {"text": "HỖTRỢNGƯỜINGHÈOGIÚPĐỠNGƯỜILANGTHANGCƠNHỠBẰNGCÁCHTẠOVIỆCLÀMĐÀOTẠONGHỀ", "length": 68},
  {"text": "CỐGẮNGTẬPTRUNGTRỞTHÀNHHÌNHMẪUCHOSỰĐỔIMỚIPHÁTTRIỂNBỀNVỮNGVÀTIẾNBỘXÃHỘI", "length": 69},
  {"text": "TẬPTRUNGHỖTRỢNGƯỜINGHÈOGIÚPĐỠNGƯỜILANGTHANGCƠNHỠBẰNGCÁCHTẠOVIỆCLÀM2000", "length": 70},
  {"text": "CHỈĐẠOHÀNGLOẠTCÔNGTRÌNHTRỌNGĐIỂMNHƯCẦUSÔNGHÀNĐƯỜNGVENBIỂNNGUYỄNTẤTTHÀNH", "length": 71},
  {"text": "CỐGẮNGTẬPTRUNGHỖTRỢNGƯỜINGHÈOGIÚPĐỠNGƯỜILANGTHANGCƠNHỠBẰNGCÁCHTẠOVIỆCLÀM", "length": 72},
  {"text": "KHÔNGCHỈLÀMỘTNGƯỜILÃNHĐẠOGIỎIMÀCÒNLÀMỘTCONNGƯỜIĐẦYTÌNHCẢMGẦNGŨIVỚINHÂNDÂN", "length": 73},
  {"text": "VÀOCUỘCMẠNHMẼCỦACHÍNHQUYỀNVÀNGƯỜIDÂNGÓPPHẦNTẠONÊNMỘTMÔITRƯỜNGSỐNGĐÁNGMƠƯỚC", "length": 74},
  {"text": "CHỈĐẠOHÀNGLOẠTCÔNGTRÌNHTRỌNGĐIỂMNHƯCẦUSÔNGHÀNĐƯỜNGVENBIỂNNGUYỄNTẤTTHÀNH1998", "length": 75},
  {"text": "CỐGẮNGTẬPTRUNGHỖTRỢNGƯỜINGHÈOGIÚPĐỠNGƯỜILANGTHANGCƠNHỠBẰNGCÁCHTẠOVIỆCLÀM2000", "length": 76},
  {"text": "NHỮNGCHÍNHSÁCHMÀÔNGĐỀRAVẪNĐANGTIẾPTỤCPHÁTHUYHIỆUQUẢĐƯAĐÀNẴNGNGÀYCÀNGPHÁTTRIỂN", "length": 77},
  {"text": "CỐGẮNGXÂYDỰNGHÀNGLOẠTCÔNGTRÌNHTRỌNGĐIỂMNHƯCẦUSÔNGHÀNĐƯỜNGVENBIỂNNGUYỄNTẤTTHÀNH", "length": 78},
  {"text": "CHỈĐẠOHÀNGLOẠTCÔNGTRÌNHTRỌNGĐIỂMNHƯCẦUSÔNGHÀNĐƯỜNGVENBIỂNNGUYỄNTẤTTHÀNH19982003", "length": 79},
  {"text": "CÁCCHƯƠNGTRÌNHGIÁODỤCMIỄNPHÍGIÚPXOÁNẠNMÙCHỮHOÀNTOÀNMANGĐẾNCƠHỘIHỌCTẬPCHOMỌINGƯỜI", "length": 80},
  {"text": "MỘTCHÍNHSÁCHMANGTÍNHNHÂNVĂNSÂUSẮCTẠONỀNTẢNGCHOSỰPHÁTTRIỂNVƯỢTBẬCCỦATHÀNHPHỐĐÀNẴNG", "length": 81},
{
    "text": "ĐÀNẴNGTỪMỘTTHÀNHPHỐNHỎBÉLẠCHẬUĐÃVƯƠNMÌNHTHÀNHĐÔTHỊĐÁNGSỐNGVỚITỐCĐỘPHÁTTRIỂNVƯỢTBẬC",
    "length": 82
  },
  {
    "text": "MỘTCHÍNHSÁCHMANGTÍNHNHÂNVĂNSÂUSẮCTẠONỀNTẢNGCHOSỰPHÁTTRIỂNVƯỢTBẬCCỦATHÀNHPHỐĐÀNẴNG01",
    "length": 83
  },
  {
    "text": "CÁCCHƯƠNGTRÌNHGIÁODỤCMIỄNPHÍGIÚPXOÁNẠNMÙCHỮHOÀNTOÀNMANGĐẾNCƠHỘIHỌCTẬPCHOMỌINGƯỜI2000",
    "length": 84
  },
  {
    "text": "MỘTCHÍNHSÁCHMANGTÍNHNHÂNVĂNSÂUSẮCTẠONỀNTẢNGCHOSỰPHÁTTRIỂNVƯỢTBẬCCỦATHÀNHPHỐĐÀNẴNG2000",
    "length": 85
  },
  {
    "text": "NGUYỄNBÁTHANHKHÔNGCHỈLÀMỘTNGƯỜILÃNHĐẠOGIỎIMÀCÒNLÀMỘTCONNGƯỜIĐẦYTÌNHCẢMGẦNGŨIVỚINHÂNDÂN",
    "length": 86
  },
  {
    "text": "NGUYỄNBÁTHANHKHÔNGCHỈLÀMỘTNGƯỜILÃNHĐẠOGIỎIMÀCÒNLÀMỘTCONNGƯỜIĐẦYTÌNHCẢMGẦNGŨIVỚINHÂNDÂN1",
    "length": 87
  },
  {
    "text": "TẬPTRUNGCÁCCHƯƠNGTRÌNHGIÁODỤCMIỄNPHÍGIÚPXOÁNẠNMÙCHỮHOÀNTOÀNMANGĐẾNCƠHỘIHỌCTẬPCHOMỌINGƯỜI",
    "length": 88
  },
  {
    "text": "NGUYỄNBÁTHANHVỊLÃNHĐẠOKIỆTXUẤTNGƯỜIĐÃĐƯAĐÀNẴNGTỪMỘTTHÀNHPHỐNGHÈONÀNTRỞTHÀNHĐÔTHỊPHÁTTRIỂN",
    "length": 89
  },
  {
    "text": "ĐÀNẴNGTỪMỘTTHÀNHPHỐNHỎBÉLẠCHẬUĐÃTẬPTRUNGVƯƠNMÌNHTHÀNHĐÔTHỊĐÁNGSỐNGVỚITỐCĐỘPHÁTTRIỂNVƯỢTBẬC",
    "length": 90
  },
  {
    "text": "ĐÀNẴNGTỪMỘTTHÀNHPHỐNHỎBÉLẠCHẬUĐÃTẬPTRUNGVƯƠNMÌNHTHÀNHĐÔTHỊĐÁNGSỐNGVỚITỐCĐỘPHÁTTRIỂNVƯỢTBẬC1",
    "length": 91
  },
  {
    "text": "ĐÀNẴNGTỪMỘTTHÀNHPHỐNHỎBÉLẠCHẬUĐÃTẬPTRUNGVƯƠNMÌNHTHÀNHĐÔTHỊĐÁNGSỐNGVỚITỐCĐỘPHÁTTRIỂNVƯỢTBẬC12",
    "length": 92
  },
  {
    "text": "ĐÀNẴNGTỪMỘTTHÀNHPHỐNHỎBÉLẠCHẬUĐÃTẬPTRUNGVƯƠNMÌNHTHÀNHĐÔTHỊĐÁNGSỐNGVỚITỐCĐỘPHÁTTRIỂNVƯỢTBẬC123",
    "length": 93
  },
  {
    "text": "ĐÀNẴNGTỪMỘTTHÀNHPHỐNHỎBÉLẠCHẬUĐÃTẬPTRUNGVƯƠNMÌNHTHÀNHĐÔTHỊĐÁNGSỐNGVỚITỐCĐỘPHÁTTRIỂNVƯỢTBẬC2003",
    "length": 94
  },
  {
    "text": "ĐÀNẴNGTỪ1THÀNHPHỐNHỎBÉLẠCHẬUĐÃCỐGẮNGTẬPTRUNGVƯƠNMÌNHTHÀNHĐÔTHỊĐÁNGSỐNGVỚITỐCĐỘPHÁTTRIỂNVƯỢTBẬC1",
    "length": 95
  },
  {
    "text": "ĐÀNẴNGTỪMỘTTHÀNHPHỐNHỎBÉLẠCHẬUĐÃCỐGẮNGTẬPTRUNGVƯƠNMÌNHTHÀNHĐÔTHỊĐÁNGSỐNGVỚITỐCĐỘPHÁTTRIỂNVƯỢTBẬC",
    "length": 96
  },
  {
    "text": "NGUYỄNBÁTHANHKHÔNGCHỈLÀMỘTNGƯỜILÃNHĐẠOTÀIGIỎIMÀÔNGCÒNLÀ1CONNGƯỜIĐẦYTÌNHCẢMGẦNGŨIYÊUTHƯƠNGNHÂNDÂN1",
    "length": 97
  },
  {
    "text": "NGUYỄNBÁTHANHKHÔNGCHỈLÀMỘTNGƯỜILÃNHĐẠOTÀIGIỎIMÀÔNGCÒNLÀMỘTCONNGƯỜIĐẦYTÌNHCẢMGẦNGŨIVÀYÊUNHÂNDÂN1998",
    "length": 98
  },
  {
    "text": "NGUYỄNBÁTHANHKHÔNGCHỈLÀMỘTNGƯỜILÃNHĐẠOGIỎIMÀNGUYỄNBÁTHANHCÒNLÀMỘTCONNGƯỜIĐẦYTÌNHCẢMGẦNGŨIVỚINHÂNDÂN",
    "length": 99
  },
  {
    "text": "NGUYỄNBÁTHANHKHÔNGCHỈLÀMỘTNGƯỜILÃNHĐẠOTÀIGIỎIMÀÔNGCÒNLÀMỘTCONNGƯỜIĐẦYTÌNHCẢMGẦNGŨIVÀYÊUTHƯƠNGNHÂNDÂN",
    "length": 100
  },
  {
    "text": "NGUYỄNBÁTHANHKHÔNGCHỈLÀMỘTNGƯỜILÃNHĐẠOTÀIGIỎIMÀÔNGCÒNLÀMỘTCONNGƯỜIĐẦYTÌNHCẢMGẦNGŨIVÀYÊUTHƯƠNGNHÂNDÂN1",
    "length": 101
  },
  {
    "text": "DƯỚISỰDẪNDẮTTÀITÌNHCỦAÔNGĐÀNẴNGĐÃBỨTPHÁNGOẠNMỤCTRỞTHÀNHHÌNHMẪUCHOSỰĐỔIMỚIPHÁTTRIỂNBỀNVỮNGVÀTIẾNBỘXÃHỘI",
    "length": 102
  },
  {
    "text": "DƯỚISỰDẪNDẮTTÀITÌNHCỦAÔNGĐÀNẴNGĐÃBỨTPHÁNGOẠNMỤCTRỞTHÀNHHÌNHMẪUCHOSỰĐỔIMỚIPHÁTTRIỂNBỀNVỮNGVÀTIẾNBỘXÃHỘI1",
    "length": 103
  },
  {
    "text": "DƯỚISỰDẪNDẮTTÀITÌNHCỦAÔNGĐÀNẴNGĐÃBỨTPHÁNGOẠNMỤCTRỞTHÀNHHÌNHMẪUCHOSỰĐỔIMỚIPHÁTTRIỂNBỀNVỮNGVÀTIẾNBỘXÃHỘI01",
    "length": 104
  },
  {
    "text": "NHỮNGCÔNGTRÌNHMÀÔNGKHỞIXƯỚNGNHỮNGCHÍNHSÁCHMÀÔNGĐỀRAVẪNĐANGTIẾPTỤCPHÁTHUYHIỆUQUẢĐƯAĐÀNẴNGNGÀYCÀNGPHÁTTRIỂN",
    "length": 105
  }
]

MORSE_CODE_DICT = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.', 'G': '--.', 'H': '....',
    'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 'P': '.--.',
    'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.', '!': '-.-.--'
}


def text_to_morse(text):
    text = text.upper()
    return ' '.join(MORSE_CODE_DICT.get(char, '') for char in text if char in MORSE_CODE_DICT)


def morse_to_text(morse):
    dot_count = Counter(morse)['.']
    for entry in TEXT_MAPPING:
        if entry["length"] == dot_count:
            return entry["text"]
    return None


rule_descriptions = [
    "Có ít nhất 10 ký tự chữ cái, không được quá 25 chữ cái và không có khoảng trắng.",
    "Có tất cả các ký tự là chữ cái trong bảng chữ cái Alphabet.",
    "Có ít nhất một chữ số.",
    "Có đúng một chữ cái in hoa và nó phải nằm ở giữa.",
    "Có tổng các chữ số bằng 25.",
    "Contains no more than one month of the year.",
    "Có ít nhất một số La Mã (tính cả viết hoa và thường).",
    "Có tích của các số La Mã bằng 35.",
    "Có ít nhất một năm nhuận bắt đầu từ năm 1000.",
]

# Hàm kiểm tra số La Mã (cho phép viết thường)
def check_roman_numerals(password):
    roman_pattern = r'(?i)(ix|iv|viii|vii|vi|iii|ii|i|v|x|xl|l|xc|c|d|m)'  # Không dùng \b, thêm d và m
    return bool(re.search(roman_pattern, password))

# Hàm tính tích số La Mã
def check_roman_numeral_product(password):
    roman_values = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10, "XL": 40, "L": 50, "XC": 90, "C": 100, "D": 500, "M": 1000}
    roman_pattern = r'(?i)(IX|IV|VIII|VII|VI|III|II|I|V|X|XL|L|XC|C|D|M)'  # Không dùng \b, thêm D và M
    matches = re.findall(roman_pattern, password, re.IGNORECASE)
    
    if not matches:
        return False  # Không có số La Mã nào, không cần kiểm tra
    
    
    product = 1
    for match in matches:
        product *= roman_values[match.upper()]  # Chuyển về viết hoa để tra bảng giá trị
    
    return product == 35
# Hàm kiểm tra năm nhuận
def check_leap_year(password):
    years = re.findall(r'\d{4}', password)
    for year in years:
        year_int = int(year)
        if (year_int % 4 == 0 and year_int % 100 != 0) or (year_int % 400 == 0):
            return True
    return False

# Lưu trạng thái người chơi
user_progress = {}
user_codes = {}

# Hàm kiểm tra mã code có tồn tại trong bảng users
async def check_code_exists(code):
    try:
        response = supabase.table('users').select('*').eq('code', code).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Lỗi khi kiểm tra mã code: {e}")
        return False

async def start(update, context):
    user_id = update.message.from_user.id
    await update.message.reply_text("Chào mừng bạn đến với thử thách Ba Có! Vui lòng nhập mã code của đội để bắt đầu.\nBạn có thể sử dụng lệnh /restart để bắt đầu lại thử thách bất cứ lúc nào.")

async def restart(update, context):
    user_id = update.message.from_user.id
    
    # Xóa dữ liệu người dùng
    if user_id in user_progress:
        del user_progress[user_id]
    if user_id in user_codes:
        del user_codes[user_id]
    
    await update.message.reply_text("Đã khởi động lại thử thách. Vui lòng nhập mã code của đội để bắt đầu lại.")

async def verify_code(update, context):
    user_id = update.message.from_user.id
    code = update.message.text.strip()
    
    # Kiểm tra xem người dùng đã nhập mã code chưa
    if user_id in user_codes:
        # Người dùng đã có mã code, chuyển sang xử lý mật khẩu
        await check_password(update, context)
        return
    
    # Kiểm tra mã code có tồn tại không
    if await check_code_exists(code):
        user_codes[user_id] = code
        user_progress[user_id] = 0  # Bắt đầu từ quy tắc 0
        await update.message.reply_text(f"Mã code hợp lệ! Nhiệm vụ của bạn là tạo ra một OTT đáp ứng yêu cầu của chúng tôi đưa ra. Bạn sẽ nhận được BV của mật thư khi hoàn thành thử thách. Hãy nhập một OTT bất kì để bắt đầu.\nQuy tắc 1: {rule_descriptions[0]}")
    else:
        await update.message.reply_text("Mã code không hợp lệ. Vui lòng thử lại.")

async def check_password(update, context):
    user_id = update.message.from_user.id
    # Hàm ghi log
    print(f"Checking password for user_id: {user_id}")
    print(f"Message received: {update.message.text}")
    # Log user_codes để theo dõi mã code của người dùng
    print(f"Current user_codes: {user_codes}")
    if user_id in user_codes:
        print(f"User {user_id} has code: {user_codes[user_id]}")
    else:
        print(f"User {user_id} has no code assigned yet")
    
    # Kiểm tra xem người dùng đã nhập mã code chưa
    if user_id not in user_codes:
        await verify_code(update, context)
        return
    
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
    morse_code = text_to_morse(password)
    text_result = morse_to_text(morse_code)
    if not text_result:
        await update.message.reply_text("OTT của bạn quá dài hoặc quá ngắn, vui lòng thử lại OTT khác")
        return
    await update.message.reply_text("\n".join(passed_rules) + "\n🎉 Chúc mừng! Bạn đã hoàn thành việc tạo khoá!")

    encoded_message = encode_message(morse_code, text_result)
    await update.message.reply_text(f"Đây là BV của mật thư: {encoded_message.replace(' ', '')}")
    await update.message.reply_text(f"Vui lòng không nhập đáp án mật thư ở đây")
    insert_anwsers(text_result.replace(' ', ''),user_id)
    del user_progress[user_id]

def encode_message(morse_template, decoded_message):
    decoded_chars = list(decoded_message)
    encoded_message = []
    vietnamese_chars = 'áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđabcdefghijklmnopqrstuvwxyz'
    
    for char in morse_template:
        if char == '.':
            encoded_message.append(decoded_chars.pop(0) if decoded_chars else '.')
        elif char == '-':
            encoded_message.append(random.choice(vietnamese_chars.upper()))
        else:
            encoded_message.append(char)
    
    return ''.join(encoded_message)


def insert_anwsers(anwser: str, user_id: int) -> None:
    """Insert answers to Supabase."""
  
    try:
        supabase.table('answers').insert({
            'answer': anwser.lower(),
            'chapter': 5,
            'of_user': user_codes[user_id]
        }).execute()
    except Exception as e:
        print(f"Failed to insert anwsers: {e}")
        raise

def main():
    # Token bot của bạn
    TOKEN = "8174630573:AAHoOluAArZx15egGCrF4BrcWfIhGEJkV6w"
    
    # Tạo ứng dụng
    application = Application.builder().token(TOKEN).build()

    # Thêm handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("restart", restart))  # Add restart command that calls the same function as start
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_password))

    # Chạy bot
    application.run_polling()
if __name__ == "__main__":
    main()