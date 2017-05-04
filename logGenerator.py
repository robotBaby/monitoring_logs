# Thread object which generates random entries
# and writes to a simulation log to test the LogHandler

from time import sleep
from datetime import datetime
from threading import Thread, enumerate
import random
import configparser


class LogGenerator(Thread):
    """Generates random entries and writes to a simulation log"""

    def __init__(self, logPath, rate):
        """Constructor:
        logPath: path to the log file
        rate: log generation rate in number of log entries per minute"""
        Thread.__init__(self)
        self.logPath = logPath
        # Set to False to stop the generation loop and end the thread (stop())
        self.running = True
        self.ips = ["192.168.0.110", 
        "127.0.0.1", 
        "60.242.26.14", 
        "192.127.0.0",
        '50.18.212.157',
        '50.18.212.223',
        '52.25.214.31',
        '52.26.11.205',
        '52.26.14.11',
        '52.8.19.58',
        '52.8.8.189',
        '54.149.153.72',
        '54.187.182.230',
        '54.187.199.38',
        '54.187.208.163',
        '54.67.48.128',
        '54.67.52.245',
        '54.68.165.206',
        '54.68.183.151',
        '107.23.48.182',
        '107.23.48.232',]
        self.methods = ["GET", "GET", "GET", "POST", "POST", "PUT", "DELETE"]
        self.sections = ['/js',
        '/img',
        '/css',
        '/',
         '/css',
        '/',
       '/load.php',
        "/img", 
        "/captcha", 
        "/css", 
        "/foo", 
        "/foo", 
        "/bar",
        '/categories',
        '/pages',
        '/resources',
        '/pages',
        '/resources',
        '/images',
        '/nxmen']
        self.codes = ["200", "200", "200", "200", "200", "304", "403", "404"]
        self.hosts = ['user-identifier frank', '- -', 'user-identifier -', '- frank']
        self.rate = rate

    def generate_entry(self, entryTime):
        """Returns a random entry string at the time given in parameter
        :param entryTime: Time of the generated entry"""
        # Chooses randomly between predefined ips or a random one
        ip = random.choice([random.choice(self.ips), self.random_ip()])
        method = random.choice(self.methods)
        # Randomize section choose first part as random
        # and then choose if it's a file or if there will be another section
        section = random.choice(self.sections) \
            + random.choice([".html",
                            random.choice(self.sections)+".html"])
        code = random.choice(self.codes)
        size = random.randint(10, 100000)
        host = self.hosts[random.randint(0, 3)]
        return ('%s %s [%s +1000] "%s %s HTTP/1.1" %s %d\n'
                % (ip,
                    host,
                   entryTime.strftime("%d/%b/%Y:%H:%M:%S"),
                   method,
                   section,
                   code,
                   size))

    def write_entry(self, entryTime):
        """Write a random entry to the simulation log file
        :param entryTime: Time of the generated entry"""
        try:
            with open(self.logPath, "a") as generatedLog:
                    generatedLog.write(self.generate_entry(entryTime))
        except:
            print("ERROR: Cannot write to the log file")

    def write(self, entry):
        """Writes pre-written entry given in parameter to simulation log file
        :param entry: Formatted string representing an entry"""
        try:
            with open(self.logPath, "a") as generatedLog:
                    generatedLog.write(entry)
        except:
            print("ERROR: Cannot write to the log file")

    def clear_log(self):
        """Clear simulation log of all entries"""
        try:
            open(self.logPath, "w").close()
        except:
            print("ERROR: Cannot open the log file")

    def random_ip(self):
        """Returns a random IP as a string"""
        return str(random.randint(0, 255)) + "." + str(random.randint(0, 255)) \
            + "." + str(random.randint(0, 255)) + "." \
            + str(random.randint(0, 255))

    def stop(self):
        """Stops the generation loop and thus stop the thread"""
        self.running = False

    def run(self):
        """Main generation loop"""
        while(self.running):
            now = datetime.now()
            self.write_entry(now)
            # Sleep on average during (1/rate*60) seconds
            sleep(random.random()*2/self.rate*60)



if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read("parameters.cfg")
    logPath = str(config.get("Generator", "logPath"))
    generationRate = float(config.get("Generator", "generationRate"))
    LogGenerator = LogGenerator(logPath, generationRate)
    LogGenerator.start()
    while True:
        key = input('Inser q and press ENTER to quit     :')
        if (key == 'q'):
            LogGenerator.stop()
            LogGenerator.join()
            break 


