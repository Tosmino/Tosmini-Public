# Main file to run the bot. Includes all functionality
# Look into refactoring if possible.
from datetime import timedelta

# Import Discord dependencies
import discord
from colorama import Fore
from discord import Spotify, app_commands, utils
from discord.ext import commands

# Import ChatGPT dependencies
import log
import responses

logger = log.setup_logger(__name__)
config = responses.get_config()

# Load id values from 'log.py' into desired variables
token = config['bot-token']
guild = config['guild-id']
mod_id = config['mod-id']
stream_channel = config['stream-channel']
quote_channel = config['quote-channel']
report_channel = config['report-channel']
deletion_log_channel = config['deletion-log-channel']
spam_channel = config['spam-channel']
member_leave_channel = config['member-leave-channel']
welcome_channel = config['welcome-channel']
stream_announcement = config['stream-announcement']
role_message_id = config['role-message-id']

isPrivate = False

# Create guild object based on guild id
MY_GUILD = discord.Object(id=guild)

# MOD_ROLE should be the id value of desired moderator role
MOD_ROLE = mod_id

# Anti Spam Setup
class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.activity = discord.Activity(
            type=discord.ActivityType.watching, name="over the Tosminions")
        self.anti_spam = commands.CooldownMapping.from_cooldown(
            5, 15, commands.BucketType.member)
        self.too_many_violations = commands.CooldownMapping.from_cooldown(
            4, 60, commands.BucketType.member)
        self.synced = False
        self.added = False
        self.mod_role = MOD_ROLE
        self.role_message_id = role_message_id
        
        self.emoji_to_role = {
        discord.PartialEmoji(name='Minecraft', id=1038647794245836870): 1038649520763973692,
        discord.PartialEmoji(name='League', id=1038647793113383002): 1038649252617912400,
        discord.PartialEmoji(name='Overwatch', id=1038647795386683533): 1038648972618772561,
        discord.PartialEmoji(name='Valorant', id=1057721657181098024): 1057725308851200020,
        discord.PartialEmoji(name='Hunt', id=1057769568359153704): 1057767445013729293,
        discord.PartialEmoji(name='Junimo', id=1057769569500024914): 1057767836065464482,
        discord.PartialEmoji(name='Twitch', id=1346573864930644110): 1346569941377220658,
        discord.PartialEmoji(name='YouTube', id=1346573890796916798): 1346570024860782763,
    }

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

#region React Role Setup
    # Listens for when a user reacts to a message
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Gives a role based on a reaction emoji."""
        # Make sure that the message the user is reacting to is the one we care about.
        if payload.message_id != self.role_message_id:
            return

        # Check if we're still in the guild
        guild = self.get_guild(payload.guild_id)
        if guild is None:
            # Check if we're still in the guild and it's cached.
            return

        try:
            # Assign role_id based on which emoji is used and mapped
            role_id = self.emoji_to_role[payload.emoji]
        except KeyError:
            # If the emoji isn't the one we care about then exit as well.
            return

        # Get the role object using the id
        role = guild.get_role(role_id)
        if role is None:
            # Make sure the role still exists and is valid.
            return

        try:
            # Finally, add the role.
            await payload.member.add_roles(role)
        except discord.HTTPException:
            # If we want to do something in case of errors we'd do it here.
            pass

    # Listens for when a user removes a message reaction
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Removes a role based on a reaction emoji."""
        # Make sure that the message the user is reacting to is the one we care about.
        if payload.message_id != self.role_message_id:
            return

        guild = self.get_guild(payload.guild_id)
        if guild is None:
            # Check if we're still in the guild and it's cached.
            return

        try:
            role_id = self.emoji_to_role[payload.emoji]
        except KeyError:
            # If the emoji isn't the one we care about then exit as well.
            return

        role = guild.get_role(role_id)
        if role is None:
            # Make sure the role still exists and is valid.
            return

        # The payload for `on_raw_reaction_remove` does not provide `.member`
        # so we must get the member ourselves from the payload's `.user_id`.
        member = guild.get_member(payload.user_id)
        if member is None:
            # Make sure the member still exists and is valid.
            return

        try:
            # Finally, remove the role.
            await member.remove_roles(role)
        except discord.HTTPException:
            # If we want to do something in case of errors we'd do it here.
            pass
#endregion

#region Message Management
    # Listens for when a message is sent in the guild
    async def on_message(self, message):
        # if message author is a bot then ignore it
        if message.author.id == self.user.id:
            return

        # Print messages and authors to console REMOVED TEMPORARILY
        # print(f'Received a message from {message.author}: {message.content}')

        # If a message begins with 'Hello', bot responds hello
        if message.content.startswith('Hello') or message.content.startswith('hello'):
            # Respond to user and mention them in the response
            await message.reply(f'Hello {message.author}!', mention_author=True)

        # If a message begins with 'Goodnight', respond goodnight
        if message.content.startswith('Goodnight') or message.content.startswith('goodnight'):
            await message.reply('Sleep well gamer!', mention_author=True)

        # If message is 'ping' hit em with a 'pong'
        if (message.content == "ping" or message.content == "Pong"):
            await message.channel.send('pong')

        # If message is 'pong' schlap em with da 'ping'
        if (message.content == "pong" or message.content == "Pong"):
            await message.channel.send('ping')

        # If message contains any instance of 'rickroll', responds with link to "Never gonna give you up"
        if "rickroll" in message.content:
            await message.channel.send("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        # Anti Spam check
        if ((type(message.channel) is discord.TextChannel) and (message.channel != int(spam_channel)) and not (message.author.bot)):
            # Create a bucket
            bucket = self.anti_spam.get_bucket(message)

            # Check if spamming too quickly
            retry_after = bucket.update_rate_limit()

            # If spamming, delete message and warn user
            if retry_after:
                await message.delete()
                await message.channel.send(f"{message.author.mention}, Stop Spamming Messages!", delete_after=10)

                # Create violations bucket
                violations = self.too_many_violations.get_bucket(message)

                # Check if too many violations
                check = violations.update_rate_limit()

                # If too many violations
                if check:
                    # Timeout user for spamming
                    await message.author.timeout(timedelta(minutes=10), reason="Spamming")
                    try:
                        # Send message to user that they have been muted
                        await message.author.send("You have been muted for spamming!")
                    except:
                        pass

    # Listen for message delete
    async def on_message_delete(self, message):
        # Collect message attributes into a new message
        msg = f'Message by {message.author} was deleted from {message.channel}: {message.content}'

        # Check if message was deleted from deletion log
        if (client.get_channel(int(deletion_log_channel)) != message.channel):
            # Get deletion log channel
            channel = client.get_channel(int(deletion_log_channel))

            # Send log entry
            await channel.send(msg)

    # Listen for thread deletion
    async def on_thread_delete(self, thread):
        # Assign message that a thread has been deleted
        msg = f'Thread has been deleted: {thread.name}'

        # Get deletion log channel
        channel = client.get_channel(int(deletion_log_channel))

        # Send log message to specified channel
        await channel.send(msg)

    # Listen for a member exiting the guild
    async def on_member_remove(self, member):
        # Assign log message
        msg = f'{member.name} has left Tosminions'

        # Get desired logging channel
        channel = client.get_channel(int(member_leave_channel))

        # Send log entry to desired channel
        await channel.send(msg)

    # Listen for a member joining the guild
    async def on_member_join(member):
        # Create message for welcoming new user to server (mentions user)
        msg = f'Welcome to the server! {member.name.mention}'

        # Get desried channel object
        channel = client.get_channel(int(welcome_channel))

        # Send message to channel
        await channel.send(msg)
#endregion

#region Ticket Setup
class main(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, custom_id="close")
    async def close(self, interaction, button):
        embed = discord.Embed(
            title="Are you sure you want to close this ticket?", color=discord.Colour.blurple())
        await interaction.response.send_message(embed=embed, view=confirm(), ephemeral=True)


class ticket_launcher(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.cooldown = commands.CooldownMapping.from_cooldown(
            1, 600, commands.BucketType.member)

    @discord.ui.button(label="Create a Ticket", style=discord.ButtonStyle.blurple, custom_id="ticket_button")
    async def ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        ticket = utils.get(interaction.guild.text_channels,
                           name=f"ticket-for-{interaction.user.name.lower().replace(' ', '-')}-{interaction.user.discriminator}")
        if ticket is not None:
            await interaction.response.send_message(f"You already have a ticket open at {ticket.mention}!", ephemeral=True)
        else:
            if type(client.mod_role) is not discord.Role:
                client.mod_role = interaction.guild.get_role(int(MOD_ROLE))
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel = False),
                interaction.user: discord.PermissionOverwrite(view_channel = True, read_message_history = True, send_messages = True, attach_files = True, embed_links = True),
                interaction.guild.me: discord.PermissionOverwrite(view_channel = True, send_messages = True, read_message_history = True),
                client.mod_role: discord.PermissionOverwrite(view_channel = True, read_message_history = True, send_messages = True, attach_files = True, embed_links = True),
            }
            try:
                channel = await interaction.guild.create_text_channel(name=f"ticket-for-{interaction.user.name}-{interaction.user.discriminator}", overwrites=overwrites)
            except:
                return await interaction.response.send_message("Ticket creation failed! Make sure I have 'manage_channels' permissions!", ephemeral=True)
            # await channel.send(f"{interaction.user.mention} created a ticket!", view=main())
            await channel.send(f"{client.mod_role.mention}, {interaction.user.mention} created a ticket!", view=main())
            await interaction.response.send_message(f"I've opened a ticket for you at {channel.mention}!", ephemeral=True)


class confirm(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.red, custom_id="confirm")
    async def confirm_button(self, interaction, button):
        try:
            await interaction.channel.delete()
        except:
            await interaction.response.send_message("Channel deletion failed! Make sure I have `manage_channels` permissions!", ephemeral=True)
#endregion

# I believe this enables the use of these features and alerts server owners
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True
client = MyClient(intents=intents)

# When bot is ready
@client.event
async def on_ready():
    if not client.synced:
        client.synced = True
    if not client.added:
        client.add_view(ticket_launcher())
        client.added = True

    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')
    print(Fore.GREEN + 'Bot is live :)')
    print(Fore.WHITE)
    
    # Initialize react role id
    client.role_message_id = role_message_id

#region Homebrew
# START HOMEBREW FUNCTIONS
# *********************************************************************************************************************************************

# Listens for when a users presence (status or activity) change
@client.event
async def on_presence_update(before, after):
    if (before.status != after.status):
        # print(f"{after.name} is {after.status}")
        if ((str(after.name) == "seoulorbit") and (str(after.status) == "online")):
            await after.send('<3')

    # If the user activity changes to something other than "none" while remaining online
    if ((before.activities != after.activities) and (after.activities != None) and (before.status == after.status)):
        for activity in after.activities:
            if (activity not in before.activities):
                
                # Print change to terminal
                '''
                 if isinstance(activity, Spotify):
                     print(
                         f"{after.name} is listening to {activity.title} by {activity.artist}")
                '''

                # Announce the user is streaming to the streaming channel
                if ((str(activity.type) == "ActivityType.streaming") and (("Tosminion" in str(after.roles)) or ("Founder" in str(after.roles)))):
                    channel = client.get_channel(int(stream_channel))
                    await channel.send(f"{after.name} is live on __{activity.platform}__ playing [{activity.game}!]\({activity.url}\)")

                # Tosmino specific announcement. Good starting point for Issue #11
                elif ((str(activity.type) == "ActivityType.streaming") and (str(after.name) == "Tosmino")):
                    channel = client.get_channel(int(stream_announcement))
                    await channel.send(f"{after.name} is live on __{activity.platform}__ playing [{activity.game}!]\({activity.url}\)")

                # If one of the mods boots League, they get sent a gif in their dms. Funny but can be removed
                '''
                elif (str(activity.type) == "ActivityType.playing"):
                    print(f"{after.name} has started playing {activity.name}")
                    if (("Hoe Patrol" in str(after.roles)) and (str(activity.name) == "League of Legends")):
                        await after.send('https://tenor.com/view/minecraft-twerk-hop-on-minecraft-gif-19222374')
                '''

# Greet user with a happy hello!
@client.tree.command()
async def hello(interaction: discord.Interaction):
    """Says hello!"""
    await interaction.response.send_message(f'Hi, {interaction.user.mention}!')

# /deleteme command used to delete given message
@client.tree.command(guild=MY_GUILD, name='deleteme', description='Deletes attached message')
async def deleteme(interaction: discord.Interaction, message: discord.Member):
    # Respond that both will be deleted in 3.0 seconds
    await interaction.response.send_message('Goodbye in 3 seconds...', delete_after=3.0)

    # Delete requested message
    await message.delete()


# Privately shows the date a member has joined
@client.tree.context_menu(name='Show Join Date')
async def show_join_date(interaction: discord.Interaction, member: discord.Member):
    # The format_dt function formats the date time into a human readable representation in the official client
    await interaction.response.send_message(f'{member} joined at {discord.utils.format_dt(member.joined_at)}', ephemeral=True)

# Report a message to the moderators
@client.tree.context_menu(name='Report to Moderators')
async def report_message(interaction: discord.Interaction, message: discord.Message):
    # We're sending this response message with ephemeral=True, so only the command executor can see it
    await interaction.response.send_message(
        f'Thanks for reporting this message by {message.author.display_name} to our moderators.', ephemeral=True
    )

    # Handle report by sending it into a log channel
    log_channel = interaction.guild.get_channel(int(report_channel))

    embed = discord.Embed(
        title=f"Message Reported by {interaction.user}")
    if message.content:
        embed.description = message.content

    embed.set_author(name=message.author.display_name,
                     icon_url=message.author.display_avatar.url)
    embed.timestamp = message.created_at

    url_view = discord.ui.View()
    url_view.add_item(discord.ui.Button(label='Go to Message',
                      style=discord.ButtonStyle.url, url=message.jump_url))

    await log_channel.send(embed=embed, view=url_view)

# Quote a message
@client.tree.context_menu(name='Quote this message')
async def quote(interaction: discord.Interaction, message: discord.Message):
    author = message.author.display_name
    await interaction.response.send_message(f'This message by {author} has been immortalized in #quotes!', ephemeral = True)

    quote_location = interaction.guild.get_channel(int(quote_channel))
    await quote_location.send(f'{message.content} \n \n -{message.author.mention} {discord.utils.format_dt(message.created_at)}')


# *********************************************************************************************************************************************
# END HOMEBREW FUNCTIONS
#endregion

#region Ticket System
# START TICKETING SYSTEM
# *********************************************************************************************************************************************

# Launches the ticketing system
@client.tree.command(guild=MY_GUILD, name='ticket', description='Launches the ticketing system')
async def ticketing(interaction: discord.Interaction):
    embed = discord.Embed(
        title="If you need support, click the button below and create a ticket!", color=discord.Colour.blue())
    await interaction.channel.send(embed=embed, view=ticket_launcher())
    await interaction.response.send_message("Ticketing system launched!", ephemeral=True)

# Closes a ticket
@client.tree.command(guild=MY_GUILD, name='close', description='Closes the ticket')
async def close(interaction: discord.Interaction):
    if "ticket-for-" in interaction.channel.name:
        embed = discord.Embed(
            title="Are you sure you want to close this ticket?", color=discord.Colour.blurple())
        await interaction.response.send_message(embed=embed, view=confirm(), ephemeral=True)
    else:
        await interaction.response.send_message("This isn't a ticket!", ephemeral=True)

# Add a user to a ticket
@client.tree.command(guild=MY_GUILD, name='add', description='Adds a user to the ticket')
async def add(interaction: discord.Interaction, user: discord.Member):
    if "ticket-for-" in interaction.channel.name:
        await interaction.channel.set_permissions(user, view_channel=True, send_messages=True, attach_files=True, embed_links=True)
        await interaction.response.send_message(f"{user.mention} has been added to the ticket by {interaction.user.mention}!")
    else:
        await interaction.response.send_message("This isn't a ticket!", ephemeral=True)

# Remove a user from the ticket
@client.tree.command(guild=MY_GUILD, name='remove', description='removes a user to the ticket')
async def remove(interaction: discord.Interaction, user: discord.Member):
    if "ticket-for-" in interaction.channel.name:
        if type(client.mod_role) is not discord.Role:
            client.mod_role = interaction.guild.get_role(MOD_ROLE)
        if client.mod_role not in interaction.user.roles:
            return await interaction.response.send_message("You aren't authorized to do this!", ephemeral=True)
        if client.mod_role not in user.roles:
            await interaction.channel.set_permissions(user, overwrite=None)
            await interaction.response.send_message(f"{user.mention} has been removed from the ticket by {interaction.user.mention}!", ephemeral=True)
        else:
            await interaction.response.send_message(f"{user.mention} is a moderator!", ephemeral=True)
    else:
        await interaction.response.send_message("This isn't a ticket!", ephemeral=True)

# *********************************************************************************************************************************************
# END TICKETING SYSTEM
#endregion

#region Reaction Roles
# START REACTION ROLES
# *********************************************************************************************************************************************

# Assign a message react roles
@client.tree.context_menu(name='Set React Role')
async def assign_react_role(interaction: discord.Interaction, message: discord.Message):
    # ID of the message that can be reacted to to add/remove a role.
    print(f"Changing message id from {client.role_message_id} to {message.id}")
    responses.update_config('role-message-id', message.id)
    client.role_message_id = message.id
    client.emoji_to_role = {
        discord.PartialEmoji(name='Minecraft', id=1038647794245836870): 1038649520763973692,
        discord.PartialEmoji(name='League', id=1038647793113383002): 1038649252617912400,
        discord.PartialEmoji(name='Overwatch', id=1038647795386683533): 1038648972618772561,
        discord.PartialEmoji(name='Valorant', id=1057721657181098024): 1057725308851200020,
        discord.PartialEmoji(name='Hunt', id=1057769568359153704): 1057767445013729293,
        discord.PartialEmoji(name='Junimo', id=1057769569500024914): 1057767836065464482,
        discord.PartialEmoji(name='Twitch', id=1346573864930644110): 1346569941377220658,
        discord.PartialEmoji(name='YouTube', id=1346573890796916798): 1346570024860782763,

    }

    await interaction.response.send_message(f'This message will now be used for Role Reactions', ephemeral=True)

# Make the bot react to a message to add reactions
@client.tree.context_menu(name='Add Bot Reactions')
async def react_role_react(interaction: discord.Interaction, message: discord.Message):
    await message.add_reaction('<:Overwatch:1038647795386683533>')
    await message.add_reaction('<:League:1038647793113383002>')
    await message.add_reaction('<:Minecraft:1038647794245836870>')
    await message.add_reaction('<:Valorant:1057721657181098024>')
    await message.add_reaction('<:Hunt:1057769568359153704>')
    await message.add_reaction('<:Junimo:1057769569500024914>')
    await message.add_reaction('<:Twitch:1346573864930644110>')
    await message.add_reaction('<:YouTube:1346573890796916798>')
    await interaction.response.send_message(f'Reactions have been added!', ephemeral=True)

# Remove bot reactions to a message
@client.tree.context_menu(name='Remove Bot Reactions')
async def remove_bot_reactions(interaction: discord.Interaction, message: discord.Message):
    await message.remove_reaction('<:Overwatch:1038647795386683533>', discord.utils.get(message.guild.members, name='Tosmini'))
    await message.remove_reaction('<:League:1038647793113383002>', discord.utils.get(message.guild.members, name='Tosmini'))
    await message.remove_reaction('<:Minecraft:1038647794245836870>', discord.utils.get(message.guild.members, name='Tosmini'))
    await message.remove_reaction('<:Valorant:1057721657181098024>', discord.utils.get(message.guild.members, name='Tosmini'))
    await message.remove_reaction('<:Hunt:1057769568359153704>', discord.utils.get(message.guild.members, name='Tosmini'))
    await message.remove_reaction('<:Junimo:1057769569500024914>', discord.utils.get(message.guild.members, name='Tosmini'))
    await message.remove_reaction('<:Twitch:1346573864930644110>', discord.utils.get(message.guild.members, name='Tosmini'))
    await message.remove_reaction('<:YouTube:1346573890796916798>', discord.utils.get(message.guild.members, name='Tosmini'))
    await interaction.response.send_message(f'Reactions have been removed!', ephemeral=True)

# *********************************************************************************************************************************************
# END REACTION ROLES
#endregion

#region ChatGPT
# START CHATGPT INCORPORATION
# *********************************************************************************************************************************************

async def send_message(message, user_message):
    await message.response.defer(ephemeral=isPrivate)
    try:
        response = '> **' + user_message + '** - <@' + \
            str(message.user.id) + '>\n\n'
        response = f"{response}{user_message}{await responses.handle_response(user_message)}"
        if len(response) > 1900:
            # Split the response into smaller chunks of no more than 1900 characters each(Discord limit is 2000 per chunk)
            if "```" in response:
                # Split the response if the code block exists
                parts = response.split("```")
                # Send the first message
                await message.followup.send(parts[0])
                # Send the code block in a seperate message
                code_block = parts[1].split("\n")
                formatted_code_block = ""
                for line in code_block:
                    while len(line) > 1900:
                        # Split the line at the 50th character
                        formatted_code_block += line[:1900] + "\n"
                        line = line[1900:]
                    formatted_code_block += line + "\n"  # Add the line and seperate with new line

                # Send the code block in a separate message
                if (len(formatted_code_block) > 2000):
                    code_block_chunks = [formatted_code_block[i:i+1900]
                                         for i in range(0, len(formatted_code_block), 1900)]
                    for chunk in code_block_chunks:
                        await message.followup.send("```" + chunk + "```")
                else:
                    await message.followup.send("```" + formatted_code_block + "```")

                # Send the remaining of the response in another message

                if len(parts) >= 3:
                    await message.followup.send(parts[2])
            else:
                response_chunks = [response[i:i+1900]
                                   for i in range(0, len(response), 1900)]
                for chunk in response_chunks:
                    await message.followup.send(chunk)
        else:
            await message.followup.send(response)
    except Exception as e:
        await message.followup.send("> **Error: Something went wrong, please try again later!**")
        logger.exception(f"Error while sending message: {e}")


async def send_start_prompt(client):
    import os
    import os.path

    config_dir = os.path.abspath(__file__ + "/../../")
    prompt_name = 'starting-prompt.txt'
    prompt_path = os.path.join(config_dir, prompt_name)
    try:
        if os.path.isfile(prompt_path) and os.path.getsize(prompt_path) > 0:
            with open(prompt_path, "r") as f:
                prompt = f.read()
                logger.info(f"Send starting prompt with size {len(prompt)}")
                responseMessage = await responses.handle_response(prompt)
                if (config['discord_channel_id']):
                    channel = client.get_channel(
                        int(config['discord_channel_id']))
                    await channel.send(responseMessage)
            logger.info(f"Starting prompt response:{responseMessage}")
        else:
            logger.info(f"No {prompt_name}. Skip sending starting prompt.")
    except Exception as e:
        logger.exception(f"Error while sending starting prompt: {e}")


@client.tree.command(name="chat", description="Have a chat with ChatGPT")
async def chat(interaction: discord.Interaction, *, message: str):
        if client.is_replying_all == "True":
            await interaction.response.defer(ephemeral=False)
            await interaction.followup.send(
                "> **WARN: You already on replyAll mode. If you want to use the Slash Command, switch to normal mode by using `/replyall` again**")
            logger.warning("\x1b[31mYou already on replyAll mode, can't use slash command!\x1b[0m")
            return
        if interaction.user == client.user:
            return
        username = str(interaction.user)
        client.current_channel = interaction.channel
        logger.info(
            f"\x1b[31m{username}\x1b[0m : /chat [{message}] in ({client.current_channel})")

        await client.enqueue_message(interaction, message)


@client.tree.command(name="private", description="Toggle private access")
async def private(interaction: discord.Interaction):
    global isPrivate
    await interaction.response.defer(ephemeral=True)
    if not isPrivate:
        isPrivate = not isPrivate
        logger.warning("\x1b[31mSwitch to private mode\x1b[0m")
        await interaction.followup.send("> **Info: Next, the response will be sent via private message. If you want to switch back to public mode, use `/public`**")
    else:
        logger.info("You already on private mode!")
        await interaction.followup.send("> **Warn: You already on private mode. If you want to switch to public mode, use `/public`**")


@client.tree.command(name="public", description="Toggle public access")
async def public(interaction: discord.Interaction):
    global isPrivate
    await interaction.response.defer(ephemeral=True)
    if isPrivate:
        isPrivate = not isPrivate
        await interaction.followup.send("> **Info: Next, the response will be sent to the channel directly. If you want to switch back to private mode, use `/private`**")
        logger.warning("\x1b[31mSwitch to public mode\x1b[0m")
    else:
        await interaction.followup.send("> **Warn: You already on public mode. If you want to switch to private mode, use `/private`**")
        logger.info("You already on public mode!")


@client.tree.command(name="help", description="Show help for the bot")
async def help(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    msg = f":star:**BASIC COMMANDS** \n   `/hello` Say hello to Tosmini!\n `/deleteme` Delete this message and self destructs!\n `/chat [message]` Chat with ChatGPT!\n    `/public` ChatGPT switch to public mode \n"
    await interaction.followup.send(msg)
    logger.info(
        "\x1b[31mSomeone need help!\x1b[0m")

# *********************************************************************************************************************************************
# END CHATGPT INCORPORATION
#endregion

# Run the bot
client.run(token)
