
- Login to Heroku account

heroku login

- Add a dyno to the web app

heroku ps:scale web=1 --app fmtc


- local DB Login credentials:
username: admin
password: dev password

When you installed YamJam, it created a console script yjlint that you can run from the command line to check your config.yaml files. To lint your config file:

yjlint ~/.yamjam/config.yaml
