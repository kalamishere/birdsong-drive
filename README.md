# Birdsong Drive

A driving map of the San Francisco Bay Area that plays the songs of birds recently seen near the road.

- Map and routes: Mapbox GL JS and the Mapbox Directions API.
- Sightings: eBird API 2.0 (Cornell Lab of Ornithology), refreshed every 6 hours by a GitHub Action.
- Songs and photos: iNaturalist research-grade observations. Each one credits its author in the app.
- Spoken bird names use the voices installed on the visitor's device.
- Game: claim birds you hear ("That's my bird!") for daily points. Rarer birds score more. There's a day streak, a life list, an optional song quiz, and posted speed limits from Mapbox. Speeding gets bird poo on the screen.

## Setup
Two repository secrets are needed:
- `MAPBOX_TOKEN`: a Mapbox public token. Restrict it to this site's URL in your Mapbox account.
- `EBIRD_KEY`: an eBird API key. It is used only inside the Action and never reaches the browser.

To run it locally, serve the folder and open `index.html`. With no `config.js` present, the page asks for both keys and calls eBird directly.
