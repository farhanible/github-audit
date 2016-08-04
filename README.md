# github-audit

Github doesn't expose the audit log via the Github API (up until v3)

The Organizational webhook integration is missing a lot of event types and sometimes doesn't report correct information (e.g. collaborators being added to teams)

This project uses Mechanize to automate the collection of the Github Organization audit log.



