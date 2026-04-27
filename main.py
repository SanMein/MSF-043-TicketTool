import discord
from discord.ext import commands
import asyncio
import os
from discord.ui import Button, View
import json
from datetime import datetime

# Настройка бота
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Конфигурация
TICKET_FILE = 'tickets.json'
TICKET_CATEGORY_ID = 1399869304995971316
ADMIN_ROLE_IDS = [
    1353493489526243369,  # Администратор
    1349365796970954833,  # Командный состав 1
    1349365796970954834  # Командный состав 2
]
SEND_CHANNEL_ID = 1349365797658824716
LOG_CHANNEL_ID = 1399890569165275348
TICKET_LIMIT = 1000
HISTORY_LIMIT = 10000


# Асинхронная загрузка/сохранение данных о тикетах
async def load_tickets():
    if os.path.exists(TICKET_FILE):
        async with aiofiles.open(TICKET_FILE, 'r') as f:
            return json.loads(await f.read())
    return {'count': 0, 'last_reset': datetime.now().strftime('%Y-%m-%d'), 'tickets': []}


async def save_tickets(data):
    async with aiofiles.open(TICKET_FILE, 'w') as f:
        await f.write(json.dumps(data, indent=4))


# Проверка сброса лимита тикетов
async def check_reset():
    tickets = await load_tickets()
    today = datetime.now()
    last_reset = datetime.strptime(tickets['last_reset'], '%Y-%m-%d')
    if today.day == 1 and today.month != last_reset.month:
        tickets['count'] = 0
        tickets['last_reset'] = today.strftime('%Y-%m-%d')
        tickets['tickets'] = []
        await save_tickets(tickets)
        print(
            f"[DEBUG] Счетчик тикетов сброшен автоматически: {tickets['count']} тикетов, дата сброса: {tickets['last_reset']}")
    return tickets


# Класс для кнопок тикетов
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎟・Тикет", style=discord.ButtonStyle.primary, custom_id="admin_complaint")
    async def admin_complaint_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        try:
            await create_ticket(interaction, "admin_complaint")
        except Exception as e:
            print(f"[ERROR] Ошибка при создании тикета: {e}")
            await interaction.followup.send("Произошла ошибка при создании тикета. Проверьте права бота и настройки.",
                                            ephemeral=True)

    @discord.ui.button(label="🎫・Тикет", style=discord.ButtonStyle.primary, custom_id="op_complaint")
    async def op_complaint_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        try:
            await create_ticket(interaction, "op_complaint")
        except Exception as e:
            print(f"[ERROR] Ошибка при создании тикета: {e}")
            await interaction.followup.send("Произошла ошибка при создании тикета. Проверьте права бота и настройки.",
                                            ephemeral=True)

    @discord.ui.button(label="💡・Тикет", style=discord.ButtonStyle.primary, custom_id="suggestion")
    async def suggestion_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        try:
            await create_ticket(interaction, "suggestion")
        except Exception as e:
            print(f"[ERROR] Ошибка при создании тикета: {e}")
            await interaction.followup.send("Произошла ошибка при создании тикета. Проверьте права бота и настройки.",
                                            ephemeral=True)

    @discord.ui.button(label="🔗・Тикет", style=discord.ButtonStyle.primary, custom_id="registration")
    async def registration_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        try:
            await create_ticket(interaction, "registration")
        except Exception as e:
            print(f"[ERROR] Ошибка при создании тикета: {e}")
            await interaction.followup.send("Произошла ошибка при создании тикета. Проверьте права бота и настройки.",
                                            ephemeral=True)


# Класс для кнопок в тикетах
class TicketControlView(View):
    def __init__(self, ticket_type: str):
        super().__init__(timeout=None)
        self.ticket_type = ticket_type

    @discord.ui.button(label="⭕・Закрыть тикет", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_button(self, interaction: discord.Interaction, button: Button):
        print(f"[DEBUG] Пользователь {interaction.user} нажал кнопку закрытия в канале {interaction.channel.name}")
        await interaction.response.defer()
        try:
            await close_ticket(interaction, self.ticket_type)
        except discord.errors.Forbidden:
            print(f"[ERROR] Недостаточно прав для изменения канала {interaction.channel.name}")
            await interaction.followup.send("У бота нет прав для закрытия тикета. Обратитесь к администратору.",
                                            ephemeral=True)
        except Exception as e:
            print(f"[ERROR] Ошибка при закрытии тикета: {e}")
            await interaction.followup.send("Произошла ошибка при закрытии тикета.", ephemeral=True)


# Класс для кнопок в закрытых тикетах
class ClosedTicketView(View):
    def __init__(self, ticket_type: str):
        super().__init__(timeout=None)
        self.ticket_type = ticket_type

    @discord.ui.button(label="❎・Открыть тикет", style=discord.ButtonStyle.success, custom_id="reopen_ticket")
    async def reopen_button(self, interaction: discord.Interaction, button: Button):
        channel = interaction.channel
        user_id = int(channel.name.split('-')[-1])
        user = interaction.guild.get_member(user_id)
        if user:
            await channel.set_permissions(user, read_messages=True, send_messages=True)
        for role_id in ADMIN_ROLE_IDS:
            role = interaction.guild.get_role(role_id)
            if role:
                await channel.set_permissions(role, read_messages=True, send_messages=True)
        await interaction.response.send_message("Тикет открыт повторно.")
        print(f"[DEBUG] Тикет {channel.name} открыт повторно пользователем {interaction.user}")

    @discord.ui.button(label="🛑・Логирование", style=discord.ButtonStyle.secondary, custom_id="log_ticket")
    async def log_button(self, interaction: discord.Interaction, button: Button):
        if not any(interaction.guild.get_role(role_id) in interaction.user.roles for role_id in ADMIN_ROLE_IDS):
            await interaction.response.send_message("У вас нет прав для логирования тикета.", ephemeral=True)
            return

        messages = []
        async for message in interaction.channel.history(limit=HISTORY_LIMIT):
            messages.append(f'[{message.created_at}] {message.author}: {message.content}')
        log = '\n'.join(reversed(messages))
        log_message = f'Лог тикета {interaction.channel.name}:\n'

        if len(log_message + log) > 2000:
            parts = [log[i:i + 1900] for i in range(0, len(log), 1900)]
            for i, part in enumerate(parts, 1):
                await interaction.user.send(f'{log_message} (Часть {i})\n```\n{part}\n```')
        else:
            await interaction.user.send(f'{log_message}\n```\n{log}\n```')

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            if len(log_message + log) > 2000:
                parts = [log[i:i + 1900] for i in range(0, len(log), 1900)]
                for i, part in enumerate(parts, 1):
                    await log_channel.send(f'{log_message} (Часть {i})\n```\n{part}\n```',
                                           allowed_mentions=discord.AllowedMentions.none())
            else:
                await log_channel.send(f'{log_message}\n```\n{log}\n```',
                                       allowed_mentions=discord.AllowedMentions.none())

        await interaction.response.send_message("Лог тикета отправлен в ваши личные сообщения и в канал логов.",
                                                ephemeral=True)
        print(f"[DEBUG] Лог тикета {interaction.channel.name} отправлен пользователю {interaction.user}")

    @discord.ui.button(label="⭕・Удалить тикет", style=discord.ButtonStyle.danger, custom_id="delete_ticket")
    async def delete_button(self, interaction: discord.Interaction, button: Button):
        if not any(interaction.guild.get_role(role_id) in interaction.user.roles for role_id in ADMIN_ROLE_IDS):
            await interaction.response.send_message("У вас нет прав для удаления тикета.", ephemeral=True)
            return
        await delete_ticket(interaction)


# Класс для кнопки отмены удаления
class CancelDeleteView(View):
    def __init__(self, ticket_type: str):
        super().__init__(timeout=60)
        self.ticket_type = ticket_type

    @discord.ui.button(label="❌・Отменить удаление", style=discord.ButtonStyle.success, custom_id="cancel_delete")
    async def cancel_delete_button(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title=f"{self.ticket_type}・Тикет жалобы" if self.ticket_type in ["🎟",
                                                                              "🎫"] else "💡・Тикет предложений" if self.ticket_type == "💡" else "🔗・Тикет регистрации",
            description="Тикет закрыт. Вы можете его открыть повторно или подождать удаления Администратором.",
            color=16777215
        )
        embed.set_footer(
            text="MSF-043 TicketTool"
        )
        await interaction.response.edit_message(embed=embed, view=ClosedTicketView(self.ticket_type))
        print(f"[DEBUG] Удаление тикета {interaction.channel.name} отменено пользователем {interaction.user}")


# Функция создания тикета
async def create_ticket(interaction_or_ctx, ticket_type: str):
    tickets = await check_reset()
    if tickets['count'] >= TICKET_LIMIT:
        if hasattr(interaction_or_ctx, 'response'):
            await interaction_or_ctx.followup.send(
                "Достигнут лимит тикетов (1000). Дождитесь сброса в следующем месяце.", ephemeral=True)
        else:
            await interaction_or_ctx.send("Достигнут лимит тикетов (1000). Дождитесь сброса в следующем месяце.")
        return

    guild = interaction_or_ctx.guild if hasattr(interaction_or_ctx, 'guild') else interaction_or_ctx.message.guild
    user = interaction_or_ctx.user if hasattr(interaction_or_ctx, 'user') else interaction_or_ctx.author

    # Для регистрационных тикетов используем другой формат названия канала
    if ticket_type == "registration":
        existing_channel = discord.utils.get(guild.text_channels, name=f'регистрация-{user.name.lower()}')
    else:
        existing_channel = discord.utils.get(guild.text_channels, name=f'ticket-{user.id}')

    if existing_channel:
        if hasattr(interaction_or_ctx, 'response'):
            await interaction_or_ctx.followup.send(f'У вас уже есть открытый тикет: {existing_channel.mention}',
                                                   ephemeral=True)
        else:
            await interaction_or_ctx.send(f'У вас уже есть открытый тикет: {existing_channel.mention}')
        return

    category = discord.utils.get(guild.categories, id=TICKET_CATEGORY_ID)
    if not category:
        if hasattr(interaction_or_ctx, 'response'):
            await interaction_or_ctx.followup.send('Категория для тикетов не найдена. Обратитесь к администратору.',
                                                   ephemeral=True)
        else:
            await interaction_or_ctx.send('Категория для тикетов не найдена. Обратитесь к администратору.')
        return

    if ticket_type == "admin_complaint":
        channel_name = f'🎟・Жалоба-{user.id}'
        embed_data = {
            "title": "🎟・Тикет жалобы",
            "description": "# 🎟・Тикет жалобы\n\nЭтот тикет предназначен для публикаций жалобы на должностных лиц (<@&1353493489526243369>, <@&1353493070192050357>, <@&1353492927833178172>, <@&1349365796970954832>, <@&1349365796970954833>)\n\n---\n\n# АНКЕТА ДЛЯ ЗАПОЛНЕНИЯ ЖАЛОБЫ\n## ЛИЧНЫЕ ДАННЫЕ ОТЗЫВЩИКА\n1- [Общий позывной] (в DS-Сервере или свой имя)\n2- [Должность в ЧВК]\n3- [Срок службы] (количество недель/месяцев/лет)\n\n## ЖАЛОБА\n1- [На кого подаётся жалоба] (Упоминание, Позывной, Никнейм в DS, Айди)\n2- [Что именно нарушил или сделал не так на кого подаётся жалоба] (Желательно с указанием)\n3- [Сама причина подачи жалобы] (Подробно, чётко и ясно)\n4- [Доказательства] (Изображения, Видео, Ссылки на ресурсы и т.п.. Если блокируется, то вы должны отправить доказательства в личные сообщения курирующему вас Администратору)\n\n---\n\n***После написания жалобы упомяните любое должностное лицо командного состава (<@&1349365796970954833>, <@&1349365796970954834>) или любого Администратора (<@&1353493489526243369>)***",
            "color": 16777215,
            "footer": {"text": "MSF-043 TicketTool"}
        }
        emoji = "🎟"
    elif ticket_type == "op_complaint":
        channel_name = f'🎫・Жалоба-{user.name}'
        embed_data = {
            "title": "🎫・Тикет жалобы",
            "description": "#🎫・Тикет жалобы\n\nЭтот тикет предназначен для публикаций жалобы на иных оперативников (<@&1349365796949856273>, <@&1349365796949856274>)\n\n---\n\n# АНКЕТА ДЛЯ ЗАПОЛНЕНИЯ ЖАЛОБЫ\n## ЛИЧНЫЕ ДАННЫЕ ОТЗЫВЩИКА\n1- [Общий позывной] (в DS-Сервере или свой имя)\n2- [Должность в ЧВК]\n3- [Срок службы] (количество недель/месяцев/лет)\n\n## ЖАЛОБА\n1- [На кого подаётся жалоба] (Упоминание, Позывной, Никнейм в DS, Айди)\n2- [Что именно нарушил или сделал не так на кого подаётся жалоба] (Желательно с указанием)\n3- [Сама причина подачи жалобы] (Подробно, чётко и ясно)\n4- [Доказательства] (Изображения, Видео, Ссылки на ресурсы и т.п.. Если блокируется, то вы должны отправить доказательства в личные сообщения курирующему вас Администратору)\n\n---\n\n***После написания жалобы упомяните любое должностное лицо командного состава (<@&1349365796970954833>, <@&1349365796970954834>) или любого Администратора (<@&1353493489526243369>)***",
            "color": 16777215,
            "footer": {"text": "MSF-043 TicketTool"}
        }
        emoji = "🎫"
    elif ticket_type == "suggestion":
        channel_name = f'💡・Тикет-{user.name}'
        embed_data = {
            "title": "💡・Тикет предложений",
            "description": "Этот тикет предназначен для публикаций предложения по какому-либо звену, структуре или обновлениям для MSF-043.\n\n---\n\n# АНКЕТА ДЛЯ ПРЕДЛОЖЕНИЯ НА СТРУКТУРУ И УСТРОЙСТВО ЧВК MSF-043\n## ЛИЧНЫЕ ДАННЫЕ ОТЗЫВЩИКА\n1- [Общий позывной] (в DS-Сервере или свой имя)\n2- [Должность в ЧВК]\n3- [Срок службы] (количество недель/месяцев/лет)\n\n## КРАТКАЯ ОЦЕНКА И РЕКОМЕНДАЦИЯ\n1- [На чём именно строится ваше предложение] (каналы, оформление, сайт или т.п.)\n2- [Краткая оценка] (насколько довольны или как вы расцениваете этот раздел)\n3- [Само предложение] (без ограничений по количеству символов или манере речи, старайтесь подробно описать проблему и само предложение)\n\n---\n\n***После написания предложения упомяните любое должностное лицо командного состава (<@&1349365796970954833>, <@&1349365796970954834>) или любого Администратора (<@&1353493489526243369>)***",
            "color": 16777215,
            "footer": {"text": "MSF-043 TicketTool"}
        }
        emoji = "💡"
    else:  # registration
        channel_name = f'🔗・Регистрация-{user.name}'
        embed_data = {
            "title": "🔗・Тикет регистрации",
            "description": "# Регистрация\n\nЗдравия 🙌\nЧтобы пройти регистрацию вам нужно выполнить несколько шагов:\n> - Перейдите на [сайт](https://sanmein.github.io/MSF-D-Protocol/) и нажмите на кнопку \"Сгенерировать оба кода\";\n> - Скопируйте понравившиеся вам код и аудит MSF;\n> - Также скачайте также QR-Код (содержит только код и аудит MSF в текстовом формате, можете не сканировать);\n> - В этом тикете впишите ваш предпочитаемый Позывной, код MSF (который длинный) и аудит MSF (начинается на MSF-D-...) через разделитель `|`, и прикрепите ваш QR-Код.\n> - По окончанию упомяните любого из Административного состава (<@&1349365796970954834>, <@&1349365796970954833>) и ожидайте ответа.\n\n*__Если ожидаете дольше разумного, упомяните снова любого из Административного состава (<@&1349365796970954834>, <@&1349365796970954833>) и ожидайте ответа.__*\n\n*Обратите внимание! Если вы находитесь на сервере только ради Дипломатических отношений, форму заполнять не обязательно. Достаточно указать официально зарегистрированное название своего субъекта, свой позывной (+никнейм через @ если вы продвигаете Roblox), свою должность, которую вы занимаете в своём субъекте, и упомянуть Г.Д. (<@1086319338371428372>) или О.П. (<@&1349365796970954833>)",
            "color": 16777215,
            "footer": {"text": "MSF-043 Ticket Tool"}
        }
        emoji = "🔗"

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        bot.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    for role_id in ADMIN_ROLE_IDS:
        role = guild.get_role(role_id)
        if role:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)

    tickets = await check_reset()
    tickets['count'] += 1
    tickets['tickets'].append({'user_id': str(user.id), 'ticket_type': ticket_type,
                               'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                               'channel_name': channel_name})
    await save_tickets(tickets)
    print(
        f"[DEBUG] Создан тикет: user_id={user.id}, type={ticket_type}, channel={channel_name}, count={tickets['count']}")

    embed = discord.Embed(title=embed_data["title"], description=embed_data["description"], color=embed_data["color"])
    if "author" in embed_data:
        embed.set_author(name=embed_data["author"]["name"], icon_url=embed_data["author"]["icon_url"])
    if "footer" in embed_data:
        embed.set_footer(text=embed_data["footer"]["text"])

    view = TicketControlView(emoji)
    await channel.send(f'{user.mention}, ваш тикет создан!', embed=embed, view=view)
    if hasattr(interaction_or_ctx, 'response'):
        await interaction_or_ctx.followup.send(f'Тикет создан: {channel.mention}', ephemeral=True)
    else:
        await interaction_or_ctx.send(f'Тикет создан: {channel.mention}')


# Функция закрытия тикета
async def close_ticket(interaction_or_ctx, emoji: str):
    channel = interaction_or_ctx.channel if hasattr(interaction_or_ctx,
                                                    'channel') else interaction_or_ctx.message.channel
    print(f"[DEBUG] Закрытие тикета {channel.name}, emoji={emoji}")
    for overwrite in channel.overwrites:
        if overwrite is not channel.guild.default_role and overwrite is not bot.user:
            await channel.set_permissions(overwrite, read_messages=True, send_messages=False)

    if emoji == "🔗":
        title = "🔗・Тикет регистрации"
    elif emoji in ["🎟", "🎫"]:
        title = f"{emoji}・Тикет жалобы"
    else:
        title = "💡・Тикет предложений"

    embed = discord.Embed(
        title=title,
        description="Тикет закрыт. Вы можете его открыть повторно или подождать удаления Администратором.",
        color=16777215
    )
    embed.set_footer(
        text="MSF-043 TicketTool"
    )
    if hasattr(interaction_or_ctx, 'response'):
        await interaction_or_ctx.followup.send(embed=embed, view=ClosedTicketView(emoji))
    else:
        await interaction_or_ctx.send(embed=embed, view=ClosedTicketView(emoji))
    print(
        f"[DEBUG] Тикет {channel.name} закрыт пользователем {interaction_or_ctx.user if hasattr(interaction_or_ctx, 'user') else interaction_or_ctx.author}")


# Функция удаления тикета
async def delete_ticket(interaction_or_ctx):
    channel = interaction_or_ctx.channel if hasattr(interaction_or_ctx,
                                                    'channel') else interaction_or_ctx.message.channel
    embed = discord.Embed(
        title="Удаление....",
        description="Тикет будет удалён через 60 секунд....",
        color=16777215
    )
    embed.set_footer(
        text="MSF-043 TicketTool"
    )

    # Определяем эмодзи для отображения
    if "ДТ" in channel.name or "Должностой" in channel.name:
        emoji = "🎟"
    elif "ОТ" in channel.name or "Операционный" in channel.name:
        emoji = "🎫"
    elif "РТ" in channel.name:
        emoji = "💡"
    else:
        emoji = "🔗"

    message = await (interaction_or_ctx.response.send_message(embed=embed, view=CancelDeleteView(emoji)) if hasattr(
        interaction_or_ctx, 'response') else interaction_or_ctx.send(embed=embed, view=CancelDeleteView(emoji)))
    print(
        f"[DEBUG] Запланировано удаление тикета {channel.name} пользователем {interaction_or_ctx.user if hasattr(interaction_or_ctx, 'user') else interaction_or_ctx.author}")

    def check_cancel(interaction):
        return interaction.user == interaction_or_ctx.user and interaction.data.get('custom_id') == 'cancel_delete'

    try:
        await bot.wait_for('interaction', check=check_cancel, timeout=60)
        print(f"[DEBUG] Удаление тикета {channel.name} отменено пользователем")
    except asyncio.TimeoutError:
        try:
            await channel.delete()
            print(f"[DEBUG] Тикет {channel.name} успешно удалён")
        except discord.errors.Forbidden:
            print(f"[ERROR] У бота нет прав для удаления канала {channel.name}")
            if hasattr(interaction_or_ctx, 'response'):
                await interaction_or_ctx.followup.send("У бота нет прав для удаления тикета.", ephemeral=True)
            else:
                await interaction_or_ctx.send("У бота нет прав для удаления тикета.")
        except discord.errors.HTTPException as e:
            print(f"[ERROR] Ошибка при удалении тикета {channel.name}: {e}")
            if hasattr(interaction_or_ctx, 'response'):
                await interaction_or_ctx.followup.send("Произошла ошибка при удалении тикета.", ephemeral=True)
            else:
                await interaction_or_ctx.send("Произошла ошибка при удалении тикета.")
    finally:
        try:
            await message.delete()
        except discord.errors.NotFound:
            print(f"[DEBUG] Сообщение удаления для {channel.name} уже удалено")


# Команда !send
@bot.command(name="send")
async def send(ctx):
    if ctx.channel.id != SEND_CHANNEL_ID:
        await ctx.send(f'Команда `!send` работает только в канале <#{SEND_CHANNEL_ID}>.')
        return

    if not any(ctx.guild.get_role(role_id) in ctx.author.roles for role_id in ADMIN_ROLE_IDS):
        await ctx.send('У вас нет прав для выполнения этой команды. Только администраторы могут использовать `!send`.')
        return

    embed = discord.Embed(
        description="# Тикеты\n\nДанный канал предназначен для открытия тикетов по определённым категориям - Административные жалобы, Оперативные жалобы, Предложения, Регистрация.\n\n> - Чтобы открыть тикет для жалобы на Административный и Офицерский состав (<@&1349365796970954834>, <@&1349365796970954833>, <@&1353493489526243369>, <@&1353493070192050357>, <@&1353492927833178172>, <@&1438600064166789180>, <@&1349365796970954832>), нажмите на кнопку ***«🎟・Тикет»***;\n> - Чтобы открыть тикет для жалобы на Оперативный состав (<@&1349365796949856273>, <@&1349365796949856274>), нажмите на кнопку ***«🎫・Тикет»***;\n> - Чтобы открыть тикет для предложений нажмите на кнопку ***«💡・Тикет»***;\n> - Чтобы открыть тикет для регистрации вас в ЧВК, нажмите на кнопку ***«🔗・Тикет»***.\n\n*__После создания тикета и написания жалобы/предложения упомяните любое должностное лицо Административного состава (<@&1349365796970954834>, <@&1349365796970954833>, <@&1353493489526243369>) и ожидайте ответа.__*",
        color=16777215
    )
    embed.set_footer(
        text="MSF-043 TicketTool"
    )

    view = TicketView()
    await ctx.send(embed=embed, view=view)


# Команда !clear
@bot.command(name="clear")
async def clear(ctx):
    if ctx.channel.id != SEND_CHANNEL_ID:
        await ctx.send(f'Команда `!clear` работает только в канале <#{SEND_CHANNEL_ID}>.')
        return

    if not any(ctx.guild.get_role(role_id) in ctx.author.roles for role_id in ADMIN_ROLE_IDS):
        await ctx.send('У вас нет прав для выполнения этой команды. Только администраторы могут использовать !clear.')
        return

    tickets = await load_tickets()
    old_count = tickets['count']
    tickets['count'] = 0
    tickets['last_reset'] = datetime.now().strftime('%Y-%m-%d')
    tickets['tickets'] = []
    await save_tickets(tickets)

    await ctx.send('Счетчик тикетов успешно сброшен.')
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(
            f'Счетчик тикетов сброшен пользователем {ctx.author.mention}. Было тикетов: {old_count}.')
    print(f"[DEBUG] Счетчик тикетов сброшен пользователем {ctx.author}: было {old_count} тикетов, теперь 0")


# Команда !close
@bot.command(name="close")
async def close(ctx):
    if not (ctx.channel.name.startswith('ДТ-') or ctx.channel.name.startswith('ОТ-') or ctx.channel.name.startswith(
            'РТ-') or ctx.channel.name.startswith('Регистрация-')):
        await ctx.send('Эта команда работает только в канале тикета.')
        return

    if ctx.author.id == int(ctx.channel.name.split('-')[-1]) or any(
            ctx.guild.get_role(role_id) in ctx.author.roles for role_id in ADMIN_ROLE_IDS):
        if "ДТ" in ctx.channel.name:
            emoji = "🎟"
        elif "ОТ" in ctx.channel.name:
            emoji = "🎫"
        elif "РТ" in ctx.channel.name:
            emoji = "💡"
        else:
            emoji = "🔗"
        await close_ticket(ctx, emoji)
    else:
        await ctx.send('У вас нет прав для закрытия этого тикета.')


# Команда !delete
@bot.command(name="delete")
async def delete(ctx):
    if not (ctx.channel.name.startswith('ДТ-') or ctx.channel.name.startswith('ОТ-') or ctx.channel.name.startswith(
            'РТ-') or ctx.channel.name.startswith('Регистрация-')):
        await ctx.send('Эта команда работает только в канале тикета.')
        return

    if not any(ctx.guild.get_role(role_id) in ctx.author.roles for role_id in ADMIN_ROLE_IDS):
        await ctx.send(
            'У вас нет прав для выполнения этой команды. Только администраторы могут использовать `!delete`.')
        return

    await delete_ticket(ctx)


# Команда !open с выбором типа
@bot.command(name="open")
async def open(ctx, ticket_type: str = None):
    if ctx.channel.id != SEND_CHANNEL_ID:
        await ctx.send(f'Команда `!open` работает только в канале <#{SEND_CHANNEL_ID}>.')
        return

    if not any(ctx.guild.get_role(role_id) in ctx.author.roles for role_id in ADMIN_ROLE_IDS):
        await ctx.send('У вас нет прав для выполнения этой команды. Только администраторы могут использовать !open.')
        return

    if not ticket_type:
        await ctx.send(
            'Укажите тип тикета: `!open adm` (должностной), `!open op` (операционный), `!open sug` (предложения), `!open reg` (регистрация).')
        return

    ticket_type_map = {
        'adm': 'admin_complaint',
        'op': 'op_complaint',
        'sug': 'suggestion',
        'reg': 'registration'
    }
    if ticket_type not in ticket_type_map:
        await ctx.send('Неверный тип тикета. Используйте: `!open adm`, `!open op`, `!open sug`, `!open reg`.')
        return

    await create_ticket(ctx, ticket_type_map[ticket_type])


# Событие готовности бота
@bot.event
async def on_ready():
    print(f'Бот {bot.user} готов к работе!')


# Событие отключения бота
@bot.event
async def on_disconnect():
    print("Бот отключён от Discord.")


# Запуск бота
async def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("[ERROR] Токен не найден. Установите переменную окружения BOT_TOKEN в файле .env")
        return
    
    print(f"Запуск бота с токеном: {token}")
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        print("Остановка бота по запросу пользователя...")
        await bot.close()
    except discord.errors.LoginFailure:
        print("[ERROR] Неверный токен. Проверьте .env и сбросьте токен в Developer Portal.")
    except Exception as e:
        print(f"[ERROR] Произошла ошибка: {e}")
    finally:
        print("Завершение работы...")
        await bot.close()


if __name__ == "__main__":
    import aiofiles

    asyncio.run(main())