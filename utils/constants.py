"""
Centralized constants for the SVU Helper Bot.
"""

# --- STATUS CONSTANTS ---
# --- STATUS CONSTANTS ---
STATUS_PENDING = 'قيد المراجعة'  # Pending Review
STATUS_ACCEPTED = 'قيد التنفيذ'  # Work in Progress / Accepted
STATUS_AWAITING_VERIFICATION = 'بانتظار التحقق'
STATUS_FINISHED = 'منتهى'
STATUS_OFFERED = 'تم تقديم عرض'
STATUS_REJECTED_PAYMENT = 'مرفوض: مشكلة في الدفع'
STATUS_DENIED_ADMIN = 'مرفوض من المشرف'
STATUS_DENIED_STUDENT = 'ملغى من الطالب'

# --- MESSAGES ---
MSG_WELCOME = (
    "👋 مرحباً! استخدم القائمة أدناه لإدارة مشاريعك.\n\n"
    "الأوامر المتاحة:\n"
    "/new_project - تقديم مشروع جديد\n"
    "/my_projects - عرض مشاريعي\n"
    "/my_offers - عرض العروض المستلمة\n"
    "/help - المساعدة\n"
    "/cancel - إلغاء العملية الحالية"
)

MSG_HELP = (
    "ℹ️ **الأوامر المتاحة:**\n\n"
    "📚 **المشاريع:**\n"
    "/new_project - تقديم طلب مشروع جديد\n\n"
    "📊 **إدارة المشاريع:**\n"
    "/my_projects - استعراض حالة مشاريعي\n"
    "/my_offers - استعراض العروض المقدمة لي\n\n"
    "🛠 **أخرى:**\n"
    "/cancel - إلغاء العملية\n"
    "/start - القائمة الرئيسية"
)

MSG_CANCELLED = "🚫 تم الإلغاء."
MSG_NO_ACTIVE_PROCESS = "❌ لا توجد عملية نشطة للإلغاء."

# --- MENU BUTTONS ---
BTN_NEW_PROJECT = "📚 مشروع جديد"
BTN_MY_PROJECTS = "📂 مشاريعي"
BTN_MY_OFFERS = "🎁 عروضي"
