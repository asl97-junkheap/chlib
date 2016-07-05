import queue
import threading
import select
import os
import time


class JobManager:
	def __init__(self):
		self.tasks = queue.Queue()
		self.threads = []
		for l in range(5):
			thread = threading.Thread(target=self.job_worker)
			thread.daemon = True
			thread.start()
			self.threads.append(thread)

	def job_worker(self):
		while True:
			func, args, kw = self.tasks.get()
			func(*args, **kw)

	def addJob(self, func, *args, **kw):
		self.tasks.put((func, args, kw))


class SockManager:
	def __init__(self, mgr):
		self.mgr = mgr
		self.write_queue = queue.Queue()
		self.socks = []
		self.sock_to_group = {}
		self.group_to_sock = {}
		self.read_buf = {}
		self.interrupt_pipe_out, self.interrupt_pipe_in = os.pipe()
		self.socks.append(self.interrupt_pipe_out)
		self.jobmanager = JobManager()
		self.read_thread = threading.Thread(target=self.read_worker)
		self.read_thread.daemon = True
		self.read_thread.start()
		self.write_thread = threading.Thread(target=self.write_worker)
		self.write_thread.daemon = True
		self.write_thread.start()

	def read_worker(self):
		last = time.time()
		while True:
			rd, _, _ = select.select(self.socks, [], [])
			for sock in rd:
				if sock == self.interrupt_pipe_out:
					os.read(sock, 1)
					continue
				data = sock.recv(8192)
				group = self.sock_to_group[sock]
				if not data: 
					self.mgr.removeGroup(group)
					continue
				*raws, self.read_buf[sock] = (self.read_buf.get(sock, b'') + data).split(b'\x00')
				for raw in raws:
					if raw:
						self.jobmanager.addJob(self.mgr.acid.digest, group, raw)
			now = time.time()
			dtime = now - last
			if dtime < 0.1:
				time.sleep(0.1-dtime)
			last = now

	def write_worker(self):
		while True:
			sock, data = self.write_queue.get()
			try:
				sock.sendall(data)
			except:
				self.mgr.removeGroup(self.sock_to_group[sock])

	def addSock(self, sock, group):
		wrapped_sock = Sock(self, sock, group)
		self.socks.append(sock)
		self.sock_to_group[sock] = group
		self.group_to_sock[group] = sock
		os.write(self.interrupt_pipe_in, b'x')
		return wrapped_sock

	def remove(self, wrapped_sock):
		self.socks.remove(wrapped_sock.sock)


class Sock:
	def __init__(self, sockmgr, sock, group):
		self.sockmgr = sockmgr
		self.sock = sock
		self.group = group

	def cancel(self):
		self.sockmgr.remove(self)
