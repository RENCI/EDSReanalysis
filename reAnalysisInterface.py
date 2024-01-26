'''
MIT License

Copyright (c) 2022, Renaissance Computing Institute

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import base64, hashlib, sys
from ipywidgets import HBox, VBox, Output, HTML, Dropdown, Button, Layout, Label, FileUpload, IntRangeSlider, Text, ToggleButtons
from IPython.display import display, FileLink, clear_output, HTML as IHTML
from collections import namedtuple
from io import StringIO
from contextlib import redirect_stdout
from typing import Callable
from html import escape
import pandas as pd
import numpy as np
import time
import utilities as utilities

Kmax=utilities.Kmax
Ymin=utilities.Ymin
Ymax=utilities.Ymax
print(f'demoInterface:Ymin, Ymax = {Ymin,Ymax}')

dataurl=utilities.urldirformat
print(f'demoInterface:urldirformat = {dataurl}')

fileext=utilities.fileext
print(f'demoInterface:fileext = {fileext}')
        
# Function that downloads DataFrame to CSV file, using RAM.
def create_download_link(df, filename, title = "Download CSV file using RAM"):
    csv = df.to_csv()
    b64 = base64.b64encode(csv.encode())
    payload = b64.decode()
    html = '<a download="{filename}" href="data:text/csv;base64,{payload}" target="_blank">{title}</a>'
    html = html.format(payload=payload,title=title,filename=filename)
    return IHTML(html)

# Function that downloads existing CSV file, that was saved in the process_submit function.
class DownloadFileLink(FileLink):
    html_link_str = "<a href='{link}' download={file_name}>{link_text}</a>"

    def __init__(self, path, file_name=None, link_text=None, *args, **kwargs):
        super(DownloadFileLink, self).__init__(path, *args, **kwargs)

        self.file_name = file_name or os.path.split(path)[1]
        self.link_text = link_text or self.file_name

    def _format_path(self):
        fp = ''.join([self.url_prefix, escape(self.path)])
        return ''.join([self.result_html_prefix,
                        self.html_link_str.format(link=fp, file_name=self.file_name, link_text=self.link_text),
                        self.result_html_suffix])

class demoInterface():
    def __init__(self):
        # Create variable dictionary
        self.vardict={}
        self.vardict['Water Level']        = {'filename': 'fort.63'+fileext,     'varname':'zeta'}
        self.vardict['Wave Height']        = {'filename': 'swan_HS.63'+fileext,  'varname':'swan_HS'}
        self.vardict['Wave Period']        = {'filename': 'swan_TPS.63'+fileext, 'varname':'swan_TPS'}
        self.vardict['Wave Direction']     = {'filename': 'swan_DIR.63'+fileext, 'varname':'swan_DIR'}
        self.vardict['Dynamic Correction'] = {'filename': 'dynamicWaterlevelCorrection.63'+fileext,   'varname':'dynamicWaterlevelCorrection'}
        
        #Create Styles
        style="""
            <style>
                /* enlarges the default jupyter cell outputs, can revert by Cell->Current Outputs->Clear */
                .container { width:1020 !important; } 
                
                /* styles for output widgets */
                .o2 {width:400px; border:2px solid #000}
                .o3 {width:400px; border:2px solid #000}
                .o4 {width:400px; border:2px solid #000}
                .o5 {width:400px; border:2px solid #000}
                .o6 {width:400px; border:2px solid #000}
                .o7 {width:400px; border:2px solid #000}
                
                .style_coords {background-color:#fafaaa}
                .style_data {background-color:#faaafa}
                .style_meta {background-color:#aab3fa}
                .style_excluded {background-color:#faaab6}
            </style>
        """

        # Add style to HTML
        display(HTML(style))
        
        #Create interface sections
        self.o1 = Output(layout=Layout(width='1210px',  border='2px solid #000'))        
        self.o8 = Output(layout=Layout(width='1210px',  border='2px solid #000'))        
        self.o9 = Output(layout=Layout(width='1210px',  border='2px solid #000'))        
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
        self.o7 = Output()
        self.o7.add_class('o7')

        # Combine interface sections, using VBox and HBox, to scene and display
        scene = VBox([self.o1,self.o8,self.o9,
                      HBox([self.o2, self.o3, self.o4]),
                      HBox([self.o5, self.o6, self.o7])
                     ])
        display(scene)
    
        # Add title to header section o1
        with self.o1:
            display(HTML('<center><h2>Reanalysis V2 Timeseries Extractor Demonstrator</h2></center>'))
            
        with self.o8:
            self.dataurl=Text(value=dataurl,
                                  placeholder='',
                                  description='Data Url:',
                                  disabled=False)
            self.dataurl.layout = Layout(width='1000px')
            display(self.dataurl)
            
#         with self.o8:
#             self.dataurl=Text(value=dataurl,
#                                   placeholder='',
#                                   description='Data Url:',
#                                   disabled=False)
#             self.dataurl.layout = Layout(width='550px')
#             display(self.dataurl)
             
        # Add the fileuploader, var_selector, year_selector, and btn to menu section o2
        with self.o2:
            display(HTML('<h3>User Inputs</h3>'))
            self.fileuploader = FileUpload(accept='', multiple=False, description='Point File Upload:')
            self.fileuploader.layout = Layout(width='50%')
            # self.var_selector = Dropdown(description='Variable:', 
            #                              options=['water level', 'wave height', 'wave period', 'wave direction', 'offset'])
            self.var_selector = ToggleButtons(
                                #options=['Water Level', 'Wave Height', 'Wave Period', 'Wave Direction', 'Dynamic Correction'],
                                options=['Water Level', 'Wave Height', 'Dynamic Correction'],
                                #options=['Water Level'],
                                description='Variable:',
                                disabled=False,
                                button_style='', # 'success', 'info', 'warning', 'danger' or ''
                                #tooltips=['Description of slow', 'Description of regular', 'Description of fast'],
                                #icons=['check'] * 3
            )
            
            self.year_selector=IntRangeSlider(value=[Ymin, Ymin],
                                              min=Ymin,
                                              max=Ymax,
                                              step=1,
                                              description='Years:',
                                              disabled=False,
                                              continuous_update=False,
                                              orientation='horizontal',
                                              readout=True,readout_format='d')
            #self.year_selector.layout = Layout(width='50%')

            
            self.btn = Button(description='Submit')
            self.btn.style.button_color = 'lightgreen'

            self.outfilename=Text(value='data.csv',
                                  placeholder='data.csv',
                                  description='Output Filename:',
                                  disabled=False)
            
            self.btn.on_click(self.process_submit)
            
            display(self.fileuploader, self.var_selector, self.year_selector, self.outfilename, self.btn)

    # set the output filename according to input selections
    # temp=self.var_selector.value
    # y0=year_selector.value[0]
    # y1=self.year_selector.value[1]
    # self.outfilename.value=f'{temp}_{y0}_{y1}.csv'
            
    # Function which is used to process results    
    def process_submit(self, b):
        if len(self.fileuploader.value)==0:
            # If fileuploader has no values clear output and print warning message
            with self.o3:
                clear_output()
                print('Please upload a file of lon,lat coordinates.')
            return
        else:
            # If fileloader has values extract coordinates and input to variable sites
            df_points = pd.read_csv(StringIO(list(self.fileuploader.value.values())[0]['content'].decode('utf-8')))
            points = df_points[['lon','lat']].to_numpy()

            # Add df_sites to coordinate output sections o3
            with self.o3:
                clear_output()
                display(HTML('<h4>List of Stations Uploaded</h4>'))
                lbl = Label(value=f'There are {len(df_points.index)} coordinate pair(s)')
                lbl.add_class(f'style_coords')
                display(lbl)
                display(df_points)
                
            with self.o4:
                display(HTML('<h2>Diagnostics:</h2>'))
                display(HTML('<h4>Executing extraction pipeline...</h4>'))

        # Clear output of frames before running Combined_multiyear_pipeline 
        self.o4.clear_output()
        self.o5.clear_output()
        self.o6.clear_output()
        self.o7.clear_output()
    
        # Get file name and variable name from vardict using var_selector value
        filename=self.vardict[self.var_selector.value]['filename']
        variable_name=self.vardict[self.var_selector.value]['varname']
        
        # Get year tuple from year_selector value
        year_tuple=self.year_selector.value

        # Create variable to output print statements from utilities.Combined_multiyear_pipeline
        po = StringIO()

        dataurl=self.dataurl.value
        with self.o4:
            display(dataurl)
            
        # With redirect_stdout run utilities.Combined_multiyear_pipeline 
        with redirect_stdout(po):
            start_time=time.time()
            self.df_product_data,self.df_product_metadata,self.df_excluded = utilities.Combined_multiyear_pipeline(year_tuple=year_tuple,
                                                                                                                   filename=filename, 
                                                                                                                   variable_name=variable_name,
                                                                                                                   geopoints=points,
                                                                                                                   nearest_neighbors=Kmax,
                                                                                                                   alt_urlsource=dataurl)
            end_time=time.time()


        # Save df_product_data DataFrame to data.csv, so it can be downloaded using DownloadFileLink.
        self.df_product_data.to_csv(self.outfilename.value) 

        # Output print statements from utilities.Combined_multiyear_pipeline to data frame
        with self.o4:
            clear_output()
            display(HTML('<h4>Diagnostics</h4>'))
            display(po.getvalue())
            lbl = Label(value=f'{len(df_points.index)} points and {year_tuple[1]-year_tuple[0]+1} years took {end_time-start_time:.1f} secs.')
            lbl.add_class(f'style_data')
            display(lbl)
                        
        # Add product data to output sections o5
        with self.o5:
            clear_output()
            display(HTML('<h4>Data Extracted for Stations</h4>'))
            lbl = Label(value=f'There are {len(self.df_product_data.index)} data records(s)')
            lbl.add_class(f'style_data')
            display(lbl)
            DownloadFileLinkInfo = namedtuple('DownloadFileLinkInfo', ['path', 'file_name', 'link_text'])
            dfs = DownloadFileLinkInfo('data.csv', 'data.csv', 'Download CSV file, using saved file')
            display(DownloadFileLink(dfs.path, file_name=dfs.file_name, link_text=dfs.link_text))
            display(create_download_link(self.df_product_data, 'data.csv'))
            display(self.df_product_data)
            
         # Add product meta-data to output sections o6
        with self.o6:
            clear_output()
            display(HTML('<h4>Meta Data</h4>'))
            lbl = Label(value=f'There are {len(self.df_product_metadata.index)} meta records(s)')
            lbl.add_class(f'style_meta')
            display(lbl)
            sm = StringIO()
            self.df_product_metadata.to_csv(sm)
            display(create_download_link(self.df_product_metadata, 'meta.csv'))
            display(self.df_product_metadata)
            
        # Add excluded product data to output sections o7
        with self.o7:
            clear_output()
            display(HTML('<h4>Stations Excluded</h4>'))
            lbl = Label(value=f'There are {len(self.df_excluded.index)} data records(s) that have been excluded')
            lbl.add_class(f'style_excluded')
            display(lbl)
            se = StringIO()
            self.df_excluded.to_csv(se)
            display(create_download_link(self.df_excluded, 'excluded_points.csv'))
            display(self.df_excluded)

