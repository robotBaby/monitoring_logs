** Consume an actively written-to w3c-formatted HTTP access log (https://en.wikipedia.org/wiki/Common_Log_Format)


Example of a log is 127.0.0.1 user-identifier frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326


** Every 10s, display in the console the sections of the web site with the most hits (a section is defined as being what's before the second '/' in a URL. i.e. the section for "http://my.site.com/pages/create' is "http://my.site.com/pages"), as well as interesting summary statistics on the traffic as a whole.

The simulated sections are

'/js',
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
"/bar"]
'/categories',
'/pages',
'/resources',
'/pages',
'/resources',
'/images',
'/nxmen'

If an URL does not have a section (a section is defined as being what's before the second '/' in a URL.), then the section is made 'root'

You can change the parameters in parameters.cfg

** Make sure a user can keep the console app running and monitor traffic on their machine


generate logs as "pthon logGenerator.py"
monitor logs as "python logMonitor.py"


** Whenever total traffic for the past 2 minutes exceeds a certain number on average, add a message saying that “High traffic generated an alert - hits = {value}, triggered at {time}”
** Whenever the total traffic drops again below that value on average for the past 2 minutes, add another message detailing when the alert recovered


run tests in logTests.py as "python logTest.py"


** Make sure all messages showing when alerting thresholds are crossed remain visible on the page for historical reasons.

Currently the user can scroll up and see old alerts. Also the alert log is written to a file.

** Write a test for the alerting logic

tests in logTest.py


** Explain how you’d improve on this application design

1) The code currently handles only one log file. In practical user applications there would be multiple log files, which the code cannot currently handle. This is a straightforward extension of the program to take in a group of files and create a queue of files to be processed.
Ideally there should be multiple logMonitors that would process one or part of a file. These should be later collected to generate the final statistics. That is to say we should consider distributed design. 

2) The alerts can be classified based on their types, and written to multiple files

3) The code uses ncurses that only runs on unix machines. We can do custom implementation for windows.

4) We can better define a 'section'. That is to say, currently is an URL does not have a second hash, we consider it to be 'root' even though the base URL might be different. 

5) Introducing a warning threshold level to signal approaching the alert threshold level might be benefinical to the generator app.

6) Average hits/min are interesting, but we might also want to record spikes in the access log.

