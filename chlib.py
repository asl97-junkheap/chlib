################################
#File: chlib.py
#Made by: cellsheet
#Description: My take on a flexable chatango library.
#Contact: piks.chatango.com, cellsheet.chatango.com, or sorch.chatango.com.
#Release date: 7/31/2013
#Version: 1.7
################################

################################
#Python Imports
################################

import socket
import select
import time
import re
import urllib.request
import random
import threading
import queue

import ping
import sock

################################
#Get server number
################################

weights = [['5', 75], ['6', 75], ['7', 75], ['8', 75], ['16', 75], ['17', 75], ['18', 75], ['9', 95], ['11', 95], ['12', 95], ['13', 95], ['14', 95], ['15', 95], ['19', 110], ['23', 110], ['24', 110], ['25', 110], ['26', 110], ['28', 104], ['29', 104], ['30', 104], ['31', 104], ['32', 104], ['33', 104], ['35', 101], ['36', 101], ['37', 101], ['38', 101], ['39', 101], ['40', 101], ['41', 101], ['42', 101], ['43', 101], ['44', 101], ['45', 101], ['46', 101], ['47', 101], ['48', 101], ['49', 101], ['50', 101], ['52', 110], ['53', 110], ['55', 110], ['57', 110], ['58', 110], ['59', 110], ['60', 110], ['61', 110], ['62', 110], ['63', 110], ['64', 110], ['65', 110], ['66', 110], ['68', 95], ['71', 116], ['72', 116], ['73', 116], ['74', 116], ['75', 116], ['76', 116], ['77', 116], ['78', 116], ['79', 116], ['80', 116], ['81', 116], ['82', 116], ['83', 116], ['84', 116]]
specials = {"de-livechat": 5, "ver-anime": 8, "watch-dragonball": 8, "narutowire": 10, "dbzepisodeorg": 10, "animelinkz": 20, "kiiiikiii": 21, "soccerjumbo": 21, "vipstand": 21, "cricket365live": 21, "pokemonepisodeorg": 22, "watchanimeonn": 22, "leeplarp": 27, "animeultimacom": 34, "rgsmotrisport": 51, "cricvid-hitcric-": 51, "tvtvanimefreak": 54, "stream2watch3": 56, "mitvcanal": 56, "sport24lt": 56, "ttvsports": 56, "eafangames": 56, "myfoxdfw": 67, "peliculas-flv": 69, "narutochatt": 70}

def getServer(group):
	'''Return server number'''
	if group in specials.keys():
		return specials[group]
	group = re.sub("-|_", "q", group)
	wt, gw = sum([n[1] for n in weights]), 0
	num1 = 1000 if len(group) < 7 else max(int(group[6:9], 36), 1000)
	num2 = (int(group[:5],36) % num1) / num1
	for i, v in weights:
		gw += v / wt
		if gw >= num2:
			return i
	return None

################################
#Generate Auth/Anon ID
################################

class Generate:

	@staticmethod
	def aid(n, uid):
		'''Generate anon ID'''
		n, uid = str(n).split(".")[0], str(uid)  # Fault-Tolerance
		try:
			if int(n) == 0 or len(n) < 4:
				n = "3452"
		except:
			n = "3452"
		n = n[-4:]
		an, u = "", str(uid)[4:][:4]
		z = list(zip(n, u))
		for i, v in z:
			an += str(int(i) + int(v))[-1]
		return an

	@staticmethod
	def auth(pm):
		'''Generate auth token'''
		auth = urllib.request.urlopen("http://chatango.com/login",
			urllib.parse.urlencode({
			"user_id": pm.user,
			"password": pm.password,
			"storecookie": "on",
			"checkerrors": "yes" }).encode()
			).getheader("Set-Cookie")
		try:
			return re.search("auth.chatango.com=(.*?);", auth).group(1)
		except:
			return None

################################
#Represents event objects
################################

class Event(object):

	def __init__(self, manager, group, name, interval, delay, target, *args):
		self.manager = manager
		self.name = name
		self.interval = interval
		self.delay = delay
		self.target = target
		self.group = group
		if hasattr(self.group, self.target) and not self.manager.getEvent(self.group, self.name):
			if self.interval > 0:
				self.loop = True
				self.thread = threading.Timer(interval, self.create, args=(args))
				self.thread.name = self.name
			else:
				self.loop = False
				self.thread = threading.Thread(target=self.create, name=self.name, args=(args))
			self.active = True
			self.thread.daemon = True
			self.thread.start()
			self.manager.eArray[self.group.name].append(self)

	def create(self, *args):
		if self.delay > 0:
			time.sleep(self.delay)
		if self.loop:
			while self.active:
				getattr(self.group, self.target)(*args)
				time.sleep(self.interval)
		else:
			getattr(self.group, self.target)(*args)

	def cancel(self):
		self.active = False
		self.manager.eArray[self.group.name].remove(self)

################################
#Represents connection objects
################################

class Group(object):

	def __init__(self, manager, group, user, password, uid, pm):

		self.manager = manager
		self.name = group
		self.user = user.lower()
		self.password = password
		self.time = None
		self.pm = pm
		self.chSocket = None
		self.wqueue = self.manager.sockmanager.write_queue
		self.manager.eArray[self.name] = list()
		self.loginFail = False
		self.uid = str(int(random.randrange(10 ** 15, (10 ** 16) - 1)))
		self.fSize = "11"
		self.fFace = "0"
		self.fColor = "000"
		self.connected = False
		if self.name != self.user: #group variables
			self.nColor = "CCC"
			self.snum = getServer(group)
			self.limit = 0
			self.limited = 0
			self.unum = None
			self.pArray = {}
			self.uArray = {}
			self.users = list()
			self.bw = list()
			self.mods = list()
			self.owner = None
			self.blist = list()
			self.nomore = False # Change to 'True' to only load recent posts on join. Posts that are not loaded will not be added to pArray, and cannot be deleted directly
		else: #PM variables
			self.nColor = "000"
			self.pmAuth = None
			self.ip = None
			self.fl = list()
			self.bl = list()
			self.prefix = None
		self.connect()

	def connect(self):
		'''connect to socket'''
		self.chSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.chSocket.setblocking(True)
		if self.name != self.user:
			self.chSocket.connect(("s"+str(self.snum)+".chatango.com", 443))
			self.sendCmd("bauth", self.name, self.uid, self.user, self.password, firstcmd=True)
		else:
			self.chSocket.connect(("c1.chatango.com", 5222))
			self.pmAuth = Generate.auth(self)
			self.sendCmd("tlogin", self.pmAuth, "2", self.uid, firstcmd=True)
		self.connected = True
		self.manager.connected = True
		self.manager.eArray[self.name].append(self.manager.sockmanager.addSock(self.chSocket, self))
		self.manager.eArray[self.name].append(ping.add(self.ping))

	def manage(self):
		rbuf = b""
		wbuf = b""
		try:
			rSock, wSock, eSock = select.select([self.chSocket], [self.chSocket], [self.chSocket])
		except:
			self.manager.removeGroup(self)
		if wSock:
			try:
				wbuf = self.wqueue.get_nowait()
				self.chSocket.send(wbuf)
			except queue.Empty:
				pass
			except socket.error:
				self.manager.removeGroup(self)
			except:
				self.manager.removeGroup(self)
		if rSock:
			while not rbuf.endswith(b'\x00'):
				try:
					rbuf += self.chSocket.recv(1024) #need the WHOLE buffer ;D
				except:
					self.manager.removeGroup(self.name)
			if len(rbuf) > 0:
				self.manager.manage(self, rbuf)

	def ping(self):
		'''Ping? Pong!'''
		self.sendCmd("\r\n\x00")

	def cleanPM(self, pm):
		'''Clean's all PM XML'''
		return re.sub("<(.*?)>", "", pm)

	def sendPost(self, post, html = True):
		'''Send a post to the group'''
		if not html:
			post = post.replace("<", "&lt;").replace(">", "&gt;")
		if len(post) < 2700 and self.limited == 0:
			self.sendCmd("bmsg", "t12r", "<n"+self.nColor+"/><f x"+self.fSize+self.fColor+"=\""+self.fFace+"\">"+post)

	def sendCmd(self, *args, firstcmd = False):
		'''Send data to socket'''
		args = [str(i) for i in args]
		if not firstcmd:
			self.wqueue.put((self.chSocket, bytes(':'.join(args)+"\r\n\x00", "utf-8")))
		else:
			self.wqueue.put((self.chSocket, bytes(':'.join(args)+"\x00", "utf-8")))

	def getBanList(self):
		'''Retreive ban list'''
		self.blist = list()
		self.sendCmd("blocklist", "block", "", "next", "500")

	def getLastPost(self, match, data = "user"):
		'''Retreive last post object from user'''
		try:
			post = sorted([x for x in list(self.pArray.values()) if getattr(x, data) == match], key=lambda x: x.time, reverse=True)[0]
		except:
			post = None
		return post

	def login(self, user, password = None):
		'''Login to an account or as a temporary user or anon'''
		if user and password:
			self.sendCmd("blogin", user, password) #user
			self.user = user
		elif user:
			self.user = "#" + user
			self.sendCmd("blogin", user) #temporary user
		else:
			self.sendCmd("blogin")

	def logout(self):
		'''Log's out of an account'''
		self.sendCmd("blogout")

	def enableBg(self):
		'''Enables background'''
		self.sendCmd("getpremium", "1")

	def disableBg(self):
		'''Disables background'''
		self.sendCmd("msgbg", "0")

	def enableVr(self):
		'''Enable group's VR on each post'''
		self.sendCmd("msgmedia", "1")

	def disableVr(self):
		'''Disable group's VR on each post'''
		self.sendCmd("msgmedia", "0")

	def setNameColor(self, nColor):
		'''Set's a user's name color'''
		self.nColor = nColor

	def setFontColor(self, fColor):
		'''Set's a user's font color'''
		self.fColor = fColor

	def setFontSize(self, fSize):
		'''Set's a user's font size'''
		fSize = str(fSize)
		if 9 <= int(fSize) <= 22:
			if len(fSize) == 1:
				fSize = "0"+fSize
			self.fSize = fSize

	def setFontFace(self, fFace):
		'''Set's a user's font face'''
		self.fFace = fFace

	def getAuth(self, user):
		'''return the users group level 2 = owner 1 = mod 0 = user'''
		if user == self.owner:
			return 2
		if user in self.mods:
			return 1
		else:
			return 0

	def getBan(self, user):
		'''Get banned object for a user'''
		banned = [x for x in self.blist if x.user == user]
		if banned:
			return banned[0]
		else:
			return None

	def dlPost(self, post):
		'''delete a user's post'''
		self.sendCmd("delmsg", post.pid)

	def dlUser(self, user):
		'''Delete all of a user's posts'''
		post = self.getLastPost(user)
		unid = None
		if post:
			unid = post.unid
		if unid:
			if post.user[0] in ["!","#"]:
				self.sendCmd("delallmsg", unid, post.ip, "")
			else:
				self.sendCmd("delallmsg", unid, post.ip, post.user)

	def ban(self, user):
		'''Ban a user'''
		unid = None
		ip = None
		try:
			unid = self.getLastPost(user).unid
			ip = self.getLastPost(user).ip
		except:
			pass
		if unid and ip:
			if user[0] in ['#', '!']:
				self.sendCmd("block", unid, ip, "")
			else:
				self.sendCmd("block", unid, ip, user)
		self.getBanList()

	def flag(self, user):
		'''Flag a user'''
		pid = self.getLastPost(user).pid
		self.sendCmd("g_flag", pid)

	def unban(self, user):
		'''Unban a user'''
		banned = [x for x in self.blist if x.user == user]
		if banned:
			self.sendCmd("removeblock", banned[0].unid, banned[0].ip, banned[0].user)
			self.getBanList()

	def setMod(self, mod):
		'''Add's a group moderator'''
		self.sendCmd("addmod", mod)

	def eraseMod(self, mod):
		'''Removes a group moderator'''
		self.sendCmd("removemod", mod)

	def clearGroup(self):
		'''Deletes all messages'''
		if self.user == self.owner:
			self.sendCmd("clearall")
		else: #;D
			pArray = self.pArray.values()
			for user in list(set([x.user for x in pArray])):
				post = self.getLastPost(user)
				if post and hasattr(post, "unid"):
					self.dlUser(user)

class Digest(object):

	def __init__(self, manager):
		self.manager = manager

	def digest(self, group, raw):
		bites = raw.decode("latin-1").rstrip("\r\n").split(":")
		if hasattr(self, bites[0]):
			getattr(self, bites[0])(group, bites)

	def call(self, function, *args):
		if hasattr(self.manager, "recv"+function):
			getattr(self.manager, "recv"+function)(*args)

	def denied(self, group, bites):
		self.manager.removeGroup(group)

	def ok(self, group, bites):
		if bites[3] != 'M':
			self.manager.removeGroup(group.name)
		else:
			group.owner = bites[1]
			group.time = bites[5]
			group.ip = bites[6]
			group.mods = [x.split(',')[0] for x in bites[7].split(';')]
			group.mods.sort()

	def inited(self, group, bites):
		group.sendCmd("blocklist", "block", "", "next", "500")
		group.sendCmd("g_participants", "start")
		group.sendCmd("getbannedwords")
		group.sendCmd("getratelimit")
		if group.nomore == False:
			group.sendCmd("get_more", "50", "0")
		self.call(bites[0], group)

	def nomore(self, group, bites):
		group.nomore = True
		self.call(bites[0], group)

	def gotmore(self, group, bites):
		self.call(bites[0], group)
		time.sleep(1)
		if group.nomore == False:
			group.sendCmd("get_more", "50", str(int(bites[1])+1))



	def premium(self, group, bites):
		if int(bites[2]) > time.time():
			group.sendCmd("msgbg", "1")

	def g_participants(self, group, bites):
		pl = ":".join(bites[1:]).split(";")
		for p in pl:
			p = p.split(":")[:-1]
			if p[-2] != "None" and p[-1] == "None":
				group.users.append(p[-2].lower())
				group.uArray[p[-3]] = p[-2].lower()
		group.users.sort()

	def blocklist(self, group, bites):
		if bites[1]:
			blklist = (":".join(bites[1:])).split(";")
			for banned in blklist:
				bData = banned.split(":")
				group.blist.append(type("BannedUser", (object,), {"unid": bData[0], "ip": bData[1], "user": bData[2], "time": bData[3], "mod": bData[4]}))
			lastTime = group.blist[-1].time
			group.sendCmd("blocklist", "block", lastTime, "next", "500")

	def bw(self, group, bites):
		group.bw = bites[1].split("%2C")

	def participant(self, group, bites):
		bit = bites[1]
		uid = bites[3]
		if bites[1] == '0':
			user = bites[4].lower()
			if bites[4] != "None" and bites[4].lower() in group.users:
				group.users.remove(user)
			group.users.sort()
		if bites[1] == '1':
			user = bites[4].lower()
			if bites[-4] != "None":
				group.users.append(user)
			group.users.sort()
		if bites[1] == '2':
			user = group.uArray[uid].lower() if uid.lower() in group.uArray and bites[4] == "None" else bites[4].lower()
			if (bites[4] == "None") and (user in group.users):
				group.users.remove(user.lower())
				user = group.uArray[uid]
				del group.uArray[uid]
			if (bites[4] != "None") and (user not in group.users):
				group.users.append(user)
				group.uArray[uid] = user
			group.users.sort()
		self.call(bites[0], group, bit, user, uid)

	def ratelimited(self, group, bites):
		group.limit = int(bites[1])

	def getratelimit(self, group, bites):
		group.limit = int(bites[1])
		group.limited = int(bites[2])

	def b(self, group, bites):
		tag = re.search("(<n([a-fA-F0-9]{1}|[a-fA-F0-9]{3}|[a-fA-F0-9]{4}|[a-fA-F0-9]{6})\/>)?(<f x([\d]{0}|[\d]{2})([0-9a-fA-F]{1}|[0-9a-fA-F]{3}|[0-9a-fA-F]{6})=\"([0-9a-zA-Z]*)\">)?", bites[10])
		if tag:
			nColor = tag.group(1) if tag.group(1) else ""
			fSize = tag.group(2) if tag.group(2) else ""
			fColor = tag.group(3) if tag.group(3) else ""
			fFace = tag.group(4) if tag.group(4) else "0"
		else:
			nColor = ""
			fSize = ""
			fColor = ""
			fFace = "0"
		group.pArray[bites[6]] = type("Post", (object,), {"group": group, "time": bites[1], "user": bites[2].lower() if bites[2] != '' else "#" + bites[3] if bites[3] != '' else "!anon" + Generate.aid(nColor, bites[4]) if nColor else "!anon" , "uid": bites[4], "unid": bites[5], "pnum": bites[6], "ip": bites[7], "post": re.sub("<(.*?)>", "", ":".join(bites[10:])).replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", "\"").replace("&apos;", "'").replace("&#39;", "'").replace("&amp;", "&"), "nColor": nColor, "fSize": fSize, "fFace": fFace, "fColor": fColor})

	def u(self, group, bites):
		post = group.pArray[bites[1]] if group.pArray.get(bites[1]) else None
		if post:
			setattr(post, "pid", bites[2])
			if post.post: #not blank post
				user = post.user
				self.call("Post", group, user, post)
				if post.post[0] == self.manager.prefix:
					auth = group.getAuth(post.user)
					cmd = post.post.split()[0][1:].lower()
					args = post.post.split()[1:]
					self.call("Command", group, user, auth, post, cmd, args)

	def i(self, group, bites):
		tag = re.search("(<n([a-fA-F0-9]{1}|[a-fA-F0-9]{3}|[a-fA-F0-9]{4}|[a-fA-F0-9]{6})\/>)?(<f x([\d]{0}|[\d]{2})([0-9a-fA-F]{1}|[0-9a-fA-F]{3}|[0-9a-fA-F]{6})=\"([0-9a-zA-Z]*)\">)?", bites[10])
		if tag:
			nColor = tag.group(1) or ""
			fSize = tag.group(2) or ""
			fColor = tag.group(3) or ""
			fFace = tag.group(4) or "0"
		else:
			nColor = ""
			fSize = ""
			fColor = ""
			fFace = "0"
		group.pArray[bites[6]] = type("Post", (object,), {"group": group, "time": bites[1], "user": bites[2].lower() if bites[2] != '' else "#" + bites[3] if bites[3] != '' else "!anon" + Generate.aid(nColor, bites[4]) if nColor else "!anon" , "uid": bites[4], "unid": bites[5], "pid": bites[6], "ip": bites[7], "post": re.sub("<(.*?)>", "", ":".join(bites[10:])).replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", "\"").replace("&apos;", "'").replace("&#39;", "'").replace("&amp;", "&"), "nColor": nColor, "fSize": fSize, "fFace": fFace, "fColor": fColor})

	def n(self, group, bites):
		group.unum = bites[1]

	def mods(self, group, bites):
		modded = None
		mlist = [x.split(',')[0] for x in bites[1:]]
		mod = ""
		if len(mlist) < len(group.mods):
			mod = [m for m in group.mods if m not in mlist][0]
			group.mods.remove(mod)
			group.mods.sort()
			modded = False
		elif len(mlist) > len(group.mods):
			mod = [m for m in mlist if m not in group.mods][0]
			group.mods.append(mod)
			group.mods.sort()
			modded = True
		self.call(bites[0], group, modded, mod)

	def deleteall(self, group, bites):
		for pid in bites[1:]:
			deleted = group.getLastPost(pid, "pid")
			if deleted:
				if hasattr(deleted, "pnum"):
					del group.pArray[deleted.pnum]
				else:
					del group.pArray[deleted.pid]
				self.call(bites[0], group, deleted)

	def delete(self, group, bites):
		deleted = group.getLastPost(bites[1], "pid")
		if deleted:
			if hasattr(deleted, "pnum"):
				del group.pArray[deleted.pnum]
			else:
				del group.pArray[deleted.pid]
			self.call(bites[0], group, deleted)

	def blocked(self, group, bites):
		group.getBanList()
		mod = bites[4]
		if bites[3]:
			user = bites[3]
			self.call(bites[0], group, user, mod)
		else:
			post = group.getLastPost(bites[1], "unid")
			if post:
				user = post.user
				self.call(bites[0], group, user, mod)

	def unblocked(self, group, bites):
		if group.name == group.user:
			group.bl.remove(bites[1])
		else:
			mod = bites[4]
			if bites[3]:
				user = bites[3]
				group.getBanList()
				self.call(bites[0], group, user, mod)
			else:
				self.call(bites[0], group, "Non-member", bites[4])

	def logoutok(self, group, bites):
		self.manager.user = "!anon" + Generate.aid(group.nColor, group.uid)

	def clearall(self, group, bites):
		if bites[1] == "ok":
			group.pArray = {}

	def kickingoff(self, group, bites):
		self.call(bites[0], group)

	def toofast(self, group, bites):
		self.call(bites[0], group)

	def tb(self, group, bites):
		mins, secs = divmod(int(bites[1]), 60)
		self.call(bites[0], group, mins, secs)

	def show_tb(self, group, bites):
		mins, secs = divmod(int(bites[1]), 60)
		self.call(bites[0], group, mins, secs)

	def OK(self, group, bites):
		group.sendCmd("wl")
		self.call(bites[0], group)

	def wl(self, group, bites):
		if len(bites) >= 4:
			for i in range(1, len(bites), 4):
				group.fl.append({"user": bites[i], "time": bites[i+1], "status": bites[i+2]})

	def wladd(self, group, bites):
		group.fl.append({"user": bites[1], "status": bites[2], "time": bites[3]})

	def msg(self, group, bites):
		user = bites[1]
		pm = group.cleanPM(":".join(bites[6:]))
		self.call(bites[0], group, user, pm)

	def msgoff(self, group, bites):
		user = bites[1]
		pm = group.cleanPM(":".join(bites[6:]))
		self.call(bites[0], group, user, pm)

################################
#Connections Manager
#Handles: New Connections and Connection data
################################

class ConnectionManager(object):

	def __init__(self, user, password, pm):
		self.user = user.lower()
		self.name = self.user
		self.password = password
		self.pm = pm
		self.cArray = list()
		self.eArray = dict()
		self.eArray[self.name] = list()
		self.groups = list()
		self.wbuf = b""
		self.uid = str(int(random.randrange(10 ** 15, (10 ** 16) - 1)))
		self.prefix = None
		self.acid = Digest(self)
		self.connected = any([x.connected for x in self.cArray])
		self.sockmanager = sock.SockManager(self)

	def stop(self):
		'''disconnect from all groups'''
		g = list(self.cArray)
		for group in g:
			self.removeGroup(group.name)

	def addGroup(self, group):
		'''Join a group'''
		if not self.getGroup(group) in self.cArray:
			group = Group(self, group, self.user, self.password, self.uid, self.pm)
			self.cArray.append(group)
			if group.name != self.user:
				self.groups.append(group.name)

	def removeGroup(self, group):
		'''Leave a group'''
		group = self.getGroup(group)
		if group in self.cArray:
			group.connected = False
			self.cArray.remove(group)
			if group.name != self.user:
				self.groups.remove(group.name)
			for event in self.eArray[group.name]:
				event.cancel()
			group.chSocket.close()
			self.recvRemove(group)
		if not self.cArray:
			self.connected = False

	def getEvent(self, group, name):
		event = [x for x in self.eArray[group.name] if x.name == name]
		return event[0] if event else None

	def getGroup(self, group):
		'''Get a group object'''
		group = [g for g in self.cArray if g.name == group]
		if group:
			return group[0]

	def getUser(self, user):
		'''Get all groups a user is in'''
		groups = list()
		for group in self.cArray:
			if hasattr(group, "users"):
				if user.lower() in group.users:
					groups.append(group.name)
		if groups:
			return groups
		else:
			return None

	def sendPM(self, user, pm):
		'''Send's a PM'''
		group = self.getGroup(self.user)
		self.sendCmd("msg", user, "<n"+group.nColor+"/><m v=\"1\"><g xs0=\"0\"><g x"+group.fSize+"s"+group.fColor+"=\""+group.fFace+"\">"+pm+"</g></g></m>")

	def sendCmd(self, *args):
		'''Send data to socket'''
		group = self.getGroup(self.user)
		group.wqueue.put((group.chSocket, bytes(':'.join([str(i) for i in args])+"\r\n\x00", "utf-8")))

	def manage(self, group, data):
		buffer = data.split(b"\x00")
		for raw in buffer:
			if raw:
				self.acid.digest(group, raw)

	def main(self):
		self.start()
		if self.pm:
			self.addGroup(self.user)
		while self.connected:
			try:
				time.sleep(1)
			except KeyboardInterrupt:
				self.stop()
				exit(0)
