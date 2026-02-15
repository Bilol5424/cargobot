from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    """Состояния для администратора"""
    WAITING_TRACK_FOR_UPDATE = State()
    WAITING_NEW_STATUS = State()
    WAITING_ARRIVAL_DATE = State()
    WAITING_DATE_FOR_BULK_UPDATE = State()
    WAITING_BULK_STATUS = State()
    WAITING_PRODUCT_DETAILS = State()
    WAITING_PRODUCT_NAME = State()
    WAITING_PRODUCT_CATEGORY = State()
    WAITING_PRODUCT_QUANTITY = State()
    WAITING_PRODUCT_PRICE = State()
    WAITING_PRODUCT_WEIGHT = State()
    WAITING_PRODUCT_SPECIAL = State()
    WAITING_PRODUCT_COUNTRY = State()
    WAITING_DELIVERY_TYPE = State()
    WAITING_CONFIRMATION = State()

    # Массовая загрузка трек-кодов
    BULK_IMPORT_CHOICE = State()
    BULK_IMPORT_TEXT_INPUT = State()
    BULK_IMPORT_EXCEL_UPLOAD = State()
    BULK_IMPORT_MANUAL_TRACK = State()
class LanguageState(StatesGroup):
    choosing_language = State()

class ClientState(StatesGroup):
    main_menu = State()

    # Трек-коды
    track_codes_menu = State()
    check_track_code = State()
    add_pending_track_code = State()

    # Профиль
    profile_menu = State()
    edit_name = State()
    edit_region = State()

    # Адрес
    address_menu = State()

    # Калькулятор
    calculator_menu = State()
    calculator_country = State()
    calculator_dimensions = State()
    calculator_weight = State()
    calculator_result = State()

    # Доставка до дверей
    door_delivery_menu = State()
    door_delivery_track = State()
    door_delivery_name = State()
    door_delivery_phone = State()
    door_delivery_address = State()
    door_delivery_notes = State()

    # Курс
    course_menu = State()

    waiting_for_contact = State()
 
class AdminChinaState(StatesGroup):
    main_menu = State()
    add_product = State()
    bulk_update = State()
    reports_menu = State()

class AdminTajikistanState(StatesGroup):
    main_menu = State()
    confirm_arrival = State()
    update_status = State()
    door_delivery_management = State()
    reports_menu = State()
    
class AdminState(StatesGroup):
    main_menu = State()
    add_product = State()
    update_status_option = State()
    update_status_input = State()
    update_status_select = State()
    reports_menu = State()

class TrackCodeStates(StatesGroup):
    """Состояния для работы с трек-кодами"""
    WAITING_TRACK_CODE = State()
    WAITING_PRODUCT_NAME = State()
    WAITING_PRODUCT_CATEGORY = State()
    WAITING_QUANTITY = State()
    WAITING_PRICE = State()
    WAITING_WEIGHT = State()
    WAITING_DIMENSIONS = State()
    WAITING_SPECIAL_INFO = State()
    EDIT_PRODUCT = State()
    EDIT_OPTION = State()
    EDIT_VALUE = State()