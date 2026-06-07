import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import asyncio
import os
import json
import aiofiles
from datetime import datetime

# НАСТРОЙКА БОТА
intents = discord.Intents.default()
intents.message_content = True
intents.members = True


class AegisBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        # Регистрируем слеш-команды
        self.tree.add_command(TicketCommands())
        await self.tree.sync()
        print("[Aegis] ✓ Слеш-команды синхронизированы")


bot = AegisBot()

# КОНФИГУРАЦИЯ
TICKET_FILE = 'tickets.json'
TICKET_CATEGORY_ID = 1399869304995971316
ADMIN_ROLE_IDS = [
    1353493489526243369,  # Модератор
    1349365796970954833,  # Операционный директор
    1349365796970954834  # Генеральный Директор
]
SEND_CHANNEL_ID = 1349365797658824716
LOG_CHANNEL_ID = 1399890569165275348
TICKET_LIMIT = 1000
HISTORY_LIMIT = 10000
FOOTER_TEXT = "Aegis // Αιγίς"
GUILD_ID = 1349365796949856265

# ЗАГРУЗКА/СОХРАНЕНИЕ ДАННЫХ
async def load_tickets():
    if os.path.exists(TICKET_FILE):
        async with aiofiles.open(TICKET_FILE, 'r', encoding='utf-8') as f:
            return json.loads(await f.read())
    return {'count': 0, 'last_reset': datetime.now().strftime('%Y-%m-%d'), 'tickets': []}


async def save_tickets(data):
    async with aiofiles.open(TICKET_FILE, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(data, indent=4, ensure_ascii=False))


async def check_reset():
    tickets = await load_tickets()
    today = datetime.now()
    last_reset = datetime.strptime(tickets['last_reset'], '%Y-%m-%d')
    if today.day == 1 and today.month != last_reset.month:
        tickets['count'] = 0
        tickets['last_reset'] = today.strftime('%Y-%m-%d')
        tickets['tickets'] = []
        await save_tickets(tickets)
        print(f"[Aegis] Счётчик тикетов сброшен: {tickets['count']}, дата: {tickets['last_reset']}")
    return tickets

# ЭМБЕДЫ ДЛЯ ТИКЕТОВ
TICKET_EMBEDS = {
    "admin_complaint": {
        "title": "🛡️ А.Жалоба",
        "description": "# ЖАЛОБА НА ДОЛЖНОСТНЫХ ЛИЦ\n\nНастоящий канал предназначен для подачи официальных жалоб на действия должностных лиц ЧВК \"MSF-043\" (включая, но не ограничиваясь: Модераторы, Аналитики, Логисты, Инструкторы, Старшие оперативники, а также вышестоящий командный состав — роли <@&1353493489526243369>, <@&1353493070192050357>, <@&1353492927833178172>, <@&1349365796970954832>, <@&1349365796970954833>).\n\n## ФОРМА ЖАЛОБЫ\n### РАЗДЕЛ 1. ДАННЫЕ ЗАЯВИТЕЛЯ\n> **1.1. Позывной заявителя:**  \n> [Укажите ваш позывной, используемый на сервере Discord]\n> **1.2. Должность в ЧВК (при наличии):**  \n> [Укажите вашу должность / корпус / грейд]\n> **1.3. Срок службы в ЧВК:**  \n> [Укажите количество недель / месяцев / лет]\n\n### РАЗДЕЛ 2. СУЩЕСТВО ЖАЛОБЫ\n> **2.1. Данные должностного лица, в отношении которого подаётся жалоба:**  \n> [Укажите: позывной, никнейм в Discord, занимаемую должность]\n> **2.2. Характер нарушения:**  \n> [Опишите, что именно сделало или не сделало должностное лицо, какие нормы Регламента, Положений или должностной инструкции были нарушены]\n> **2.3. Обстоятельства инцидента (подробно):**  \n> [Изложите событие чётко, последовательно и фактологически – время, место, участники, последствия, наличие свидетелей]\n> **2.4. Доказательства:**  \n> [Приложите изображения, видеозаписи, ссылки на ресурсы, логи переписки. Если материалы блокируются системой, направьте их в личные сообщения курирующему Модератору]\n\n### РАЗДЕЛ 3. ЗАКЛЮЧЕНИЕ\nПосле заполнения всех разделов формы упомяните любое должностное лицо командного состава (<@&1349365796970954833>, <@&1349365796970954834>) или Модератора (<@&1353493489526243369>) для рассмотрения жалобы.",
        "thumbnail": "https://i.imgur.com/xeORxhD.jpeg",
        "color": 0xFF4444,
        "emoji": "🛡️"
    },
    "op_complaint": {
        "title": "👤 О.Жалоба",
        "description": "# ЖАЛОБА НА ЛИЧНЫЙ СОСТАВ\n\nНастоящий канал предназначен для подачи официальных жалоб на действия штатных оперативников ЧВК \"MSF-043\" (роли <@&1349365796949856273>, <@&1349365796949856274>).\n\n## ФОРМА ЖАЛОБЫ\n### РАЗДЕЛ 1. ДАННЫЕ ЗАЯВИТЕЛЯ\n> **1.1. Позывной заявителя:**  \n> [Укажите ваш позывной, используемый на сервере Discord или в Roblox]\n> **1.2. Должность в ЧВК (при наличии):**  \n> [Укажите вашу должность / корпус / грейд]\n> **1.3. Срок службы в ЧВК:**  \n> [Укажите количество недель / месяцев / лет]\n\n### РАЗДЕЛ 2. СУЩЕСТВО ЖАЛОБЫ\n> **2.1. Данные оперативника, в отношении которого подаётся жалоба:**  \n> [Укажите: упоминание через @, позывной, никнейм в Discord, Discord ID]\n> **2.2. Характер нарушения:**  \n> [Опишите, что именно сделал или не сделал оперативник, какие нормы Регламента или Положений были нарушены]\n> **2.3. Обстоятельства инцидента (подробно):**  \n> [Изложите событие чётко, последовательно и фактологически – время, место, участники, последствия]\n> **2.4. Доказательства:**  \n> [Приложите изображения, видеозаписи, ссылки на ресурсы. Если материалы блокируются системой, направьте их в личные сообщения курирующему Модератору]\n\n### РАЗДЕЛ 3. ЗАКЛЮЧЕНИЕ\n\nПосле заполнения всех разделов формы упомяните любое должностное лицо командного состава (<@&1349365796970954833>, <@&1349365796970954834>) или Модератора (<@&1353493489526243369>).",
        "thumbnail": "https://i.imgur.com/xeORxhD.jpeg",
        "color": 0xFFA500,
        "emoji": "👤"
    },
    "suggestion": {
        "title": "💡 Идея",
        "description": "# ПРЕДЛОЖЕНИЕ ПО РАЗВИТИЮ ЧВК\n\nНастоящий канал предназначен для подачи официальных предложений, касающихся структуры, механизмов функционирования, обновлений регламентной базы и иных аспектов деятельности ЧВК \"MSF-043\".\n\n## ФОРМА ПРЕДЛОЖЕНИЯ\n### РАЗДЕЛ 1. ДАННЫЕ ЗАЯВИТЕЛЯ\n> **1.1. Позывной заявителя:**  \n> [Укажите ваш позывной, используемый на сервере Discord]\n> **1.2. Должность в ЧВК (при наличии):**  \n> [Укажите вашу должность / корпус / грейд]\n> **1.3. Срок службы в ЧВК:**  \n> [Укажите количество недель / месяцев / лет]\n\n### РАЗДЕЛ 2. ОЦЕНКА И ПРЕДЛОЖЕНИЕ\n> **2.1. Область предложения:**  \n> [Укажите, какой именно элемент структуры или деятельности Компании затрагивает предложение: каналы связи, оформление сервера, сайт регистратуры, система грейдирования, регламенты, тактические процедуры, техническое обеспечение и т.п.]\n> **2.2. Анализ текущего состояния:**  \n> [Оцените текущее положение дел в указанной области: что работает эффективно, что требует улучшения, насколько вы удовлетворены существующим положением]\n> **2.3. Суть предложения (подробно):**  \n> [Изложите предложение развёрнуто, с указанием проблемы и способа её решения. Рекомендуется придерживаться структуры: текущая проблема → желаемое состояние → конкретные шаги по достижению]\n> **2.4. Обоснование целесообразности (при наличии):**  \n> [Поясните, почему данное предложение должно быть принято, какие выгоды или улучшения оно принесёт Компании]\n\n### РАЗДЕЛ 3. ЗАКЛЮЧЕНИЕ\nПосле заполнения всех разделов формы упомяните любое должностное лицо командного состава (<@&1349365796970954833>, <@&1349365796970954834>) или Модератора (<@&1353493489526243369>) для рассмотрения предложения.",
        "color": 0x44FF44,
        "emoji": "💡"
    },
    "registration": {
        "title": "📝 Регистрация",
        "description": "# РЕГИСТРАЦИЯ ОПЕРАТИВНИКА\n\nДля прохождения регистрации в составе ЧВК \"MSF-043\" необходимо выполнить следующие действия в строгом соответствии с установленным порядком.\n\n> **1.** Перейдите на официальный [сайт регистратуры](https://sanmein.github.io/MSF-D-Protocol/).\n> **2.** В поле \"ПОЗЫВНОЙ\" укажите ваш предпочитаемый позывной на кириллице (2–8 символов, только буквы, без цифр).\n> **3.** В поле \"DS-ID\" вставьте ваш полный Discord ID (цифровой идентификатор пользователя).\n> **4.** Выберите корпус, в который вы хотите вступить.\n> **5.** Пролистайте страницу вниз и активируйте кнопку \"СГЕНЕРИРОВАТЬ ОБА КОДА\".\n> **6.** По завершении генерации нажмите кнопку \"РЕГИСТРАЦИЯ\". Требуемые данные (позывной, маскированный DS-ID, код MSF, аудит MSF, аббревиатура корпуса) будут автоматически скопированы в буфер обмена в текстовом формате, а QR-код – в формате изображения.\n> **7.** Вернитесь в канал регистрации Discord и вставьте скопированные данные. QR-код приложите к сообщению в виде изображения.\n> **8.** По окончании процедуры упомяните любого из представителей Административного состава (<@&1349365796970954834>, <@648821656424546324>) и ожидайте подтверждения регистрации.\n\n*__При превышении разумных сроков ожидания допускается повторное упоминание Административного состава (<@&1349365796970954834>, <@648821656424546324>) для ускорения рассмотрения.__*",
        "thumbnail": "https://i.imgur.com/xeORxhD.jpeg",
        "color": 0x4488FF,
        "emoji": "📝"
    },
    "diplomacy": {
        "title": "🤝 Дипломатия",
        "description": "# Заключение дипломатии\n\nНастоящий тикет предназначен для установления и поддержания дипломатических отношений между ЧВК \"MSF-043\" и внешними субъектами.\n\n## ФОРМА ДИПЛОМАТИЧЕСКОГО ОБРАЩЕНИЯ\n### РАЗДЕЛ 1. ДАННЫЕ СУБЪЕКТА\n> **1.1. Полное наименование субъекта:**  \n> [Укажите официально зарегистрированное наименование]\n> **1.2. Тип субъекта:**  \n> [Частная военная компания / Военная организация / Государственное учреждение / Иное]\n> **1.3. Численность состава:**  \n> [Укажите количество оперативников штатного состава]\n\n### РАЗДЕЛ 2. ДАННЫЕ ПРЕДСТАВИТЕЛЯ\n> **2.1. Позывной представителя:**  \n> [Укажите ваш позывной или имя]\n> **2.2. Занимаемая должность:**  \n> [Укажите вашу должность в составе субъекта]\n> **2.3. Контактные данные:**  \n> [Discord, Roblox, иные платформы]\n\n### РАЗДЕЛ 3. ЦЕЛЬ ОБРАЩЕНИЯ\n> **3.1. Тип дипломатического запроса:**  \n> [Союз / Партнёрство / Нейтралитет / Иное]\n> **3.2. Описание предложения или запроса:**  \n> [Изложите суть дипломатического обращения]\n\n### РАЗДЕЛ 4. ЗАКЛЮЧЕНИЕ\n*После заполнения формы упомяните Генерального Директора (<@1086319338371428372>) или Операционного Директора (<@648821656424546324>) для рассмотрения дипломатического запроса*.",
        "thumbnail": "https://i.imgur.com/xeORxhD.jpeg",
        "color": 0xFFD700,
        "emoji": "🤝"
    }
}

# КЛАССЫ VIEW (КНОПКИ)
class MainTicketView(discord.ui.View):
    """Главное меню с кнопками тикетов"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🛡️ А.Жалоба", style=discord.ButtonStyle.danger, custom_id="btn_admin_complaint")
    async def admin_complaint(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await create_ticket(interaction, "admin_complaint")

    @discord.ui.button(label="👤 О.Жалоба", style=discord.ButtonStyle.primary, custom_id="btn_op_complaint")
    async def op_complaint(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await create_ticket(interaction, "op_complaint")

    @discord.ui.button(label="💡 Идея", style=discord.ButtonStyle.success, custom_id="btn_suggestion")
    async def suggestion(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await create_ticket(interaction, "suggestion")

    @discord.ui.button(label="📝 Регистрация", style=discord.ButtonStyle.primary, custom_id="btn_registration")
    async def registration(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await create_ticket(interaction, "registration")

    @discord.ui.button(label="🤝 Дипломатия", style=discord.ButtonStyle.secondary, custom_id="btn_diplomacy")
    async def diplomacy(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await create_ticket(interaction, "diplomacy")


class TicketControlView(discord.ui.View):
    """Кнопки управления в активном тикете"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Закрыть тикет", style=discord.ButtonStyle.danger, custom_id="btn_close_ticket")
    async def close_ticket_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await close_ticket(interaction)


class ClosedTicketView(discord.ui.View):
    """Кнопки управления в закрытом тикете"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔓 Открыть тикет", style=discord.ButtonStyle.success, custom_id="btn_reopen_ticket")
    async def reopen_ticket_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        # Определяем создателя тикета
        for overwrite in channel.overwrites:
            if isinstance(overwrite, discord.Member) and overwrite != interaction.guild.me:
                user = overwrite
                await channel.set_permissions(user, read_messages=True, send_messages=True)
        for role_id in ADMIN_ROLE_IDS:
            role = interaction.guild.get_role(role_id)
            if role:
                await channel.set_permissions(role, read_messages=True, send_messages=True)

        embed = discord.Embed(
            title="🔓 Тикет открыт",
            description="Тикет был открыт повторно.",
            color=0x00FF00
        )
        embed.set_footer(text=FOOTER_TEXT)
        await interaction.response.send_message(embed=embed, view=TicketControlView())

    @discord.ui.button(label="📋 Логирование", style=discord.ButtonStyle.secondary, custom_id="btn_log_ticket")
    async def log_ticket_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Проверка прав
        if not any(interaction.guild.get_role(rid) in interaction.user.roles for rid in ADMIN_ROLE_IDS):
            await interaction.response.send_message("❌ У вас нет прав для логирования тикета.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        messages = []
        async for message in interaction.channel.history(limit=HISTORY_LIMIT):
            messages.append(f'[{message.created_at.strftime("%d.%m.%Y %H:%M:%S")}] {message.author}: {message.content}')

        log_text = '\n'.join(reversed(messages))
        log_header = f'📋 Лог тикета {interaction.channel.name}\n'

        # Отправка в ЛС
        if len(log_header + log_text) > 2000:
            parts = [log_text[i:i + 1900] for i in range(0, len(log_text), 1900)]
            for i, part in enumerate(parts, 1):
                await interaction.user.send(f'{log_header}(Часть {i})\n```\n{part}\n```')
        else:
            await interaction.user.send(f'{log_header}\n```\n{log_text}\n```')

        # Отправка в лог-канал
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            if len(log_header + log_text) > 2000:
                parts = [log_text[i:i + 1900] for i in range(0, len(log_text), 1900)]
                for i, part in enumerate(parts, 1):
                    await log_channel.send(f'{log_header}(Часть {i})\n```\n{part}\n```')
            else:
                await log_channel.send(f'{log_header}\n```\n{log_text}\n```')

        await interaction.followup.send("✅ Лог тикета отправлен в ваши личные сообщения и в канал логов.",
                                        ephemeral=True)

    @discord.ui.button(label="🗑️ Удалить тикет", style=discord.ButtonStyle.danger, custom_id="btn_delete_ticket")
    async def delete_ticket_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(interaction.guild.get_role(rid) in interaction.user.roles for rid in ADMIN_ROLE_IDS):
            await interaction.response.send_message("❌ У вас нет прав для удаления тикета.", ephemeral=True)
            return
        await delete_ticket(interaction)


class CancelDeleteView(discord.ui.View):
    """Кнопка отмены удаления"""

    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="❌ Отменить удаление", style=discord.ButtonStyle.success, custom_id="btn_cancel_delete")
    async def cancel_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔒 Тикет закрыт",
            description="Тикет закрыт. Вы можете его открыть повторно или подождать удаления Администратором.",
            color=0x808080
        )
        embed.set_footer(text=FOOTER_TEXT)
        await interaction.response.edit_message(embed=embed, view=ClosedTicketView())

# ФУНКЦИИ УПРАВЛЕНИЯ ТИКЕТАМИ
async def create_ticket(interaction: discord.Interaction, ticket_type: str):
    """Создание нового тикета"""
    tickets = await check_reset()

    if tickets['count'] >= TICKET_LIMIT:
        await interaction.followup.send("❌ Достигнут лимит тикетов (1000). Дождитесь сброса в следующем месяце.",
                                        ephemeral=True)
        return

    guild = interaction.guild
    user = interaction.user

    # Проверка на существующий тикет
    ticket_prefixes = {
        "admin_complaint": "🛡・а-жалоба",
        "op_complaint": "👤・о-жалоба",
        "suggestion": "💡・идея",
        "registration": "📝・регистрация",
        "diplomacy": "🤝・дипломатия"
    }

    prefix = ticket_prefixes.get(ticket_type, ticket_type)

    # Для регистрации проверяем по имени
    if ticket_type == "registration":
        existing = discord.utils.get(guild.text_channels, name=f'{prefix}-{user.name}')
    else:
        existing = discord.utils.get(guild.text_channels, name=f'{prefix}-{user.name}')

    if existing:
        await interaction.followup.send(f'❌ У вас уже есть открытый тикет: {existing.mention}', ephemeral=True)
        return

    category = guild.get_channel(TICKET_CATEGORY_ID)
    if not category:
        await interaction.followup.send('❌ Категория для тикетов не найдена.', ephemeral=True)
        return

    embed_data = TICKET_EMBEDS[ticket_type]

    # Создание канала
    if ticket_type == "registration":
        channel_name = f'{prefix}-{user.name}'
    else:
        channel_name = f'{prefix}-{user.name}'

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    for role_id in ADMIN_ROLE_IDS:
        role = guild.get_role(role_id)
        if role:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    channel = await guild.create_text_channel(
        name=channel_name,
        category=category,
        overwrites=overwrites
    )

    # Обновление счётчика
    tickets = await check_reset()
    tickets['count'] += 1
    tickets['tickets'].append({
        'user_id': str(user.id),
        'user_name': user.name,
        'ticket_type': ticket_type,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'channel_name': channel_name
    })
    await save_tickets(tickets)

    # Отправка эмбеда в канал
    embed = discord.Embed(
        title=embed_data["title"],
        description=embed_data["description"],
        color=embed_data["color"]
    )
    embed.set_footer(text=FOOTER_TEXT)

    await channel.send(f'{user.mention}, ваш тикет создан!', embed=embed, view=TicketControlView())
    await interaction.followup.send(f'✅ Тикет создан: {channel.mention}', ephemeral=True)

    print(f"[Aegis] ✓ Тикет создан: {user.name} ({user.name}), тип: {ticket_type}, канал: {channel_name}")


async def close_ticket(interaction: discord.Interaction):
    """Закрытие тикета"""
    channel = interaction.channel

    # Закрываем доступ для создателя
    for overwrite, perms in channel.overwrites.items():
        if isinstance(overwrite, discord.Member) and overwrite != interaction.guild.me:
            await channel.set_permissions(overwrite, read_messages=True, send_messages=False)

    embed = discord.Embed(
        title="🔒 Тикет закрыт",
        description="Тикет закрыт. Вы можете его открыть повторно или подождать удаления Администратором.",
        color=0x808080
    )
    embed.set_footer(text=FOOTER_TEXT)

    await interaction.followup.send(embed=embed, view=ClosedTicketView())
    print(f"[Aegis] Тикет {channel.name} закрыт пользователем {interaction.user}")


async def delete_ticket(interaction: discord.Interaction):
    """Удаление тикета с задержкой"""
    channel = interaction.channel

    embed = discord.Embed(
        title="🗑️ Удаление...",
        description="Тикет будет удалён через 60 секунд...",
        color=0xFF0000
    )
    embed.set_footer(text=FOOTER_TEXT)

    await interaction.response.send_message(embed=embed, view=CancelDeleteView())

    # Ожидание отмены или удаление
    def check(inter):
        return inter.data.get('custom_id') == 'btn_cancel_delete' and inter.channel.id == channel.id

    try:
        await bot.wait_for('interaction', check=check, timeout=60)
        print(f"[Aegis] Удаление тикета {channel.name} отменено")
    except asyncio.TimeoutError:
        try:
            await channel.delete()
            print(f"[Aegis] Тикет {channel.name} удалён")
        except Exception as e:
            print(f"[Aegis] ✗ Ошибка при удалении тикета {channel.name}: {e}")

# СЛЕШ-КОМАНДЫ (/c)
class TicketCommands(app_commands.Group):
    def __init__(self):
        super().__init__(name="c", description="Управление тикетами")

    @app_commands.command(name="send", description="Отправить панель тикетов в канал")
    @app_commands.checks.has_any_role(*ADMIN_ROLE_IDS)
    async def send_panel(self, interaction: discord.Interaction):
        """Отправка панели с кнопками тикетов"""
        embed = discord.Embed(
            title="🎫 СИСТЕМА ТИКЕТОВ ЧВК \"MSF-043\"",
            description="Настоящий канал предназначен для открытия тикетов по установленным категориям.\n\n"
                        "## ДОСТУПНЫЕ КАТЕГОРИИ:\n"
                        "> 🛡️ **А.Жалоба** — жалобы на административный и офицерский состав\n"
                        "> 👤 **О.Жалоба** — жалобы на оперативный состав\n"
                        "> 💡 **Идея** — предложения по развитию компании\n"
                        "> 📝 **Регистрация** — регистрация в составе ЧВК\n"
                        "> 🤝 **Дипломатия** — дипломатические обращения\n\n"
                        "## ПОРЯДОК РАССМОТРЕНИЯ\n"
                        "После создания тикета и заполнения соответствующей формы необходимо упомянуть "
                        "любое должностное лицо Административного состава и ожидать ответа.\n\n"
                        "*Несоблюдение порядка подачи может привести к задержкам в рассмотрении.*",
            color=0xFFFFFF
        )
        embed.set_footer(text=FOOTER_TEXT)

        view = MainTicketView()
        await interaction.response.send_message(embed=embed, view=view)
        print(f"[Aegis] Панель тикетов отправлена пользователем {interaction.user}")

    @app_commands.command(name="clear", description="Сбросить счётчик тикетов")
    @app_commands.checks.has_any_role(*ADMIN_ROLE_IDS)
    async def clear_counter(self, interaction: discord.Interaction):
        """Сброс счётчика тикетов"""
        tickets = await load_tickets()
        old_count = tickets['count']
        tickets['count'] = 0
        tickets['last_reset'] = datetime.now().strftime('%Y-%m-%d')
        tickets['tickets'] = []
        await save_tickets(tickets)

        await interaction.response.send_message(f"✅ Счётчик тикетов сброшен. Было: {old_count}.", ephemeral=True)

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(
                f"📊 Счётчик тикетов сброшен пользователем {interaction.user.mention}. Было: {old_count}.")

    @app_commands.command(name="close", description="Закрыть текущий тикет")
    async def close_ticket_cmd(self, interaction: discord.Interaction):
        """Закрытие тикета"""
        channel = interaction.channel

        # Проверка, что это канал тикета
        valid_prefixes = ['ажалоба-', 'ожалоба-', 'идея-', 'регистрация-', 'дипломатия-']
        is_ticket = any(channel.name.startswith(p) for p in valid_prefixes)

        if not is_ticket:
            await interaction.response.send_message("❌ Эта команда работает только в каналах тикетов.", ephemeral=True)
            return

        # Проверка прав (создатель или админ)
        user_id_from_channel = None
        for overwrite in channel.overwrites:
            if isinstance(overwrite, discord.Member) and overwrite != interaction.guild.me:
                user_id_from_channel = overwrite.id
                break

        is_admin = any(interaction.guild.get_role(rid) in interaction.user.roles for rid in ADMIN_ROLE_IDS)
        is_creator = interaction.user.id == user_id_from_channel

        if not is_admin and not is_creator:
            await interaction.response.send_message("❌ У вас нет прав для закрытия этого тикета.", ephemeral=True)
            return

        await interaction.response.defer()
        await close_ticket(interaction)

    @app_commands.command(name="delete", description="Удалить тикет (только для администраторов)")
    @app_commands.checks.has_any_role(*ADMIN_ROLE_IDS)
    async def delete_ticket_cmd(self, interaction: discord.Interaction):
        """Удаление тикета"""
        channel = interaction.channel

        valid_prefixes = ['ажалоба-', 'ожалоба-', 'идея-', 'регистрация-', 'дипломатия-']
        is_ticket = any(channel.name.startswith(p) for p in valid_prefixes)

        if not is_ticket:
            await interaction.response.send_message("❌ Эта команда работает только в каналах тикетов.", ephemeral=True)
            return

        await delete_ticket(interaction)

# СОБЫТИЯ БОТА
@bot.event
async def on_ready():
    print(f"[Aegis] ✓ Бот {bot.user} готов к работе!")
    print(f"[Aegis] ✓ Серверов: {len(bot.guilds)}")

    # Регистрируем персистентные view
    bot.add_view(MainTicketView())
    bot.add_view(TicketControlView())
    bot.add_view(ClosedTicketView())
    print("[Aegis] ✓ Персистентные view зарегистрированы")


@bot.event
async def on_disconnect():
    print("[Aegis] Бот отключён от Discord")

# ЗАПУСК БОТА
async def main():
    load_dotenv()
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("[Aegis] ❌ Токен не найден. Установите переменную BOT_TOKEN в файле .env")
        return

    print(f"[Aegis] 🚀 Запуск бота...")
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        print("\n[Aegis] 👋 Остановка бота по запросу...")
        await bot.close()
    except discord.errors.LoginFailure:
        print("[Aegis] ❌ Неверный токен. Проверьте .env файл.")
    except Exception as e:
        print(f"[Aegis] ❌ Ошибка: {e}")
    finally:
        print("[Aegis] 🛑 Завершение работы...")
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
