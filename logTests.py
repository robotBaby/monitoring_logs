# Unit tests that check if the classes and methods are working as intended

import unittest
from logEntry import LogEntry
from logGenerator import LogGenerator
from logMonitor import LogMonitor
from time import sleep
from datetime import datetime
from datetime import timedelta
import os


class TestLogEntry(unittest.TestCase):
    """Tests the LogEntry class"""

    def test_logEntry(self):
        """Tests creation of a LogEntry instance from one line of the log"""
        print("test_logEntry()")
        now = datetime.now()
        now = datetime(now.year,
                       now.month,
                       now.day,
                       now.hour,
                       now.minute,
                       now.second)
        # Truncate current datetime to remove microseconds
        # (for the test to succeed)
        entryLine = '127.0.0.1 - - [%s +1000] "GET /icons/blank.gif HTTP/1.1" \
403 301' % now.strftime("%d/%b/%Y:%H:%M:%S")
        logEntry = LogEntry(entryLine)
        self.assertEqual(logEntry.ip, "127.0.0.1")
        self.assertEqual(logEntry.time, now)
        self.assertEqual(logEntry.method, "GET")
        self.assertEqual(logEntry.section, "icons")
        self.assertEqual(logEntry.size, 301)

    def test_not_formatted_entry(self):
        """Checks that non formatted input are handled correctly"""
        print("test_not_formatted_entry()")
        entryLine = "This is not a log entry!"
        logEntry = LogEntry(entryLine)
        self.assertFalse(logEntry.parsed)


class TestLogGenerator(unittest.TestCase):
    """Test the LogGenerator class"""

    def test_logGenerator(self):
        """Check that the generation process works"""
        print("test_logGenerator()")
        logPath = "tmp.log"
        logGenerator = LogGenerator(logPath, rate=600)
        logGenerator.start()
        sleep(0.5)
        logGenerator.stop()
        logGenerator.join()
        with open(logPath, "r") as generatedLog:
            lines = generatedLog.readlines()
        self.assertTrue(len(lines) > 0)


class TestLogMonitor(unittest.TestCase):
    """Test the LogMonitor class"""

    def setUp(self):
        """Initialization of the tests"""
        # Create temporary log file for testing the methods
        self.logPath = "tmp.log"
        self.generatingRate = 60
        self.logGenerator = LogGenerator(self.logPath, self.generatingRate)
        now = datetime.now()
        # Add a 10 hours old entry
        self.logGenerator.write_entry(now - timedelta(hours=10))
        # Add two entries to the current time
        self.logGenerator.write_entry(now)
        self.logGenerator.write_entry(now)

        # Setup the LogMonitor object prior testing
        self.refreshPeriod = 2
        self.alertThreshold = 20
        self.monitorDuration = 10
        self.logMonitor = LogMonitor(self.logPath,
                                     self.refreshPeriod,
                                     self.alertThreshold,
                                     self.monitorDuration)
        # Disable logMonitor console output for the tests
        self.logMonitor.printStatus = False
        self.logGenerator.printStatus = False

    def test_add_entry(self):
        """Tests adding entries to the logMonitor"""
        print("test_add_logEntry()")
        unparsedEntry = self.logGenerator.generate_entry(datetime.now())
        logEntry = LogEntry(unparsedEntry)
        self.logMonitor.add_entry(logEntry)
        # Check that all the attributes of the entry have been processed
        self.assertEqual(self.logMonitor.log[0], logEntry)
        self.assertEqual(self.logMonitor.hits, 1)
        self.assertEqual(self.logMonitor.size, logEntry.size)
        self.assertEqual(self.logMonitor.sections, {logEntry.section: 1})
        self.assertEqual(self.logMonitor.ips, {logEntry.ip: 1})
        self.assertEqual(self.logMonitor.methods, {logEntry.method: 1})
        self.assertEqual(self.logMonitor.codes, {logEntry.code: 1})
        # Put an entry that is not formatted
        # to check if it's correctly dropped
        logEntry = LogEntry("This is not a formatted entry\n")
        self.logMonitor.add_entry(logEntry)
        self.assertEqual(len(self.logMonitor.log), 1)
        self.assertEqual(self.logMonitor.hits, 1)

    def test_delete_entry(self):
        """Tests deleting entries from the LogMonitor"""
        print("test_delete_logEntry()")
        # Add 2 entries and delete the oldest
        unparsedEntry = self.logGenerator.generate_entry(datetime.now())
        logEntry1 = LogEntry(unparsedEntry)
        unparsedEntry = self.logGenerator.generate_entry(datetime.now())
        logEntry2 = LogEntry(unparsedEntry)

        self.logMonitor.add_entry(logEntry1)
        self.logMonitor.add_entry(logEntry2)
        self.logMonitor.delete_entry()  # logEntry1 should be deleted (oldest)

        # Check that only logEntry2 is left
        self.assertEqual(self.logMonitor.log[0], logEntry2)
        self.assertEqual(self.logMonitor.hits, 1)
        self.assertEqual(self.logMonitor.size, logEntry2.size)
        self.assertEqual(self.logMonitor.sections, {logEntry2.section: 1})
        self.assertEqual(self.logMonitor.ips, {logEntry2.ip: 1})
        self.assertEqual(self.logMonitor.methods, {logEntry2.method: 1})
        self.assertEqual(self.logMonitor.codes, {logEntry2.code: 1})

    def test_read(self):
        """Test that the LogMonitor correctly reads the log
        and creates a corresponding list of LogEntry objects"""
        print("test_read()")
        # Add a non formatted line to the log to check if it's dropped
        self.logGenerator.write("this is not a formatted entry\n")
        self.logMonitor.read()

        # Check that only the two most recent entries have been processed
        self.assertEqual(len(self.logMonitor.log), 2)
        self.assertEqual(self.logMonitor.hits, 2)
        # Check that all entries are of type LogEntry
        for entry in self.logMonitor.log:
            self.assertIsInstance(entry, LogEntry)

    def test_several_reads(self):
        """Test behaviour of LogMonitor when reading several times in a row"""
        print("test_several_reads()")
        self.logMonitor.read()
        # Check that only the two most recententries have been processed
        self.assertEqual(len(self.logMonitor.log), 2)
        # Add a new entry
        self.logGenerator.write_entry(datetime.now())
        self.logMonitor.read()
        # Check that logMonitor has 3 entries in total
        self.assertEqual(len(self.logMonitor.log), 3)

    def test_run(self):
        """Test the main monitoring loop of the LogMonitor"""
        print("test_run()")
        # Start the thread (checks the log every refreshPeriod)
        self.logMonitor.start()
        # Wait a bit so that logMonitor has time to read the log once
        sleep(0.1*self.refreshPeriod)
        updateTime1 = self.logMonitor.lastReadTime
        # Let's wait one and a half refreshPeriod for another read to happen
        sleep(self.refreshPeriod*1.5)
        updateTime2 = self.logMonitor.lastReadTime
        # Time between the 2 reads
        delta = (updateTime2 - updateTime1).total_seconds()
        self.logMonitor.stop()
        self.logMonitor.join()
        # Check delta between two log reads is within a 10% error margin
        # from the specified refreshPeriod
        self.assertTrue(abs((delta-self.refreshPeriod)
                            / self.refreshPeriod) < 0.1)

    def test_drop_old_entries(self):
        """Test the removal of entries older than the monitored period"""
        print("test_drop_old_entries()")
        # Create an old entry object in the log
        oldEntryStr = self.logGenerator.generate_entry(datetime.now()
                                                         - timedelta(hours=10))
        oldEntry = LogEntry(oldEntryStr)
        # Create a recent entry
        newEntryString = self.logGenerator.generate_entry(datetime.now())
        newEntry = LogEntry(newEntryString)
        # Add them manually to the LogMonitor
        self.logMonitor.add_entry(oldEntry)
        self.logMonitor.add_entry(newEntry)
        self.assertEqual(len(self.logMonitor.log), 2)
        self.logMonitor.drop_old_entries()
        # Only one of the entries should be left
        self.assertEqual(len(self.logMonitor.log), 1)
        self.assertEqual(self.logMonitor.hits, 1)

    def test_alert(self):
        """Test alert triggering"""
        print("test_alert()")
        self.logMonitor.refreshPeriod = 2
        self.logMonitor.start()
        self.assertEqual(self.logMonitor.alertStatus, False)
        # Add twice as much entries than the threshold to trigger the alert
        now = datetime.now()
        entryCount = int(2 * self.logMonitor.alertThreshold
                         * self.logMonitor.monitorDuration / 60)
        for i in range(0, entryCount):
            self.logGenerator.write_entry(now)
        # Wait for the LogMonitor to read the log
        sleep(1.5*self.logMonitor.refreshPeriod)
        self.logMonitor.stop()
        self.logMonitor.join()
        self.assertTrue(self.logMonitor.alertStatus)

    def test_end_alert(self):
        """Test the alert ending went traffic went back to normal"""
        print("test_end_alert()")
        # Set time frame of monitoring to 1 second to test faster
        self.logMonitor.monitorDuration = 2
        self.logMonitor.refreshPeriod = 1
        self.logMonitor.start()
        self.assertEqual(self.logMonitor.alertStatus, False)
        # Add twice as much entries than the threshold to trigger the alert
        now = datetime.now()
        entryCount = int(2 * self.logMonitor.alertThreshold
                         * self.logMonitor.monitorDuration / 60)
        for i in range(0, entryCount):
            self.logGenerator.write_entry(now)
        # Wait for the LogMonitor to read the log
        sleep(self.refreshPeriod)
        self.assertTrue(self.logMonitor.alertStatus)
        # Wait for the LogMonitor to remove the entries
        sleep(1.5*self.logMonitor.monitorDuration)
        self.logMonitor.stop()
        self.logMonitor.join()
        self.assertFalse(self.logMonitor.alertStatus)

    def test_summary(self):
        """Test the processing of information contained in the entries"""
        print("test_summary()")
        # Write some predefined entries to the log file
        self.logMonitor.monitorDuration = 2
        now = datetime.now()
        # Truncate current datetime to remove microseconds
        # (for the test to succeed)
        now = datetime(now.year,
                       now.month,
                       now.day,
                       now.hour,
                       now.minute,
                       now.second)
        # Disposition required to satisfy PEP8
        entries = ('127.0.0.1 user-identifier frank [%s +1000] "GET /icons/blank.gif HTTP/1.1" \
200 100\n' % now.strftime("%d/%b/%Y:%H:%M:%S")
                   + '289.8.42.1 - - [%s +1000] "POST /index.html HTTP/1.1" \
200 1000\n' % now.strftime("%d/%b/%Y:%H:%M:%S")
                   + '127.0.0.1 - - [%s +1000] "GET /icons/blank.gif HTTP/1.1" \
200 900\n' % now.strftime("%d/%b/%Y:%H:%M:%S")
                   + '289.8.42.1 user-identifier frank [%s +1000] "GET /css/display.css HTTP/1.1" \
403 4000\n' % now.strftime("%d/%b/%Y:%H:%M:%S")
                   + '127.0.0.1 - - [%s +1000] "GET /index.php HTTP/1.1" \
404 1000\n' % now.strftime("%d/%b/%Y:%H:%M:%S")
                   + '289.8.42.1 user-identifier frank [%s +1000] "POST /icons/blank.gif HTTP/1.1" \
200 9000\n' % now.strftime("%d/%b/%Y:%H:%M:%S")
                   + '127.0.0.1 - - [%s +1000] "GET /icons/blank.gif HTTP/1.1" \
403 4000\n' % now.strftime("%d/%b/%Y:%H:%M:%S"))
        self.logGenerator.clear_log()
        self.logGenerator.write(entries)
        self.logMonitor.read()
        # Check that summary information are correct
        self.assertEqual(self.logMonitor.hits, 7)
        self.assertEqual(self.logMonitor.size, 20000)
        self.assertEqual(self.logMonitor.sections, {"icons": 4,
                                                    "root": 2,
                                                    "css": 1})
        self.assertEqual(self.logMonitor.ips, {"127.0.0.1": 4,
                                               "289.8.42.1": 3})
        self.assertEqual(self.logMonitor.methods, {"GET": 5,
                                                   "POST": 2})
        self.assertEqual(self.logMonitor.codes, {"200": 4,
                                                 "403": 2,
                                                 "404": 1})


def tearDownModule():
    """Deletes the temporary log after all the tests"""
    logPath = "tmp.log"
    if os.path.isfile(logPath):
        os.remove(logPath)

if __name__ == '__main__':
    unittest.main()
