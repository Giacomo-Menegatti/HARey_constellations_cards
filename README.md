# HARey constellations cards
This python module aims to teach people about constellations by creating a set of flashcards that will be useful to learn to recognize the constellations in the night sky.

## How this idea was born
HARey, pen name of [Hans Augusto Reyersbach](https://en.wikipedia.org/wiki/H._A._Rey), was a skilled author and illustrator, mostly known for being the creator, together with his wife Margret, of the _Curious George_ book series. He also took an interest in star charts, and felt that the beautiful and intricate illustrations used at the time made it challenging for people to find the constellation in the night sky.

<p align="center">
<img src="https://github.com/Giacomo-Menegatti/HARey_constellations_cards/blob/main/images/harey.jpg", height = 250>
<img src="https://github.com/Giacomo-Menegatti/HARey_constellations_cards/blob/main/images/george.jpg", height = 250>
</p>

So he redrew the constellations to be as simple as possible, like the balls-and-sticks drawings used by astronomers today, but with a shape that recalled their namesakes. This led to the publication of [The Stars: A New Way to See Them](https://en.wikipedia.org/wiki/The_Stars:_A_New_Way_to_See_Them) and his drawings became famous among stargazers, even if some of its figures make use of very faint stars.

This project is my personal homage to his book _Find the Constellations_, which is intended for teaching kids stargazing. In this book I found expecially useful the Memory-like quiz system that presented the constellations with and without the diagram lines, which challenged me to look at the stars and imagine the lines between them. This proved very, very effective when stargazing. 


<p align="center">
<img src="https://images-na.ssl-images-amazon.com/images/I/716tfSmegfL._AC_UL210_SR210,210_.jpg", height=250  >
<img src="https://github.com/Giacomo-Menegatti/HARey_constellations_cards/blob/main/images/stars.jpg", height=250 >
</p>

Thus was born this project: an attempt to create a deck of flashcards that borrowed from H.A.Rey's beautifil drawings: after all, _Imitation is the sincerest form of flattering_. 
And what skills I lack in drawing, I hopefully make up in python programming.

<p align="center">
  <img src="https://github.com/Giacomo-Menegatti/HARey_constellations_cards/blob/main/images/Orion_lines.png" width="256">
  <img src="https://github.com/Giacomo-Menegatti/HARey_constellations_cards/blob/main/images/Orion_back.png" width="256">
  <img src="https://github.com/Giacomo-Menegatti/HARey_constellations_cards/blob/main/images/Orion_tinted_lines.png" width="256">
</p>

### Disclaimer
In no part of this work I made use of copyright protected material. The constellations diagrams data are found in the Stellarium github repository, while the star markers and the cardback images are my personal work in [InkScape](https://inkscape.org). The fonts used are free for personal use.


## What is inside this module
The __HAReyMain__ module contains the code to display the night sky with H.A.Rey's style. It can make star charts for a given time and place, or maps of the whole sky. It focuses on creating constellation cards because I felt it a useful way to learn and remember images, like the _countries of the world_ flashcards.  

This project is based on the Stellarium [modern_rey](https://github.com/Stellarium/stellarium/tree/master/skycultures/modern_rey) sky culture. [Stellarium](https://stellarium.org/it) is an open source planetarium software that shows the stars as they appear to the naked eye or to a telescope. The sky cultures are different diagrams of the constellations than the modern IAU ones, drawn by past cultures around the world. My project starts from the _index.json_ containing the constellations shapes and the Hipparcos star catalogue. 

For a complete example and a (pedantic) explanation, see the __Constellations_memory_demo.ipynb__ notebook.

## Functions and Methods
The __HAReyMain__ module contains the following methods:
- __load_constellations()__, __load_stars()__, __load_names()__ : load the sky culture diagrams and the Hipparcos catalogue. They are applied automatically when creating a new HARey instance.
- __plot_card()__: plot the sky around a constellation inside a card template. The __BEST_AR__ flag rotates the constellation to better fit the card, otherwise the plot is done with the North side up
- __sky_view()__: plot the visble sky as seen by an observer at a given time and time
- - __polar_map()__: plot the stars around the poles, using a stereographic projection
- __equatorial_map()__: plot the stars close to the equator, using a Gall-stereographic projection
- __set_card_template()__ : set the card template and the cardback image. The template properties are specified in the _card_template.py_ module.
- __plot_cardback()__ : create the cardback for a card by setting the colors and writing the constellation name.
- __print_card_set()__ : create a set of cards for one constellation: the constellation with and without lines and two different cardbacks
- __print_and__play()__ : arrange the images inside a folder inside a pdf ready for printing. 

Most of the methods rely on the same plotting functions, with the following flags common to most of them:
- __CON_LINES__ : Plot the constellation lines
- __ASTERISMS__ : Plot the asterisms lines. Asterisms are patterns of stars that are easy to recognize but not a constellation (e.g. the Big Dipper)
- __HELPERS__ : Plot the helper lines. These are imaginary lines that connect bright stars to each other and make it easier to find features in the sky.
- __CON_NAMES__ : Show the constellation names
- __CON_PARTS__ : Show the constellation parts (e.g. feet, head, ecc.) from the HARey drawings
- __STAR_NAMES__ : Plot the brightest stars names
- __STAR_COLORS__ : Use the Stellarium color map to draw the stars. Otherwise, all stars are drawn white as H.A.Rey did
- __SHOW__ : Show the image (default True)
- __SAVE__ : Save the figure
- __SIS_SCRIPT__ : Creates a Simple InkScape Script to create the labels as interactive text windows.

## Inkscape Scripts
When the labels are added to the image, they often end up overlapping and being difficult to see. I tried to use the adjustText library to get a better result, but never got a satisfactory plot. For this reason I decided to focus on manually adjusting the labels in InkScape, where I did all the rest of the graphical work. This uses the Simple Inkscape Scripting extension, which enables python programs to create text windows in the svg image. 
Importing the labels is done in the following way:
- Install the __SIMPLE INKSCAPE SCRIPTING__ extension to InkScape
- Open the PNG image in Inkscape (the image is saved without labels)
- Inside Inkscape, open Extensions -> Render -> Simple Inkscape Scripting
- Search the right .py script (it is saved with the same name as the image) and click Apply.
The labels will appear with the correct sizes and colors and in the correct places, hopefully requiring only minimal movements and resizing to improve readability.

## Translations
The __names.csv__ file contains the translations used in the module. Right now only IAU names, English (used by HARey in his books) and Italian are supported. New contributions are welcome, please contact me to add a new language.


## Contributing

Contributions are highly welcome. I know my artworks suck, and I would greatly appreciate some help in that sector. Also new ideas and translations may help spread this project around.

## Acknoledgements

Thanks to all who contributed to this project, and my friends whom I pestered continuously for ideas on the artworks and on the colors!

<p align="center">
<img src="https://github.com/Giacomo-Menegatti/HARey_constellations_cards/blob/main/images/Sky_map_with_labels.png" width=600>
</p>


