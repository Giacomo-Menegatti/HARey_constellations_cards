import numpy as np
import pandas as pd
import json

from svgpathtools import svg2paths
from svgpath2mpl import parse_path

from importlib.resources import files, as_file

"""
This module deals with loading the stars positions and the constellations information.

Contains :
- load_stars: read the Hipparcos catalogue and return the stars positions and magnitudes
- load_constellations: read the constellations from the Stellarium file and returns constellation names, ids of the constellations,
    asterisms, helper lines and the stars names

- load_markers: read the svg files containing the markers and convert them to be used by matplotlib   
"""



def get_file(filename=None, default=''):
    """ Function to handle reading data inside the package. 
    If filenames is not specified, returns the path of the default file inside the package.
    """
    # If the filename is specified, return it directly
    if filename:
        return filename
    # If is not specified, get the file from the package folder
    else:
        return str(files('HARey').joinpath(default))

########################################### Loading Stars and constellations ####################################

def load_hipparcos_stars(filename):
    '''Read the stars coordinates and colors from the whole HIPPARCOS catalogue. This function is not used anymore, 
    but could be useful if someone wants to load the original catalogue.
    '''

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

###### LOAD THE REDUCED HIPPARCOS CATALOGUE ######################à

def load_stars(filename=None):
    """Read the stars coordinates and colors indexes from the reduced HIP catalogue."""

    filename = get_file(filename=filename, default='datafiles/hip_redux.dat')       

    return pd.read_csv(filename, index_col=0)

# Function to read the constellations from the index.json file and the translations from the language.csv file

def load_constellations(index_file = None):
    '''Load the constellations from a Stellarium SkyCultures file. This contains the constellation lines,
       the helper rays and asterisms, and the brighter stars that have their own names.
    '''
    # Get the constellation file. The default one is datafiles/index.json inside the HARey package
    file_name = get_file(index_file, default='datafiles/index.json')

    with open(file_name, 'r') as json_file:
        data = json.load(json_file)

    constellations = {}
    #names = []

    dummy_len = len('CON modern_ray ')
    for constellation in data['constellations']:
        # the first part of the id is the identificative 'CON modern_ray ' which is removed     
        id = constellation['id'][dummy_len:]
        
        stars = []
        # Join all the stars in the individual lines and convert it to a list
        stars = np.unique(np.concatenate(constellation['lines'])).tolist()
        
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

    return constellations, main_ids, asterisms, helpers, named_stars

##### Load Names #######################################################

def load_names(names_file=None, language='IAU-EN'):
    """ Load the object translated names. To add more translations, edit the names.csv file and add it to the github repo. """
    
    # get the names file. The default is datafiles/names.csv inside the HARey package
    names_file = get_file(names_file, default='datafiles/names.csv')

    names = pd.read_csv(names_file)
    # Fill the empty spaces with an empty string     
    names = names.fillna('')
    # Read the names and keep the newline char
    names = dict(zip(names['ID'], [name.replace('\\n', '\n') for name in names[language]]))

    return names

############################# Load Markers #############################à

def load_markers(markers_folder=None):
    '''Load the custom svg markers and convert them to be used by matplotlib'''

    folder_path = get_file(markers_folder, default='markers')

    #Load empty marker (background of all other markers)
    _, attributes = svg2paths(f'{folder_path}/empty.svg')
    empty_marker = parse_path(attributes[0]['d'])
    empty_marker.vertices -= (empty_marker.vertices.max(axis=0) - empty_marker.vertices.min(axis=0))/2

    markers = {'empty':empty_marker}
    star_markers = []

    # Cardinal direction markers
    for direction in ['north', 'east', 'south', 'west']:
        _, attributes = svg2paths(f'{folder_path}/{direction}.svg')
        marker = parse_path(attributes[0]['d'])
        marker.vertices -= (marker.vertices.max(axis=0) - marker.vertices.min(axis=0))/2
        markers[direction]=marker

    # HARey star markers
    for i in range(5):
        _, attributes = svg2paths(f'{folder_path}/star_marker_{i}.svg')
        star_marker = parse_path(attributes[0]['d'])
        star_marker.vertices -= star_marker.vertices.mean(axis=0)
        star_markers.append(star_marker)

    # The last marker is a simple dot
    star_markers.append('.')

    return markers, star_markers
