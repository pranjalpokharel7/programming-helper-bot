# programming-helper-bot
Discord bot to assist general programmers

### Command Prefix
ph!

*Important*: Please setup the server information fist using the `ph!setup` command before you run any other command, if this is the first time you're running the bot on your guild/server

### External Libraries Needed

**discord.py**

Documentation link: (https://discordpy.readthedocs.io/en/latest/index.html) \
Installation command using pip: `pip install discord.py`

### How The Bot Works:
Ask a question using `ph!ask @role`, the bot formats your question in a neat little embed and also allows other users to respond to your query using emotes.\
When a question is answered, the original author who asked the question is sent answer in a neat embed in DM and also in the server channel.
#### Commands List (Prefix - `ph!`):
Command | Description
--------|------------
  help  |     Shows the help message
  setup   |   Setup the server settings for the bot
  rank  |   Display your current level and exp points
  ask  |  Ask a question
  welcome  |  Set the message to send to new guild users, default='None'
  addrole  |  Add a role which you can ask using ph!ask
  delrole  |  Remove the role for ph!ask command
  hardreset  |  Reset the bot for the current server
 
Default Roles
We provide default roles that you can add in your sever for ph!ask commands. Simply create one of the below roles (copy and paste the names) in the guild and keep it below the bot in the role hierarchy:\
`typescript  swift  sql  rust  ruby  php  perl  python  csharp  cpp  c_ r_  kotlin  java  javascript  haskell  golang  erlang  mac  linux  windows  `
 
### Notes:
1) Anything you want to know about the bot, launch the bot in your server and use the command `ph!help` for instructions. Create a .env file in the same folder as your main directory and add the bot token there as `TOKEN=<your-bot-token>`
2) Updates will be made on a regular basis on this repo, please inform us about any bugs you encountered while running the bot.

### Thanks to:
@Zero5620 for helping me test my bot and giving sound advice on discord bot making process. Check out his repo, he has some more bots to boast of.
