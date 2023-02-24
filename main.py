import discord
from discord.ext import commands

import sqlite3
from config import settings

import pandas as pd
from discord_slash import SlashCommand

client = commands.Bot(command_prefix = settings['PREFIX'], intents = discord.Intents.all())
slash = SlashCommand(client,sync_commands = True)
client.remove_command('help')

connection = sqlite3.connect('server.db') #creating database file
cursor = connection.cursor()


@client.event
async def on_ready():
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
        name TEXT,
        id INT,
        cash BIGINT
    )""")
    connection.commit()
    

    for guild in client.guilds: #recording users into a table
        for member in guild.members:
            if cursor.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
              for i in member.roles:
                if i.id == settings['AMBASSADOR_ROLE'] or i.id == settings['CREATOR_ROLE']:
                  cursor.execute(f"INSERT INTO users VALUES ('{member}', {member.id}, 0)")
            else:
                pass

    connection.commit()
    print('Bot connected')


@slash.slash(name="cash", description = "shows your balance")
async def cash(ctx, member: discord.Member = None): #function for checking balance
    if member is None:
        await ctx.send(embed = discord.Embed(
            description = f""":fire: **{ctx.author}**, your balance: **{cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]} ** :coin:"""))
    else:
      for i in ctx.author.roles:
        if i.id == settings['ADMIN_ROLE']:
          await ctx.send(embed = discord.Embed(
            description = f""":fire: **{member}**, your balance: **{cursor.execute("SELECT cash FROM users WHERE id = {}".format(member.id)).fetchone()[0]} ** :coin:"""))


@slash.slash(name="add", description = "Add coins", options =[{"name":"member","description": "coin receiver nickname","type":6,"required":True},{"name":"amount","description": "number of coins", "type":4,"required":True}])
@commands.has_role(settings['ADMIN_ROLE'])
async def add(ctx, member: discord.Member = None, amount: int = None): #function for adding cash
  if cursor.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
    cursor.execute(f"INSERT INTO users VALUES ('{member}', {member.id}, 0)")
  if amount < 1:
    await ctx.send(f"**{ctx.author}**, set amount >= 1", hidden = True)
  else:
    cursor.execute("UPDATE users SET cash = cash + {} WHERE id = {}".format(amount, member.id))
    connection.commit()
    channel=client.get_channel(settings['ID_TRAN'])
    await channel.send(f"✅ **{member}** received {amount} :coin:")
    await ctx.send("operation completed successfully ✅", hidden = True)


@slash.slash(name="take", description = "Take coins", options =[{"name":"member","description": "coin receiver nickname","type":6,"required":True},{"name":"amount","description": "number of coins", "type":4,"required":True}])
@commands.has_role(settings['ADMIN_ROLE'])
async def __take(ctx, member: discord.Member = None, amount = None): #function for taking cash
  if int(amount) < 1:
    await ctx.send(f"**{ctx.author}**, set amount >= 1", hidden = True)
  if cursor.execute("SELECT cash FROM users WHERE id = {} AND cash > {}".format(member.id,amount)).fetchone() is None:
    
    await ctx.send("❌Error: you cannot take more money than the user has", hidden = True)
  else:
    cursor.execute("UPDATE users SET cash = cash - {} WHERE id = {}".format(amount, member.id))
    connection.commit()
    channel=client.get_channel(settings['ID_TRAN'])
    await channel.send(f"⛔ **{member}** fined {amount} :coin:")
    await ctx.send("operation completed successfully ✅", hidden = True)


@slash.slash(name="setnull", description = "Reset balance", options =[{"name":"member","description": "choose member to reset his balance","type":6,"required":False}])
@commands.has_role(settings['ADMIN_ROLE'])
async def __setnull(ctx, member: discord.Member = None): #function for reset cash value
  if member is None:
    cursor.execute(f"UPDATE users SET cash = {0}")
    connection.commit()
    await ctx.send("⚠️ All balances cleared")
  else:
    cursor.execute("UPDATE users SET cash = {} WHERE id = {}".format(0, member.id))
    connection.commit()
    await ctx.send(f"⭕ **{member}** nulled **0** 🪙")


@slash.slash(name="getfile", description = "get db file")
@commands.has_role(settings['ADMIN_ROLE'])
async def __getfile(ctx): #function for getting excel file with database
  df = pd.read_sql('SELECT name, cash FROM users', connection)
  df.to_excel(r'result.xlsx', index=False)
  channel=client.get_channel(settings['ID_LOG'])
  await channel.send(file=discord.File('result.xlsx'))
  await ctx.send("operation completed successfully ✅", hidden = True)


@slash.slash(name="leaderboard", description = "List leaderboard", options = [{"name":"amount", "description": "amount of leaders", "type":4 ,"required":False}])
@commands.has_role(settings['ADMIN_ROLE'])
async def __leaderboard(ctx, amount: int = None): #function for printing leaderboard
  if amount is None:
    embed = discord.Embed(title = f"Top 10")
  else:
    embed = discord.Embed(title = f"Top {amount}")
  counter = 0
  if amount is None:
    for row in cursor.execute(f"SELECT name,cash FROM users ORDER BY cash DESC LIMIT 10"):
      counter += 1
      embed.add_field(
        name = f'# {counter} | `{row[0]}`',
        value = f'Balance:{row[1]}',
        inline = False                                
      )
    await ctx.send(embed = embed)
  elif int(amount) >= 1:
    for row in cursor.execute(f"SELECT name,cash FROM users ORDER BY cash DESC LIMIT {amount}"):
      counter += 1
      embed.add_field(
        name = f'# {counter} | `{row[0]}`',
        value = f'Balance:{row[1]}',
        inline = False    
      )
    await ctx.send(embed = embed)
  else:
    await ctx.send("❌Error❌", hidden = True)
  

client.run(settings['TOKEN'])