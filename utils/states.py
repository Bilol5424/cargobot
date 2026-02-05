from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    """Состояния для администратора"""
    WAITING_TRACK_FOR_UPDATE = State()
    WAITING_NEW_STATUS = State()
    WAITING_ARRIVAL_DATE = State()
    WAITING_DATE_FOR_BULK_UPDATE = State()
    WAITING_BULK_STATUS = State()
    WAITING_PRODUCT_DETAILS = State()
class LanguageState(StatesGroup):
    choosing_language = State()

class ClientState(StatesGroup):
    main_menu = State()

    # Трек-коды
    track_codes_menu = State()

    # Профиль
    profile_menu = State()
    edit_name = State()
    edit_region = State()
    
    # Адрес
    address_menu = State()
    
    # Калькулятор - исправленная версия
    calculator_menu = State()
    calculator_country = State()
    calculator_dimensions = State()
    calculator_weight = State()
    calculator_result = State()  # Добавили недостающее состояние
    
    # Доставка до дверей
    door_delivery_menu = State()
    door_delivery_track = State()
    door_delivery_name = State()
    door_delivery_phone = State()
    door_delivery_address = State()
    door_delivery_notes = State()
    
    # НОВЫЕ СОСТОЯНИЯ ДЛЯ РЕДАКТИРОВАНИЯ ТОВАРА
    edit_product_name = State()
    edit_product_desc = State()
    edit_product_quantity = State()
    edit_product_price = State()
    edit_product_weight = State()
    edit_product_category = State()
   
    # Курс
    course_menu = State()
   
    # Для редактирования товара
    edit_product_start = State()
    edit_product_menu = State()
    edit_product_name = State()
    edit_product_desc = State()
    edit_product_quantity = State()
    edit_product_price = State()
    edit_product_weight = State()
    edit_product_category = State()
    edit_product_description = State()
    # Для редактирования товара
    edit_product = State()

    # Для трек-кодов
    check_track_code = State()
    add_track_code = State()
    product_name = State()
    product_category = State()
    product_description = State()
    product_quantity = State()
    product_unit_price = State()
    product_weight = State()
    product_dimensions = State()
    product_special_info = State()
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