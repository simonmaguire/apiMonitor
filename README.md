A tool that will check a few APIs for reservation availability and email any recent cancellations to a list of my friend's.

These reservations are competetive and cancellations are quickly snatched up. So a fast alert is incredibly helpful.

I'm using AWS Lambda functions with a DynamoDB table.

TODO

- The API appears to randomly send a whole month of availability for some of the APIs. I need to catch these occurences and not alert people.
