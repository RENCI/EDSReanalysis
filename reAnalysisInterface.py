#import ipywidgets as widgets
import base64, hashlib
from ipywidgets import HBox, VBox, Output, HTML, Dropdown, Button, Layout, Label, FileUpload, IntRangeSlider
from IPython.display import display, clear_output, HTML as IHTML
from io import StringIO
from typing import Callable
import pandas as pd
import numpy as np
import utilities as utilities

class DownloadButton(Button):
    """Download button with dynamic content

    The content is generated using a callback when the button is clicked.
    """

    def __init__(self, filename: str, contents: Callable[[], str], **kwargs):
        super().__init__(**kwargs)
        #DownloadButton, self
        self.filename = filename
        self.contents = contents
        self.on_click(self.__on_click)

    def __on_click(self, b):
        contents: bytes = self.contents().encode('utf-8')
        b64 = base64.b64encode(contents)
        payload = b64.decode()
        digest = hashlib.md5(contents).hexdigest()  # bypass browser cache
        id = f'dl_{digest}'

        display(IHTML(f"""
<html>
<body>
<a id="{id}" download="{self.filename}" href="data:text/csv;base64,{payload}" download>
</a>

<script>
(function download() {{
document.getElementById('{id}').click();
}})()
</script>

</body>
</html>
"""))

class demoInterface():
    def __init__(self):
        # Create variable dictionary
        self.vardict={}
        self.vardict['water level']={'filename': 'fort.63_transposed_and_rechunked_1024.nc', 'varname':'zeta'}
        self.vardict['wave height']={'filename': 'swan_HS_transposed_and_rechunked_1024.nc', 'varname':'swan_HS'}
        self.vardict['wave period']={'filename': 'swan_TPS_transposed_and_rechunked_1024.nc', 'varname':'swan_TPS'}
        self.vardict['wave direction']={'filename': 'swan_DIR_transposed_and_rechunked_1024.nc', 'varname':'swan_DIR'}
        
        #Create Styles
        style="""
            <style>
                /* enlarges the default jupyter cell outputs, can revert by Cell->Current Outputs->Clear */
                .container { width:1020 !important; } 
                
                /* styles for output widgets */
                .o2 {width:400px; border:1px solid #ddd}
                .o3 {width:400px; border:1px solid #ddd}
                .o4 {width:400px; border:1px solid #ddd}
                .o5 {width:400px; border:1px solid #ddd}
                .o6 {width:400px; border:1px solid #ddd}
                
                .style_coords {background-color:#fafaaa}
                .style_data {background-color:#faaafa}
                .style_meta {background-color:#aab3fa}
                .style_excluded {background-color:#faaab6}
            </style>
        """

        # Add style to HTML
        display(HTML(style))
        
        #Create interface sections
        self.o1 = Output(layout=Layout(width='400px'))        
        self.o2 = Output() 
        self.o2.add_class('o2')
        self.o3 = Output()
        self.o3.add_class('o3')
        self.o4 = Output()
        self.o4.add_class('o4')
        self.o5 = Output()
        self.o5.add_class('o5')
        self.o6 = Output()
        self.o6.add_class('o6')

        # Combine interace sections, using VBox, and HBox, to scene and display
        scene = VBox([self.o1,
                      HBox([self.o2, self.o3, self.o4]),
                      HBox([self.o5, self.o6])
                     ])
        display(scene)
    
        # Add title to header section o1
        with self.o1:
            display(HTML('<h2>Demo Interface</h2>'))

        # Add the fileuploader, var_selector, year_selector, and btn to menu section o2
        with self.o2:
            self.fileuploader = FileUpload(accept='', multiple=False)
            self.var_selector = Dropdown(description='Variable', options=['water level', 'wave height', 'wave period', 'wave direction'])
            self.year_selector=IntRangeSlider(value=[1979, 2021],min=1979,max=2021,step=1,description='Years:',
                                                    disabled=False,continuous_update=False,orientation='horizontal',
                                                    readout=True,readout_format='d')
            self.kmax_selector = Dropdown(description='KMax', options=np.arange(10)+1)
            
            self.btn = Button(description='Submit')
            self.btn.on_click(self.process_submit)
            
            display(self.fileuploader, self.var_selector, self.year_selector, self.kmax_selector, self.btn)

    # Function which is used to process results
    def process_submit(self, b):
        if len(self.fileuploader.value)==0:
            # If fileuploader has no values clear output and print warning message
            with self.o3:
                clear_output()
                print('Please select coordinate file')
            return
        else:
            # If fileloader has values extract coordinates and input to variable sites
            df_geopoints = pd.read_csv(StringIO(list(self.fileuploader.value.values())[0]['content'].decode('utf-8')))
            geopoints = df_geopoints[['lon','lat']].to_numpy()

            # Add df_sites to coordinate output sections o3
            with self.o3:
                clear_output()
                lbl = Label(value=f'There are {len(df_geopoints.index)} coordinate pair(s)')
                lbl.add_class(f'style_coords')
                display(lbl)
                display(df_geopoints)
        
        # Get file name and variable name from vardict using var_selector value
        filename=self.vardict[self.var_selector.value]['filename']
        variable_name=self.vardict[self.var_selector.value]['varname']
        
        # Get year tuple from year_selector value
        year_tuple=self.year_selector.value
        nearest_neighbors=self.kmax_selector.value
        #alt_urlsource = '/Users/jmpmcman/Work/Surge/data/reanalysis/ADCIRC/ERA5/hsofs/%d'

        df_product_data,df_product_metadata,df_excluded = utilities.Combined_multiyear_pipeline(year_tuple=year_tuple,
                                                                                                filename=filename, 
                                                                                                variable_name=variable_name,
                                                                                                geopoints=geopoints,
                                                                                                nearest_neighbors=nearest_neighbors)
        
        # Add product data to output sections o4
        with self.o4:
            clear_output()
            lbl = Label(value=f'There are {len(df_product_data.index)} data records(s)')
            lbl.add_class(f'style_data')
            display(lbl)
            sd = StringIO()
            df_product_data.to_csv(sd)
            display(DownloadButton(filename='data.csv', contents=lambda: f'{sd.getvalue()}', description='Download'))
            display(df_product_data)

        # Add product meta-data to output sections o5
        with self.o5:
            clear_output()
            lbl = Label(value=f'There are {len(df_product_metadata.index)} meta records(s)')
            lbl.add_class(f'style_meta')
            display(lbl)
            sm = StringIO()
            df_product_metadata.to_csv(sm)
            display(DownloadButton(filename='meta.csv', contents=lambda: f'{sm.getvalue()}', description='Download'))
            display(df_product_metadata)
            
        # Add excluded product data to output sections o4
        with self.o6:
            clear_output()
            lbl = Label(value=f'There are {len(df_excluded.index)} data records(s) that have been excluded')
            lbl.add_class(f'style_excluded')
            display(lbl)
            se = StringIO()
            df_excluded.to_csv(se)
            display(DownloadButton(filename='excluded_geopoints.csv', contents=lambda: f'{se.getvalue()}', description='Download'))
            display(df_excluded)
