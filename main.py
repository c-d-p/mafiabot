import os
import random
from collections import defaultdict
import asyncio
from discord.ext import commands
import time
from discord.utils import get

TOKEN = ""
bot = commands.Bot(command_prefix='!')

players = {}
inversePlayers = defaultdict(list)
playerHealth = {}
playersHandles = []
roles = ['mafia', 'doctor', 'villager', 'detective']
availableRoles = []
options = {'amntmafia': 2, 'amntdoctor': 1, 'amntvillager': 2, 'amntdetective': 1}

waitingDetective = 0
waitingMafia = 0
waitingDoctor = 0
pendingKill = ''
pendingSave = ''
doctorPrev = ''
currentPlayers = 0

votes = 0
yesVotes = 0
noVotes = 0

#channel ids
adminChannelId = 730358320040378499
generalChannelId = 730327537162387468
votingChannelId = 730387036283994164
guildId = 730327536646750279

#booleans
started = False
currentlyVoting = False

@bot.event
async def on_ready():
	print(f'{bot.user.name} has connected to Discord!')

@bot.command(name='init')
async def init(ctx):
	global started
	if ctx.channel.id != adminChannelId:
		pass
	else:
		print('starting')
		rsp = 'starting game. please type !ready to enter the game.'
		await bot.get_channel(generalChannelId).send(rsp)
		started = True

@bot.command(name='ready')
async def ready(ctx):
	global currentPlayers
	msgAuthor = str(ctx.message.author.id)
	if started:
		if msgAuthor not in players.keys() and msgAuthor not in playersHandles:
			currentPlayers += 1
			playersHandles.append(msgAuthor)
			rsp = f'added player {msgAuthor} ({ctx.message.author}) to the game!'
			await bot.get_channel(generalChannelId).send(rsp)
		else:
			rsp = 'You are already in the game!'
			await bot.get_channel(generalChannelId).send(rsp)

	else:
		rsp = 'No game is currently starting!'
		await bot.get_channel(generalChannelId).send(rsp)


@bot.command(name='start')
async def start(ctx):
	global players, inversePlayers, playerHealth
	#set the available roles
	for role in range(len(roles)):
		for i in range(options['amnt'+roles[role]]):
			availableRoles.append(roles[role])

	#give players role
	for player in range(len(playersHandles)):
		random.shuffle(availableRoles)
		#players[playersHandles[player]] = availableRoles[player]
		#playerHealth[playersHandles[player]] = 'alive'
		#inversePlayers[availableRoles[player]].append(playersHandles[player])
		availableRoles.pop(player)


	players = {'415431473605115904': 'detective', '710647772117729330': 'mafia', '731089141835628565': 'doctor'}
	playerHealth = {'415431473605115904': 'alive', '710647772117729330': 'alive', '731089141835628565': 'alive'}
	inversePlayers = defaultdict(list)
	inversePlayers['mafia'].append('710647772117729330')
	inversePlayers['detective'].append('415431473605115904')
	inversePlayers['doctor'].append('731089141835628565')
	#dm players role
	for handle in playersHandles:
		playerObj = ctx.guild.get_member(int(handle))

		await playerObj.create_dm()
		await playerObj.dm_channel.send(
			f'Your role is: {players[handle]}'
		)
		if options['amntmafia'] < 2:
			pass
		elif options['amntmafia'] == 3:
			for i in inversePlayers:
				print(i)
			if players[handle] == 'mafia':
				await playerObj.create_dm()
				await playerObj.dm_channel.send(
					f'The other mafias are: asdf'
				)
		elif options['amntmafia'] == 2:
			if players[handle] == 'mafia':
				for person in players:
					if person in inversePlayers['mafia'] and person != handle:
						otherMafia = ctx.guild.get_member(int(person))
						await playerObj.create_dm()
						await playerObj.dm_channel.send(
							f'The other mafia is: {otherMafia}'
						)

	await night(ctx)

async def night(ctx):
	global waitingMafia, waitingDetective, waitingDoctor, pendingKill, pendingSave
	msg = 'It is now night time.'
	await bot.get_channel(generalChannelId).send(msg)

	msg = 'Mafia, please wake up.'
	await bot.get_channel(generalChannelId).send(msg)
	
	for person in players:
		if person in inversePlayers['mafia'] and playerHealth[person] == 'alive':
			playerObj = ctx.guild.get_member(int(person))
			await playerObj.create_dm()
			await playerObj.dm_channel.send(
				'Who would you like to kill tonight?'
			)

	waitingMafia = options['amntmafia']
	while waitingMafia != 0:
		await asyncio.sleep(1)

	msg = 'Mafia, go to bed.'
	await bot.get_channel(generalChannelId).send(msg)

	msg = 'Detective, please wake up.'
	await bot.get_channel(generalChannelId).send(msg)

	for person in players:
		if person in inversePlayers['detective'] and playerHealth[person] == 'alive':
			playerObj = ctx.guild.get_member(int(person))
			await playerObj.create_dm()
			await playerObj.dm_channel.send(
				'Who would you like to investigate tonight?'
			)

	waitingDetective = options['amntdetective']
	while waitingDetective != 0:
		await asyncio.sleep(1)

	msg = 'Detective, go to bed.'
	await bot.get_channel(generalChannelId).send(msg)

	msg = 'Doctor, please wake up.'
	await bot.get_channel(generalChannelId).send(msg)

	for person in players:
		if person in inversePlayers['doctor'] and playerHealth[person] == 'alive':
			playerObj = ctx.guild.get_member(int(person))
			await playerObj.create_dm()
			await playerObj.dm_channel.send(
				'Who would you like to save tonight?'
			)

	waitingDoctor = options['amntdoctor']
	while waitingDoctor != 0:
		await asyncio.sleep(1)

	msg = 'Doctor, go to bed.'
	await bot.get_channel(generalChannelId).send(msg)

	await day(ctx)

async def day(ctx):
	global currentPlayers
	msg = 'It is now day time!'
	await bot.get_channel(generalChannelId).send(msg)

	if pendingSave == pendingKill:
		msg = 'During the night, nobody died.'
		await bot.get_channel(generalChannelId).send(msg)
	else:
		msg = f'During the night, {pendingKill} died.'
		await bot.get_channel(generalChannelId).send(msg)
		currentPlayers -= 1
		playerHealth[bot.get_guild(guildId).get_member_named(pendingKill)] = 'Dead'
		member = bot.get_guild(guildId).get_member_named(pendingKill)
		role = get(member.guild.roles, name='Dead')
		await member.add_roles(role)

	msg = 'Everyone can now discuss. You have 5 minutes, or you can end the day early.'
	await bot.get_channel(generalChannelId).send(msg)

@bot.command(name='endDay')
async def endDay(ctx):
	if ctx.channel.id != adminChannelId:
		pass
	else:
		await night(ctx)

@bot.command(name='accuse')
async def accuse(ctx, handle):
	global currentPlayers, currentlyVoting, votes
	msg = f'{handle} is being accused! They will say their defence, then vote in the voting channel for their fate.'
	await bot.get_channel(generalChannelId).send(msg)

	msg = f'If you think {handle} should die, please type yes now. If you think they should live, please type no:'
	await bot.get_channel(votingChannelId).send(msg)

	currentlyVoting = True
	for player in playerHealth:
		if playerHealth[player] == 'alive':
			member = ctx.guild.get_member(int(player))
			role = get(member.guild.roles, name='Voting')
			await member.add_roles(role)

	while currentlyVoting:
		if votes >= currentPlayers:
			if yesVotes >= currentPlayers / 2:
				msg = f'{handle} has been sentenced to death!'
				await bot.get_channel(generalChannelId).send(msg)
				currentPlayers -= 1
				playerHealth[bot.get_guild(guildId).get_member_named(handle)] = 'Dead'
				member = bot.get_guild(guildId).get_member_named(handle)
				role = get(member.guild.roles, name='Dead')
				await member.add_roles(role)
				currentlyVoting = False
			elif noVotes >= currentPlayers / 2:
				msg = f'{handle} will not die.'
				await bot.get_channel(generalChannelId).send(msg)
				currentlyVoting = False
		else:
			await asyncio.sleep(1)

@bot.event
async def on_message(message):
	global waitingMafia, waitingDetective, waitingDoctor, pendingKill, pendingSave, currentlyVoting, votes, doctorPrev, yesVotes, noVotes
	print('test'+str(currentlyVoting))
	print('message channel '+str(message.channel))
	if message.author == bot.user:
		pass
	else:
		if str(message.channel).startswith('Direct Message'):
			if waitingMafia == 2 and players[str(message.author.id)] == 'mafia':
				pendingKill = str(message.content)
				waitingMafia = 1

			elif waitingMafia == 1 and players[str(message.author.id)] == 'mafia':
				if str(message.content) == pendingKill:
					waitingMafia = 0

			elif waitingDetective == 1 and players[str(message.author.id)] == 'detective':
				mm = bot.get_guild(guildId).get_member_named(message.content)
				mm_id = mm.id
				answer = players[str(mm_id)]
				if answer != 'mafia':
					rsp = 'villager'
				else:
					rsp = 'mafia'
				await message.author.create_dm()
				await message.author.dm_channel.send(rsp)
				waitingDetective = 0

			elif waitingDoctor == 1 and players[str(message.author.id)] == 'doctor':
				if message.content == doctorPrev:
					rsp = 'You saved that person last night.'
					await message.author.create_dm()
					await message.author.dm_channel.send(rsp)
				else:
					pendingSave = str(message.content)
					doctorPrev = pendingSave
					waitingDoctor = 0

		elif str(message.channel) == 'voting' and currentlyVoting:
			print('test1')
			if message.content == 'yes':
				print('test2')
				votes += 1
				yesVotes += 1
				member = message.author
				role = get(member.guild.roles, name='Voting')
				await member.remove_roles(role)

			elif message.content == 'no':
				print('test3')
				votes += 1
				noVotes += 1
				member = message.author
				role = get(member.guild.roles, name='Voting')
				await member.remove_roles(role)

		else:
			pass
	await bot.process_commands(message)

@bot.command(name='reset')
async def reset(ctx):
	global players, inversePlayers, playersHandles, roles, availableRoles, options
	players = {}
	inversePlayers = defaultdict(list)
	playersHandles = []
	roles = ['mafia', 'doctor', 'villager', 'detective']
	availableRoles = []
	options = {'amntmafia': 2, 'amntdoctor': 1, 'amntvillager': 2, 'amntdetective': 1}



bot.run(TOKEN)
