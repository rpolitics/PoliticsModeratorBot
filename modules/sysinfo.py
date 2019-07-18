from pmb import *

config = get_config()

def cmd_get_sysinfo(uptime):

	to_mb = 1024 * 1024
	to_gb = to_mb * 1024

	out = "```\n"

	ut = (datetime.datetime.now() - uptime).total_seconds()

	days = int(ut // (24 * 3600))
	ut = ut % (24 * 3600)
	hours = "%02i" % (ut // 3600)
	ut %= 3600
	minutes = "%02i" % (ut // 60)

	process = psutil.Process(os.getpid())
	mem = format(process.memory_info().rss / to_mb, '.2f')
	cpu = format(process.cpu_percent(), '.1f')

	out += "{}\nPython: {}\nCPU: {}%\nThreads: {}\nMemory: {}MB\nStart Time: {}\nUptime: {} days, {}:{} \n\n".format(config['bot_name'].upper(), platform.python_version(), cpu, threading.active_count(), mem, uptime.strftime("%Y-%m-%d %H:%M:%S"), days, hours, minutes)

	bt = datetime.datetime.fromtimestamp(psutil.boot_time())
	ut = (datetime.datetime.now() - bt).total_seconds()

	days = int(ut // (24 * 3600))
	ut = ut % (24 * 3600)
	hours = "%02i" % (ut // 3600)
	ut %= 3600
	minutes = "%02i" % (ut // 60)

	cpu = get_cpu_info()
	out += "SYSTEM\nOS: {} {}\nProcessor: {}\nArchitecture: {}\nBoot Time: {}\nUptime: {} days, {}:{}\n\n".format(distro.linux_distribution()[0], distro.linux_distribution()[1], cpu['brand'], cpu['arch'], bt.strftime("%Y-%m-%d %H:%M:%S"), days, hours, minutes)

	cpupercs = psutil.cpu_percent(interval=1, percpu=True)
	cpus = ["[" + str(x+1) + "] " + str(cpupercs[x]) + "%" for x in range(len(cpupercs))]

	out += "CPU\n{}\n[T] {}%\n\n".format('\n'.join(cpus), str(format(sum(cpupercs), '.1f')))

	disk = psutil.disk_usage('/')
	udisk = format(disk.used / to_gb, '.2f')
	pudisk = format((disk.used / disk.total) * 100, '.1f')
	fdisk = format(disk.free / to_gb, '.2f')
	pfdisk = format((disk.free / disk.total) * 100, '.1f')
	tdisk = format(disk.total / to_gb, '.2f')

	out += "DISK\nUsed: {} GB ({}%)\nFree: {} GB ({}%)\nTotal: {} GB\n\n".format(udisk, pudisk, fdisk, pfdisk, tdisk)

	mem = psutil.virtual_memory()
	umem = format(mem.used / to_gb, '.2f')
	pumem = format((mem.used / mem.total) * 100, '.1f')
	fmem = format(mem.available / to_gb, '.2f')
	pfmem = format((mem.available / mem.total) * 100, '.1f')
	tmem = format(mem.total / to_gb, '.2f')

	out += "MEMORY\nUsed: {} GB ({}%)\nFree: {} GB ({}%)\nTotal: {} GB\n\n".format(umem, pumem, fmem, pfmem, tmem)

	'''
	swap = psutil.swap_memory()
	uswap = format(swap.used / to_gb, '.2f')
	puswap = format((swap.used / swap.total) * 100, '.1f')
	fswap = format(swap.free / to_gb, '.2f')
	pfswap = format((swap.free / swap.total) * 100, '.1f')
	tswap = format(swap.total / to_gb, '.2f')

	out += "SWAP\nUsed: {} GB ({}%)\nFree: {} GB ({}%)\nTotal: {} GB\n\n".format(uswap, puswap, fswap, pfswap, tswap)
	'''

	out += "```"

	return out