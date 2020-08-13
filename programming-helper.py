import os
import discord
import logging
import asyncio
import json
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TOKEN')
bot = commands.Bot(command_prefix='ph!')
bot.remove_command(name='help')

# setting up logger
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

# setting the filehandler for logger
file_handler = logging.FileHandler(filename='logs/programming-helper.log', encoding='UTF-8', mode='w')
file_handler.setFormatter(logging.Formatter("%(asctime)s : %(levelname)s : %(name)s:%(message)s"))
logger.addHandler(file_handler)

# Add your discord emote id here, to add more roles for the bot
allowed_roles = {
    "typescript":739879454037508236,
    "swift":739879456671531159,
    "sql":739879455333285890,
    "rust":739879454507270246,
    "ruby":739879457388757123,
    "r_":739879455522029588,
    "php":739879457606729809,
    "perl":739879457321517077,
    "python":739879456650559538,
    "mac":739913267274842213,
    "linux":739912621989298276,
    "kotlin":739879455056592906,
    "java":739881779619561532,
    "javascript":739880009967206466, 
    "haskell":739879449901793300,
    "golang":739879449624838237,
    "erlang":739879448568004609,
    "csharp":739879447871881377,
    "cpp":739879446244491466,
    "c_":739879446642950174,
    "windows":739911639586832516
}

# Load server info, message data, user data and other info during initialization into these global variables
server_info = {}
user_data = {}
messages_data = {}
custom_roles = {}
welcome_message = {}

# Previous values to be written in file, on bot close, update from the current info
prev_messages_data = {}
prev_user_data = {}

# Load the data from the file before the bot runs
with open('files/servers.json','r') as f:
    server_info = json.load(f)

with open('files/roles.json','r') as f:
    custom_roles = json.load(f)

with open('files/users.json','r') as f:
    user_data = json.load(f)
prev_user_data.update(user_data.copy())

with open('files/messages.json','r') as f:
    messages_data = json.load(f)
prev_messages_data.update(messages_data.copy())  

with open('files/welcomes.json','r') as f:
    welcome_message = json.load(f)

# ---------------------- Bot Start - On Ready ---------------------- #

@bot.event
async def on_ready():
    update_files.start()
    logger.info(f"{bot.user.name} is online.")
    print(f"{bot.user.name} is online.")
    await bot.change_presence(activity=discord.Game(name="Coding. Command prefix: ph!"))
    
# ---------------------- Ask Command - Helper Functions ---------------------- #

async def add_reaction(message, *reactions):
    """
        Helper function to add reactions to a message.
    """
    for reaction in reactions:
        try:
            await message.add_reaction(reaction)
        except discord.HTTPException:
            await message.channel.send('Failed to add reaction due to HTTP Error, your text will be displayed but users will not be able to upvote or answer it.\nSorry for the inconvenience, please retry if needed.')
            return

async def ask_question(ctx, emb_color):
    """
        Helper function to create a question embed.
    """
    emb = discord.Embed(
        title = "Add a question:",
        description = "Type your question and send. Enter 'done' when you are done with the process. Enter 'nope' to terminate the process.",
        colour = emb_color
    )
    await ctx.send(embed=emb)

async def answer_question(channel):
    """
        Helper function to create an answer embed.
    """
    emb = discord.Embed(
        title = "Add a response/answer",
        description = "Keep on messaging your response. Enter a single word 'done' to terminate the process. Enter 'nope' to terminate the process.",
        colour = discord.Colour.gold()
    )
    await channel.send(embed=emb)

# ---------------------- Level Up - Helper Functions ---------------------- #

async def add_user_data(user, server_id):
    """
        Helper function to add user data for rank and experience updates.
    """
    prev_user_data.update(user_data)
    user_id = str(user.id)
    server_id = str(server_id)

    if not server_id in user_data.keys():
        user_data[server_id] = {}

    if not user_id in user_data[server_id]:
        user_data[server_id][user_id] = {}
        user_data[server_id][user_id]['level'] = 1
        user_data[server_id][user_id]['experience'] = 0

async def add_experience(user, exp_points, server_id):
    """
        Helper function to add/update the user.
    """
    prev_user_data.update(user_data)
    user_id = str(user.id)
    server_id = str(server_id)
    user_data[server_id][user_id]['experience'] += int(exp_points * 1000)

async def level_up(user, channel):
    """
        Helper function to update the level of the user if the conditions are met.
    """
    prev_user_data.update(user_data)
    server_id = str(channel.guild.id)
    user_id = str(user.id)

    current_experience = user_data[server_id][user_id]['experience']
    current_level = user_data[server_id][user_id]['level']
    next_level = current_level + 1
    level_EXP_required = (next_level ** 3) * 600 # Modify the formula here if needed

    if current_experience >= level_EXP_required:
        try:
            role_to_add = server_info[server_id][str(next_level)]
        except KeyError: # keyerror occurs here when the user has not setup next_level higher than the current one
            return

        role = discord.utils.find(lambda r: r.name == role_to_add, channel.guild.roles)
        await channel.send(f'{user} has levelled up to level {next_level} and has been promoted to {role}!') # comment this line out if you don't want channel to get pinged for level increase
        await user.send(f'You have levelled up to level {next_level} and have been promoted to {role}!') # comment this line out if you don't want the users to fet DM
        await user.add_roles(role)
        user_data[server_id][user_id]['level'] = next_level

async def display_rank(user, channel):
    """
        Helper function that displays the rank of the current user, used by ph!rank exclusively.
    """
    user_id = str(user.id)
    server_id = str(channel.guild.id)

    user_level = user_data[server_id][user_id]['level']
    user_exp = user_data[server_id][user_id]['experience']

    emb = discord.Embed(
        title="User Level and Experience Points",
        color=discord.Colour.green()
    )
    emb.set_author(name=user.name, icon_url=user.avatar_url)
    emb.add_field(name="User Level", value=user_level, inline=True)
    emb.add_field(name="User EXP Points", value=user_exp, inline=True)

    await channel.send(embed=emb)

# ---------------------- Background Tasks ---------------------- #

@tasks.loop(minutes=15)
async def update_files():
    """
        Run a background task that handles file handling processes and creates backups on a regular interval
    """
    temp_messages_data = {}
    temp_user_data = {}

    try:
        temp_messages_data.update(messages_data.copy())
    except (ValueError, SyntaxError):
        # If the current user data is corrupted, use previous data and set the current data to previous one
        temp_messages_data.update(prev_messages_data.copy())
        messages_data.clear()
        messages_data.update(prev_messages_data)
    
    try: 
        temp_user_data.update(user_data.copy())
    except (ValueError, SyntaxError):
        # If the current user data is corrupted, use previous data and set the current data to previous one
        temp_user_data.update(prev_user_data.copy())
        user_data.clear()
        user_data.update(prev_user_data)

    with open('files/users.json','w') as f:
        json.dump(temp_user_data,f)

    with open('files/messages.json','w') as f:
        json.dump(temp_messages_data,f)

    logger.info("15 minutes up, file backup completed!")
    print("15 minutes up, file backup completed!")

# ---------------------- Bot Commands ---------------------- #

@bot.command()
async def help(ctx):
    """
        Displays the help menu embed.\n
        Command Format: ph!help
    """
    role_list = "typescript  swift  sql  rust  ruby  php  perl  python  mac  linux  kotlin  java  javascript  haskell  golang  erlang  csharp  cpp  windows  c_  r_"
    emb = discord.Embed(
        title="Help Menu",
        colour=discord.Colour.green()
    )
    emb.add_field(name="ph!setup", value="Set the level system of the guild/server. **Command user needs to have admin access.**", inline=False)
    emb.add_field(name="ph!hardreset", value="Hard reset the bot for the particular guild/server. **Command user needs to have admin access.**", inline=False)
    emb.add_field(name="ph!ask @role", value="Ask a question about a role. :arrows_counterclockwise: to answer the question, :arrow_up: to upvote and :white_check_mark: to mark it solved. **Bot requires permissions in the channel: manage_messages=True, manage_roles=True**", inline=False)
    emb.add_field(name="ph!rank", value="See your level and exp points as of now.", inline=False)
    emb.add_field(name="ph!welcome", value="Set the welcome message for users new to the server. By default, no message is sent to the new user. **Command user needs to have admin access.**", inline=False)
    emb.add_field(name="ph!addrole @role <web-url-to-thumnail-image>", value="Add a role to/about which questions can be asked. URL to thumbnail image is optional. **Command user needs to have admin access.**", inline=False)
    emb.add_field(name="ph!delrole @role", value="Delete a role from being asked a question. The  actual server role will NOT be deleted. **Command user needs to have admin access.**", inline=False)
    emb.add_field(name="Default Roles", value=f"We provide default roles that you can add in your sever for ph!ask commands (create one of the below roles in the guild) : \n*{role_list}*", inline=False)
    await ctx.send(embed=emb)

@bot.command()
@commands.has_permissions(administrator=True)
async def reset(ctx):
    """
        Performs a hard reset of the bot. 
        User roles will not be taken away but the messages data, user experience, custom roles and server setup will be wiped.
        Use in case the bot becomes unresponsive to the commands, for a hard fix, wiping user data as well. Needs administrative access.\n
        Command Format: ph!reset
    """
    await ctx.send("Are you really sure you want to reset all bot data?\nNote: This will not take away the roles assigned by the bot but the user exp will be reset.\nEnter **yes** to continue, **nope** to cancel")
    confirmation = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=300)
    if confirmation.content.lower() == "yes":
        server_id = str(ctx.guild.id)

        # Reset data here
        messages_data[server_id] = []
        custom_roles[server_id].clear()
        user_data[server_id].clear()
        server_info[server_id].clear()
        welcome_message[server_id] = ""

        # Clean up the files
        with open('files/servers.json','w') as f:
            json.dump(server_info,f)
        
        with open('files/roles.json','w') as f:
            json.dump(custom_roles,f)

        with open('files/users.json','w') as f:
            json.dump(user_data,f)
        
        with open('files/servers.json','w') as f:
            json.dump(messages_data,f)
        
        with open('files/welcomes.json','w') as f:
            json.dump(welcome_message,f)

        await ctx.send('Reset Completed!')
        
    else:
        await ctx.send("Reset Cancelled!")
        return

@bot.command()
@commands.has_permissions(administrator=True)
async def welcome(ctx):
    """
        Set the welcome message for the user who just joined the server/guild. 
        The bot will DM the new user with the message set using this command.
        If not configured, no messages will be sent to new users.\n
        Command Format: ph!welcome
    """
    server_id = str(ctx.guild.id)
    welcome_string = ""
    if not server_id in welcome_message.keys():
        welcome_message[server_id] = {}
    
    await ctx.send("Type the strings one by one and enter 'done' when you're finished.\nEnter 'nope' to cancel.")
    while True:
        try:
            welcome = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=300)
        except asyncio.TimeoutError:
            await ctx.send("Due to no response from the user in 5 minutes, the welcome message setting process is terminated.")
            return
        
        if welcome.content.lower() == 'done':
            break
        if welcome.content.lower() == 'nope':
            welcome_string = ""
            return

        welcome_string = welcome_string + welcome.content + "\n"
    
    welcome_string = welcome_string + "\nUse ph!help in the server I am in to see my functionalities. My command prefix is: `ph!help`"
    welcome_message[server_id] = welcome_string
    with open('files/welcomes.json','w') as f:
        json.dump(welcome_message,f)
    await ctx.send("Welcome message stored successfully!")

@bot.command()
async def rank(ctx):
    """
        Displays the level and the experience point of the user who invokes the command.\n
        Command Format: ph!rank
    """
    user = ctx.message.author
    server_id = ctx.guild.id
    await add_user_data(user=user, server_id=server_id)
    await display_rank(user=user, channel=ctx.channel)

@bot.command()
@commands.has_permissions(administrator=True)
async def addrole(ctx, *message):
    """
        Add a new role to which questions can now be asked using the ph!ask command.\n
        Command Format: ph!addrole @role
    """
    role = ctx.message.role_mentions    
    server_id = str(ctx.guild.id)

    if not server_id in custom_roles.keys():
        custom_roles[server_id] = {}

    if len(role) != 1:
        await ctx.send("Please use the valid format: ```ph!addrole @role <link-optional>```")
        return
    
    if len(message) > 2:
        await ctx.send("Too many arguments!")
        return
    
    if len(message) == 2:
        _, link_message = message
        custom_roles[server_id].update({str(role[0].name) : str(link_message)})

    if len(message) == 1:
        custom_roles[server_id].update({str(role[0].name) : r'https://cdn.discordapp.com/emojis/741984835698163742'})

    with open('files/roles.json','w') as f:
        json.dump(custom_roles,f)
    await ctx.send("Role added successfully!")

@bot.command()
@commands.has_permissions(administrator=True)
async def delrole(ctx):
    """
        Delete a custom role wich you previously added using the ph!addrole command.
        The ph!ask command will no longer have access to the role.\n
        Command Format: ph!delrole @role
    """
    role = ctx.message.role_mentions    
    server_id = str(ctx.guild.id)

    if not server_id in custom_roles.keys():
        await ctx.send("No custom roles added yet.")
        return

    if len(role) != 1:
        await ctx.send("Please include at least (and not more than) one role mention!")
        return
    
    roleName = role[0].name
    try:
        custom_roles[server_id].pop(roleName)
    except KeyError:
        await ctx.send(f"{role[0].name} hasn't been added to custom roles yet.")
        return

    await ctx.send("Role access deleted successfully!")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    """
        Command to set up the server settings, particularly which channel to deploy the ph!ask capabilities, thus preventing spam in unwanted channels.
        Also sets up the levelling system and the roles to award when a user attains a certain level.\n
        Command Format: ph!setup
    """
    server_id = str(ctx.guild.id)
    role_by_level = {}
    role_by_level[server_id] = {}

    await ctx.send("Please enter the number of levels you want to set for ranking system. Default level for everyone is level 1.")
    try:
        number_of_levels = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=300)
    except asyncio.TimeoutError:
        await ctx.send("Due to no response from the user in 5 minutes, the process is terminated.")
        return

    try:
        total_levels = int(number_of_levels.content)
    except ValueError:
        await ctx.send("Please enter a valid integer/number! The process is terminated...")
        return

    for level in range(total_levels):
        await ctx.send(f"Please enter the role to be assigned when the user reaches level {level+2}")
        try:
            role_message = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=300)
        except asyncio.TimeoutError:
            await ctx.send("Due to no response from the user in 5 minutes, the process is terminated.")
            return
        
        role = role_message.role_mentions
        if len(role) != 1:
            await ctx.send("Please include at least (and not more than) one role!")
            await ctx.send("Process terminated.")
            return
        role_by_level[server_id][level+2] = role[0].name
    
    # Ask in which channel the bot has to check for reactions/emotes, the reactions in rest of the channels will be ignored
    await ctx.send("Please enter the channel where the bot is to be active #channel.")
    try:
        channel_for_bot = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=300)
    except asyncio.TimeoutError:
        await ctx.send("Due to no response from the user in 5 minutes, the process is terminated.")
        return 

    channel_mentions = channel_for_bot.channel_mentions

    if len(role) != 1:
        await ctx.send("Please include at least (and not more than) one  channel_mention! Process is terminated...")
        return

    role_by_level[server_id]["channel_id"] = channel_mentions[0].id
    server_info.update(role_by_level)

    # Since setup is only done at most once, no need to back it up in a background process continously, just run it once 
    with open('files/servers.json','w') as f:
        json.dump(server_info,f)

    await ctx.send('Setup Complete!')

@bot.command()
@commands.bot_has_permissions(manage_messages=True, manage_roles=True)
async def ask(ctx):
    """
        Ask a question about a role. Only default roles can be asked a question about, or a role added using ph!addrole.\n
        Command Format: ph!ask @role
    """
    prev_messages_data.update(messages_data.copy())
    server_id = str(ctx.guild.id)

    if not server_id in messages_data.keys():
        messages_data[server_id] = []

    try:
        if ctx.message.channel.id != server_info[server_id]["channel_id"]:
            await ctx.send("You can not use the command in this channel!\nChange target channel using ph!setup (admin acess required)")
            return
    except KeyError:
        await ctx.send("The server has not been set up yet!")
        return

    role = ctx.message.role_mentions
    author = ctx.message.author
    server_id = str(ctx.guild.id)
    
    messages_to_clean_up = [ctx.message]
    question_full_string = ""

    if len(role) != 1:
        await ctx.send("Please include at least (and not more than) one mention!")
        return

    role_name = role[0].name
    role_color = role[0].color

    in_custom_roles =  False
    try:
        in_custom_roles = role_name in custom_roles[server_id].keys()
    except KeyError:
        pass

    # Check if a query can be made about the role and if yes, then fetch the thumbnail url for the embed
    if (not role_name in allowed_roles.keys()) and (not in_custom_roles):
        await ctx.send("Question can not be asked about this role!")
        await ctx.channel.delete_messages(messages_to_clean_up)
        await asyncio.sleep(1)
        await ctx.channel.purge(limit=1)
        return

    thumbnail_url = r'https://cdn.discordapp.com/emojis/741984835698163742'
    if not in_custom_roles:
        thumbnail_url = r'https://cdn.discordapp.com/emojis/'+str(allowed_roles[role_name])
    else:
        try:
            thumbnail_url = custom_roles[server_id][role_name] or r'https://cdn.discordapp.com/emojis/'+str(allowed_roles[role_name])  
        except KeyError:
            pass
    
    # Ask for a question
    await ask_question(ctx, role_color)
    try:
        ask_message_embed = await ctx.channel.fetch_message(ctx.channel.last_message_id)
    except (discord.NotFound, discord.HTTPException):
        await ctx.send('Something went wrong, either the original message was not found or a 404 HTTP Error occured.\nSorry for the inconvenience, please retry.')
        return
    messages_to_clean_up.append(ask_message_embed)

    # Run an infinite loop until the user inputs 'done', 'nope' or timeout occurs due to no user response in 5 mins
    while True:
        try:
            question = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=300)
        except asyncio.TimeoutError:
            await ctx.send("Due to no response from the user in 5 minutes, the process is terminated.")
            await ctx.channel.delete_messages(messages_to_clean_up)
            await ctx.channel.purge(limit=1)
            return
        
        if question.content.lower() == 'done':
            messages_to_clean_up.append(question)
            break
        if question.content.lower() == 'nope':
            messages_to_clean_up.append(question)
            await ctx.channel.delete_messages(messages_to_clean_up)
            return

        question_full_string = question_full_string + question.content + "\n"
        messages_to_clean_up.append(question)

    if len(question_full_string) == 0:
        await ctx.channel.delete_messages(messages_to_clean_up)
        return

    # Create embed
    emb = discord.Embed(
        title = f'{author.display_name} has a query about : *{role_name}*',
        colour = role_color
    )
    emb.set_author(name=author.display_name, icon_url=author.avatar_url)
    emb.add_field(name="**#Question**",value=question_full_string, inline=False)
    emb.set_thumbnail(url=thumbnail_url)
    emb.set_footer(text="Upvote ⬆️ | Answer | Mark Solved")

    # Deleting the original messages and sending the embed
    await ctx.send('Cleaning up...wait for a few seconds...')
    try:
        await ctx.channel.delete_messages(messages_to_clean_up)
        await ctx.channel.purge(limit=1) # delete the most recent message
    except discord.HTTPException:
        pass

    await ctx.send(embed=emb)

    # Add emojis to the embed
    bot_message_id = ctx.channel.last_message_id
    messages_data[server_id].append(bot_message_id)

    try:
        bot_message = await ctx.channel.fetch_message(bot_message_id)
    except (discord.NotFound, discord.HTTPException):
        await ctx.send('Something went wrong, either the original message could not be fetched or a 404 HTTP Error occured.\nSorry for the inconvenience, please retry.')
        return
    await add_reaction(bot_message,'⬆️','🔄','✅')
    
    await add_user_data(user=author, server_id=server_id)
    await add_experience(user=author, exp_points=1, server_id=server_id) # provide 1 * 1000 exp_point for asking a question
    await level_up(user=author, channel=ctx.channel)

# ---------------------- Bot Events ---------------------- #

@bot.event
async def on_member_join(member):
    server_id = str(member.guild.id)
    await add_user_data(user=member, server_id=server_id)
    if len(welcome_message[server_id]) > 0:
        await member.send(welcome_message[server_id])

@bot.event
@commands.bot_has_permissions(manage_messages=True, manage_roles=True)
async def on_raw_reaction_add(payload):
    prev_messages_data.update(messages_data.copy())
    message_id, channel_id, guild_id, user_id = (payload.message_id, payload.channel_id, payload.guild_id, payload.user_id)

    if user_id == 741382171515945070: # id of the bot, ignore reaction event from bot itself
        return

    if channel_id != server_info[str(guild_id)]["channel_id"]: # not the configured channel, ignore reaction event
        return
    
    answer_full_string = ""
    messages_to_clean_up = []

    guild = discord.utils.find(lambda g: g.id == guild_id, bot.guilds)
    channel = discord.utils.find(lambda c: c.id == channel_id, guild.channels)

    if message_id in reversed(messages_data[str(guild_id)]):
        user = payload.member # Can only fetch this property for on_reaction_add
        try:
            message = await channel.fetch_message(message_id)
        except:
            await channel.send('Something went wrong, either the original message could not be fetched or a 404 HTTP Error occured.\nSorry for the inconvenience, please retry.')
            return
        
        embed_list = message.embeds
        message_embed = embed_list[0]
        message_author = message_embed.author
        original_author = discord.utils.find(lambda u: u.name == message_author.name, guild.members)

        # Handle event in case of 'upvote' emote being added
        if payload.emoji.name == '⬆️':
            if user == original_author:
                return

            # Check if there are already more than 10+ upvotes on the message, if yes, then pin it
            reactions = discord.utils.get(message.reactions, emoji=payload.emoji.name)
            if reactions and reactions.count >= 10:
                try:
                    await message.pin()
                except discord.HTTPException:
                    await channel.send(f"Message {message_id} could not be pinned because there are already more than 50 pins in this channel.")

            await add_user_data(user=original_author, server_id=guild_id)
            await add_experience(user=original_author, exp_points=0.25, server_id=guild_id) # provide 0.25 * 1000 exp_point per upvote
            await level_up(user=original_author, channel=channel)
        
        # Handle event in case of 'mark solved' being added
        if payload.emoji.name == '✅':            
            if user == original_author:
                await channel.send(f"{original_author} do you really want to mark the question completed? Doing so will close the question, making other users unable to answer/upvote to it. Enter **'yes'** to continue and **'nope'** to cancel.")                
                try:
                    bot_query = await channel.fetch_message(channel.last_message_id)
                except:
                    await channel.send('Something went wrong, either the original message could not be fetched or a 404 HTTP Error occured.\nSorry for the inconvenience, please retry.')
                    return
                messages_to_clean_up.append(bot_query)

                try:
                    user_response = await bot.wait_for('message', check=lambda message: message.author == user, timeout=300)
                except asyncio.TimeoutError:
                    await channel.send("Due to no response from the user in 5 minutes, the process is terminated.")
                    await channel.delete_messages(messages_to_clean_up)
                    await channel.purge(limit=1)
                    return
                
                if user_response.content.lower() == 'yes':
                    try:
                        await channel.purge(limit=1)
                        await channel.delete_messages(messages_to_clean_up)
                    except discord.HTTPException:
                        pass
                    await message.clear_reactions()
                    messages_data[str(guild_id)].remove(message_id)
                else:
                    await channel.purge(limit=1)
                    await channel.delete_messages(messages_to_clean_up)
                    return

        # Handle event in case of 'answer' emote being added
        if payload.emoji.name == '🔄':    
            if user == original_author:
                return
                    
            await answer_question(channel)
            try:
                ask_answer = await channel.fetch_message(channel.last_message_id)
            except:
                await channel.send('Something went wrong, either the original message could not be fetched or a 404 HTTP Error occured.\nSorry for the inconvenience, please retry.')
                return
            messages_to_clean_up.append(ask_answer)

            # Run an infinite loop until the user inputs 'done', 'nope' or timeout occurs due to no user response in 5 mins
            while True:
                try:
                    answer_message = await bot.wait_for('message', check=lambda message: message.author == user, timeout=300)
                except asyncio.TimeoutError:
                    await channel.send("Due to no response from the user in 5 minutes, the process is terminated.")
                    await channel.delete_messages(messages_to_clean_up)
                    await channel.purge(limit=1)
                    return
                
                if answer_message.content.lower() == 'done':
                    messages_to_clean_up.append(answer_message)
                    break
                if answer_message.content.lower() == 'nope':
                    messages_to_clean_up.append(answer_message)
                    await channel.delete_messages(messages_to_clean_up)
                    await message.remove_reaction('🔄',user)
                    return
                
                messages_to_clean_up.append(answer_message)
                answer_full_string = answer_full_string + answer_message.content + "\n"

            # If user inputs 'done' without entering anything before, invalidate the answer and remove the reaction
            if len(answer_full_string) == 0:
                await channel.delete_messages(messages_to_clean_up)
                await message.remove_reaction('🔄',user)
                return

            # Create an embed of the answer
            question_title = message_embed.title
            emb = discord.Embed(
                title= f"Response to: \n{question_title}",
                colour= discord.Colour.red()
            )
            emb.set_author(name=user.name, icon_url=user.avatar_url)
            emb.add_field(name='Answer in full:', value=answer_full_string, inline=False)
            emb.set_footer(text='Upvote')

            await channel.send('Cleaning up...wait for a few seconds...')
            try:
                await channel.delete_messages(messages_to_clean_up)
                await channel.purge(limit=1)
            except discord.HTTPException:
                pass
            await channel.send(embed=emb)

            # Add reactions to the answer embed
            try:
                embed_message_id = await channel.fetch_message(channel.last_message_id)
            except:
                await channel.send('Something went wrong, either the original message could not be fetched or a 404 HTTP Error occured.\nSorry for the inconvenience, please retry.')
                return
            await add_reaction(embed_message_id, '⬆️')
            messages_data[str(guild_id)].append(embed_message_id.id)
                
            # DM the user who made the request that his/her question was answered
            await original_author.send(f'{user.display_name} just answered your question!')

            await add_user_data(user=user, server_id=guild_id)
            await add_experience(user=user, exp_points=2, server_id=guild_id) # provide 2 * 1000 exp_point for answering a question
            await level_up(user=user, channel=channel)

@bot.event
@commands.bot_has_permissions(manage_messages=True, manage_roles=True)
async def on_raw_reaction_remove(payload):
    prev_messages_data.update(messages_data.copy())
    message_id, channel_id, guild_id, user_id = (payload.message_id, payload.channel_id, payload.guild_id, payload.user_id)

    if user_id == 741382171515945070: # id of the bot, ignore reactions from the bot itself
        return
    
    if channel_id != server_info[str(guild_id)]["channel_id"]: # not the configured channel, ignore reaction event
        return

    guild = discord.utils.find(lambda g: g.id == guild_id, bot.guilds)
    channel = discord.utils.find(lambda c: c.id == channel_id, guild.channels)
    user = discord.utils.find(lambda u: u.id == user_id, guild.members)

    if message_id in reversed(messages_data[str(guild_id)]):
        try:
            message = await channel.fetch_message(message_id)
        except (discord.HTTPException, discord.NotFound):
            await channel.send('Something went wrong, either the original message was not found or a 404 HTTP Error occured.\nSorry for the inconvenience, please retry.')
            return

        # Fetch info about the original embed
        embed_list = message.embeds
        message_embed = embed_list[0]
        message_author = message_embed.author
        original_author = discord.utils.find(lambda u: u.name == message_author.name, guild.members)  

        if user == original_author: # Comment this portion out if you want users to react to their own message
            return

        # Handle event in case of 'upvote' emote being removed
        if payload.emoji.name == '⬆️':  
            # Check if removing an upvote decreases upvote count to less than 10, if yes, then unpin it
            reactions = discord.utils.get(message.reactions, emoji=payload.emoji.name)
            if reactions and reactions.count < 10 and message.pinned:
                await message.unpin()     

            await add_user_data(user=original_author, server_id=guild_id)
            await add_experience(user=original_author, exp_points=-0.25, server_id=guild_id) # deduct 0.25 * 1000 exp_point per upvote
            await level_up(user=original_author, channel=channel)
        
        # Handle event in case of 'answer' emote being removed
        if payload.emoji.name == '🔄': 
            await add_user_data(user=user, server_id=guild_id)
            await add_experience(user=user, exp_points=-2, server_id=guild_id) # deduct 2 * 1000 exp_point for removing answer emote
            await level_up(user=user, channel=channel)

# ---------------------- Logger Tasks ---------------------- #

@bot.event
async def on_command_error(ctx,error):
    if isinstance(error, commands.CommandNotFound):
        logger.warning(str(error))
        return
    if isinstance(error, commands.BotMissingPermissions):
        logger.warning(str(error))
        await ctx.send('The bot does not have the required permissions for this channel.')
        return
    raise error

@bot.event
async def on_command_completion(ctx):
    logger.info(f"{ctx.invoked_with} was called successfully by {ctx.author.name}")
    return

# ---------------------- Run the bot ---------------------- #

bot.run(TOKEN)