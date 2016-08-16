# github-audit

Github doesn't expose the audit log via the Github API (up until v3)

The Organizational webhook integration is missing a lot of event types and sometimes doesn't report correct information (e.g. collaborators being added to teams)

This project uses Mechanize to automate the collection of the Github Organization audit log.

Set environment variable $log_uri to the HTTP/HTTPS URI where you want to send (HTTP POST) the logs to: 

$ set log_uri="https://endpoint2.collection.sumologic.com/receiver/v1/http/token"

$ export  log_uri


Credentials can be fetched from a config file with the name "config.json" within the working directory.
Format:

{

	"username": "your_username",

	"password": "your_password"

}

Usage Examples:

$ github_audit_export.py -username your_username -password your_password -otp 123456 -org SomeGithubOrg

$ github_audit_export.py -file -otp 123456 -org SomeGithubOrg





