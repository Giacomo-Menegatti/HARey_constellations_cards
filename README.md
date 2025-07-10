# HARey constellations cards
This python module aims to teach people how to recognize constellations by creating a set of flashcards to memorize their shape.

## How this project was born
__HARey__, pen name of [Hans Augusto Reyersbach](https://en.wikipedia.org/wiki/H._A._Rey), was a skilled author and illustrator, mostly known for being the creator, together with his wife Margret, of the _Curious George_ book series. He also took an interest in star charts, and felt that the ball-and-stick constellation diagrams were too abstract, not resembilng at all what they were named after.

<p align="center">
<img src="https://github.com/Giacomo-Menegatti/HARey_constellations_cards/blob/main/images/harey.jpg", height = 250>
</p>

So he redrew the constellations to be as simple as possible but with a shape that recalled their namesakes. This led to the publication of [The Stars: A New Way to See Them](https://en.wikipedia.org/wiki/The_Stars:_A_New_Way_to_See_Them) and his drawings became famous among stargazers, even if some of its figures make use of very faint stars.

This project is my personal homage to his book _Find the Constellations_, which is intended for teaching kids stargazing. In this book I found expecially useful the Memory-like quiz system that presented the constellations with and without the diagram lines, which challenged me to look at the stars and imagine the lines between them. This proved very, very effective when stargazing. 


<p align="center">
<img src="https://images-na.ssl-images-amazon.com/images/I/716tfSmegfL._AC_UL210_SR210,210_.jpg", height=250  >
<img src="https://github.com/Giacomo-Menegatti/HARey_constellations_cards/blob/main/images/stars.jpg", height=250 >
</p>

Thus was born this project: an attempt to create a deck of flashcards that borrowed from H.A.Rey's beautiful drawings: after all, _imitation is the sincerest form of flattering_. 
And what skills I lack in drawing, I hopefully make up in python coding.

### Disclaimer
In no part of this work I made use of copyright protected material. The constellations diagrams data are found in the Stellarium github repository, while the star markers and the cardback images were made by me in [InkScape](https://inkscape.org). The fonts used are free for personal use.

## The HAReyMain module
The __HAReyMain__ module contains the code to display the night sky with H.A.Rey's style. It can make star charts for a given time and place, or maps of the whole sky, or create planispheres. 
It focuses on creating constellation cards because I felt it a useful way to learn and remember images, like the _countries of the world_ flashcards.  

This project is based on the Stellarium [modern_rey](https://github.com/Stellarium/stellarium/tree/master/skycultures/modern_rey) sky culture. [Stellarium](https://stellarium.org/it) is an open source planetarium software that shows the stars as they appear to the naked eye or to a telescope. The sky cultures are different diagrams of the constellations than the modern IAU ones, drawn by past cultures around the world. My project starts from the _index.json_ containing the constellations shapes and the Hipparcos star catalogue. It also uses the free vector graphic software [Inkscape](https://inkscape.org/) for creaning up the images

For a complete example and a (pedantic) explanation, see the __Constellations_memory_demo.ipynb__ notebook. For a detailed explanation into astrolabes and planispheres and how to ready them, read the __Astrolabes.ipynb__ notebook.

## Constellation Flashcards
The `HAReyMain` creates flash cards with the method `plot_card()`. Card sizes are handled by the *card_template.py* module, and three different formats are supported: __poker__ (2.5x3.5 in), __tarot__ (2.75x4.75 in) and __jumbo__ (3.5x5.5 in). 
<p align="center">
  <img src="https://github.com/Giacomo-Menegatti/HARey_constellations_cards/blob/main/images/Ori_bare.png" width="256">
  <img src="https://github.com/Giacomo-Menegatti/HARey_constellations_cards/blob/main/images/Ori_lines_colors.png" width="256">
  <img src="https://github.com/Giacomo-Menegatti/HARey_constellations_cards/blob/main/images/Ori_lines.png" width="256">
</p>

`set_card_template()` and `plot_cardback()` create the back of the card, taking from a black and white image and recoloring it.

<p align="center">
  <img src="https://github.com/Giacomo-Menegatti/HARey_constellations_cards/blob/main/images/Ori_cardback.png" width="256">
  <img src="https://github.com/Giacomo-Menegatti/HARey_constellations_cards/blob/main/images/Orion_back.png" width="256">
</p>

`print_card_set()` creates a set of cards: one constellations with lines, one without lines and two different cardbacks. Thes can be arranged in a pdf file ready to print with `print_and_play()`

## Skyviews

`sky_view` plots the sky visible by an observer at a given time and place

<p align="center">
  <img src="https://github.com/Giacomo-Menegatti/HARey_constellations_cards/blob/main/images/Sky_view.png" width="500">
  
</p>

## Maps of the sky
`HAReyMain` can plot maps of the whole sky. To cover the whole sky sphere, it can plot equatorial maps with Gall stereographic projection, to cover the sky close to the equator, and polar maps to cover the sky near the pole, using either Stereographic projection (with no distortion, but small usable FOV) or Azimuthal projection (with a lot of distorsion far from the center, but can show higher FOV).

<p align="center">
  <img src="https://github.com/Giacomo-Menegatti/HARey_constellations_cards/blob/main/images/Equatorial_map.png" width="800">
  
</p>

## Astrolabes and Planispheres

`HAReyMain` can plot the mask (called _mater_) and the polar map to create a planisphere. It can create both one-sided and two-sided planispheres. For a complete explanation of how to use them, read the _Astrolabe.ipynb_ notebook.

<p align="center">
  <img src="https://github.com/Giacomo-Menegatti/HARey_constellations_cards/blob/main/images/mater_45N.png" width="400">
    <img src="https://github.com/Giacomo-Menegatti/HARey_constellations_cards/blob/main/images/North_polar_map.png" width="400">
  
</p>

## Inkscape Scripts 

When the labels are added to images, they often end up overlapping and being difficult to see. I tried to use the adjustText library to get a better result, but never got a satisfactory plot. For this reason I decided to focus on manually adjusting the labels in InkScape, where I did all the rest of the graphical work. 

This takes advantage of the Simple Inkscape Scripting extension, which enables python programs to create text windows in the svg image. 

Adjusting the labels manually Is done in the following way:
- Save the plot by setting the flag SIS_SCRIPT. This saves the image with no labels and creates a .py file with all the labels inside
- Install the __SIMPLE INKSCAPE SCRIPTING__ extension to InkScape 
- Open the PNG image in Inkscape (the image is saved without labels)
- Inside Inkscape, open Extensions &rarr; Render &rarr; Simple Inkscape Scripting
- Search the right .py script (it is saved with the same name as the image) and click Apply.
The labels will appear with the correct sizes and colors and in the correct places, hopefully requiring only minimal movements and resizing to improve readability.

## Translations
The __names.csv__ file contains the translations used in the module. Right now only IAU names, English (used by HARey in his books) and Italian are supported. New contributions are welcome, please contact me to add a new language.


## Contributing

Contributions are highly welcome. I know my artworks suck, and I would greatly appreciate some help in that sector. Also new ideas and translations may help spread this project around.

## Acknoledgements

Thanks to all who contributed to this project, and my friends whom I pestered continuously for ideas on the artworks and on the colors!

_See you among the stars!_


