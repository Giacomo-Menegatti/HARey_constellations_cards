import numpy as np
import pandas as pd
import json

from svgpathtools import svg2paths
from svgpath2mpl import parse_path

'''This module deals with loading the stars positions and the constellations information.
    It contains the following functions:
    - load_stars: read the Hipparcos catalogue and return the stars positions and magnitudes
    - load_constellations: read the constellations from the Stellarium file and returns constellation names, ids of the constellations,
        asterisms, helper lines and the stars names

    - load_markers: read the svg files containing the markers and convert them to be used by matplotlib     
    '''

########################################### Loading Stars and constellations ####################################

def load_stars(filename, constellations=None):
    '''Read the Hipparcos data on stars position and magnitude and return all of it in a dataframe. 
    If data on the constellations are present, add them too.'''

    stars_df = pd.read_csv(filename, sep='|',  usecols=[1,3,4,5,37], header = None, na_values=['     ', '       ', '        ','      ', '            '])
    stars_df.columns = ('hip','ra', 'dec', 'magnitude', 'B-V')
    stars_df.set_index('hip', inplace=True)

    # The Hipparcos data contains also ra and dec already in degrees, but some values are Nan
    # Convert the sessagesimal values in degrees
    stars_df['ra'] = stars_df['ra'].apply(lambda  s :  np.sum([(f*float(a)) for a,f in zip(s.split(), [15, 1/4, 1/240])]))
    stars_df['dec'] = stars_df['dec'].apply(lambda  s :  np.sum([(f*float(a)) for a,f in zip(s[1:].split(), [1, 1/60, 1/3600])])*(-1)**(s[0]=='-'))
    
    # Drop the stars with no magnitude and no color info
    stars_df = stars_df.dropna(subset='magnitude')
    stars_df = stars_df.dropna(subset='B-V')  

    return stars_df

# Function to read the constellations from the index.json file and the translations from the language.csv file
def load_constellations(constellation_file, names_file, language='COMMON'):
    '''Load the constellations from a STellarium SkyCultures file. One file contains the labels and stars present in each constellation shape, 
        the other contains the name of each constellation for each label. To use a new language, edit the file containing the Names.
    '''
    with open(constellation_file) as json_file:
        data = json.load(json_file)

    constellations = {}
    #names = []

    dummy_len = len('CON modern_ray ')
    for constellation in data['constellations']:
        # the first part of the id is the identificative 'CON modern_ray ' which is removed     
        id = constellation['id'][dummy_len:]
        
        stars = []
        # Join all the stars in the individual lines
        stars = np.unique(np.concatenate(constellation['lines']))
        
        constellations[id] = {'lines':constellation['lines'], 'stars':stars}

        
        # This is used only to create the name file for the first time
        #names.append({'ID':id, 'NAME':constellation['common_name']['english']})

    main_ids = [key for key in constellations.keys() if not key.startswith('.')]
        
    dummy_len = len('AST modern_ray ')
    asterisms = {}  # Asterism
    helpers = {} # Helper lines 
    
    for object in data['asterisms']:
        # the first part of the id is the identificative 'AST modern_ray ' which is removed     
        id = object['id'][dummy_len:]

        # Sace the helper lines and the asterisms
        if id.startswith('HR'):
            helpers[id] = {'lines': object['lines']}
        else:
            asterisms[id] = {'lines':object['lines']}
        
        # This is used only to create the name file for the first time
        #name = asterism['common_name']['english'] if 'common_name' in asterism else ''    
        #names.append({'ID':id, 'NAME':name})
        
    dummy_len = len('HIP ')
    named_stars = [hip[dummy_len:] for hip in data['common_names'].keys()]

    # This is used only to create the name file for the first time
    #star_names_list = [star[0]['english'] for star in data['common_names'].values()]
    #for hip, name in zip(named_stars, star_names_list):
        #names.append({'ID':hip, 'NAME':name})
    #pd.DataFrame.from_dict(names).to_csv('initial_names.csv')

    names = pd.read_csv(names_file)
    names = names.fillna('')
    names = dict(zip(names['ID'], [name.replace('\\n', '\n') for name in names[language]]))
    return constellations, main_ids, asterisms, helpers, named_stars, names

############################# Load Markers #############################à

def load_markers(markers_folder='markers'):
    '''Load the custom svg markers and convert them to be used by matplotlib'''

    #Load empty marker (background of all other markers)
    _, attributes = svg2paths(f'{markers_folder}/empty.svg')
    empty_marker = parse_path(attributes[0]['d'])
    empty_marker.vertices -= (empty_marker.vertices.max(axis=0) - empty_marker.vertices.min(axis=0))/2

    markers = {'empty':empty_marker}
    star_markers = []

    # Cardinal direction markers
    for direction in ['north', 'east', 'south', 'west']:
        _, attributes = svg2paths(f'{markers_folder}/{direction}.svg')
        marker = parse_path(attributes[0]['d'])
        marker.vertices -= (marker.vertices.max(axis=0) - marker.vertices.min(axis=0))/2
        markers[direction]=marker

    # HARey star markers
    for i in range(5):
        _, attributes = svg2paths(f'{markers_folder}/star_marker_{i}.svg')
        star_marker = parse_path(attributes[0]['d'])
        star_marker.vertices -= star_marker.vertices.mean(axis=0)
        star_markers.append(star_marker)

    # The last marker is a simple dot
    star_markers.append('.')

    return markers, star_markers

        