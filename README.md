# Spotify Song Suggestion

Package with tools originally made for supporting my Alexa Skill named **Song Discovery** and available via [Amazon Marketplace](https://www.amazon.com/ZipBomb-Song-Discovery/dp/B07G236PNN/ref=sr_1_1?s=digital-skills&ie=UTF8&qid=1533660700&sr=1-1&keywords=song+discovery). It consists of:

- *random_song.py*: Module that contains functions to make requests to the [Spotify Web API](https://developer.spotify.com/documentation/web-api/) to retrieve pseudo-random obscure songs. The default popularity threshold is 1, but you can enter your own via the command line, as well as a specific genre if wanted.
- *genres.json*: List containing every valid Spotify genre retrieved from [Everynoise.com](http://everynoise.com/everynoise1d.cgi?scope=all&vector=popularity).
---
**Project licensed under the MIT License.**
