# streamed
a simple media server for videos
#### [Video Demo](https://www.youtube.com/watch?v=EzZ0E9ARLbg)

# Files - explained

## index.html | style.css

index.html and style.css display the webpage, wich lists the movies and series that the user has.


## data.js

data.js holds the metadata for all the movies and series, so it can be loaded into index.html dynamically.
The structure of a object in data.js looks like this:
```bash
        {
            title: 'a nightmare on elm street',
            path: 'a-nightmare-on-elm-street',

            length: '1h 31m',
            description: 'the movie is about....',

            type: 'movies',
            id: 'M1',
        }
```
## update.bat | main.py

are for creating the content of the data.js, where update.bat just functions as a easy way to start main.py


## thanks.py

prints "no problem" after executing, make sure to always execute it after succesfully debugging something



# License

[MIT](https://choosealicense.com/licenses/mit/)
