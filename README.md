# Spotify-Track-Tour-Server
repo for spotify track tour's backend

This server is built using: **Flask**, **Google Firestore**, and deployed using **Heroku**

The server is **stateless** and built to be as RESTful as possible.

Although you could technically call this server's endpoints directly to leverage the algorithms for your own use, I highly recommend running the server locally or using the web app as is.

This is because **the entire thing is running on one heroku dyno** and with one process due to memory limitations (512MB RAM). 

Because of this concurrent users can slow down the user experience drastically (won't crash though).

In the future I hope to move the majority of the code into a seperate worker process to help with concurrency.
