
## What is long-polling? 
Long polling (or Comet) is a technique for sending real-time updates to clients without using sockets. ([Wikipedia](https://en.wikipedia.org/wiki/Push_technology#Long_polling).) This helps about keeping less state for user connections (although real-time updates require a stateful approach) and also simplifies code and makes system scaling easier.



## About this project
After doing some research for examples of long-polling in Python, I found no interesting results. So, I got inspired to write some tooling around it myself. However, it turned out to be more challenging than I expected due to my initial assumptions. In my initial assumption, the sender sends a message to a user, but I realized that the user may have multiple online sessions, and all of those sessions should receive all the messages. Anyway, I hope this tool will be helpful and usable to others. So after the first version, I added some load testing and integration testing.

